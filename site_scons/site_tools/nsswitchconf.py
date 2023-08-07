from SCons.Action import Action

def read_nsswitch_conf(path):
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            dbname, svcs = line.split(':')
            dbname = dbname.strip()
            svcs = svcs.strip().split()
            yield dbname, svcs

def _gen_nsswitch_conf_h(target, source, env):
    conf = read_nsswitch_conf(source[0].get_path())
    with open(target[0].get_path(), 'w') as tgtf:
        for dbname, svcs in conf:
            svc_line = " ".join(svcs)
            tgtf.write(f'NSSWITCH_CONF("{dbname}", "{svc_line}")\n')


def _strfunc(target, source, env):
    return f"Creating '{target[0]}'"

def NsswitchConfH(env, target, source):
    return env.Command(
        action = Action(_gen_nsswitch_conf_h, _strfunc),
        target = target,
        source = source,
    )

# https://www.gnu.org/software/libc/manual/html_node/Adding-another-Service-to-NSS.html
# https://www.gnu.org/software/libc/manual/html_node/NSS-Module-Names.html
def _nss_module_name(service):
    NSS_INTERFACE_VERSION = 2
    return f"libnss_{service}.so.{NSS_INTERFACE_VERSION}"

def GetNsswitchLibs(env, source):
    """Gets a list of NSS module names for the given nsswitch.conf

    Args:
      env: Construction environment
      source: nsswitch.conf configuration file
    Returns:
      A list of module names for the services configured in nsswitch.conf.
      Example: ["libnss_files.so.2", "libnss_dns.so.2"]
    """
    source = env.File(source)
    libs = set()
    conf = read_nsswitch_conf(source.srcnode().abspath)
    for dbname, svcs in conf:
        libs.update(_nss_module_name(svc) for svc in svcs)
    return list(libs)

def generate(env):
    env.AddMethod(NsswitchConfH)
    env.AddMethod(GetNsswitchLibs)
    return True

def exists(env):
    return True
