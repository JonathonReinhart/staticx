#define _XOPEN_SOURCE 500
#include <stdlib.h>
#include <stdio.h>          /* for remove(3) */
#include <unistd.h>
#include <errno.h>
#include <ftw.h>            /* file tree walk */
#include <sys/stat.h>
#include "util.h"

#define MAX_READLINK_ATTEMPT    10

char *
readlinka(const char *path)
{
    char *buf = NULL;
    struct stat st;
    size_t bufsz;
    int i;

    errno = 0;

    for (i = 0; i < MAX_READLINK_ATTEMPT; i++) {
        /* Determine size of buf contents */
        if (lstat(path, &st) < 0) {
            goto fail;
        }

        /* Allocate buffer */
        bufsz = st.st_size + 1;
        buf = malloc(bufsz);
        if (buf == NULL) {
            errno = ENOMEM;
            goto fail;
        }

        /* Read link into buffer */
        ssize_t r = readlink(path, buf, bufsz);
        if (r < 0) {
            goto fail;
        }

        /* Check to see if symlink increased in size between
         * lstat() and readlink() */
        if (r > st.st_size) {
            free(buf);
            buf = NULL;
            continue;   /* retry */
        }

        /* NUL terminate and return */
        buf[r] = '\0';
        return buf;
    }

    errno = EAGAIN;

fail:
    if (buf) {
        free(buf);
        buf = NULL;
    }
    return NULL;
}


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
