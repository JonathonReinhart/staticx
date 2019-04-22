#define _XOPEN_SOURCE 500
#include <stdlib.h>
#include <stdio.h>          /* for remove(3) */
#include <unistd.h>
#include <errno.h>
#include <ftw.h>            /* file tree walk */
#include <sys/stat.h>
#include "util.h"


static int
remove_tree_fn(const char *fpath, const struct stat *sb,
        int typeflag, struct FTW *ftwbuf)
{
    return remove(fpath);
}

int
remove_tree(const char *pathname)
{
    int max_open_fd = 20;

    /**
     * Musl libc < 1.0.0 had a bug where FTW_MOUNT flag prevented walking any
     * directories at all. We don't really need it, so just leave it off.
     * See https://github.com/JonathonReinhart/staticx/issues/25
     */
    int flags = FTW_DEPTH | /* FTW_MOUNT | */ FTW_PHYS;

    errno = 0;
    return nftw(pathname, remove_tree_fn, max_open_fd, flags);
}
