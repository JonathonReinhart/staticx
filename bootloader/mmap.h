#ifndef MMAP_H
#define MMAP_H

#include <stdbool.h>

struct map
{
    int fd;
    size_t size;
    void *map;
};

struct map *
mmap_file(const char *path, bool readonly);

void
unmap_file(struct map *map);

#endif /* MMAP_H */
