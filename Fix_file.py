import os
import sys

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def fix_password_folder():
    folder = os.path.join(get_base_dir(), "Password")
    if os.path.isdir(folder):
        return "OK"
    else:
        os.mkdir(folder)
        return "ERROR"

def fix_password_index():
    file = os.path.join(get_base_dir(), "Password", "index.dat")
    if os.path.isfile(file):
        return "OK"
    else:
        open(file, "wb").close()
        return "ERROR"