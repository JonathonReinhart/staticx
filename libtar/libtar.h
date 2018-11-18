/*
**  Copyright 1998-2003 University of Illinois Board of Trustees
**  Copyright 1998-2003 Mark D. Roth
**  All rights reserved.
**
**  libtar.h - header file for libtar library
**
**  Mark D. Roth <roth@uiuc.edu>
**  Campus Information Technologies and Educational Services
**  University of Illinois at Urbana-Champaign
*/

#ifndef LIBTAR_H
#define LIBTAR_H

#include <sys/types.h>
#include <sys/stat.h>
#include <tar.h>

#ifdef __cplusplus
extern "C"
{
#endif


/* useful constants */
#define T_BLOCKSIZE		512
#define T_NAMELEN		100
#define T_PREFIXLEN		155
#define T_MAXPATHLEN		(T_NAMELEN + T_PREFIXLEN)

/* GNU extensions for typeflag */
#define GNU_LONGNAME_TYPE	'L'
#define GNU_LONGLINK_TYPE	'K'

/* our version of the tar header structure */
struct tar_header
{
	char name[100];
	char mode[8];
	char uid[8];
	char gid[8];
	char size[12];
	char mtime[12];
	char chksum[8];
	char typeflag;
	char linkname[100];
	char magic[6];
	char version[2];
	char uname[32];
	char gname[32];
	char devmajor[8];
	char devminor[8];
	char prefix[155];
	char padding[12];
	char *gnu_longname;
	char *gnu_longlink;
};


/***** handle.c ************************************************************/

typedef int (*openfunc_t)(const char *, int, ...);
typedef int (*closefunc_t)(int);
typedef ssize_t (*readfunc_t)(int, void *, size_t);

typedef struct
{
	openfunc_t openfunc;
	closefunc_t closefunc;
	readfunc_t readfunc;
}
tartype_t;

typedef struct
{
	tartype_t *type;
	const char *pathname;
	long fd;
	int oflags;
	int options;
	struct tar_header th_buf;
}
TAR;

/* constant values for the TAR options field */
#define TAR_GNU			 1	/* use GNU extensions */
#define TAR_VERBOSE		 2	/* output file info to stdout */
#define TAR_NOOVERWRITE		 4	/* don't overwrite existing files */
#define TAR_IGNORE_EOT		 8	/* ignore double zero blocks as EOF */
#define TAR_CHECK_MAGIC		16	/* check magic in file header */
#define TAR_CHECK_VERSION	32	/* check version in file header */
#define TAR_IGNORE_CRC		64	/* ignore CRC in file header */

/* this is obsolete - it's here for backwards-compatibility only */
#define TAR_IGNORE_MAGIC	0

extern const char libtar_version[];


/* open a new tarfile handle */
int tar_open(TAR **t, const char *pathname, tartype_t *type,
	     int oflags, int mode, int options);

/* make a tarfile handle out of a previously-opened descriptor */
int tar_fdopen(TAR **t, int fd, const char *pathname, tartype_t *type,
	       int oflags, int mode, int options);

/* returns the descriptor associated with t */
int tar_fd(TAR *t);

/* close tarfile handle */
int tar_close(TAR *t);

/***** block.c *************************************************************/

/* macros for reading tarchive blocks */
#define tar_block_read(t, buf) \
	(*((t)->type->readfunc))((t)->fd, (char *)(buf), T_BLOCKSIZE)

/* read a header block */
int th_read(TAR *t);


/***** decode.c ************************************************************/

/* determine file type */
#define TH_ISREG(t)	((t)->th_buf.typeflag == REGTYPE \
			 || (t)->th_buf.typeflag == AREGTYPE \
			 || (t)->th_buf.typeflag == CONTTYPE \
			 || (S_ISREG((mode_t)oct_to_int((t)->th_buf.mode)) \
			     && (t)->th_buf.typeflag != LNKTYPE))
#define TH_ISLNK(t)	((t)->th_buf.typeflag == LNKTYPE)
#define TH_ISSYM(t)	((t)->th_buf.typeflag == SYMTYPE \
			 || S_ISLNK((mode_t)oct_to_int((t)->th_buf.mode)))
#define TH_ISCHR(t)	((t)->th_buf.typeflag == CHRTYPE \
			 || S_ISCHR((mode_t)oct_to_int((t)->th_buf.mode)))
#define TH_ISBLK(t)	((t)->th_buf.typeflag == BLKTYPE \
			 || S_ISBLK((mode_t)oct_to_int((t)->th_buf.mode)))
#define TH_ISDIR(t)	((t)->th_buf.typeflag == DIRTYPE \
			 || S_ISDIR((mode_t)oct_to_int((t)->th_buf.mode)) \
			 || ((t)->th_buf.typeflag == AREGTYPE \
			     && ((t)->th_buf.name[strlen((t)->th_buf.name) - 1] == '/')))
#define TH_ISFIFO(t)	((t)->th_buf.typeflag == FIFOTYPE \
			 || S_ISFIFO((mode_t)oct_to_int((t)->th_buf.mode)))
#define TH_ISLONGNAME(t)	((t)->th_buf.typeflag == GNU_LONGNAME_TYPE)
#define TH_ISLONGLINK(t)	((t)->th_buf.typeflag == GNU_LONGLINK_TYPE)

/* decode tar header info */
#define th_get_crc(t) oct_to_int((t)->th_buf.chksum)
#define th_get_size(t) oct_to_int((t)->th_buf.size)
#define th_get_mtime(t) oct_to_int((t)->th_buf.mtime)
#define th_get_devmajor(t) oct_to_int((t)->th_buf.devmajor)
#define th_get_devminor(t) oct_to_int((t)->th_buf.devminor)
#define th_get_linkname(t) ((t)->th_buf.gnu_longlink \
                            ? (t)->th_buf.gnu_longlink \
                            : (t)->th_buf.linkname)
char *th_get_pathname(TAR *t);
mode_t th_get_mode(TAR *t);
uid_t th_get_uid(TAR *t);
gid_t th_get_gid(TAR *t);


/***** extract.c ***********************************************************/

/* sequentially extract next file from t */
int tar_extract_file(TAR *t, char *realname);

/* extract different file types */
int tar_extract_dir(TAR *t, char *realname);
int tar_extract_hardlink(TAR *t, char *realname);
int tar_extract_symlink(TAR *t, char *realname);
int tar_extract_chardev(TAR *t, char *realname);
int tar_extract_blockdev(TAR *t, char *realname);
int tar_extract_fifo(TAR *t, char *realname);

/* for regfiles, we need to extract the content blocks as well */
int tar_extract_regfile(TAR *t, char *realname);
int tar_skip_regfile(TAR *t);


/***** output.c ************************************************************/

/* print the tar header */
void th_print(TAR *t);

/* print "ls -l"-like output for the file described by th */
void th_print_long_ls(TAR *t);


/***** util.c *************************************************************/

/* create any necessary dirs */
int mkdirhier(char *path);

/* calculate header checksum */
int th_crc_calc(TAR *t);

/* calculate a signed header checksum */
int th_signed_crc_calc(TAR *t);

/* compare checksums in a forgiving way */
#define th_crc_ok(t) (th_get_crc(t) == th_crc_calc(t) || th_get_crc(t) == th_signed_crc_calc(t))

/* string-octal to integer conversion */
int oct_to_int(char *oct);

/* integer to NULL-terminated string-octal conversion */
#define int_to_oct(num, oct, octlen) \
	snprintf((oct), (octlen), "%*lo ", (octlen) - 2, (unsigned long)(num))

/* integer to string-octal conversion, no NULL */
void int_to_oct_nonull(int num, char *oct, size_t octlen);


/***** wrapper.c **********************************************************/

/* extract groups of files */
int tar_extract_glob(TAR *t, char *globname, char *prefix);
int tar_extract_all(TAR *t, char *prefix);


#ifdef __cplusplus
}
#endif

#endif /* ! LIBTAR_H */

