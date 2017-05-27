#ifndef LIBTAR_COMPAT_H
#define LIBTAR_COMPAT_H
#include <sys/stat.h>

size_t strlcpy(char *, const char *, size_t);

void strmode(mode_t mode, char *p);

#endif /* LIBTAR_COMPAT_H */
