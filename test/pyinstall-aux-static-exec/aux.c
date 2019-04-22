#include <stdio.h>

int main(int argc, char **argv)
{
    printf("aux: Hello from our auxiliary statically-linked app:\n");
    printf("aux: %s\n", argv[0]);
    return 0;
}
