Unsupported ``RPATH``/``RUNPATH``
=================================

You might be here because you encountered an error like this::

    staticx: Unsupported PyInstaller input

    One or more libraries included in the PyInstaller archive uses unsupported RPATH/RUNPATH tags:

      /tmp/staticx-pyi-5ys8gizg/libbar.so: DT_RUNPATH='/bogus/absolute/path'
      /tmp/staticx-pyi-5ys8gizg/libfoo.so: DT_RUNPATH='/bogus/absolute/path'

This page will attempt to explain the problem.


What are ``RPATH`` / ``RUNPATH``?
---------------------------------
``RPATH`` and ``RUNPATH`` are a feature of the GNU dynamic linker/loader. These
are entries in the ``.dynamic`` section which allow a dynamic executable or
library to augment or override the preconfigured library path list of the
dynamic loader (``ld.so``).

See also: `RPATH on Wikipedia <https://en.wikipedia.org/wiki/Rpath>`_


Why are ``RPATH`` / ``RUNPATH`` problematic?
--------------------------------------------
These options can circumvent StaticX's ability to maintain positive control of
the library search path used by ``ld.so``. By doing so, they can allow
target-system libraries to be undesirably loaded, possibly causing symbol
errors or runtime crashes. After all, StaticX's *modus operandi* is to only
execute code included in the bundled archive.

Since StaticX works by setting ``RPATH`` on the bundled user executable, there
is no need for any of the bundled libraries to use ``RPATH``/``RUNPATH``.
Because of this, StaticX will *strip* ``RPATH``/``RUNPATH`` entries from any
library added to the archive. However, StaticX **cannot** modify libraries
which are already included in the archive of a PyInstaller application.

``RPATH``
~~~~~~~~~
``RPATH`` is allowed in PyInstaller-included libraries as long as the path is
relative to ``$ORIGIN`` (the directory where the dynamic executable lives).

If StaticX is complaining about ``RPATH``, it is probably because the library
is referencing an absolute path (e.g. ``/usr/local/lib``).

``RUNPATH``
~~~~~~~~~~~
``RUNPATH`` is even more problematic, because it causes ``ld.so`` to
**completely disregard** the ``RPATH`` set by the StaticX bootloader at program
launch. For this reason, ``RUNPATH`` is always forbidden.

Unfortunately, this problem is becoming more common since GNU ``ld`` now
defaults to emitting ``RUNPATH`` when  the ``-rpath`` option is given.


So what do I do now?
--------------------
Unfortunately, fixing a problematic PyInstaller-generated executable is not
straightforward. The goal is to remove the problematic libraries or replace
them with builds which do not use ``RUNPATH``. (A build which uses ``RPATH``
is probably acceptable, see above.)

One can sometimes fix this problem by adding ``--disable-new-dtags`` to
``CFLAGS`` when building/installing a Python package which uses native
extensions. The best way to do this is to install them from source into a
virtual environment.



References
----------

* The underlying issue was originally described in `#169`_.
* The auditing check which emits this error was added in `#173`_,
  and updated in `#208`_.

.. _#169: https://github.com/JonathonReinhart/staticx/issues/169
.. _#173: https://github.com/JonathonReinhart/staticx/pull/173
.. _#208: https://github.com/JonathonReinhart/staticx/pull/208
