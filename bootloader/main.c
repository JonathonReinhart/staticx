#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <stdarg.h>
#include <string.h>
#include <errno.h>
#include <assert.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/mman.h>
#include <elf.h>
#include <libtar.h>

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

#define Elf_Ehdr    Elf64_Ehdr
#define Elf_Shdr    Elf64_Shdr

static void
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

static inline const void *
cptr_add(const void *p, size_t off)
{
    return ((const uint8_t *)p) + off;
}

static bool
elf_is_valid(const Elf_Ehdr *ehdr)
{
    return (ehdr->e_ident[EI_MAG0] == ELFMAG0)
        && (ehdr->e_ident[EI_MAG1] == ELFMAG1)
        && (ehdr->e_ident[EI_MAG2] == ELFMAG2)
        && (ehdr->e_ident[EI_MAG3] == ELFMAG3);
}

static const Elf_Shdr *
elf_get_section_by_name(const Elf_Ehdr *ehdr, const char *secname)
{
    /* Pointer to the section header table */
    const Elf_Shdr *shdr_table = cptr_add(ehdr, ehdr->e_shoff);

    /* Pointer to the string table section header */
    const Elf_Shdr *sh_strtab = &shdr_table[ehdr->e_shstrndx];

    /* Pointer to the string table data */
    const char *strtab = cptr_add(ehdr, sh_strtab->sh_offset);

    /* Sanity check on size of Elf_Shdr */
    if (ehdr->e_shentsize != sizeof(Elf_Shdr))
        error(2, 0, "ELF file disagrees with section size: %d != %zd",
            ehdr->e_shentsize, sizeof(Elf_Shdr));

    /* Iterate sections */
    debug_printf("Sections:\n");
    for (int i=0; i < ehdr->e_shnum; i++) {
        const Elf_Shdr *sh = &shdr_table[i];
        const char *sh_name = strtab + sh->sh_name;

        debug_printf("[%d] %s  offset=0x%lX\n", i, sh_name, sh->sh_offset);

        if (strcmp(sh_name, secname) == 0)
            return sh;
    }
    return NULL;
}

static int
write_all(int fd, const void *buf, size_t sz)
{
    const uint8_t *p = buf;
    while (sz) {
        ssize_t written = write(fd, p, sz);
        if (written == -1)
            return -1;

        p += written;
        sz -= written;
    }
    return 0;
}

static char *
path_join(const char *p1, const char *p2)
{
    char *result;
    if (asprintf(&result, "%s/%s", p1, p2) < 0)
        error(2, 0, "Failed to allocate path string");
    return result;
}

static void
extract_archive(const char *destpath)
{
    /* mmap this ELF file */
    int fd = open("/proc/self/exe", O_RDONLY);
    if (fd < 0)
        error(2, errno, "Failed to open self");

    struct stat st;
    if (fstat(fd, &st) < 0)
        error(2, errno, "Failed to stat self");

    void *m = mmap(NULL, st.st_size, PROT_READ, MAP_SHARED, fd, 0);
    if (m == MAP_FAILED)
        error(2, errno, "Failed to mmap self");

    /* Find the .staticx.archive section */
    const Elf_Ehdr *ehdr = m;
    if (!elf_is_valid(ehdr))
        error(2, 0, "Invalid ELF header");

    const Elf_Shdr *shdr = elf_get_section_by_name(ehdr, ARCHIVE_SECTION);
    if (!shdr)
        error(2, 0, "Failed to find "ARCHIVE_SECTION" section");

    /* TODO: Extract from memory instead of dumping out tar file */

    /* Write out the tarball */
    char *tarpath = path_join(destpath, "archive.tar");
    debug_printf("Tar path: %s\n", tarpath);

    int tarfd = open(tarpath, O_CREAT|O_WRONLY, 0400);
    if (tarfd < 0)
        error(2, errno, "Failed to open tar path: %s", tarpath);

    size_t tar_size = shdr->sh_size;
    const void *tar_data = cptr_add(ehdr, shdr->sh_offset);

    if (write_all(tarfd, tar_data, tar_size))
        error(2, errno, "Failed to write tar file: %s", tarpath);

    if (close(tarfd))
        error(2, errno, "Error on tar file close: %s", tarpath);

    /* Extract the tarball */
    /* TODO: Open using gztype
     * See https://github.com/tklauser/libtar/blob/master/libtar/libtar.c
     */
    TAR *t;
    errno = 0;
    if (tar_open(&t, tarpath, NULL, O_RDONLY, 0, TAR_DEBUG_OPTIONS) != 0)
        error(2, errno, "tar_open() failed for %s", tarpath);

    /* XXX Why is it so hard for people to use 'const'? */
    if (tar_extract_all(t, (char*)destpath) != 0)
        error(2, errno, "tar_extract_all() failed for %s", tarpath);

    if (tar_close(t) != 0)
        error(2, errno, "tar_close() failed for %s", tarpath);
    t = NULL;
    debug_printf("Successfully extracted archive to %s\n", destpath);


    free(tarpath);
    tarpath = NULL;
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

static char **
make_argv(int orig_argc, char **orig_argv, const char *destpath)
{
    /**
     * Generate an argv to execute the user app:
     * ./.staticx.interp --library-path . ./.staticx.prog */
    int len = 1 + 2 + 1 + (orig_argc-1) + 1;
    char **argv = calloc(len, sizeof(char*));

    int w = 0;
    argv[w++] = path_join(destpath, INTERP_FILENAME);
    argv[w++] = "--library-path";
    argv[w++] = strdup(destpath);
    argv[w++] = path_join(destpath, PROG_FILENAME);

    for (int i=1; i < orig_argc; i++) {
        argv[w++] = orig_argv[i];
    }
    argv[w++] = NULL;
    assert(w == len);

    return argv;
}

int
main(int argc, char **argv)
{
    char *path = create_tmpdir();
    debug_printf("Temp dir: %s\n", path);

    extract_archive(path);

    char **new_argv = make_argv(argc, argv, path);

    debug_printf("New argv:\n");
    for (int i=0; ; i++) {
        char *a = new_argv[i];
        if (!a) break;

        debug_printf("[%d] = \"%s\"\n", i, a);
    }

    errno = 0;
    execv(new_argv[0], new_argv);
    error(3, errno, "Failed to execv() %s", new_argv[0]);

    return 0;
}
