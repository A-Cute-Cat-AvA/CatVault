import requests

class Get():
    def __init__(self, user_name, file_name, URL):
        self.user_name = user_name
        self.file_name = file_name
        self.URL = URL  #'http://127.0.0.1:8000/{self.user_name}/backup/'

    def get(self):
        rest = requests.get(self.URL.rstrip('/')+'/'+self.file_name+'/')

        if rest.status_code == 200:
            with open('CatVault/Password/'+self.file_name,'wb') as file:
                file.write(rest.content)
                print(f"替换成功！本文件共{len(rest.content)}字节！")
        else:
            print(f"下载{self.file_name}失败：{rest.status_code} - {rest.text}")