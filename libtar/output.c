/*
**  Copyright 1998-2003 University of Illinois Board of Trustees
**  Copyright 1998-2003 Mark D. Roth
**  All rights reserved.
**
**  output.c - libtar code to print out tar header blocks
**
**  Mark D. Roth <roth@uiuc.edu>
**  Campus Information Technologies and Educational Services
**  University of Illinois at Urbana-Champaign
*/

#include <stdio.h>
#include <pwd.h>
#include <grp.h>
#include <time.h>
#include <limits.h>
#include <sys/param.h>
#include <string.h>
#include "libtar.h"
#include "compat.h"


#ifndef _POSIX_LOGIN_NAME_MAX
# define _POSIX_LOGIN_NAME_MAX	9
#endif


void
th_print_long_ls(TAR *t)
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
	printf("%.10s %-8.8s %-8.8s ", modestring, username, groupname);

	if (TH_ISCHR(t) || TH_ISBLK(t))
		printf(" %3d, %3d ", th_get_devmajor(t), th_get_devminor(t));
	else
		printf("%9ld ", (long)th_get_size(t));

	mtime = th_get_mtime(t);
	mtm = localtime(&mtime);
#ifdef HAVE_STRFTIME
	strftime(timebuf, sizeof(timebuf), "%h %e %H:%M %Y", mtm);
	printf("%s", timebuf);
#else
	printf("%.3s %2d %2d:%02d %4d",
	       months[mtm->tm_mon],
	       mtm->tm_mday, mtm->tm_hour, mtm->tm_min, mtm->tm_year + 1900);
#endif

	printf(" %s", th_get_pathname(t));

	if (TH_ISSYM(t) || TH_ISLNK(t))
	{
		if (TH_ISSYM(t))
			printf(" -> ");
		else
			printf(" link to ");
		if ((t->options & TAR_GNU) && t->th_buf.gnu_longlink != NULL)
			printf("%s", t->th_buf.gnu_longlink);
		else
			printf("%.100s", t->th_buf.linkname);
	}

	putchar('\n');
}


