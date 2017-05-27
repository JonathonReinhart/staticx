#include <stdio.h>
#include <stdlib.h>
#include <error.h>
#include <errno.h>

#define verbose_msg(fmt, ...)   fprintf(stderr, fmt, ##__VA_ARGS__)

static char *
create_tmpdir(void)
{
    static char template[] = "/tmp/staticx-XXXXXX";
    char *tmpdir = mkdtemp(template);
    if (!tmpdir)
        error(2, errno, "Failed to create tempdir");
    return tmpdir;
}

int
main(int argc, char **argv)
{
    char *path = create_tmpdir();
    verbose_msg("Temp dir: %s\n", path);

    return 0;
}
