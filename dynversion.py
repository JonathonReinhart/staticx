import os
import staticx.version

# Dynamic versioning

def get_dynamic_version():

    # Travis builds
    # If we're not building for a tag, then append the build number
    build_num = os.getenv('TRAVIS_BUILD_NUMBER')
    build_tag = os.getenv('TRAVIS_TAG')
    if (not build_tag) and (build_num != None):
        return '{}.{}'.format(staticx.version.BASE_VERSION, build_num)

    return staticx.version.__version__

if __name__ == '__main__':
    print(get_dynamic_version())
