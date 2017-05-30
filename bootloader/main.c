#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <errno.h>
#include <assert.h>
#include <unistd.h>
#include <fcntl.h>
#include <elf.h>
#include <libtar.h>
#include "error.h"
#include "mmap.h"

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
#define Elf_Phdr    Elf64_Phdr
#define Elf_Shdr    Elf64_Shdr


/* Our "home" directory, where the archive is extracted */
static const char *m_homedir;


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

static bool
elf_is_valid(const Elf_Ehdr *ehdr)
{
    return (ehdr->e_ident[EI_MAG0] == ELFMAG0)
        && (ehdr->e_ident[EI_MAG1] == ELFMAG1)
        && (ehdr->e_ident[EI_MAG2] == ELFMAG2)
        && (ehdr->e_ident[EI_MAG3] == ELFMAG3);
}

static Elf_Phdr *
elf_get_proghdr_by_type(Elf_Ehdr *ehdr, unsigned int ptype)
{
    /* Pointer to the program header table */
    Elf_Phdr *phdr_table = ptr_add(ehdr, ehdr->e_phoff);

    /* Sanity check on size of Elf_Phdr */
    if (ehdr->e_phentsize != sizeof(Elf_Phdr))
        error(2, 0, "ELF file disagrees with program header size: %d != %zd",
            ehdr->e_phentsize, sizeof(Elf_Phdr));

    for (int i=0; i < ehdr->e_phnum; i++) {
        Elf_Phdr *ph = &phdr_table[i];

        if (ph->p_type == ptype)
            return ph;
    }
    return NULL;
}

#define SHT_NOT_USED    (SHT_HIUSER + 1)

static Elf_Shdr *
elf_get_section(Elf_Ehdr *ehdr, const char *lookup_name, Elf64_Word lookup_type)
{
    /* Pointer to the section header table */
    Elf_Shdr *shdr_table = ptr_add(ehdr, ehdr->e_shoff);

    /* Pointer to the string table section header */
    Elf_Shdr *sh_strtab = &shdr_table[ehdr->e_shstrndx];

    /* Pointer to the string table data */
    char *strtab = ptr_add(ehdr, sh_strtab->sh_offset);

    /* Sanity check on size of Elf_Shdr */
    if (ehdr->e_shentsize != sizeof(Elf_Shdr))
        error(2, 0, "ELF file disagrees with section size: %d != %zd",
            ehdr->e_shentsize, sizeof(Elf_Shdr));

    /* Iterate sections */
    debug_printf("Sections:\n");
    for (int i=0; i < ehdr->e_shnum; i++) {
        Elf_Shdr *sh = &shdr_table[i];
        const char *sh_name = strtab + sh->sh_name;

        debug_printf("[%d] %s type=0x%lX  offset=0x%lX\n",
                i, sh_name, sh->sh_type, sh->sh_offset);

        /* Look up by name */
        if (lookup_name) {
            if (strcmp(sh_name, lookup_name) == 0)
                return sh;
        }

        /* Look up by type */
        if (lookup_type != SHT_NOT_USED) {
            if (sh->sh_type == lookup_type)
                return sh;
        }
    }
    return NULL;
}

static Elf_Shdr *
elf_get_section_by_name(Elf_Ehdr *ehdr, const char *lookup_name)
{
    return elf_get_section(ehdr, lookup_name, SHT_NOT_USED);
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
extract_archive(void)
{
    /* mmap this ELF file */
    struct map *map = mmap_file("/proc/self/exe", true);

    /* Find the .staticx.archive section */
    Elf_Ehdr *ehdr = map->map;
    if (!elf_is_valid(ehdr))
        error(2, 0, "Invalid ELF header");

    const Elf_Shdr *shdr = elf_get_section_by_name(ehdr, ARCHIVE_SECTION);
    if (!shdr)
        error(2, 0, "Failed to find "ARCHIVE_SECTION" section");

    /* TODO: Extract from memory instead of dumping out tar file */

    /* Write out the tarball */
    char *tarpath = path_join(m_homedir, "archive.tar");
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
    if (tar_extract_all(t, (char*)m_homedir) != 0)
        error(2, errno, "tar_extract_all() failed for %s", tarpath);

    if (tar_close(t) != 0)
        error(2, errno, "tar_close() failed for %s", tarpath);
    t = NULL;
    debug_printf("Successfully extracted archive to %s\n", m_homedir);


    free(tarpath);
    tarpath = NULL;

    unmap_file(map);
    map = NULL;
}

static void
set_interp(const char *prog_path, const char *new_interp)
{
    /* mmap the prog */
    struct map *map = mmap_file(prog_path, false);

    Elf_Ehdr *ehdr = map->map;
    if (!elf_is_valid(ehdr))
        error(2, 0, "Invalid ELF header");

    /* Find the interpreter string */
    Elf_Phdr *ph = elf_get_proghdr_by_type(ehdr, PT_INTERP);
    if (!ph)
        error(2, 0, "Failed to find PT_INTERP header");

    /* Make sure it is NUL terminated */
    char *interp = ptr_add(ehdr, ph->p_offset);
    size_t interp_size = ph->p_filesz;

    if (interp[interp_size - 1] != '\0')
        error(2, 0, "Current INTERP not NUL terminated");

    debug_printf("Current program interpreter: \"%s\"\n", interp);

    if (strlen(new_interp) > interp_size - 1)
        error(2, 0, "Current INTERP too small");

    strcpy(interp, new_interp);
    debug_printf("Set new interpreter: \"%s\"\n", new_interp);

    unmap_file(map);
    map = NULL;
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
make_argv(int orig_argc, char **orig_argv, char *argv0)
{
    /**
     * Generate an argv to execute the user app:
     * ./.staticx.interp --library-path . ./.staticx.prog */
    int len = 1 + (orig_argc-1) + 1;
    char **argv = calloc(len, sizeof(char*));

    int w = 0;
    argv[w++] = argv0;

    for (int i=1; i < orig_argc; i++) {
        argv[w++] = orig_argv[i];
    }
    argv[w++] = NULL;
    assert(w == len);

    return argv;
}

static void
run_app(int argc, char **argv)
{
    char *prog_path = path_join(m_homedir, PROG_FILENAME);

    char *interp_path = path_join(m_homedir, INTERP_FILENAME);
    set_interp(prog_path, interp_path);
    free(interp_path);

    char **new_argv = make_argv(argc, argv, prog_path);

    debug_printf("New argv:\n");
    for (int i=0; ; i++) {
        char *a = new_argv[i];
        if (!a) break;

        debug_printf("[%d] = \"%s\"\n", i, a);
    }

    errno = 0;
    execv(new_argv[0], new_argv);
    error(3, errno, "Failed to execv() %s", new_argv[0]);
}

int
main(int argc, char **argv)
{
    m_homedir = create_tmpdir();
    debug_printf("Home dir: %s\n", m_homedir);

    extract_archive();

    run_app(argc, argv);

    return 119;
}
