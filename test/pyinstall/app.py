import os
import sys
import pwd

def get_resource_dir():
    default = os.path.dirname(os.path.abspath(__file__))
    return getattr(sys, '_MEIPASS', default)
    
print("Hello {}! Resource dir: {}".format(
    pwd.getpwuid(os.getuid()).pw_name,
    get_resource_dir()),
)

