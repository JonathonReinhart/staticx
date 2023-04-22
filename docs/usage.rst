Usage
=====

Synopsis
--------
.. code-block::

   staticx [-h]
           [-l LIB] [--strip] [--no-compress] [-V]
           [--loglevel LEVEL]
           PROG OUTPUT

Positional Arguments:
  **PROG**
          Input program to bundle

  **OUTPUT**
          Output path

Options:
  -h, --help            Show help message and exit
  -l LIB                Add additional library (absolute path)

                        This option can be given multiple times.

  --strip               Strip binaries before adding to archive (reduces size)
  --no-compress         Don't compress the archive (increases size)
  --loglevel LEVEL      Set the logging level (default: WARNING)

                        Options: DEBUG,INFO,WARNING,ERROR,CRITICAL

  --debug               Set loglevel to DEBUG and use a debug version of the
                        bootloader

  --tmprootdir          Set tmprootdir (where the files will be unpacked
                        default /tmp/staticx-XXXXXX)

  -V, --version         Show StaticX version and exit



Usage
-----
Basic wrapping of an executable::

    staticx /path/to/exe /path/to/output

StaticX will automatically discover and bundle most normal linked libraries.
However, libraries loaded by an application at runtime via ``dlopen()`` cannot
currently be detected. These can be manually included in the application bundle
by using the ``-l`` option (any number can be specified by repeating the -l
option)::

    staticx -l /path/to/fancy/library.so /path/to/exe /path/to/output

Caveats
-------
StaticX employs a number of tricks to run applications with only their bundled
libraries to ensure compatibilitiy. Because of this, there are some caveats
that apply to StaticX-bundled applications:

- The dynamic linker is instructed (via ``nodeflib``) to only permit bundled
  libraries to be loaded.
- Target `NSS`_ configuration (``/etc/nsswitch.conf``) is ignored (for
  GLIBC-linked applications) which means that some advanced name services (e.g.
  Active Directory) will not be available at runtime. For example, looking up
  the UID number of a domain user will not work.

.. _NSS: https://en.wikipedia.org/wiki/Name_Service_Switch


Run-time Information
--------------------
StaticX sets the following environment variables for the wrapped user program:

- ``STATICX_BUNDLE_DIR``: The absolute path of the "bundle" directory, the
  temporary dir where the archive has been extracted.
- ``STATICX_PROG_PATH``: The absolute path of the program being executed.
