# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

## [0.13.4] - 2021-10-22
### Changed
- Perform RUNPATH auditing on all PyInstaller archive libraries before aborting ([#208])


## [0.13.3] - 2021-10-14
### Fixed
- Fix ldd warning about libnssfix.so not being executable ([#204])


## [0.13.2] - 2021-10-09
### Added
- Log additional diagnostic information at startup ([#199])


## [0.13.1] - 2021-10-06
### Added
- Log staticx version and arguments at startup ([#197])


## [0.13.0] - 2021-10-04
### Added
- Added auditing of all shared libraries to detect problematic usages of
  `RPATH`/`RUNPATH`. Libraries now have `RPATH`/`RUNPATH` removed while being
  added, unless those libraries come from a PyInstalled application. ([#173])

### Changed
- Rework library-adding code to lazily copy libraries before modifying ([#192])


## [0.12.3] - 2021-09-04
### Added
- Added `STATICX_LDD` environment variable to override the `ldd` executable
  used by Staticx to discover library dependencies. ([#180])

### Changed
- `LD_LIBRARY_PATH` enviroment variable is now maintained when invoking `ldd`
  to discover dependencies ([#185])


## [0.12.2] - 2021-05-22
### Fixed
- Worked around patchelf bug which caused `Couldn't find DT_RPATH tag`
  error at runtime ([#175])
- Fixed a bug which caused the glibc hook to crash on non-glibc
  executables ([#179])


## [0.12.1] - 2021-02-06
### Fixed
- Fixed bug causing libnssfix to be built incorrectly under
  SCons v4.1.0 ([#168])


## [0.12.0] - 2020-09-29
### Added
- Added support for native 32-bit builds of bootloader ([#149])

### Changed
- Binary wheels now identify as `manylinux1_x86_64` ([#151])

### Fixed
- Source distributions build correctly again ([#153], [#157])

### Removed
- Removed more Python 2.7 compatibility cruft ([#142], [#146], [#148])
- Removed additional unnecessary elements of libtar ([#154])


## [0.11.0] - 2020-07-27
### Changed
- Improved tar extraction to minimize number of write() calls ([#131])
- Set NODEFLIB flag to prevent any libraries from the target system
  from being loaded ([#138])
- "nssfix" is used to prevent target system `/etc/nssswitch.conf` from being
  used which would attempt to load system `libnss_*.so` libraries ([#139])

### Fixed
- Bundled applications retain their original name ([#135])


## [0.10.0] - 2020-05-30
### Added
- Added `sx-extract` archive extraction/dumping tool ([#114])

### Removed
- Drop support for Python 2.7 ([#115])


## [0.9.1] - 2020-01-29
### Fixed
- Correct handling of absolute path symlink in ldd output ([#118])
- Fixed null tmpdir argument error on GCC9 ([#120])
- Fixed ldd "you do not have execution permission..." warning ([#122])


## [0.9.0] - 2020-01-11
### Added
- Staticx binaries now respect `$TMPDIR` for creating temporary directory ([#101])

### Changed
- Ensure user program is always marked executable in archive ([#112])

### Fixed
- Don't hard-code exclusion of `linux-vdso.so.1` ([#102])

### Removed
- Drop support for Python 3.4 ([#111])


## [0.8.1] - 2019-12-30
### Changed
- Changed `setup.py` to respect `BOOTLOADER_CC`, to simplify `.travis.yml` and
  ensure that released wheels are always built with musl-libc.

## [0.8.0] - 2019-12-30
### Added
- Set `STATICX_BUNDLE_DIR` and `STATICX_PROG_PATH` in child process ([#81])
- Add `--debug` flag to bundle debug bootloader ([#87])

### Changed
- Changed pyinstaller hook to ignore static executables ([#83])

### Fixed
- Always generate tar archive in GNU format. Python 3.8 changed the default to
  PAX which is not supported by our libtar. ([#85])
- Add backports.lzma to setup.py for Python 2, removing manual requirement ([#89])

## [0.7.0] - 2019-03-10
### Changed
- Refactored and trimmed libtar ([#74])

### Fixed
- Correctly handle applications and libraries that specify an `RPATH` including
  `$ORIGIN`, including apps built with PyInstaller ([#75])
- Fixed potential issue in ignored libraries list ([#77])
- Fixed missing libxz in source distributions ([#77])


## [0.6.0] - 2018-11-13
### Added
- Add `--no-compress` option to store archive uncompressed ([#58])

### Changed
- Detect if user app is a different machine type than the bootloader ([#56])
- Drop support for Python 3.2 and 3.3 ([#65])

### Fixed
- Use `<sys/sysmacros.h>` for makedev() ([#63])
- Handle subdirectories when extracting Pyinstaller archives ([#69])
- Handle shared objects with no dependencies ([#70])


## [0.5.0] - 2017-07-16
### Added
- Added `--strip` option to strip binaries while adding to archive ([#39])

### Changed
- Raise error if given output path is a directory ([#52])
- Dynamically select XZ BCJ filter ([#54])


## [0.4.1] - 2017-07-15
### Fixed
- Fixes for release builds deployed to PyPI

## [0.4.0] - 2017-07-13
### Added
- Compress archive with LZMA (plus x86 BCJ filter) ([#46])


## [0.3.2] - 2017-06-15
### Fixed
- Fixed PyPI bdists not including bootloader ([#32])


## [0.3.1] - 2017-06-14
### Fixed
- Work around `FTW_MOUNT` bug in musl<1.0.0 ([#30])


## [0.3.0] - 2017-06-13
### Added
- Auto-detect additional dependencies for apps built with PyInstaller ([#21])

### Changed
- Compatibility fixes for older versions of Python and GCC
- Handle multiple levels of library symlinks ([#18])


## [0.2.0] - 2017-05-31
### Changed
- Work on temporary file while building application ([#12])
- Run user application in child process to enable cleanup ([#9])


## 0.1.0 - 2017-05-30
Initial release


[Unreleased]: https://github.com/JonathonReinhart/staticx/compare/v0.13.4...HEAD
[0.13.4]: https://github.com/JonathonReinhart/staticx/compare/v0.13.3...v0.13.4
[0.13.3]: https://github.com/JonathonReinhart/staticx/compare/v0.13.2...v0.13.3
[0.13.2]: https://github.com/JonathonReinhart/staticx/compare/v0.13.1...v0.13.2
[0.13.1]: https://github.com/JonathonReinhart/staticx/compare/v0.13.0...v0.13.1
[0.13.0]: https://github.com/JonathonReinhart/staticx/compare/v0.12.3...v0.13.0
[0.12.3]: https://github.com/JonathonReinhart/staticx/compare/v0.12.2...v0.12.3
[0.12.2]: https://github.com/JonathonReinhart/staticx/compare/v0.12.1...v0.12.2
[0.12.1]: https://github.com/JonathonReinhart/staticx/compare/v0.12.0...v0.12.1
[0.12.0]: https://github.com/JonathonReinhart/staticx/compare/v0.11.0...v0.12.0
[0.11.0]: https://github.com/JonathonReinhart/staticx/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/JonathonReinhart/staticx/compare/v0.9.1...v0.10.0
[0.9.1]: https://github.com/JonathonReinhart/staticx/compare/v0.9.0...v0.9.1
[0.9.0]: https://github.com/JonathonReinhart/staticx/compare/v0.8.1...v0.9.0
[0.8.1]: https://github.com/JonathonReinhart/staticx/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/JonathonReinhart/staticx/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/JonathonReinhart/staticx/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/JonathonReinhart/staticx/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/JonathonReinhart/staticx/compare/v0.4.1...v0.5.0
[0.4.1]: https://github.com/JonathonReinhart/staticx/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/JonathonReinhart/staticx/compare/v0.3.2...v0.4.0
[0.3.2]: https://github.com/JonathonReinhart/staticx/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/JonathonReinhart/staticx/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/JonathonReinhart/staticx/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/JonathonReinhart/staticx/compare/v0.1.0...v0.2.0

[#9]: https://github.com/JonathonReinhart/staticx/pull/9
[#12]: https://github.com/JonathonReinhart/staticx/pull/12
[#18]: https://github.com/JonathonReinhart/staticx/pull/18
[#21]: https://github.com/JonathonReinhart/staticx/pull/21
[#30]: https://github.com/JonathonReinhart/staticx/pull/30
[#32]: https://github.com/JonathonReinhart/staticx/pull/32
[#39]: https://github.com/JonathonReinhart/staticx/pull/39
[#46]: https://github.com/JonathonReinhart/staticx/pull/46
[#52]: https://github.com/JonathonReinhart/staticx/pull/52
[#54]: https://github.com/JonathonReinhart/staticx/pull/54
[#56]: https://github.com/JonathonReinhart/staticx/pull/56
[#58]: https://github.com/JonathonReinhart/staticx/pull/58
[#63]: https://github.com/JonathonReinhart/staticx/pull/63
[#65]: https://github.com/JonathonReinhart/staticx/pull/65
[#69]: https://github.com/JonathonReinhart/staticx/pull/69
[#70]: https://github.com/JonathonReinhart/staticx/pull/70
[#74]: https://github.com/JonathonReinhart/staticx/pull/74
[#75]: https://github.com/JonathonReinhart/staticx/pull/75
[#77]: https://github.com/JonathonReinhart/staticx/pull/77
[#81]: https://github.com/JonathonReinhart/staticx/pull/81
[#83]: https://github.com/JonathonReinhart/staticx/pull/83
[#85]: https://github.com/JonathonReinhart/staticx/pull/85
[#87]: https://github.com/JonathonReinhart/staticx/pull/87
[#89]: https://github.com/JonathonReinhart/staticx/pull/89
[#101]: https://github.com/JonathonReinhart/staticx/pull/101
[#102]: https://github.com/JonathonReinhart/staticx/pull/102
[#111]: https://github.com/JonathonReinhart/staticx/pull/111
[#112]: https://github.com/JonathonReinhart/staticx/pull/112
[#114]: https://github.com/JonathonReinhart/staticx/pull/114
[#115]: https://github.com/JonathonReinhart/staticx/pull/115
[#118]: https://github.com/JonathonReinhart/staticx/pull/118
[#120]: https://github.com/JonathonReinhart/staticx/pull/120
[#122]: https://github.com/JonathonReinhart/staticx/pull/122
[#131]: https://github.com/JonathonReinhart/staticx/pull/131
[#135]: https://github.com/JonathonReinhart/staticx/pull/135
[#138]: https://github.com/JonathonReinhart/staticx/pull/138
[#142]: https://github.com/JonathonReinhart/staticx/pull/142
[#146]: https://github.com/JonathonReinhart/staticx/pull/146
[#148]: https://github.com/JonathonReinhart/staticx/pull/148
[#149]: https://github.com/JonathonReinhart/staticx/pull/149
[#151]: https://github.com/JonathonReinhart/staticx/pull/151
[#153]: https://github.com/JonathonReinhart/staticx/pull/153
[#154]: https://github.com/JonathonReinhart/staticx/pull/154
[#157]: https://github.com/JonathonReinhart/staticx/pull/157
[#168]: https://github.com/JonathonReinhart/staticx/pull/168
[#173]: https://github.com/JonathonReinhart/staticx/pull/173
[#175]: https://github.com/JonathonReinhart/staticx/pull/175
[#179]: https://github.com/JonathonReinhart/staticx/pull/179
[#180]: https://github.com/JonathonReinhart/staticx/pull/180
[#185]: https://github.com/JonathonReinhart/staticx/pull/185
[#192]: https://github.com/JonathonReinhart/staticx/pull/192
[#197]: https://github.com/JonathonReinhart/staticx/pull/197
[#199]: https://github.com/JonathonReinhart/staticx/pull/199
[#204]: https://github.com/JonathonReinhart/staticx/pull/204
[#208]: https://github.com/JonathonReinhart/staticx/pull/208
