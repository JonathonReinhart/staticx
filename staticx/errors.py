import abc
from pathlib import Path
from typing import Union

class Error(Exception):
    """Base type for all exceptions raised by staticx"""
    pass

class InternalError(Error):
    """Something internal to staticx went wrong"""
    pass

class ToolError(Error):
    """An external tool indicated an error"""
    def __init__(self, program: str, message: str = ""):
        super().__init__(message or f"'{program}' failed")
        self.program = program

class MissingToolError(Error):
    """A required external tool is missing"""
    def __init__(self, program: str, package: str):
        super().__init__(f"Couldn't find '{program}'. Is '{package}' installed?")
        self.program = program
        self.package = package

class InvalidInputError(Error):
    """Input provided by the user is invalid"""
    pass


class UnsupportedDynTagError(InvalidInputError, abc.ABC):
    """A library uses an unsupported dynamic entry

    See https://github.com/JonathonReinhart/staticx/issues/172
    """
    tag: str

    def __init__(self, libpath: str, value: str):
        self.libpath = libpath
        self.value = value
        super().__init__(
                f"{libpath} uses unsupported {self.tag} ({value!r}).\n"
                "See https://github.com/JonathonReinhart/staticx/issues/188"
                )

class UnsupportedRpathError(UnsupportedDynTagError):
    tag = 'DT_RPATH'

class UnsupportedRunpathError(UnsupportedDynTagError):
    tag = 'DT_RUNPATH'


class FormatMismatchError(Error):
    pass


class ArchiveError(Error):
    """Base type for exceptions raised from archive.py"""
    pass

class LibExistsError(ArchiveError):
    """Given library already exists in archive"""
    def __init__(self, lib: str):
        super().__init__(
                f"Library '{lib}' already exists in archive")
        self.lib = lib


class DirectoryExistsError(Error):
    """A given directory already exists"""
    def __init__(self, path: Union[Path, str]):
        super().__init__(
                f"{path}: is a directory")
        self.path = path
