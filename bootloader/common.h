#ifndef BOOTLOADER_COMMON_H
#define BOOTLOADER_COMMON_H
#include <stdio.h>
#include <stdint.h>

#define ARCHIVE_SECTION         ".staticx.archive"
#define INTERP_FILENAME         ".staticx.interp"
#define PROG_FILENAME           ".staticx.prog"

#ifdef DEBUG
#define debug_printf(fmt, ...)   fprintf(stderr, fmt, ##__VA_ARGS__)
#define TAR_DEBUG_OPTIONS		(TAR_VERBOSE)
#else
#define debug_printf(fmt, ...)
#define TAR_DEBUG_OPTIONS		0
#endif

static inline void *
ptr_add(void *p, size_t off)
{
    return ((uint8_t *)p) + off;
}

static inline const void *
cptr_add(const void *p, size_t off)
{
    return ((const uint8_t *)p) + off;
}

#endif /* BOOTLOADER_COMMON_H */
