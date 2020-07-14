#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include <stdlib.h>
#include <unistd.h>
#include <dlfcn.h>
#include <nss.h>

static const char *m_orig_ld_preload;

extern char **environ;

#define ARRAY_LEN(x)        (sizeof(x)/sizeof(x[0]))

#ifdef DEBUG
# define debug(fmt, ...)    fprintf(stderr, "%s [%d]: %s:" fmt, \
                                "nssfix", (int)getpid(), __FUNCTION__, \
                                ##__VA_ARGS__)
#else
# define debug(fmt, ...)
#endif
#define debug_ind(indent, fmt, ...)     debug("%*s" fmt, indent, "", ##__VA_ARGS__)

static void dump_char_array(const char *name, char *const ar[], int indent, const char *trailer)
{
    return;
#ifdef DEBUG
    char *const *p;
    debug_ind(indent, "%s = {\n", name);
    for (p = ar; *p; p++) {
        debug_ind(indent+2, "\"%s\",\n", *p);
    }
    debug_ind(indent, "}%s\n", trailer);
#endif
}

static bool starts_with(const char *string, const char *prefix)
{
    while (*prefix)
    {
        if (*prefix++ != *string++)
            return false;
    }

    return true;
}

static const char *getenvdup(const char *name)
{
    char *val = getenv(name);
    if (!val)
        return NULL;

    char *v = strdup(val);
    if (!v) {
        fprintf(stderr, "Failed to duplicate env var %s=%s\n", name, val);
        _exit(99);
    }

    return v;
}

#if 0
static void my_setenv(const char *name, const char *value)
{
    debug("Setting %s=%s\n", name, value);
    setenv(name, value, 1);
}

static void restore_preload(void)
{
    my_setenv("LD_PRELOAD", m_orig_ld_preload);
}
#endif

/******************************************************************************/
/** NSS Configuration **/

struct dbspec {
    const char *dbname;
    const char *service_line;
};
#define DBSVC(name, line)   { .dbname = #name, .service_line = line, }
#define DBFILES(name)       DBSVC(name, "files")

static struct dbspec m_dbspecs[] = {
    // https://github.com/bminor/glibc/blob/glibc-2.31/nss/databases.def
    DBFILES(aliases),
    DBFILES(ethers),
    DBFILES(group),
    DBFILES(gshadow),
    DBSVC(hosts, "files dns"),
    DBFILES(initgroups),
    DBFILES(netgroup),
    DBFILES(networks),
    DBFILES(passwd),
    DBFILES(protocols),
    DBFILES(publickey),
    DBFILES(rpc),
    DBFILES(services),
    DBFILES(shadow),
};

/**
 * Configure NSS
 *
 * Use __nss_configure_lookup to effectively force NSS to ignore
 * /etc/nsswitch.conf, and instead use only "files" and "dns"
 * services. This library depends on libnss_files.so and libnss_dns.so.
 *
 * This must be called before any functions which use NSS (e.g. getpwnam).
 */
static void configure_nss(void)
{
    size_t i;
    int rc;

    for (i = 0; i < ARRAY_LEN(m_dbspecs); i++) {
        struct dbspec *d = &m_dbspecs[i];

#if 0
        debug("__nss_configure_lookup(\"%s\", \"%s\")\n",
                d->dbname, d->service_line);
#endif

        rc = __nss_configure_lookup(d->dbname, d->service_line);
        if (rc) {
            fprintf(stderr, "__nss_configure_lookup(\"%s\", \"%s\") failed: %m\n",
                    d->dbname, d->service_line);
        }
    }
}

/******************************************************************************/
/** Symbol lookup **/

#define realsym(func)       static typeof(func) *m_real_##func
#define lookup(func)        m_real_##func = lookup_real(#func)

realsym(execve);
realsym(execvpe);

static void *lookup_real(const char *name)
{
    void *r = dlsym(RTLD_NEXT, name);
    if (!r) {
        fprintf(stderr, "Failed to look up %s: %s\n", name, dlerror());
        _exit(99);
    }
    return r;
}

static void lookup_syms(void)
{
    lookup(execve);
    lookup(execvpe);
}

#undef realsym
#undef lookup

/******************************************************************************/

/* Make a copy of envp and add name=value entry */
static char *make_env_entry(const char *name, const char *value)
{
    const size_t namelen = strlen(name);
    const size_t vallen = strlen(value);

    char * const r = malloc(namelen + 1 + vallen + 1);
    if (r) {
        char *p = r;
        p = mempcpy(p, name, namelen);
        *p++ = '=';
        p = mempcpy(p, value, vallen);
        *p++ = '\0';
    }
    return r;
}

static char **copy_append_env(char *const envp[], char *entry)
{
    char **new_envp;
    char *const *p;

    // Count elements
    size_t env_count = 0;
    for (p = envp; *p; p++) {
        env_count++;
    }
    env_count++;    // new one
    env_count++;    // NULL term

    // Allocate the array
    new_envp = malloc(env_count* sizeof(char*));
    if (!new_envp) {
        debug("Failed to allocate new_envp\n");
        return NULL;
    }

    // Copy the pointers
    char **d;
    for (p = envp, d = new_envp; *p; p++) {
        *d++ = *p;
    }
    *d++ = entry;
    *d++ = NULL;
    assert(d-new_envp == env_count);

    return new_envp;
}

static bool should_reinject_into(const char *path)
{
    // If this variable is set, nssfix will re-inject itself into any
    // programs whose executables start with the given prefix.
    const char *prefix = getenv("NSSFIX_REINJECT_PATH_PREFIX");
    if (prefix) {
        return starts_with(path, prefix);
    }
    return false;
}


static int do_exec(typeof(execve) func, const char *path, char *const argv[], char *const envp[])
{
    char **new_envp = NULL;
    char *new_entry = NULL;

    dump_char_array("argv", argv, 2, ",");
    dump_char_array("envp", envp, 2, ");");

    if (should_reinject_into(path)) {
        debug("=== RESTORING LD_PRELOAD! ===\n");

        /**
         * XXX: Technically, this is a violation of POSIX because it makes
         * these exec* functions not async-signal-safe due to the use of
         * malloc(). See the note in glibc/posix/execl.c. To remedy this, we
         * might be able to use a stack allocation instead.
         */

        // Restore LD_PRELOAD
        new_entry = make_env_entry("LD_PRELOAD", m_orig_ld_preload);
        new_envp = copy_append_env(envp, new_entry);
        dump_char_array("New envp", new_envp, 0, "");

        envp = new_envp;
    }

    int rc = func(path, argv, envp);

    free(new_envp);
    free(new_entry);

    return rc;
}

static int do_execve(const char *path, char *const argv[], char *const envp[])
{
    return do_exec(m_real_execve, path, argv, envp);
}

static int do_execvpe(const char *file, char *const argv[], char *const envp[])
{
    if (strchr(file, '/')) {
        // If the specified filename includes a slash character, then PATH is
        // ignored, and the file at the specified pathname is executed.
        return do_exec(m_real_execvpe, file, argv, envp);
    }

    // If PATH is being searched, then the file being executed most likely
    // should not be reinjected into.
    return m_real_execvpe(file, argv, envp);
}

/******************************************************************************/
/** Hooks **/

#if 0
// TODO
int execl(const char *path, const char *arg, ...);
int execlp(const char *file, const char *arg, ...);
int execle(const char *path, const char *arg, ...);

int execveat(int dirfd, const char *pathname, char *const argv[], char *const envp[], int flags);
int fexecve(int fd, char *const argv[], char *const envp[]);
#endif


int execv(const char *path, char *const argv[])
{
    debug("execv(\n");
    debug("  path=\"%s\",\n", path);

    return do_execve(path, argv, environ);
}

int execve(const char *path, char *const argv[], char *const envp[])
{
    debug("execve(\n");
    debug("  path=\"%s\",\n", path);

    return do_execve(path, argv, envp);
}

/* ...p variants (PATH search) */

int execvp(const char *file, char *const argv[])
{
    debug("execvp(\n");
    debug("  file=\"%s\",\n", file);

    return do_execvpe(file, argv, environ);
}

int execvpe(const char *file, char *const argv[], char *const envp[])
{
    debug("execvpe(\n");
    debug("  file=\"%s\",\n", file);

    return do_execvpe(file, argv, envp);
}


/******************************************************************************/



__attribute__((constructor(101)))
static void init_nssfix(void)
{
    debug("Entry\n");
    lookup_syms();

    m_orig_ld_preload = getenvdup("LD_PRELOAD");
    debug("Original LD_PRELOAD: %s\n", m_orig_ld_preload);

    unsetenv("LD_PRELOAD");
    debug("Unset LD_PRELOAD\n");

    configure_nss();
}
