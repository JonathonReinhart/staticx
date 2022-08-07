/*
**  Copyright 1998-2003 University of Illinois Board of Trustees
**  Copyright 1998-2003 Mark D. Roth
**  All rights reserved.
**
**  decode.c - libtar code to decode tar header blocks
**
**  Mark D. Roth <roth@uiuc.edu>
**  Campus Information Technologies and Educational Services
**  University of Illinois at Urbana-Champaign
*/

#include <stdio.h>
#include <sys/param.h>
#include <string.h>
#include "libtar.h"

#define TLS_THREAD __thread

/* determine full path name */
const char *
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


mode_t
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


