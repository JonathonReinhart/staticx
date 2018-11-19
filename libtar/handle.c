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

static TAR *
tar_init(tartype_t *type, int mode, int options)
{
	TAR *t;

	t = calloc(1, sizeof(*t));
	if (t == NULL)
		return NULL;

	t->options = options;
	t->type = type;

	return t;
}

TAR *
tar_new(void *context, tartype_t *type, int options)
{
	int mode = 0;
	TAR *t;

	t = tar_init(type, mode, options);
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
