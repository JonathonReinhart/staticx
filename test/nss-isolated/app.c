#include <errno.h>
#include <grp.h>
#include <pwd.h>
#include <netdb.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <arpa/inet.h>

#define ERROR_STATUS        1
#define EXCEPTION_STATUS    2

#define e_error(fmt, ...)     do {                                             \
    fprintf(stderr, "Error: " fmt "\n", ##__VA_ARGS__);                        \
    exit(ERROR_STATUS);                                                        \
} while(0)

#define e_exception(fmt, ...)     do {                                         \
    fprintf(stderr, "EXCEPTION: " fmt "\n", ##__VA_ARGS__);                    \
    exit(EXCEPTION_STATUS);                                                    \
} while(0)

#define QSTR                "\"%s\""

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
    printf("getpwuid(%d) => .pw_name="QSTR"\n", uid, pwd->pw_name);
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
    printf("getgrgid(%d) => .gr_name="QSTR"\n", gid, gr->gr_name);
}

static void test_hosts(const char *hostname)
{
    struct hostent *host = gethostbyname(hostname);
    char buf[16];

    if (!host) {
        e_error("Failed to look up host %s: %s (%d)",
                hostname, hstrerror(h_errno), h_errno);
    }
    printf("gethostbyname("QSTR") => "QSTR"\n", hostname,
            inet_ntop(AF_INET, host->h_addr_list[0], buf, sizeof(buf)));
}

static void test_services(const char *svcname)
{
   struct servent *srv;
   
   srv = getservbyname(svcname, NULL);
   if (!srv) {
       e_error("Failed to look up service %s", svcname);
   }
   printf("getservbyname("QSTR", NULL) => %d/%s\n", svcname,
           ntohs(srv->s_port), srv->s_proto);
}

int main(void)
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

    return 0;
}
