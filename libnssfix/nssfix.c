#define _GNU_SOURCE
#include <assert.h>
#include <stdarg.h>
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
#define always_inline       inline __attribute__((__always_inline__))

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
static always_inline char *make_env_entry(const char *name, const char *value)
{
    const size_t namelen = strlen(name);
    const size_t vallen = strlen(value);

    // This function must be always_inline!
    char * const r = alloca(namelen + 1 + vallen + 1);
    {
        char *p = r;
        p = mempcpy(p, name, namelen);
        *p++ = '=';
        p = mempcpy(p, value, vallen);
        *p++ = '\0';
    }
    return r;
}

static always_inline char **copy_append_env(char *const envp[], char *entry)
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

    // Allocate the array using alloca
    // This function must be always_inline!
    new_envp = alloca(env_count* sizeof(char*));

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
    if (prefix && starts_with(path, prefix))
        return true;

    // If a program is re-execing itself via /proc/self/exe, reinject.
    // We look for this symlink specifically, to avoid calling readlink() here.
    if (strcmp(path, "/proc/self/exe") == 0)
        return true;

    return false;
}


static int do_exec(typeof(execve) func, const char *path, char *const argv[], char *const envp[])
{
    dump_char_array("argv", argv, 2, ",");
    dump_char_array("envp", envp, 2, ");");

    if (should_reinject_into(path)) {
        debug("=== RESTORING LD_PRELOAD! ===\n");
        /**
         * Restore LD_PRELOAD
         *
         * These functions are marked always_inline and use alloca() to avoid
         * calling malloc(). This is to ensure exec*() stays async-signal-safe
         * and to avoid violating the requirements of vfork/clone(CLONE_VFORK).
         *
         * See the note in glibc/posix/execl.c.
         */
        char *new_entry = make_env_entry("LD_PRELOAD", m_orig_ld_preload);
        char **new_envp = copy_append_env(envp, new_entry);
        dump_char_array("New envp", new_envp, 0, "");

        envp = new_envp;
    }

    return func(path, argv, envp);
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
int execveat(int dirfd, const char *pathname, char *const argv[], char *const envp[], int flags);
int fexecve(int fd, char *const argv[], char *const envp[]);
#endif

#define count_args(firstarg) ({                             \
    va_list ap;                                             \
    size_t argc;                                            \
    va_start(ap, firstarg);                                 \
    for (argc = 1; va_arg(ap, const char *); argc++) { }    \
    va_end(ap);                                             \
    argc;                                                   \
})

#define copy_args(argc, argv, ap, firstarg) ({              \
    size_t i;                                               \
    argv[0] = (char *)firstarg;                             \
    for (i = 1; i <= argc; i++)                             \
        argv[i] = va_arg(ap, char *);                       \
})

#define build_argv(argc, argv, firstarg) ({                 \
    va_list ap;                                             \
    va_start(ap, firstarg);                                 \
    copy_args(argc, argv, ap, firstarg);                    \
    va_end(ap);                                             \
})

int execl(const char *path, const char *arg, ...)
{
    debug("execl(\n");
    debug("  path=\"%s\",\n", path);

    size_t argc = count_args(arg);
    char *argv[argc + 1];   // NULL term

    build_argv(argc, argv, arg);

    return do_execve(path, argv, environ);
}

int execlp(const char *file, const char *arg, ...)
{
    debug("execlp(\n");
    debug("  file=\"%s\",\n", file);

    size_t argc = count_args(arg);
    char *argv[argc + 1];   // NULL term

    build_argv(argc, argv, arg);

    return do_execvpe(file, argv, environ);
}

int execle(const char *path, const char *arg, ...)
{
    debug("execle(\n");
    debug("  path=\"%s\",\n", path);

    size_t argc = count_args(arg);
    char *argv[argc + 1];   // NULL term
    char **envp;

    va_list ap;
    va_start(ap, arg);
    copy_args(argc, argv, ap, arg);
    envp = va_arg(ap, char **);
    va_end(ap);

    return do_execve(path, argv, envp);
}


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
