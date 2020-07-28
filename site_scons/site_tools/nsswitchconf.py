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
            tgtf.write('NSSWITCH_CONF("{}", "{}")\n'.format(dbname, ' '.join(svcs)))


def _strfunc(target, source, env):
    return "Creating '%s'" % target[0]

def NsswitchConfH(env, target, source):
    return env.Command(
        action = Action(_gen_nsswitch_conf_h, _strfunc),
        target = target,
        source = source,
    )

def GetNsswitchLibs(env, source):
    source = env.File(source)
    libs = set()
    conf = read_nsswitch_conf(source.srcnode().abspath)
    for dbname, svcs in conf:
        libs.update('libnss_'+s for s in svcs)
    return list(libs)

def generate(env):
    env.AddMethod(NsswitchConfH)
    env.AddMethod(GetNsswitchLibs)
    return True

def exists(env):
    return True
