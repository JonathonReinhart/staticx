import os
import sys
import pwd
import subprocess

def get_resource_dir():
    default = os.path.dirname(os.path.abspath(__file__))
    return getattr(sys, '_MEIPASS', default)
    
print(f"Hello {pwd.getpwuid(os.getuid()).pw_name}!")
print(f"Resource dir: {get_resource_dir()}")
