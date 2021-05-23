#include <stdio.h>

int main(int argc, char **argv)
{
    printf("Hello from musl-libc-linked app: %s\n",
            argv[0]);
    return 0;
}
