#include <stdio.h>

#ifndef STATIC
# define STATIC 0
#endif

int main(int argc, char **argv)
{
    printf("aux: Hello from our %sauxiliary app: %s\n",
            STATIC ? "statically-linked " : "",
            argv[0]);
    return 0;
}
