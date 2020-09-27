#ifndef BOOTLOADER_ELFUTIL_H
#define BOOTLOADER_ELFUTIL_H

#include <elf.h>
#include <stdbool.h>
#include <stdint.h>

/**
 * Determine native ELF type by looking at size of pointer.
 * This should work even for x32 which uses elf32:
 * https://stackoverflow.com/a/36347228
 */
#if UINTPTR_MAX == UINT64_MAX
/* 64-bit */
# define Elf_Ehdr    Elf64_Ehdr
# define Elf_Phdr    Elf64_Phdr
# define Elf_Shdr    Elf64_Shdr
# define Elf_Dyn     Elf64_Dyn
#elif UINTPTR_MAX == UINT32_MAX
/* 32-bit */
# define Elf_Ehdr    Elf32_Ehdr
# define Elf_Phdr    Elf32_Phdr
# define Elf_Shdr    Elf32_Shdr
# define Elf_Dyn     Elf32_Dyn
#else
# error unexpected UINTPTR_MAX
#endif

bool
elf_is_valid(const Elf_Ehdr *ehdr);

Elf_Phdr *
elf_get_proghdr_by_type(Elf_Ehdr *ehdr, unsigned int ptype);

Elf_Shdr *
elf_get_section_by_name(Elf_Ehdr *ehdr, const char *lookup_name);

Elf_Shdr *
elf_get_section(Elf_Ehdr *ehdr, const char *lookup_name, Elf64_Word lookup_type);

#endif /* BOOTLOADER_ELFUTIL_H */
