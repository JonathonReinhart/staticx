#ifndef UTIL_H
#define UTIL_H

int remove_tree(const char *pathname);
char *strtrim(char *str);
int     mkpath     (const char *dir, mode_t mode);
const char * get_tmpdir(void);
char *get_tmp_root(void);
#endif /* UTIL_H */
