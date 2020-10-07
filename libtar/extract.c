/*
**  Copyright 1998-2003 University of Illinois Board of Trustees
**  Copyright 1998-2003 Mark D. Roth
**  All rights reserved.
**
**  extract.c - libtar code to extract a file from a tar archive
**
**  Mark D. Roth <roth@uiuc.edu>
**  Campus Information Technologies and Educational Services
**  University of Illinois at Urbana-Champaign
*/

#include <stdio.h>
#include <string.h>
#include <sys/param.h>
#include <sys/types.h>
#include <sys/sysmacros.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>
#include <utime.h>
#include <stdlib.h>
#include <assert.h>
#include <unistd.h>
#include <libgen.h>
#include <pwd.h>
#include <grp.h>
#include <time.h>
#include <limits.h>
#include "libtar.h"
#include "compat.h"

#ifndef MIN
# define MIN(x, y)      (((x) < (y)) ? (x) : (y))
#endif

#ifndef S_IRWXUGO
# define S_IRWXUGO      (S_IRWXU|S_IRWXG|S_IRWXO)
#endif

#ifndef S_IALLUGO
# define S_IALLUGO      (S_ISUID|S_ISGID|S_ISVTX|S_IRWXUGO)
#endif

/* print "ls -l"-like output for the file described by th */
#ifdef LIBTAR_NO_OUTPUT
static inline void th_print_long_ls(const TAR *t, FILE *f) { }
#else /* LIBTAR_NO_OUTPUT */
static void th_print_long_ls(const TAR *t, FILE *f);
#endif /* LIBTAR_NO_OUTPUT */

static const char *th_get_pathname(const TAR *t);
static mode_t th_get_mode(const TAR *t);
static uid_t th_get_uid(const TAR *t);
static gid_t th_get_gid(const TAR *t);

static int tar_extract_dir(TAR *t, const char *realname);
static int tar_extract_hardlink(TAR *t, const char *realname);
static int tar_extract_symlink(TAR *t, const char *realname);
static int tar_extract_chardev(TAR *t, const char *realname);
static int tar_extract_blockdev(TAR *t, const char *realname);
static int tar_extract_fifo(TAR *t, const char *realname);
static int tar_extract_regfile(TAR *t, const char *realname);

static int mkdirs_for(const char *filename)
{
	char *fndup;
	int rc;

	fndup = strdup(filename);
	if (!fndup) {
		errno = ENOMEM;
		return -1;
	}

	rc = mkdirhier(dirname(fndup));

	free(fndup);
	return rc;
}

static int
tar_set_file_perms(TAR *t, const char *realname)
{
#ifndef LIBTAR_NO_SET_FILE_PERMS
	mode_t mode;
	uid_t uid;
	gid_t gid;
	struct utimbuf ut;
	const char *filename;

	filename = (realname ? realname : th_get_pathname(t));
	mode = th_get_mode(t);
	uid = th_get_uid(t);
	gid = th_get_gid(t);
	ut.modtime = ut.actime = th_get_mtime(t);

	/* change owner/group */
	if (geteuid() == 0)
	{
#ifdef HAVE_LCHOWN
		if (lchown(filename, uid, gid) == -1)
		{
# ifdef DEBUG
			fprintf(stderr, "lchown(\"%s\", %d, %d): %s\n",
				filename, uid, gid, strerror(errno));
# endif
			return -1;
		}
#else /* ! HAVE_LCHOWN */
		if (!TH_ISSYM(t) && chown(filename, uid, gid) == -1)
		{
# ifdef DEBUG
			fprintf(stderr, "chown(\"%s\", %d, %d): %s\n",
				filename, uid, gid, strerror(errno));
# endif
			return -1;
		}
#endif /* HAVE_LCHOWN */
	}

	/* change access/modification time */
	if (!TH_ISSYM(t) && utime(filename, &ut) == -1)
	{
#ifdef DEBUG
		perror("utime()");
#endif
		return -1;
	}

	/* change permissions */
	if (!TH_ISSYM(t) && chmod(filename, mode) == -1)
	{
#ifdef DEBUG
		perror("chmod()");
#endif
		return -1;
	}

#endif /* LIBTAR_NO_SET_FILE_PERMS */
	return 0;
}


/* switchboard */
int
tar_extract_file(TAR *t, const char *realname)
{
	int i;
	char *lnp;
	int pathname_len;
	int realname_len;

	if (t->options & TAR_NOOVERWRITE)
	{
		struct stat s;

		if (lstat(realname, &s) == 0 || errno != ENOENT)
		{
			errno = EEXIST;
			return -1;
		}
	}

	if (TH_ISDIR(t))
	{
		i = tar_extract_dir(t, realname);
		if (i == 1)
			i = 0;
	}
	else if (TH_ISLNK(t))
		i = tar_extract_hardlink(t, realname);
	else if (TH_ISSYM(t))
		i = tar_extract_symlink(t, realname);
	else if (TH_ISCHR(t))
		i = tar_extract_chardev(t, realname);
	else if (TH_ISBLK(t))
		i = tar_extract_blockdev(t, realname);
	else if (TH_ISFIFO(t))
		i = tar_extract_fifo(t, realname);
	else /* if (TH_ISREG(t)) */
		i = tar_extract_regfile(t, realname);

	if (i != 0)
		return i;

	i = tar_set_file_perms(t, realname);
	if (i != 0)
		return i;

	pathname_len = strlen(th_get_pathname(t)) + 1;
	realname_len = strlen(realname) + 1;
	lnp = calloc(1, pathname_len + realname_len);
	if (lnp == NULL)
		return -1;
	strcpy(&lnp[0], th_get_pathname(t));
	strcpy(&lnp[pathname_len], realname);

	return 0;
}

static size_t align_up(size_t val, size_t align)
{
	size_t r = val % align;

	if (r) {
		val += align - r;
	}

	return val;
}

/* extract regular file */
/* for regfiles, we need to extract the content blocks as well */
static int
tar_extract_regfile(TAR *t, const char *realname)
{
	mode_t mode;
	size_t size;
	int fdout = -1;
	const char *filename;
	size_t to_read;
	char *buf = NULL;
	ssize_t n;
	int retval = -1;

#ifdef DEBUG
	printf("==> tar_extract_regfile(t=0x%p, realname=\"%s\")\n", t,
	       realname);
#endif

	if (!TH_ISREG(t))
	{
		errno = EINVAL;
		goto out;
	}

	filename = (realname ? realname : th_get_pathname(t));
	mode = th_get_mode(t) & S_IALLUGO;
	size = th_get_size(t);

	if (mkdirs_for(filename) == -1)
		goto out;

#ifdef DEBUG
	printf("  ==> extracting: %s (mode %04o, %zd bytes)\n",
	       filename, mode, size);
#endif
	fdout = open(filename, O_WRONLY | O_CREAT | O_TRUNC | O_BINARY, mode);
	if (fdout == -1)
	{
#ifdef DEBUG
		perror("open()");
#endif
		goto out;
	}

	/* extract the file */

	/* Must always read a multiple of T_BLOCKSIZE bytes */
	to_read = align_up(size, T_BLOCKSIZE);

	buf = malloc(to_read);
	if (!buf) {
		errno = ENOMEM;
		goto out;
	}

	/* Read blocks */
	n = t->type->readfunc(t->context, buf, to_read);
	if (n != to_read) {
# ifdef DEBUG
		fprintf(stderr, "libtar readfunc(%zu) returned %zd\n", to_read, n);
# endif
		errno = EINVAL;
		goto out;
	}

	/* Write blocks to file */
	n = write(fdout, buf, size);
	if (n != size) {
# ifdef DEBUG
		fprintf(stderr, "libtar write(%zu) returned %zd\n", size, n);
# endif
		errno = EINVAL;
		goto out;
	}

	/* Success */
	retval = 0;
#ifdef DEBUG
	printf("### done extracting %s\n", filename);
#endif

out:
	free(buf);
	buf = NULL;

	if (fdout != -1)
		close(fdout);

	return retval;
}


/* hardlink */
static int
tar_extract_hardlink(TAR * t, const char *realname)
{
	const char *filename;
	const char *linktgt = NULL;

	if (!TH_ISLNK(t))
	{
		errno = EINVAL;
		return -1;
	}

	filename = (realname ? realname : th_get_pathname(t));
	if (mkdirs_for(filename) == -1)
		return -1;
	linktgt = th_get_linkname(t);

#ifdef DEBUG
	printf("  ==> extracting: %s (link to %s)\n", filename, linktgt);
#endif
	if (link(linktgt, filename) == -1)
	{
#ifdef DEBUG
		perror("link()");
#endif
		return -1;
	}

	return 0;
}


/* symlink */
static int
tar_extract_symlink(TAR *t, const char *realname)
{
	const char *filename;

	if (!TH_ISSYM(t))
	{
		errno = EINVAL;
		return -1;
	}

	filename = (realname ? realname : th_get_pathname(t));
	if (mkdirs_for(filename) == -1)
		return -1;

	if (unlink(filename) == -1 && errno != ENOENT)
		return -1;

#ifdef DEBUG
	printf("  ==> extracting: %s (symlink to %s)\n",
	       filename, th_get_linkname(t));
#endif
	if (symlink(th_get_linkname(t), filename) == -1)
	{
#ifdef DEBUG
		perror("symlink()");
#endif
		return -1;
	}

	return 0;
}


/* character device */
static int
tar_extract_chardev(TAR *t, const char *realname)
{
	mode_t mode;
	unsigned long devmaj, devmin;
	const char *filename;

	if (!TH_ISCHR(t))
	{
		errno = EINVAL;
		return -1;
	}

	filename = (realname ? realname : th_get_pathname(t));
	mode = th_get_mode(t);
	devmaj = th_get_devmajor(t);
	devmin = th_get_devminor(t);

	if (mkdirs_for(filename) == -1)
		return -1;

#ifdef DEBUG
	printf("  ==> extracting: %s (character device %ld,%ld)\n",
	       filename, devmaj, devmin);
#endif
	if (mknod(filename, mode | S_IFCHR,
		  makedev(devmaj, devmin)) == -1)
	{
#ifdef DEBUG
		perror("mknod()");
#endif
		return -1;
	}

	return 0;
}


/* block device */
static int
tar_extract_blockdev(TAR *t, const char *realname)
{
	mode_t mode;
	unsigned long devmaj, devmin;
	const char *filename;

	if (!TH_ISBLK(t))
	{
		errno = EINVAL;
		return -1;
	}

	filename = (realname ? realname : th_get_pathname(t));
	mode = th_get_mode(t);
	devmaj = th_get_devmajor(t);
	devmin = th_get_devminor(t);

	if (mkdirs_for(filename) == -1)
		return -1;

#ifdef DEBUG
	printf("  ==> extracting: %s (block device %ld,%ld)\n",
	       filename, devmaj, devmin);
#endif
	if (mknod(filename, mode | S_IFBLK,
		  makedev(devmaj, devmin)) == -1)
	{
#ifdef DEBUG
		perror("mknod()");
#endif
		return -1;
	}

	return 0;
}


/* directory */
static int
tar_extract_dir(TAR *t, const char *realname)
{
	mode_t mode;
	const char *filename;

	if (!TH_ISDIR(t))
	{
		errno = EINVAL;
		return -1;
	}

	filename = (realname ? realname : th_get_pathname(t));
	mode = th_get_mode(t);

	if (mkdirs_for(filename) == -1)
		return -1;

#ifdef DEBUG
	printf("  ==> extracting: %s (mode %04o, directory)\n", filename,
	       mode);
#endif
	if (mkdir(filename, mode) == -1)
	{
		if (errno == EEXIST)
		{
			if (chmod(filename, mode) == -1)
			{
#ifdef DEBUG
				perror("chmod()");
#endif
				return -1;
			}
			else
			{
#ifdef DEBUG
				puts("  *** using existing directory");
#endif
				return 1;
			}
		}
		else
		{
#ifdef DEBUG
			perror("mkdir()");
#endif
			return -1;
		}
	}

	return 0;
}


/* FIFO */
static int
tar_extract_fifo(TAR *t, const char *realname)
{
	mode_t mode;
	const char *filename;

	if (!TH_ISFIFO(t))
	{
		errno = EINVAL;
		return -1;
	}

	filename = (realname ? realname : th_get_pathname(t));
	mode = th_get_mode(t);

	if (mkdirs_for(filename) == -1)
		return -1;

#ifdef DEBUG
	printf("  ==> extracting: %s (fifo)\n", filename);
#endif
	if (mkfifo(filename, mode) == -1)
	{
#ifdef DEBUG
		perror("mkfifo()");
#endif
		return -1;
	}

	return 0;
}


int
tar_extract_all(TAR *t, const char *prefix)
{
	const char *filename;
	char buf[MAXPATHLEN];
	int i;

#ifdef DEBUG
	printf("==> tar_extract_all(TAR *t, \"%s\")\n",
	       (prefix ? prefix : "(null)"));
#endif

	while ((i = th_read(t)) == 0)
	{
#ifdef DEBUG
		puts("    tar_extract_all(): calling th_get_pathname()");
#endif
		filename = th_get_pathname(t);
		if (t->options & TAR_VERBOSE)
			th_print_long_ls(t, stderr);
		if (prefix != NULL)
			snprintf(buf, sizeof(buf), "%s/%s", prefix, filename);
		else
			strlcpy(buf, filename, sizeof(buf));
#ifdef DEBUG
		printf("    tar_extract_all(): calling tar_extract_file(t, "
		       "\"%s\")\n", buf);
#endif
		if (tar_extract_file(t, buf) != 0)
			return -1;
	}

	return (i == 1 ? 0 : -1);
}


/******************************************************************************/
/*  output - libtar code to print out tar header blocks */

#ifndef LIBTAR_NO_OUTPUT

#ifndef _POSIX_LOGIN_NAME_MAX
# define _POSIX_LOGIN_NAME_MAX	9
#endif

static void
th_print_long_ls(const TAR *t, FILE *f)
{
	char modestring[12];
	struct passwd *pw;
	struct group *gr;
	uid_t uid;
	gid_t gid;
	char username[_POSIX_LOGIN_NAME_MAX];
	char groupname[_POSIX_LOGIN_NAME_MAX];
	time_t mtime;
	struct tm *mtm;

#ifdef HAVE_STRFTIME
	char timebuf[18];
#else
	const char *months[] = {
		"Jan", "Feb", "Mar", "Apr", "May", "Jun",
		"Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
	};
#endif

	uid = th_get_uid(t);
	pw = getpwuid(uid);
	if (pw == NULL)
		snprintf(username, sizeof(username), "%d", uid);
	else
		strlcpy(username, pw->pw_name, sizeof(username));

	gid = th_get_gid(t);
	gr = getgrgid(gid);
	if (gr == NULL)
		snprintf(groupname, sizeof(groupname), "%d", gid);
	else
		strlcpy(groupname, gr->gr_name, sizeof(groupname));

	strmode(th_get_mode(t), modestring);
	fprintf(f, "%.10s %-8.8s %-8.8s ", modestring, username, groupname);

	if (TH_ISCHR(t) || TH_ISBLK(t))
		fprintf(f, " %3d, %3d ", th_get_devmajor(t), th_get_devminor(t));
	else
		fprintf(f, "%9ld ", (long)th_get_size(t));

	mtime = th_get_mtime(t);
	mtm = localtime(&mtime);
#ifdef HAVE_STRFTIME
	strftime(timebuf, sizeof(timebuf), "%h %e %H:%M %Y", mtm);
	fprintf(f, "%s", timebuf);
#else
	fprintf(f, "%.3s %2d %2d:%02d %4d",
	       months[mtm->tm_mon],
	       mtm->tm_mday, mtm->tm_hour, mtm->tm_min, mtm->tm_year + 1900);
#endif

	fprintf(f, " %s", th_get_pathname(t));

	if (TH_ISSYM(t) || TH_ISLNK(t))
	{
		if (TH_ISSYM(t))
			fprintf(f, " -> ");
		else
			fprintf(f, " link to ");
		if ((t->options & TAR_GNU) && t->th_buf.gnu_longlink != NULL)
			fprintf(f, "%s", t->th_buf.gnu_longlink);
		else
			fprintf(f, "%.100s", t->th_buf.linkname);
	}

	putc('\n', f);
}

#endif /* LIBTAR_NO_OUTPUT */


/******************************************************************************/
/*  decode - libtar code to decode tar header blocks */


#define TLS_THREAD __thread

/* determine full path name */
static const char *
th_get_pathname(const TAR *t)
{
	static TLS_THREAD char filename[MAXPATHLEN];

	if (t->th_buf.gnu_longname)
		return t->th_buf.gnu_longname;

	if (t->th_buf.prefix[0] != '\0')
	{
		snprintf(filename, sizeof(filename), "%.155s/%.100s",
			 t->th_buf.prefix, t->th_buf.name);
		return filename;
	}

	snprintf(filename, sizeof(filename), "%.100s", t->th_buf.name);
	return filename;
}


static uid_t
__attribute__((unused))
th_get_uid(const TAR *t)
{
	int uid;
	struct passwd *pw;

	pw = getpwnam(t->th_buf.uname);
	if (pw != NULL)
		return pw->pw_uid;

	/* if the password entry doesn't exist */
	sscanf(t->th_buf.uid, "%o", &uid);
	return uid;
}


static gid_t
__attribute__((unused))
th_get_gid(const TAR *t)
{
	int gid;
	struct group *gr;

	gr = getgrnam(t->th_buf.gname);
	if (gr != NULL)
		return gr->gr_gid;

	/* if the group entry doesn't exist */
	sscanf(t->th_buf.gid, "%o", &gid);
	return gid;
}


static mode_t
th_get_mode(const TAR *t)
{
	mode_t mode;

	mode = (mode_t)oct_to_int(t->th_buf.mode);
	if (! (mode & S_IFMT))
	{
		switch (t->th_buf.typeflag)
		{
		case SYMTYPE:
			mode |= S_IFLNK;
			break;
		case CHRTYPE:
			mode |= S_IFCHR;
			break;
		case BLKTYPE:
			mode |= S_IFBLK;
			break;
		case DIRTYPE:
			mode |= S_IFDIR;
			break;
		case FIFOTYPE:
			mode |= S_IFIFO;
			break;
		case AREGTYPE:
			if (t->th_buf.name[strlen(t->th_buf.name) - 1] == '/')
			{
				mode |= S_IFDIR;
				break;
			}
			/* FALLTHROUGH */
		case LNKTYPE:
		case REGTYPE:
		default:
			mode |= S_IFREG;
		}
	}

	return mode;
}
