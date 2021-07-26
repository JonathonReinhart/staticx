#include <time.h>
#include "profile.h"

#define NSEC_PER_SEC      1000000000

void timespec_sub(
    const struct timespec *start,
    const struct timespec *end,
    struct timespec       *result
)
{
    if (end->tv_nsec < start->tv_nsec) {
        result->tv_sec  = end->tv_sec - start->tv_sec - 1;
        result->tv_nsec = (NSEC_PER_SEC - start->tv_nsec) + end->tv_nsec;
    } else {
        result->tv_sec  = end->tv_sec - start->tv_sec;
        result->tv_nsec = end->tv_nsec - start->tv_nsec;
    }
}
