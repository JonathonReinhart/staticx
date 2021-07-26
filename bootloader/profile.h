#ifndef BOOTLOADER_PROFILE_H
#define BOOTLOADER_PROFILE_H

#include <time.h>

#define PR_TSPEC_FMT        "%ld.%06ld"
#define PR_TSPEC_ARG(x)     x.tv_sec, x.tv_nsec

void timespec_sub(
    const struct timespec *start,
    const struct timespec *end,
    struct timespec       *result
);

#endif /* BOOTLOADER_PROFILE_H */
