#include <errno.h>
#include <libtar.h>
#include <fcntl.h>
#include <string.h>
#include <stdlib.h>
#include "common.h"
#include "debug.h"
#include "elfutil.h"
#include "error.h"
#include "extract.h"
#include "mmap.h"
#include "xz.h"

#define XZ_DICT_MAX     8<<20       /* 8 MiB */

static int common_close(void *context);
static ssize_t xz_read(void *context, void *buf, size_t const len);
static ssize_t mem_read(void *context, void *buf, size_t len);

/* Extraction context */
struct exctx {
    tartype_t tartype;

    /* This is used by both the xztype and memtype tar handlers */
    struct xz_buf buf;

    /* Used only for xz; NULL otherwise */
    struct xz_dec *xzdec;
};

static struct exctx *
exctx_new(const void *data, size_t datalen, bool xz)
{
    struct exctx *ctx;

    /* Allocate context structure */
    ctx = malloc(sizeof(*ctx));
    if (!ctx) {
        error(2, 0, "Failed to allocate exctx");
        return NULL;
    }

    /* Setup tartype */
    {
        tartype_t *typ = &ctx->tartype;

        typ->closefunc = common_close;
        typ->readfunc = xz ? xz_read : mem_read;
    }

    /* Initialize buffer descriptor */
    {
        struct xz_buf *b = &ctx->buf;

        b->in = data;
        b->in_pos = 0;
        b->in_size = datalen;

        b->out = NULL;
        b->out_pos = 0;
        b->out_size = 0;
    }

    /* Initialize XZ decoder */
    if (xz) {
        ctx->xzdec = xz_dec_init(XZ_DYNALLOC, XZ_DICT_MAX);
        if (!ctx->xzdec) {
            error(2, 0, "Failed to initialize xz decoder");
            return NULL;
        }
    }

    return ctx;
}

static int common_close(void *context)
{
    struct exctx *ctx = context;

    if (ctx->xzdec) {
        xz_dec_end(ctx->xzdec);
    }

    free(ctx);
    return 0;
}

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

static ssize_t xz_read(void *context, void * const buf, size_t const len)
{
    struct exctx *ctx = context;
    struct xz_buf *b = &ctx->buf;

    /* Decompress into given output buffer */
    b->out      = buf;
    b->out_pos  = 0;
    b->out_size = len;

    /* Always attempt to fill the given output buffer */
    while (b->out_pos != b->out_size) {

        /* Run! */
        enum xz_ret xr = xz_dec_run(ctx->xzdec, b);
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

static bool is_xz_file(const char *buf, size_t len)
{
    /* https://tukaani.org/xz/xz-file-format.txt */
    static const uint8_t HEADER_MAGIC[6] = { 0xFD, '7', 'z', 'X', 'Z', 0x00 };

    if (len < sizeof(HEADER_MAGIC))
        return false;

    return memcmp(buf, HEADER_MAGIC, sizeof(HEADER_MAGIC)) == 0;
}

/*******************************************************************************/

static ssize_t mem_read(void *context, void * const buf, size_t len)
{
    struct exctx *ctx = context;
    struct xz_buf *b = &ctx->buf;

    const uint8_t *source = b->in + b->in_pos;
    size_t ar_remain = b->in_size - b->in_pos;

    if (len > ar_remain)
        len = ar_remain;

    memcpy(buf, source, len);
    b->in_pos += len;

    return len;
}

/*******************************************************************************/

struct archive
{
    const void *data;
    size_t size;
};

static TAR *tar_smart_bufopen(const struct archive ar, int options)
{
    /* Determine if the archive is compressed */
    bool xz = is_xz_file(ar.data, ar.size);

    debug_printf("Archive %s XZ-compressed\n",
            xz ? "is" : "is not");

    /* Create extration context */
    struct exctx *ctx = exctx_new(ar.data, ar.size, xz);

    /* Open the tar file */
    return tar_new(ctx, &ctx->tartype, options);
}

static struct archive
find_archive(void *map)
{
    struct archive ar;

    /* Find the .staticx.archive section */
    Elf_Ehdr *ehdr = map;
    if (!elf_is_valid(ehdr))
        error(2, 0, "Invalid ELF header");

    const Elf_Shdr *shdr = elf_get_section_by_name(ehdr, ARCHIVE_SECTION);
    if (!shdr)
        error(2, 0, "Failed to find "ARCHIVE_SECTION" section");

    debug_printf("Found archive at offset 0x%lX (%lu bytes)\n",
            (unsigned long)shdr->sh_offset, (unsigned long)shdr->sh_size);

    ar.size = shdr->sh_size;
    ar.data = cptr_add(ehdr, shdr->sh_offset);

    return ar;
}

void
extract_archive(const char *dest_path)
{
    /* mmap this ELF file */
    struct map *map = mmap_file("/proc/self/exe", true);

    /* Find the archive */
    struct archive ar = find_archive(map->map);

    /* Open the tar file */
    errno = 0;
    TAR *t = tar_smart_bufopen(ar, TAR_DEBUG_OPTIONS);
    if (t == NULL)
        error(2, errno, "tar_open() failed");

    /* Extract it */
    debug_printf("Extracting tar archive to %s\n", dest_path);
    if (tar_extract_all(t, dest_path) != 0)
        error(2, errno, "tar_extract_all() failed");

    /* Close it */
    if (tar_close(t) != 0)
        error(2, errno, "tar_close() failed");
    t = NULL;
    debug_printf("Successfully extracted archive to %s\n", dest_path);

    unmap_file(map);
    map = NULL;
}
