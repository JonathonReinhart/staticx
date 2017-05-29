#include <stdbool.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <sys/stat.h>
#include <sys/mman.h>
#include "error.h"
#include "mmap.h"

struct map *
mmap_file(const char *path, bool readonly)
{
    struct map *map;

    if ((map = malloc(sizeof(*map))) == NULL)
        error(2, 0, "Failed to allocate map struture");

    int oflags = readonly ? O_RDONLY : O_RDWR;
    if ((map->fd = open(path, oflags)) < 0)
        error(2, errno, "Failed to open %s", path);

    struct stat st;
    if (fstat(map->fd, &st) < 0)
        error(2, errno, "Failed to stat %s", path);
    map->size = st.st_size;

    int prot = readonly ? PROT_READ : PROT_READ|PROT_WRITE;
    map->map = mmap(NULL, map->size, prot, MAP_SHARED, map->fd, 0);
    if (map->map == MAP_FAILED)
        error(2, errno, "Failed to mmap %s", path);

    return map;
}

void
unmap_file(struct map *map)
{
    if (map->map) {
        munmap(map->map, map->size);
        map->map = NULL;
    }

    if (map->fd != -1) {
        close(map->fd);
        map->fd = -1;
    }

    free(map);
}
