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
th_print_long_ls(const TAR *t, FILE *f)
{
	char modestring[12];
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

	strmode(th_get_mode(t), modestring);
	fprintf(f, "%.10s %-8.8s %-8.8s ", modestring, t->th_buf.uname, t->th_buf.gname);

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


