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


custom_tests = dict(
    CheckNSS = CheckNSS,
)
