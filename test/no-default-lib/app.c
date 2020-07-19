#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

static bool parse_uint(const char *str, unsigned int *out)
{
    unsigned long int res;
    char *endp;

    res = strtoul(str, &endp, 10);

    if (*str != '\0' && *endp == '\0') {
        *out = res;
        return true;
    }

    return false;
}

static void exit_usage(int status)
{
    fprintf(stderr, "Usage: app LIBNAME EXPECT_FAILURE\n");
    exit(status);
}

int main(int argc, char **argv)
{
    const char *path;
    unsigned int expect_fail;

    if (argc < 3) {
        exit_usage(1);
    }
    path = argv[1];
    if (!parse_uint(argv[2], &expect_fail)) {
        exit_usage(1);
    }


    void *h = dlopen(path, RTLD_NOW);
    printf("dlopen(\"%s\") returned %p\n", path, h);

    if (expect_fail) {
        if (h != NULL) {
            printf("ERROR: unexpectedly succeeded!\n");
            return 2;
        }
    }
    else {
        if (h == NULL) {
            printf("ERROR: unexpectedly failed!\n");
            return 2;
        }
    }

    printf("OK\n");
    return 0;
}
