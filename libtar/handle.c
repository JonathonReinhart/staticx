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

static inline int default_fd(void *context)
{
	return (int)(long)context;
}

static int default_close(void *context)
{
	int fd = default_fd(context);
	return close(fd);
}

static ssize_t default_read(void *context, void * const buf, size_t len)
{
	int fd = default_fd(context);
	return read(fd, buf, len);
}

static tartype_t default_type = {
	.closefunc = default_close,
	.readfunc = default_read,
};

static TAR *
tar_init(tartype_t *type,
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

	t->options = options;
	t->type = (type ? type : &default_type);
	t->oflags = oflags;

	return t;
}

TAR *
tar_new(void *context, tartype_t *type,
	   int oflags, int options)
{
	int mode = 0;
	TAR *t;

	t = tar_init(type, oflags, mode, options);
	if (t == NULL)
		return NULL;

	t->context = context;
	return t;
}


/* close tarfile handle */
int
tar_close(TAR *t)
{
	closefunc_t closefunc = t->type->closefunc;
	int rc = 0;

	if (closefunc)
		rc = closefunc(t->context);

	free(t);

	return rc;
}
