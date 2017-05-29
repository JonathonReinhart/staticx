#define _GNU_SOURCE
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <stdlib.h>
#include <errno.h>
#include "error.h"

void
error(int status, int errnum, const char *format, ...)
{
    fflush(stdout);

    fprintf(stderr, "%s: ", program_invocation_short_name);

    va_list ap;
    va_start(ap, format);
    vfprintf(stderr, format, ap);
    va_end(ap);

    if (errnum)
        fprintf(stderr, ": %s", strerror(errnum));
    fprintf(stderr, "\n");

    if (status)
        exit(status);
}
