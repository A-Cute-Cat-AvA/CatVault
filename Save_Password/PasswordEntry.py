"""
This file is used to parse save password JSON files.
"""


class PasswordEntry():
    """
    Password entry class
    """
    def __init__(self, name, remarks, password):
        self.name = name
        self.remarks = remarks
        self.password = password
    
    def to_dict(self):
        return {
            'name':self.name,
            'password':self.password, 
            'remarks':self.remarks, 
        }