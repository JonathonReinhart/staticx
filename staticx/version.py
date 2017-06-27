from __future__ import print_function
from os.path import abspath, dirname, exists, join, normpath
import subprocess
import sys

# This logic has been adapted from that of PyInstaller
# https://github.com/pyinstaller/pyinstaller/

PACKAGEPATH = abspath(dirname(__file__))
PROJPATH = dirname(PACKAGEPATH)

# Base version, which will be augmented with Git information
__version__ = '0.3.2'

def get_repo_version():
    gitdir = normpath(join(PROJPATH, '.git'))
    if exists(gitdir):
        # Get the version from the local Git repository
        subprocess.check_call(['git', 'update-index', '-q', '--refresh'], cwd=PROJPATH)
        desc = subprocess.check_output(['git', 'describe', '--long', '--dirty', '--tag'], cwd=PROJPATH).strip()

        tag, commits, rev = desc.split('-', 2)
        tag = tag.lstrip('v')

        # Ensure the base version matches the Git tag
        if tag != __version__:
            raise Exception('Git revision different from base version')

        return '+{}.{}'.format(commits, rev)

    else:
        # Git will update this string during git-archive with
        # the abbreviated commit hash.
        git_archive_rev = "$Format:%h$"
        if git_archive_rev.startswith('$'):
            # Substitution has not taken place
            raise Exception('Git revision not substituted in _gitrevision.py')

        return '+g{}'.format(git_archive_rev)


if exists(join(PACKAGEPATH, '..', 'setup.py')):
    # Running from source, or being imported from setup.py
    try:
        __version__ += get_repo_version()
    except Exception as e:
        sys.stderr.write('WARNING: Failed to get git revision: {}\n'.format(e))

else:
    # StaticX was installed
    import pkg_resources
    __version__ = pkg_resources.get_distribution('staticx').version


if __name__ == '__main__':
    print(__version__)
