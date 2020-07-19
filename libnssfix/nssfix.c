#include <stdio.h>
#include <stdlib.h>
#include <nss.h>

#define ARRAY_LEN(x)        (sizeof(x)/sizeof(x[0]))

#ifdef DEBUG
# define debug(fmt, ...)    fprintf(stderr, "%s: " fmt, "nssfix", ##__VA_ARGS__)
#else
# define debug(fmt, ...)
#endif

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


__attribute__((constructor(101)))
static void init_nssfix(void)
{
    /**
     * Unset LD_PRELOAD so libnssfix.so is not loaded for any child program
     * executed by the user application. This assumes that any such program
     * would be either a system (non-bundled) executable, or statically-linked.
     * See https://github.com/JonathonReinhart/staticx/issues/129#issuecomment-657938274
     */
    unsetenv("LD_PRELOAD");

    configure_nss();
}
