#include <string.h>
#include "common.h"
#include "debug.h"
#include "elfutil.h"
#include "error.h"

bool
elf_is_valid(const Elf_Ehdr *ehdr)
{
    return (ehdr->e_ident[EI_MAG0] == ELFMAG0)
        && (ehdr->e_ident[EI_MAG1] == ELFMAG1)
        && (ehdr->e_ident[EI_MAG2] == ELFMAG2)
        && (ehdr->e_ident[EI_MAG3] == ELFMAG3);
}


Elf_Phdr *
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

Elf_Shdr *
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
#if 0
    debug_printf("Sections:\n");
#endif
    for (int i=0; i < ehdr->e_shnum; i++) {
        Elf_Shdr *sh = &shdr_table[i];
        const char *sh_name = strtab + sh->sh_name;

#if 0
        debug_printf("[%d] %s type=0x%lX  offset=0x%lX\n",
                i, sh_name, (unsigned long)sh->sh_type, sh->sh_offset);
#endif

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

Elf_Shdr *
elf_get_section_by_name(Elf_Ehdr *ehdr, const char *lookup_name)
{
    return elf_get_section(ehdr, lookup_name, SHT_NOT_USED);
}

#if 0
Elf_Shdr *
elf_get_section_by_type(Elf_Ehdr *ehdr, unsigned long lookup_type)
{
    return elf_get_section(ehdr, NULL, lookup_type);
}
#endif

