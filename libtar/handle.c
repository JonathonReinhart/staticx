/*
**  Copyright 1998-2003 University of Illinois Board of Trustees
**  Copyright 1998-2003 Mark D. Roth
**  All rights reserved.
**
**  handle.c - libtar code for initializing a TAR handle
**
**  Mark D. Roth <roth@uiuc.edu>
**  Campus Information Technologies and Educational Services
**  University of Illinois at Urbana-Champaign
*/

#include <stdio.h>
#include <fcntl.h>
#include <errno.h>
#include <unistd.h>
#include <stdlib.h>
#include "libtar.h"


const char libtar_version[] = PACKAGE_VERSION;

static tartype_t default_type = {
	.openfunc = open,
	.closefunc = close,
	.readfunc = read,
};

static TAR *
tar_init(const char *pathname, tartype_t *type,
	 int oflags, int mode, int options)
{
	TAR *t;

	/* This libtar only supports read-only */
	if ((oflags & O_ACCMODE) != O_RDONLY)
	{
		errno = EINVAL;
		return NULL;
	}

	t = calloc(1, sizeof(*t));
	if (t == NULL)
	    return NULL;

	t->pathname = pathname;
	t->options = options;
	t->type = (type ? type : &default_type);
	t->oflags = oflags;

	return t;
}


/* open a new tarfile handle */
TAR *
tar_open(const char *pathname, tartype_t *type,
	 int oflags, int mode, int options)
{
	TAR *t;

	t = tar_init(pathname, type, oflags, mode, options);
	if (t == NULL)
		return NULL;

	if ((options & TAR_NOOVERWRITE) && (oflags & O_CREAT))
		oflags |= O_EXCL;

#ifdef O_BINARY
	oflags |= O_BINARY;
#endif

	t->fd = t->type->openfunc(pathname, oflags, mode);
	if (t->fd == -1)
	{
		free(t);
		return NULL;
	}

	return t;
}


TAR *
tar_fdopen(int fd, const char *pathname, tartype_t *type,
	   int oflags, int mode, int options)
{
	TAR *t;

	t = tar_init(pathname, type, oflags, mode, options);
	if (t == NULL)
	    return NULL;

	t->fd = fd;
	return t;
}


int
tar_fd(TAR *t)
{
	return t->fd;
}


/* close tarfile handle */
int
tar_close(TAR *t)
{
	int i;

	i = t->type->closefunc(t->fd);

	free(t);

	return i;
}


