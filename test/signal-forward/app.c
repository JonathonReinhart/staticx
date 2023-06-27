/**
 * This test app:
 * - prints "ready" when it is ready for signals
 * - prints "signal X" when it receives signal X
 * - exits on stdin EOF
 */
#define _GNU_SOURCE
#include <errno.h>
#include <error.h>
#include <stdio.h>
#include <poll.h>
#include <unistd.h>
#include <signal.h>
#include <sys/signalfd.h>

#define ERROR_STATUS    1

#define POLLIDX_STDIN   0
#define POLLIDX_SIGFD   1

#define ARRAY_LEN(x)    (sizeof(x) / sizeof(x[0]))
#define POLL_FOREVER    -1

#define DEBUG 0

#define dbg(fmt, ...)   \
    if (DEBUG) fprintf(stderr, "[%s] " fmt, __FUNCTION__, ##__VA_ARGS__)


static void sigset_all_signals(sigset_t *set)
{
    int signum;

    sigemptyset(set);
    
    /* Add all normal signals */
    for (signum = 1; signum <= 31; signum++) {
        if (sigaddset(set, signum))
            error(ERROR_STATUS, errno, "sigaddset(%d) failed", signum);
    }

    /* Add RT signals */
    for (signum = SIGRTMIN; signum <= SIGRTMAX; signum++) {
        if (sigaddset(set, signum))
            error(ERROR_STATUS, errno, "sigaddset(%d) failed", signum);
    }
}

/* Test and clear, short */
static inline short int testclrs(short int *field, unsigned int mask)
{
    short int val = *field & mask;
    *field &= ~mask;
    return val;
}

int main(int argc, char **argv)
{
    sigset_t sigmask;
    int sig_fd;

    /* output channel is lines of text */
    setlinebuf(stdout);

    sigset_all_signals(&sigmask);

    sig_fd = signalfd(-1, &sigmask, 0);
    if (sig_fd < 0)
        error(ERROR_STATUS, errno, "signalfd failed");

	/**
     * Block signals so they aren't handlded according to their default
     * dispositions.
     */
    if (sigprocmask(SIG_BLOCK, &sigmask, NULL) == -1)
        error(ERROR_STATUS, errno, "sigprocmask failed");

    struct pollfd pollfds[] = {
        [POLLIDX_STDIN] = {
            .fd = STDIN_FILENO,
            .events = POLLIN,
        },
        [POLLIDX_SIGFD] = {
            .fd = sig_fd,
            .events = POLLIN,
        },
    };

    dbg("Ready to start polling\n");
    printf("ready\n");
    for (;;) {
        int npoll;
        ssize_t nread;

        npoll = poll(pollfds, ARRAY_LEN(pollfds), POLL_FOREVER);
        if (npoll < 0)
            error(ERROR_STATUS, errno, "poll failed");
        dbg("poll() returned %d\n", npoll);

        /* stdin */
        if (testclrs(&pollfds[POLLIDX_STDIN].revents, POLLHUP)) {
            dbg("stdin HUP\n");
            goto done;
        }
        if (testclrs(&pollfds[POLLIDX_STDIN].revents, POLLIN)) {
            char buf[128];
            dbg("stdin readable\n");
            nread = read(STDIN_FILENO, buf, sizeof(buf));
            dbg("read(stdin) => %zd\n", nread);
            if (nread < 0)
                error(ERROR_STATUS, errno, "read(stdin) failed");
            if (nread == 0) {
                dbg("stdin EOF\n");
                goto done;
            }
        }
        if (pollfds[POLLIDX_STDIN].revents) {
            dbg("WARNING: STDIN revents unhandled: 0x%X\n",
                    pollfds[POLLIDX_STDIN].revents);
        }

        /* sig_fd */
        if (testclrs(&pollfds[POLLIDX_SIGFD].revents, POLLIN)) {
            struct signalfd_siginfo siginfo;
            dbg("sig_fd readable\n");
            nread = read(sig_fd, &siginfo, sizeof(siginfo));
            if (nread != sizeof(siginfo))
                error(ERROR_STATUS, errno, "read(sfd) failed");

            printf("signal %d\n", siginfo.ssi_signo);
        }
        if (pollfds[POLLIDX_SIGFD].revents) {
            dbg("WARNING: SIGFD revents unhandled: 0x%X\n",
                    pollfds[POLLIDX_SIGFD].revents);
        }
    }

done:
    close(sig_fd);

    return 0;
}
