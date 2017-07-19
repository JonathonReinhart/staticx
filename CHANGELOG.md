# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]
### Changed
- Detect if user app is a different machine type than the bootloader ([#56])


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


[Unreleased]: https://github.com/JonathonReinhart/staticx/compare/v0.5.0...HEAD
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
