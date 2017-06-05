# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]
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


[Unreleased]: https://github.com/JonathonReinhart/scuba/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/JonathonReinhart/staticx/compare/v0.1.0...v0.2.0

[#9]: https://github.com/JonathonReinhart/staticx/pull/9
[#12]: https://github.com/JonathonReinhart/staticx/pull/12
[#18]: https://github.com/JonathonReinhart/staticx/pull/18
[#21]: https://github.com/JonathonReinhart/staticx/pull/21
