/*
**  Copyright 1998-2003 University of Illinois Board of Trustees
**  Copyright 1998-2003 Mark D. Roth
**  All rights reserved.
**
**  util.c - miscellaneous utility code for libtar
**
**  Mark D. Roth <roth@uiuc.edu>
**  Campus Information Technologies and Educational Services
**  University of Illinois at Urbana-Champaign
*/

#include <stdio.h>
#include <sys/param.h>
#include <errno.h>
#include <string.h>
#include <libgen.h>
#include "libtar.h"
#include "compat.h"


/*
** mkdirhier() - create all directories in a given path
** returns:
**	0			success
**	1			all directories already exist
**	-1 (and sets errno)	error
*/
int
mkdirhier(const char *path)
{
	char src[MAXPATHLEN], dst[MAXPATHLEN] = "";
	char *dirp, *nextp = src;
	int retval = 1;

	if (strlcpy(src, path, sizeof(src)) > sizeof(src))
	{
		errno = ENAMETOOLONG;
		return -1;
	}

	if (path[0] == '/')
		strcpy(dst, "/");

	while ((dirp = strsep(&nextp, "/")) != NULL)
	{
		if (*dirp == '\0')
			continue;

		if (dst[0] != '\0')
			strcat(dst, "/");
		strcat(dst, dirp);

		if (mkdir(dst, 0777) == -1)
		{
			if (errno != EEXIST)
				return -1;
		}
		else
			retval = 0;
	}

	return retval;
}


/* calculate header checksum */
int
th_crc_calc(const TAR *t)
{
	int i, sum = 0;

	for (i = 0; i < T_BLOCKSIZE; i++)
		sum += ((unsigned char *)(&(t->th_buf)))[i];
	for (i = 0; i < 8; i++)
		sum += (' ' - (unsigned char)t->th_buf.chksum[i]);

	return sum;
}


/* calculate a signed header checksum */
int
th_signed_crc_calc(const TAR *t)
{
	int i, sum = 0;

	for (i = 0; i < T_BLOCKSIZE; i++)
		sum += ((signed char *)(&(t->th_buf)))[i];
	for (i = 0; i < 8; i++)
		sum += (' ' - (signed char)t->th_buf.chksum[i]);

	return sum;
}


/* string-octal to integer conversion */
int
oct_to_int(const char *oct)
{
	int i;

	sscanf(oct, "%o", &i);

	return i;
}
