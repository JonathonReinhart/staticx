#include <stdio.h>
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

#define NSSWITCH_CONF(name, svcline) { .dbname = name, .service_line = svcline, },
static struct dbspec m_dbspecs[] = {
#include "nsswitch_conf.h"
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
    configure_nss();
}
