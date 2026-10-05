import requests

class Save():
    def __init__(self, file_path, file_name, user_name, URL):
        self.file_path = file_path
        self.file_name = file_name
        self.user_name = user_name
        self.URL = URL  #'http://127.0.0.1:8000/{self.user_name}/backup/'

    def save(self):
        """
        file_path, file_name,user_name,URL
        """
        with open(self.file_path,'rb') as file:
            files = {
                'file':(self.file_name,file)
            }
            rest = requests.post(self.URL, files=files)
            if rest.status_code == 200:
                print(f"上传成功：{self.file_name}")
            else:
                print(f"上传失败：{rest.status_code} - {rest.text}")
            return rest