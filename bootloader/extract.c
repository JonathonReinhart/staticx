#include <errno.h>
#include <libtar.h>
#include <fcntl.h>
#include "common.h"
#include "elfutil.h"
#include "error.h"
#include "extract.h"
#include "mmap.h"
#include "xz.h"


/**
 * libtar is weird and uses an integer as the 'context' for its tartype_t
 * function pointers, so we can't use a void * to refer to a dynamic structure.
 * That's not a big deal, since we only care about a single instance anyway.
 * So we'll use a "fake" file descriptor number whose value doesn't matter
 * because it will never be passed to any system calls. We do this just to keep
 * libtar in check.
 */
#define XZ_FAKE_FD   42

#define XZ_DICT_MAX     8<<20       /* 8 MiB */

static struct xz_dec *m_xzdec = NULL;
static struct xz_buf m_xzbuf;

static const char * xzret_to_str(enum xz_ret r)
{
    switch (r) {
        case XZ_OK:                 return "XZ_OK";
        case XZ_STREAM_END:         return "XZ_STREAM_END";
        case XZ_UNSUPPORTED_CHECK:  return "XZ_UNSUPPORTED_CHECK";
        case XZ_MEM_ERROR:          return "XZ_MEM_ERROR";
        case XZ_MEMLIMIT_ERROR:     return "XZ_MEMLIMIT_ERROR";
        case XZ_FORMAT_ERROR:       return "XZ_FORMAT_ERROR";
        case XZ_OPTIONS_ERROR:      return "XZ_OPTIONS_ERROR";
        case XZ_DATA_ERROR:         return "XZ_DATA_ERROR";
        case XZ_BUF_ERROR:          return "XZ_BUF_ERROR";
        default:                    return "XZ_??????";
    }
}

static int xz_open(const char *pathname, int oflags, ...)
{
    m_xzdec = xz_dec_init(XZ_DYNALLOC, XZ_DICT_MAX);
    if (!m_xzdec) {
        error(2, 0, "Failed to initialize xz decoder");
        return -1;
    }

    return XZ_FAKE_FD;
}

static int xz_close(int fd)
{
    if (fd != XZ_FAKE_FD) {
        debug_printf("Unexpected fd %d\n", fd);
        return -1;
    }

    if (m_xzdec) {
        xz_dec_end(m_xzdec);
        m_xzdec = NULL;
    }

    return 0;
}

static ssize_t xz_read(int fd, void * const buf, size_t const len)
{
    /* Decompress into given output buffer */
    m_xzbuf.out      = buf;
    m_xzbuf.out_pos  = 0;
    m_xzbuf.out_size = len;

    /* Always attempt to fill the given output buffer */
    while (m_xzbuf.out_pos != m_xzbuf.out_size) {

        /* Run! */
        enum xz_ret xr = xz_dec_run(m_xzdec, &m_xzbuf);
        switch (xr) {
            case XZ_OK:
                continue;

            case XZ_STREAM_END:
                /* Return 0 to indicate EOF */
                return 0;

            default:
                error(2, 0, "xz_dec_run returned %s (%d)\n", xzret_to_str(xr), xr);
                return -1;
        }
    }

    return len;
}

static tartype_t xztype = {
    .openfunc   = xz_open,
    .closefunc  = xz_close,
    .readfunc   = xz_read,
};

void
extract_archive(const char *dest_path)
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

    size_t tarxz_size = shdr->sh_size;
    const void *tarxz_data = cptr_add(ehdr, shdr->sh_offset);

    m_xzbuf = (typeof(m_xzbuf)) {
        .in      = tarxz_data,
        .in_pos  = 0,
        .in_size = tarxz_size,
        /* Other fields initialized to zero */
    };

    TAR *t;
    errno = 0;
    if (tar_open(&t, "", &xztype, O_RDONLY, 0, TAR_DEBUG_OPTIONS) != 0)
        error(2, errno, "tar_open() failed");

    /* XXX Why is it so hard for people to use 'const'? */
    if (tar_extract_all(t, (char*)dest_path) != 0)
        error(2, errno, "tar_extract_all() failed");

    if (tar_close(t) != 0)
        error(2, errno, "tar_close() failed");
    t = NULL;
    debug_printf("Successfully extracted archive to %s\n", dest_path);

    unmap_file(map);
    map = NULL;
}
