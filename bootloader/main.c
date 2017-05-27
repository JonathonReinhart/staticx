#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <error.h>
#include <errno.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/mman.h>
#include <elf.h>

#define ARCHIVE_SECTION         ".staticx.archive"

#define verbose_msg(fmt, ...)   fprintf(stderr, fmt, ##__VA_ARGS__)

#define Elf_Ehdr    Elf64_Ehdr
#define Elf_Shdr    Elf64_Shdr

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
    verbose_msg("Sections:\n");
    for (int i=0; i < ehdr->e_shnum; i++) {
        const Elf_Shdr *sh = &shdr_table[i];
        const char *sh_name = strtab + sh->sh_name;

        verbose_msg("[%d] %s  offset=0x%lX\n", i, sh_name, sh->sh_offset);

        if (strcmp(sh_name, secname) == 0)
            return sh;
    }
    return NULL;
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
