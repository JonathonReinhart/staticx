
class Error(Exception):
    """Base type for all exceptions raised by staticx"""
    pass

class InternalError(Error):
    """Something internal to staticx went wrong"""
    pass

class ToolError(Error):
    """An external tool indicated an error"""
    def __init__(self, program, message=None):
        super().__init__(message or "'{}' failed".format(program))
        self.program = program

class MissingToolError(Error):
    """A required external tool is missing"""
    def __init__(self, program, package):
        super().__init__("Couldn't find '{}'. Is '{}' installed?".format(
            program, package))
        self.program = program
        self.package = package

class InvalidInputError(Error):
    """Input provided by the user is invalid"""
    pass

class UnsupportedRunpathError(InvalidInputError):
    """A library uses the unsupported RUNPATH dynamic entry

    See https://github.com/JonathonReinhart/staticx/issues/172
    """
    def __init__(self, libpath, runpath):
        super().__init__("{} uses unsupported DT_RUNPATH ({!r}).\n"
                "See https://github.com/JonathonReinhart/staticx/issues/188"
                .format(libpath, runpath))

class FormatMismatchError(Error):
    pass


class ArchiveError(Error):
    """Base type for exceptions raised from archive.py"""
    pass

class LibExistsError(ArchiveError):
    """Given library already exists in archive"""
    def __init__(self, lib):
        super().__init__(
                "Library '{}' already exists in archive".format(lib))
        self.lib = lib


class DirectoryExistsError(Error):
    """A given directory already exists"""
    def __init__(self, path):
        super().__init__(
                "{}: is a directory".format(path))
        self.path = path
