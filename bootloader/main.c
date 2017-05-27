#include <stdio.h>
#include <stdlib.h>
#include <error.h>
#include <errno.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/mman.h>

#define verbose_msg(fmt, ...)   fprintf(stderr, fmt, ##__VA_ARGS__)

static void
extract_archive(const char *destpath)
{
    /* Open this ELF file */
    int fd = open("/proc/self/exe", O_RDONLY);
    if (fd < 0)
        error(2, errno, "Failed to open self");

    struct stat st;
    if (fstat(fd, &st) < 0)
        error(2, errno, "Failed to stat self");

    void *m = mmap(NULL, st.st_size, PROT_READ, MAP_SHARED, fd, 0);
    if (m == MAP_FAILED)
        error(2, errno, "Failed to mmap self");
}

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

    extract_archive(path);

    return 0;
}
