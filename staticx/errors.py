
class Error(Exception):
    """Base type for all exceptions raised by staticx"""
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
