"""
Vault manager
"""

import os
import json
import uuid
from argon2.low_level import hash_secret_raw, Type
from Fix_file import get_base_dir
from Save_Password import PasswordEntry
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

VAULT_FOLDER = os.path.join(get_base_dir(), "Password")

class VaultManager():
    """
    Vault manager class
    """
    def __init__(self, filepath, main_password):
        self.filepath = filepath
        self.index_file = os.path.join(filepath, "index.dat")
        self.main_password = main_password.encode('utf-8')

    def _get_key(self, salt=None):
        if salt is None:
            salt = os.urandom(16)
        key = hash_secret_raw(
        secret=self.main_password,
        salt=salt,
        time_cost=3,
        memory_cost=65536,
        parallelism=4,
        hash_len=32,
        type=Type.ID
    )
        return key, salt
    def _get_json(self, name, remarks, password):
        pwd_et = PasswordEntry.PasswordEntry(name=name, remarks=remarks, password=password)
        return json.dumps(pwd_et.to_dict(), ensure_ascii=False)

    def _lock_json(self, json_str):
        key,salt = self._get_key()
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, json_str.encode("utf-8"), None)
        return salt+nonce+ciphertext

    def _have_lock(self, name, remarks, password):
        if remarks == "":
            remarks = None
        return self._lock_json(self._get_json(name, remarks, password))

    def get_password(self, row_data):
        salt = row_data[:16]
        nonce = row_data[16:28]
        ciphertext = row_data[28:]
        
        key, _ = self._get_key(salt)
        aesgcm = AESGCM(key)
        decrypted = aesgcm.decrypt(nonce, ciphertext, None)

        json_str = decrypted.decode("utf-8")
        data_dict = json.loads(json_str)
        
        return data_dict

    def _entry_file(self, file_id):
        return os.path.join(self.filepath, f"{file_id}.dat")

    def save_password(self, name, remarks, password, file_id=None):
        if file_id is None:
            file_id = name
        packed_data = self._have_lock(name, remarks, password)
        with open(self._entry_file(file_id), "xb") as file:
            file.write(packed_data)

    def update_password(self, file_id, name, remarks, password):
        packed_data = self._have_lock(name, remarks, password)
        with open(self._entry_file(file_id), "wb") as file:
            file.write(packed_data)

    def load_password(self, file_id):
        with open(self._entry_file(file_id), "rb") as file:
            packed_data = file.read()
        return self.get_password(packed_data)

    def delete_password(self, file_id):
        entry_file = self._entry_file(file_id)
        if os.path.isfile(entry_file):
            os.remove(entry_file)

    def load_index(self):
        if not os.path.isfile(self.index_file):
            return {}
        with open(self.index_file,"rb") as file:
            packed_data = file.read()
        if len(packed_data) == 0:
            return {}
        index_dict = self.get_password(packed_data)
        return index_dict

    def save_index(self, index_dict):
        packed_data = self._lock_json(json.dumps(index_dict, ensure_ascii=False))
        with open(self.index_file, "wb") as file:
            file.write(packed_data)

    def add_index(self, name, index_dict):
        uuid_name = uuid.uuid4().hex
        index_dict[uuid_name] = name
        return index_dict

    def find_index(self, name, index_dict):
        for key, value in index_dict.items():
            if value == name:
                return key
        return None

    def delete_index(self, name, index_dict):
        target_key = self.find_index(name, index_dict)
        if target_key is not None:
            del index_dict[target_key]
        else:
            raise KeyError(f"Debug:no found {name}")
        return index_dict