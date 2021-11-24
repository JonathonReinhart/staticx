Introduction
============
StaticX takes a typical dynamic executable and bundles it, along with all of
its shared library dependencies, into a single executable. This resulting
executable is actually the StaticX *bootloader* with an attached *archive*
containing the user executable and libraries. The bootloader will extract the
archive to a temporary directory, fix up the executable in its new home, launch
it, and clean up after it exits.

StaticX is inspired by `PyInstaller`_, and includes special provisions for
working well with PyInstalled executables as input::

     __________       __________          ________________
    |          |     |           \       |                |
    |  Python  |     |            \      |   PyInstalled  |
    |   App    | --> | PyInstaller > --> |      App       |
    |          |     |            /      | (reqs libc...) |
    |__________|     |___________/       |________________|
                                                |
                +-------------------------------+
                |     __________          ________________
                |    |           \       |                |
                |    |            \      |    StaticX     |
                +--> |  StaticX    > --> |      App       |
                     |            /      |                |
                     |___________/       |________________|



.. _PyInstaller: https://www.pyinstaller.org/
