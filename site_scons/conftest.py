def CheckNSS(context):
    context.Message('Checking for NSS...')
    ok, output = context.TryRun(
        extension='.c',
        text="""
#include <nss.h>
int main(void)
{
    __nss_configure_lookup("passwd", "files");
    return 0;
}
""")
    context.Result(ok)
    return ok


def BasicCheckLib(context, libname):
    """Check for a C library.

    Similar to built-in CheckLib but works around
    https://github.com/SCons/scons/issues/4373.
    """
    context.Message("Checking for library %s... " % libname)

    oldLIBS = context.AppendLIBS([libname])
    ok = context.TryLink(
        "int main(void) { return 0; }",
        ".c"
    )
    context.SetLIBS(oldLIBS)

    context.Result(ok)
    return ok


custom_tests = dict(
    CheckNSS = CheckNSS,
    BasicCheckLib = BasicCheckLib,
)
