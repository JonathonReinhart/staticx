#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <errno.h>
#include <assert.h>
#include <unistd.h>
#include <fcntl.h>
#include <elf.h>
#include <sys/wait.h>
#include "xz.h"
#include "error.h"
#include "mmap.h"
#include "util.h"
#include "common.h"
#include "extract.h"
#include "elfutil.h"


/* Our "home" directory, where the archive is extracted */
static const char *m_homedir;

static char *
path_join(const char *p1, const char *p2)
{
    char *result;
    if (asprintf(&result, "%s/%s", p1, p2) < 0)
        error(2, 0, "Failed to allocate path string");
    return result;
}

/******************************************************************************/

static void
set_interp(Elf_Ehdr *ehdr, const char *new_interp)
{
    /* Find the interpreter string */
    Elf_Phdr *ph = elf_get_proghdr_by_type(ehdr, PT_INTERP);
    if (!ph)
        error(2, 0, "Failed to find PT_INTERP header");

    /* Make sure it is NUL terminated */
    char *interp = ptr_add(ehdr, ph->p_offset);
    size_t interp_size = ph->p_filesz;

    if (interp[interp_size - 1] != '\0')
        error(2, 0, "Current INTERP not NUL terminated");

    debug_printf("Current program interpreter: \"%s\"\n", interp);

    if (strlen(new_interp) > interp_size - 1)
        error(2, 0, "Current INTERP too small");

    strcpy(interp, new_interp);
    debug_printf("Set new interpreter: \"%s\"\n", new_interp);
}

static void
set_rpath(Elf_Ehdr *ehdr, const char *new_rpath)
{
    /* Find the dynamic section */
    Elf_Shdr *dyn_sh = elf_get_section_by_name(ehdr, ".dynamic");
    if (!dyn_sh)
        error(2, 0, "Failed to find .dynamic section");

    /* Base and size of dynamic table */
    Elf_Dyn *dyn_table = ptr_add(ehdr, dyn_sh->sh_offset);
    size_t ndyn = dyn_sh->sh_size / sizeof(Elf_Dyn);


    /* Find the dynamic string section */
    /* Technically I think we should use DT_STRTAB, DT_STRSZ, but those are
     * *addresses*, and not file offsets */
    Elf_Shdr *dynstr_sh = elf_get_section_by_name(ehdr, ".dynstr");
    if (!dynstr_sh)
        error(2, 0, "Failed to find .dynamic section");


    /* Setup pointer to dynamic string table */
    char *dynstrtab = ptr_add(ehdr, dynstr_sh->sh_offset);
    size_t dynstrsz = dynstr_sh->sh_size;
    debug_printf("Dynamic string table: offset=0x%lX size=0x%lX\n",
            dynstr_sh->sh_offset, dynstrsz);

    /* Find needed dynamic tags */
#if 0
    Elf_Dyn *dt_strtab = NULL;  /* DT_STRTAB */
    Elf_Dyn *dt_strsz  = NULL;  /* DT_STRSZ */
#endif
    Elf_Dyn *dt_rpath  = NULL;  /* DT_RPATH */
    debug_printf("Dynamic tags:\n");
    for (size_t i = 0; i < ndyn; i++) {
        Elf_Dyn *dt = &dyn_table[i];
        debug_printf("0x%lX (%ld): 0x%lX\n", dt->d_tag, dt->d_tag, dt->d_un.d_val);

        switch (dt->d_tag) {
            case DT_NULL:
                goto dyn_done;
#if 0
            case DT_STRTAB:
                dt_strtab = dt;
                break;
            case DT_STRSZ:
                dt_strsz = dt;
                break;
#endif
            case DT_RPATH:
                dt_rpath = dt;
                break;
        }
    }
dyn_done:

#if 0
    if (!dt_strtab)
        error(2, 0, "Couldn't find DT_STRTAB tag");
    if (!dt_strsz)
        error(2, 0, "Couldn't find DT_STRSZ tag");
#endif
    if (!dt_rpath)
        error(2, 0, "Couldn't find DT_RPATH tag");


    /* Find RPATH */
    if (dt_rpath->d_un.d_val > dynstrsz)
        error(2, 0, "RPATH outside of dynamic strtab!");
    char *rpath = ptr_add(dynstrtab, dt_rpath->d_un.d_val);

    debug_printf("Current RPATH (0x%lX):\n", dt_rpath->d_un.d_val);
    debug_printf("\"%s\"\n", rpath);

    /* Set new RPATH */
    if (strlen(new_rpath) > strlen(rpath))
        error(2, 0, "Current RPATH too small");

    strcpy(rpath, new_rpath);
    debug_printf("Set new RPATH: \"%s\"\n", new_rpath);
}


static void
patch_prog_paths(const char *prog_path, const char *new_interp, const char *new_rpath)
{
    /* mmap the prog */
    struct map *map = mmap_file(prog_path, false);

    Elf_Ehdr *ehdr = map->map;
    if (!elf_is_valid(ehdr))
        error(2, 0, "Invalid ELF header");

    set_interp(ehdr, new_interp);
    set_rpath(ehdr, new_rpath);

    unmap_file(map);
    map = NULL;
}

static void
patch_app(const char *prog_path)
{
    char *interp_path = path_join(m_homedir, INTERP_FILENAME);
    const char *new_rpath = m_homedir;

    patch_prog_paths(prog_path, interp_path, new_rpath);

    free(interp_path);
}

static char *
create_tmpdir(void)
{
    static char template[] = "/tmp/staticx-XXXXXX";
    char *tmpdir = mkdtemp(template);
    if (!tmpdir)
        error(2, errno, "Failed to create tempdir");
    return tmpdir;
}

static char **
make_argv(int orig_argc, char **orig_argv, char *argv0)
{
    /**
     * Generate an argv to execute the user app:
     */
    int len = 1 + (orig_argc-1) + 1;
    char **argv = calloc(len, sizeof(char*));

    int w = 0;
    argv[w++] = argv0;

    for (int i=1; i < orig_argc; i++) {
        argv[w++] = orig_argv[i];
    }
    argv[w++] = NULL;
    assert(w == len);

    return argv;
}

static pid_t child_pid;

static void sig_handler(int signum)
{
    /* Forward received signal to child */
    debug_printf("Forwarding signal %d to child %d\n", signum, child_pid);
    kill(child_pid, signum);
}

static void
setup_sig_handler(int signum)
{
    struct sigaction sa = {
        .sa_handler = sig_handler,
    };
    sigemptyset(&sa.sa_mask);

    if (sigaction(signum, &sa, NULL) < 0)
        error(2, errno, "Error establishing handler for signal %d", signum);
}

static void
restore_sig_handler(int signum)
{
    struct sigaction sa = {
        .sa_handler = SIG_DFL,
    };
    sigemptyset(&sa.sa_mask);

    if (sigaction(signum, &sa, NULL) < 0)
        error(2, errno, "Error restoring handler for signal %d", signum);
}

/**
 * Run the user application in a child process.
 *
 * Returns the child wait status
 */
static int
run_app(int argc, char **argv, char *prog_path)
{
    /* Generate argv for child app */
    char **new_argv = make_argv(argc, argv, prog_path);

    debug_printf("New argv:\n");
    for (int i=0; ; i++) {
        char *a = new_argv[i];
        if (!a) break;

        debug_printf("[%d] = \"%s\"\n", i, a);
    }

    /* Create new process */
    child_pid = fork();
    if (child_pid < 0)
        error(2, errno, "Failed to fork child process");


    if (child_pid == 0) {
        /*** Child ***/
        debug_printf("child: Born\n");

        execv(new_argv[0], new_argv);

        fprintf(stderr, "Failed to execv() %s: %m\n", new_argv[0]);
        _exit(3);
    }

    /*** Parent ***/

    /* Forward terminating signals to child */
    setup_sig_handler(SIGINT);
    setup_sig_handler(SIGTERM);
    /* SIGKILL can't be caught */


    /* Wait for child to exit */
    int wstatus;
    while (waitpid(child_pid, &wstatus, 0) < 0) {
        if (errno == EINTR)
            continue;
        error(2, errno, "Failed to wait for child process %ld", child_pid);
    }
    child_pid = 0;

    /* Restore signal handlers */
    restore_sig_handler(SIGINT);
    restore_sig_handler(SIGTERM);

    return wstatus;
}

int
main(int argc, char **argv)
{
    xz_crc32_init();

    /* Create temporary directory where archive will be extracted */
    m_homedir = create_tmpdir();
    debug_printf("Home dir: %s\n", m_homedir);

    /* Extract the archive embedded in this program */
    extract_archive(m_homedir);

    /* Get path to user application inside temp dir */
    char *prog_path = path_join(m_homedir, PROG_FILENAME);

    /* Patch the user application ELF to run in the temp dir */
    patch_app(prog_path);

    /* Run the user application */
    int wstatus = run_app(argc, argv, prog_path);

    free(prog_path);
    prog_path = NULL;

    /* Cleanup */
    debug_printf("Removing temp dir %s\n", m_homedir);
    if (remove_tree(m_homedir) < 0) {
        fprintf(stderr, "staticx: Failed to cleanup %s: %m\n", m_homedir);
    }
    m_homedir = NULL;

    /* Did child exit normally? */
    if (WIFEXITED(wstatus)) {
        int code = WEXITSTATUS(wstatus);
        debug_printf("Child exited with status %d\n", code);
        return code;
    }

    /* Did child exit due to signal? */
    if (WIFSIGNALED(wstatus)) {
        int sig = WTERMSIG(wstatus);
        debug_printf("Child terminated due to signal %d\n", sig);

        /* Send the same signal to ourselves */
        raise(sig);
    }

    /* Unexpected case! */
    error(2, 0, "Child exited for unknown reason! (wstatus == %d)", wstatus);

    return 2;   // Make GCC happy
}
