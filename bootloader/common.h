#ifndef BOOTLOADER_COMMON_H
#define BOOTLOADER_COMMON_H
#include <stdint.h>

#define ARCHIVE_SECTION         ".staticx.archive"
#define INTERP_FILENAME         ".staticx.interp"
#define PROG_FILENAME           ".staticx.prog"

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
