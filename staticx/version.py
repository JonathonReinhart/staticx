from pathlib import Path
import subprocess
import sys

# This logic has been adapted from that of PyInstaller
# https://github.com/pyinstaller/pyinstaller/

PACKAGEPATH = Path(__file__).absolute().parent
PROJPATH = PACKAGEPATH.parent

# Base version, which will be augmented with Git information
BASE_VERSION = '0.13.8'

# This string will be replaced by `git-archive`
# with the abbreviated commit hash
git_archive_rev = "$Format:%h$"

def git_describe():
    # Get the version from the local Git repository
    subprocess.check_call(['git', 'update-index', '-q', '--refresh'], cwd=PROJPATH)

    desc = subprocess.check_output(['git', 'describe', '--long', '--dirty', '--tag'], cwd=PROJPATH)
    desc = desc.decode('utf-8').strip()

    tag, commits, rev = desc.split('-', 2)
    tag = tag.lstrip('v')
    commits = int(commits)

    return tag, commits, rev

def get_version():

    # Git repo
    # If a local git repository is present, use `git describe` to provide a rich version
    gitdir = PROJPATH / '.git'
    if gitdir.exists():
        try:
            tag, commits, rev = git_describe()
        except FileNotFoundError:
            # git not installed
            pass
        else:
            # Ensure the base version matches the Git tag
            if tag != BASE_VERSION:
                raise Exception('Git revision different from base version')

            # No local version if we're on a tag
            if commits == 0 and not rev.endswith('dirty'):
                return BASE_VERSION

            return '{}+{}-{}'.format(BASE_VERSION, commits, rev)


    # Git archive
    # If this was produced via `git archive`, we'll use the version it provides
    if not git_archive_rev.startswith('$'):
        return '{}+g{}'.format(BASE_VERSION, git_archive_rev)


    # Package resource
    # Otherwise, we're either installed (e.g. via pip), or running from
    # an 'sdist' source distribution, and have a local PKG_INFO file.
    import pkg_resources
    try:
        return pkg_resources.get_distribution('staticx').version
    except pkg_resources.DistributionNotFound:
        pass


    # This shouldn't be able to happen
    sys.stderr.write('WARNING: Failed to determine version!\n')
    return BASE_VERSION


__version__ = get_version()

if __name__ == '__main__':
    print(__version__)
