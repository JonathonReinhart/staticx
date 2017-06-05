
class Error(Exception):
    """Base type for all exceptions raised by staticx"""
    pass

class InternalError(Error):
    """Something internal to staticx went wrong"""
    pass

class ToolError(Error):
    """An external tool indicated an error"""
    def __init__(self, program, message=None):
        super(ToolError,self).__init__(message or "'{}' failed".format(program))
        self.program = program

class MissingToolError(Error):
    """A required external tool is missing"""
    def __init__(self, program, package):
        super(MissingToolError, self).__init__("Couldn't find '{}'. Is '{}' installed?".format(
            program, package))
        self.program = program
        self.package = package

class InvalidInputError(Error):
    """Input provided by the user is invalid"""
    pass



class ArchiveError(Error):
    """Base type for exceptions raised from archive.py"""
    pass

class LibExistsError(ArchiveError):
    """Given library already exists in archive"""
    def __init__(self, lib):
        super(LibExistsError, self).__init__(
                "Library '{}' already exists in archive".format(lib))
        self.lib = lib
