import requests
import base64


class Gitee_API:
    def __init__(self, token, owner, repo):
        self.TOKEN = token
        self.OWNER = owner
        self.REPO = repo
        self.BASE = f"https://gitee.com/api/v5/repos/{owner}/{repo}/contents"

    def _get_sha(self, filename: str):
        url = f"{self.BASE}/{filename}"
        resp = requests.get(url, params={"access_token": self.TOKEN})
        if resp.status_code != 200:
            return None
        data = resp.json()
        return data.get("sha") if isinstance(data, dict) else None

    def upload(self, filename: str, content_bytes: bytes):
        url = f"{self.BASE}/{filename}"
        encoded = base64.b64encode(content_bytes).decode()
        data = {
            "access_token": self.TOKEN,
            "content": encoded,
            "message": f"backup {filename}",
        }
        sha = self._get_sha(filename)
        if sha:
            data["sha"] = sha
            resp = requests.put(url, json=data)
        else:
            resp = requests.post(url, json=data)
        return resp.status_code in (200, 201)

    def download(self, filename: str):
        url = f"{self.BASE}/{filename}"
        resp = requests.get(url, params={"access_token": self.TOKEN})
        if resp.status_code != 200:
            return None
        data = resp.json()
        if not isinstance(data, dict):
            return None
        return base64.b64decode(data["content"])

    def delete(self, filename: str):
        url = f"{self.BASE}/{filename}"
        sha = self._get_sha(filename)
        if not sha:
            return False
        data = {"access_token": self.TOKEN, "sha": sha, "message": f"delete {filename}"}
        resp = requests.delete(url, json=data)
        return resp.status_code == 200