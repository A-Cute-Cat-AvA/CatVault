import os

from Fix_file import get_base_dir, fix_password_index
from Save_Password import VaultManager

VAULT_FOLDER = os.path.join(get_base_dir(), "Password")

def verify_password(userpassword):
    vault = VaultManager.VaultManager(VAULT_FOLDER, userpassword)
    index = os.path.join(get_base_dir(), "Password", "index.dat")
    if os.path.isfile(index):
        try:
            data = vault.load_index()
            return "OK"
        except Exception:
            return "ERROR"
    elif not os.listdir(VAULT_FOLDER):
        fix_password_index()
        return "OK"
    else:
        return 0