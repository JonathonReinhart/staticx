#ifndef UTIL_H
#define UTIL_H

int remove_tree(const char *pathname);
int     mkpath     (const char *dir, mode_t mode);
const char * get_tmpdir(void);
char *strtrim(char *str);
char *get_tmp_root(void);
#endif /* UTIL_H */
