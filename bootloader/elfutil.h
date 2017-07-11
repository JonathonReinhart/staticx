#ifndef BOOTLOADER_ELFUTIL_H
#define BOOTLOADER_ELFUTIL_H

#include <elf.h>
#include <stdbool.h>

#define Elf_Ehdr    Elf64_Ehdr
#define Elf_Phdr    Elf64_Phdr
#define Elf_Shdr    Elf64_Shdr
#define Elf_Dyn     Elf64_Dyn

bool
elf_is_valid(const Elf_Ehdr *ehdr);

Elf_Phdr *
elf_get_proghdr_by_type(Elf_Ehdr *ehdr, unsigned int ptype);

Elf_Shdr *
elf_get_section_by_name(Elf_Ehdr *ehdr, const char *lookup_name);

Elf_Shdr *
elf_get_section(Elf_Ehdr *ehdr, const char *lookup_name, Elf64_Word lookup_type);

#endif /* BOOTLOADER_ELFUTIL_H */
