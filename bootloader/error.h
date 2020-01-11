#ifndef ERROR_H
#define ERROR_H

void error(int status, int errnum, const char *format, ...)
    __attribute__ ((format (printf, 3, 4) ));

#endif /* ERROR_H */
