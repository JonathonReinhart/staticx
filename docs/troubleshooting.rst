Troubleshooting
===============

StaticX has to do some weird things in order to work. Thus, you might run into
trouble.

Run-time problems
-----------------
If, after bundling an application using StaticX, the resulting executable is
crashing due to symbol issues or segfaults:

Debug build
~~~~~~~~~~~
The first step is to use the ``--debug`` flag when bundling::

    $ staticx --debug myprog myprog.sx

This option will:

- Set loglevel to ``DEBUG`` while building the program
- Use a debug variant of the bootloader which:

    - Adds debug output (to stderr)
    - Includes DWARF debug info

.. note::

    Please include all debugging information if you open an issue.


GDB
~~~
If your program segfaults, you can run it under GDB.

Before giving the ``r`` command to run your program, use
``set follow-fork-mode child`` so GDB
`follows the child process <https://sourceware.org/gdb/onlinedocs/gdb/Forks.html>`_.

To get a backtrace::

    $ gdb --args ./myprog.sx
    set follow-fork-mode child
    r
    (segfault)
    bt -full
