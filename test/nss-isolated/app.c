#define _GNU_SOURCE
#include <errno.h>
#include <grp.h>
#include <pwd.h>
#include <netdb.h>
#include <limits.h>
#include <stdio.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/wait.h>

#define ERROR_STATUS        1
#define EXCEPTION_STATUS    2


#define debug(fmt, ...)    fprintf(stderr, "%s [%d]: %s: " fmt, \
                                "testapp", (int)getpid(), __FUNCTION__, \
                                ##__VA_ARGS__)

#define e_error(fmt, ...)     do {                                             \
    fprintf(stderr, "Error: " fmt "\n", ##__VA_ARGS__);                        \
    exit(ERROR_STATUS);                                                        \
} while(0)

#define e_exception(fmt, ...)     do {                                         \
    fprintf(stderr, "EXCEPTION: " fmt "\n", ##__VA_ARGS__);                    \
    exit(EXCEPTION_STATUS);                                                    \
} while(0)

#define always_inline       inline __attribute__((always_inline))

#define SELF_EXE    "/proc/self/exe"
#define QSTR                "\"%s\""

/********************************************************************************/
/** Util **/

static char *join_strings(const char *sep, char **argv)
{
    const size_t seplen = strlen(sep);
    size_t len = 0;
    char **arg;
    char *r;

    for (arg = argv; *arg != NULL; arg++) {
        // After first, add sep
        if (arg != argv)
            len += seplen;
        len += strlen(*arg);
    }
    len++;  // NUL term

    r = malloc(len);
    if (!r)
        return NULL;

    char *p = r;
    for (arg = argv; *arg != NULL; arg++) {
        // After first, add sep
        if (arg != argv)
            p = stpcpy(p, sep);
        p = stpcpy(p, *arg);
    }

    return r;
}

static always_inline
char *readlinka(const char *path)
{
    char *r = alloca(PATH_MAX);
    ssize_t n = readlink(path, r, PATH_MAX);    // always_inline
    if (n < 0)
        e_exception("readlink(\"%s\") failed: %m", path);

    r[n] = '\0';
    return r;
}


/********************************************************************************/
/** Name service tests **/

static void test_passwd(uid_t uid)
{
    errno = 0;
    struct passwd *pwd = getpwuid(uid);
    if (!pwd) {
        if (errno) {
            e_exception("getpwuid(%d) failed: %m", uid);
        }
        else {
            e_error("Failed to look up user for uid=%d", uid);
        }
    }
    if (0) printf("    getpwuid(%d) => .pw_name="QSTR"\n", uid, pwd->pw_name);
}



static void test_group(gid_t gid)
{
    errno = 0;
    struct group *gr = getgrgid(gid);
    if (!gr) {
        if (errno) {
            e_exception("getrggid(%d) failed: %m", gid);
        }
        else {
            e_error("Failed to look up group for gid=%d", gid);
        }
    }
    if (0) printf("    getgrgid(%d) => .gr_name="QSTR"\n", gid, gr->gr_name);
}

static void test_hosts(const char *hostname)
{
    struct hostent *host = gethostbyname(hostname);
    char buf[16];

    if (!host) {
        e_error("Failed to look up host %s: %s (%d)",
                hostname, hstrerror(h_errno), h_errno);
    }
    if (0) printf("    gethostbyname("QSTR") => "QSTR"\n", hostname,
            inet_ntop(AF_INET, host->h_addr_list[0], buf, sizeof(buf)));
}

static void test_services(const char *svcname)
{
   struct servent *srv;
   
   srv = getservbyname(svcname, NULL);
   if (!srv) {
       e_error("Failed to look up service %s", svcname);
   }
   if (0) printf("    getservbyname("QSTR", NULL) => %d/%s\n", svcname,
           ntohs(srv->s_port), srv->s_proto);
}

static void run_tests(void)
{
    // Verify "passwd: files" -- Test entry from /etc/passwd
    test_passwd(getuid());

    // Verify "group: files" -- Test entry from /etc/group
    test_group(getgid());
    
    // Verify "hosts: files" -- Test entry from /etc/hosts 
    test_hosts("localhost");

    // Verify "hosts: dns" -- Test entry from DNS
    test_hosts("google.com");

    // Verify "services: files" -- Test entry from /etc/services
    test_services("http");
}

/********************************************************************************/
/* exec tests */

struct execdata {
    const char *path;
    const char *testname;
};

#define MAKE_ARGV(e)    (char * const []) { \
        strdupa(e->path),                   \
        strdupa("child"),                   \
        strdupa(e->testname),               \
        NULL,                               \
    }

#define EXECL_ARGS(e)                       \
        e->path,                            \
        "child",                            \
        e->testname,                        \
        NULL

typedef void (*execfunc_t)(struct execdata *e);

static void do_execl(struct execdata *e)
{
    execl(e->path, EXECL_ARGS(e));
}

static void do_execlp(struct execdata *e)
{
    execlp(e->path, EXECL_ARGS(e));
}

static void do_execle(struct execdata *e)
{
    execle(e->path, EXECL_ARGS(e), environ);
}


static void do_execv(struct execdata *e)
{
    execv(e->path, MAKE_ARGV(e));
}

static void do_execve(struct execdata *e)
{
    execve(e->path, MAKE_ARGV(e), environ);
}

static void do_execvp(struct execdata *e)
{
    execvp(e->path, MAKE_ARGV(e));
}

static void do_execvpe(struct execdata *e)
{
    execvpe(e->path, MAKE_ARGV(e), environ);
}


#define run_child_test(path, execfunc)  \
    _run_child_test(path, __FUNCTION__, execfunc)

static void _run_child_test(const char *path, const char *testname, execfunc_t execfunc)
{
    struct execdata execdata = {
        .path = path,
        .testname = testname,
    };
    pid_t pid = fork();
    if (pid < 0)
        e_exception("Failed to fork: %m");
    if (pid == 0) {
        /* Child */
        execfunc(&execdata);
        e_exception("execv failed: %m\n");
        _exit(99);
    }

    /* Parent */
    int wstatus;
    while (waitpid(pid, &wstatus, 0) < 0) {
        if (errno == EINTR)
            continue;
        e_error("Failed to wait for child process %d: %m", pid);
    }

    if (WIFEXITED(wstatus)) {
        int code = WEXITSTATUS(wstatus);
        if (code != 0)
            e_error("Child exited with status %d", code);
        return;
    }

    /* Did child exit due to signal? */
    if (WIFSIGNALED(wstatus)) {
        int sig = WTERMSIG(wstatus);
        e_exception("Child terminated by signal %d", sig);
    }

    /* Unexpected case! */
    e_exception("Child exited for unknown reason! (wstatus == %d)", wstatus);
}


static void test__execl__proc_self_exe(void)
{
    run_child_test(SELF_EXE, do_execl);
}

static void test__execlp__proc_self_exe(void)
{
    run_child_test(SELF_EXE, do_execlp);
}

static void test__execle__proc_self_exe(void)
{
    run_child_test(SELF_EXE, do_execle);
}


static void test__execv__proc_self_exe(void)
{
    run_child_test(SELF_EXE, do_execv);
}

static void test__execve__proc_self_exe(void)
{
    run_child_test(SELF_EXE, do_execve);
}

static void test__execvp__proc_self_exe(void)
{
    run_child_test(SELF_EXE, do_execvp);
}

static void test__execvpe__proc_self_exe(void)
{
    run_child_test(SELF_EXE, do_execvpe);
}


static void test__execl__this_prog(void)
{
    run_child_test(readlinka(SELF_EXE), do_execl);
}

static void test__execlp__this_prog(void)
{
    run_child_test(readlinka(SELF_EXE), do_execlp);
}

static void test__execle__this_prog(void)
{
    run_child_test(readlinka(SELF_EXE), do_execle);
}

static void test__execv__this_prog(void)
{
    run_child_test(readlinka(SELF_EXE), do_execv);
}

static void test__execve__this_prog(void)
{
    run_child_test(readlinka(SELF_EXE), do_execve);
}

static void test__execvp__this_prog(void)
{
    run_child_test(readlinka(SELF_EXE), do_execvp);
}

static void test__execvpe__this_prog(void)
{
    run_child_test(readlinka(SELF_EXE), do_execvpe);
}


static void run_child_process_tests(void)
{
    test__execl__proc_self_exe();
    test__execlp__proc_self_exe();
    test__execle__proc_self_exe();

    test__execv__proc_self_exe();
    test__execve__proc_self_exe();
    test__execvp__proc_self_exe();
    test__execvpe__proc_self_exe();

    test__execl__this_prog();
    test__execlp__this_prog();
    test__execle__this_prog();

    test__execv__this_prog();
    test__execve__this_prog();
    test__execvp__this_prog();
    test__execvpe__this_prog();
}

/********************************************************************************/

int main(int argc, char **argv)
{
    const char *name = "parent";
    bool child = false;

    if (argc > 1) {
        name = join_strings("::", argv+1);
        child = true;
    }

    printf("Running test: %s\n", name);
    run_tests();

    if (!child)
        run_child_process_tests();

    return 0;
}
