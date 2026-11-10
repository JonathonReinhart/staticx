#include "libbar.h"
#include "libfoo.h"

int foo(void)
{
    return 42;
}

int foobar(void)
{
    return foo() + bar();
}
