import os
import getpass
import shlex
import json
import datetime
import Fix_file

from Save_Password import VaultManager
from Save_Password.VaultManager import VAULT_FOLDER
from Fix_file import get_base_dir
from Cloud import Save_file
from Cloud import Get_file
from Cloud import Gitee_api

OPTIONS_FILE = os.path.join(Fix_file.get_base_dir(), "Options.op")

class Command():
    def __init__(self, main_password=None, CLOUD_URL="http://127.0.0.1:8000"):
        self.CLOUD_URL = CLOUD_URL
        if os.path.isfile(OPTIONS_FILE):
            with open(OPTIONS_FILE, "r", encoding="utf-8") as file:
                self.options = json.load(file)
        else:
            self.options = {
                "cloud": True,
                "last_backup": "",
                "gitee_token": "",
                "gitee_owner": "",
                "gitee_repo": "",
            }
        extra, missing = self._check_options()
        self._fix_options(extra, missing)

        extra,missing = self._check_options()
        self._fix_options(extra, missing)

        self.vault = None
        self.completed = True
        if main_password is not None:
            self.set_main_password(main_password)

    def set_main_password(self, main_password):
        """Create the vault manager, the main password stays in memory only."""
        self.vault = VaultManager.VaultManager(VAULT_FOLDER, main_password)

    def recognition(self, command):
        """Run one command, False is returned when the program should stop."""
        command = command.strip()
        if command == "":
            return self.completed
        try:
            parts = shlex.split(command)
            if not parts:
                return self.completed
            action = parts[0].lower()
            args = parts[1:]
        except ValueError as error:
                print(f"请确保你的引号型指令格式是否正确！Error:{error}")
                return
        if action == "help":
            print("""--- CatVault 命令帮助 ---
密码条目操作：
  add <name> <remarks> <password>    新增一条密码
  add <name> <password>              新增一条没有备注的密码
  show <name>                        查看某条密码
  delete <name>                      删除某条密码
  list                               列出所有条目
  search <keyword>                    搜索条目名称

修改操作：
  update <name> <remarks> <password> 修改某条密码（会覆盖）
  update <name> <password>           修改某条密码并清空备注

主密码管理：
  passwd                             修改主密码（会提示输入旧密码和新密码）

系统命令：
  help                               显示本帮助
  clear                              清屏
  exit / quit                        退出程序
  reset                              恢复出厂设置
云端命令：
  cloud true                         开启云端备份
  cloud false                        关闭云端备份
  cloud backup <cloud_path>          手动上传 Password/ 下所有 .dat 到云端
  cloud restore <cloud_path>         从云端下载所有 .dat 覆盖本地
  cloud status                       查看云端开关和最近一次备份时间
说明：
  <cloud_path>                       选择gitee或者server
""")
        elif action == "add":
            self._cmd_add(args)
        elif action == "show":
            self._cmd_show(args)
        elif action == "delete":
            self._cmd_delete(args)
        elif action == "list":
            self._cmd_list(args)
        elif action == "search":
            self._cmd_search(args)
        elif action == "update":
            self._cmd_update(args)
        elif action == "passwd":
            self._cmd_passwd(args)
        elif action == "clear":
            self._cmd_clear(args)
        elif action == "exit" or action == "quit":
            self._cmd_exit(args)
        elif action == "reset":
            self._cmd_reset(args)
        elif action == "cloud":
            self._cmd_cloud(args)
        else:
            print(f"---Can't recognize {command} as a script, please check the spelling of the name.")
        return self.completed

    def _vault_ready(self):
        if self.vault is None:
            print("---尚未设置主密码，请重新启动并在提示时输入主密码---")
            return False
        return True

    def _load_index(self):
        """Read the index, None is returned when it cannot be decrypted."""
        try:
            return self.vault.load_index()
        except Exception:
            print("---索引解密失败，请检查数据是否已损坏---")
            return None

    def _find_entry(self, name):
        """Return (index_dict, file_id), file_id is None when not found."""
        index_dict = self._load_index()
        if index_dict is None:
            return None, None
        return index_dict, self.vault.find_index(name, index_dict)

    def _parse_entry_args(self, args, usage):
        """Parse the arguments of add/update into (name, remarks, password)."""
        if len(args) == 2:
            return args[0], "", args[1]
        if len(args) == 3:
            return args[0], args[1], args[2]
        print(usage)
        return None

    def _read_entry(self, name, file_id):
        """Decrypt one entry, None is returned when it cannot be decrypted."""
        try:
            return self.vault.load_password(file_id)
        except Exception:
            print(f"---条目 {name} 解密失败，请检查数据是否已损坏---")
            return None

    def _cmd_add(self, args):
        if not self._vault_ready():
            return
        parsed = self._parse_entry_args(args, "用法：add <name> <remarks> <password>")
        if parsed is None:
            return
        name, remarks, password = parsed
        index_dict, file_id = self._find_entry(name)
        if index_dict is None:
            return
        if file_id is not None:
            print(f"---条目 {name} 已存在，如需修改请使用 update 命令---")
            return
        index_dict = self.vault.add_index(name, index_dict)
        file_id = self.vault.find_index(name, index_dict)
        try:
            self.vault.save_password(name, remarks, password, file_id=file_id)
        except FileExistsError:
            print(f"---条目 {name} 的密码文件已存在，新增失败---")
            return
        self.vault.save_index(index_dict)
        print(f"---已新增条目 {name}---")

    def _cmd_show(self, args):
        if not self._vault_ready():
            return
        if len(args) != 1:
            print("用法：show <name>")
            return
        name = args[0]
        index_dict, file_id = self._find_entry(name)
        if index_dict is None:
            return
        if file_id is None:
            print(f"---未找到条目 {name}---")
            return
        entry = self._read_entry(name, file_id)
        if entry is None:
            return
        print(f"名称：{entry.get('name', name)}")
        print(f"备注：{entry.get('remarks') or ''}")
        print(f"密码：{entry.get('password', '')}")

    def _cmd_delete(self, args):
        if not self._vault_ready():
            return
        if len(args) != 1:
            print("用法：delete <name>")
            return
        name = args[0]
        index_dict, file_id = self._find_entry(name)
        if index_dict is None:
            return
        if file_id is None:
            print(f"---未找到条目 {name}---")
            return
        confirm = input(f"确认删除条目 {name} ？输入 YES 确认：")
        if confirm != "YES":
            print("---已取消删除---")
            return
        self.vault.delete_password(file_id)
        index_dict = self.vault.delete_index(name, index_dict)
        self.vault.save_index(index_dict)
        print(f"---已删除条目 {name}---")

    def _cmd_list(self, args):
        if not self._vault_ready():
            return
        if args:
            print("用法：list")
            return
        index_dict = self._load_index()
        if index_dict is None:
            return
        if not index_dict:
            print("---保险库中还没有任何条目---")
            return
        print(f"---共 {len(index_dict)} 条条目---")
        for number, name in enumerate(index_dict.values(), start=1):
            print(f"{number:>3}. {name}")

    def _cmd_search(self, args):
        if not self._vault_ready():
            return
        if len(args) != 1:
            print("用法：search <关键词>")
            return
        keyword = args[0].lower()
        index_dict = self._load_index()
        if index_dict is None:
            return
        matches = [name for name in index_dict.values() if keyword in name.lower()]
        if not matches:
            print(f"---没有找到与 {args[0]} 匹配的条目---")
            return
        print(f"---找到 {len(matches)} 条匹配条目---")
        for name in matches:
            print(f"    {name}")

    def _cmd_update(self, args):
        if not self._vault_ready():
            return
        parsed = self._parse_entry_args(args, "用法：update <name> <remarks> <password>")
        if parsed is None:
            return
        name, remarks, password = parsed
        index_dict, file_id = self._find_entry(name)
        if index_dict is None:
            return
        if file_id is None:
            print(f"---未找到条目 {name}，请使用 add 命令新增---")
            return
        self.vault.update_password(file_id, name, remarks, password)
        print(f"---已更新条目 {name}---")

    def _cmd_passwd(self, args):
        if not self._vault_ready():
            return
        if args:
            print("用法：passwd")
            return
        old_password = input("请输入旧主密码：")
        index_dict = self._load_index()
        if index_dict is None:
            return
        if index_dict:
            try:
                VaultManager.VaultManager(VAULT_FOLDER, old_password).load_index()
            except Exception:
                print("---旧主密码不正确，未做任何修改---")
                return
        new_password = getpass.getpass("请输入新主密码：")
        confirm = getpass.getpass("请再次输入新主密码：")
        if new_password == "":
            print("---新主密码不能为空，未做任何修改---")
            return
        if new_password != confirm:
            print("---两次输入的新主密码不一致，未做任何修改---")
            return
        entries = []
        for file_id, name in index_dict.items():
            entry = self._read_entry(name, file_id)
            if entry is None:
                print("---读取条目失败，未做任何修改---")
                return
            entries.append((file_id, entry))
        new_vault = VaultManager.VaultManager(VAULT_FOLDER, new_password)
        for file_id, entry in entries:
            new_vault.update_password(file_id, entry.get('name', ''), entry.get('remarks'), entry.get('password', ''))
        new_vault.save_index(index_dict)
        self.vault = new_vault
        print("---主密码已修改，所有条目已使用新主密码重新加密---")

    def _cmd_clear(self, args):
        if os.name == "nt":
            os.system("cls")
        else:
            os.system("clear")

    def _cmd_exit(self, args):
        if self.options.get("cloud", False):
            try:
                self._cloud_backup(exit_mode=True)
            except Exception as error:
                print(f"---自动云端备份失败：{error}（不影响退出）---")
        self.completed = False
        with open(OPTIONS_FILE,"w") as file:
            json.dump(self.options, file, ensure_ascii=False)
        print("---已退出 CatVault---")

    def _cmd_reset(self, args):
        if not self._vault_ready():
            return
        if args:
            print("用法：reset")
            return

        print("!!!恢复出厂设置!!!")
        print("这个命令会：")
        print("  1. 删除密码库中的所有条目")
        print("  2. 清空索引文件")
        print("  3. 主密码将被重置（下次启动时可设新主密码）")
        print()
        print("删除后无法恢复，除非你有备份。")
        print()
        confirm1 = input("确定要继续吗？输入 yes 继续：").strip().lower()
        if confirm1 != "yes":
            print("---已取消---")
            return

        print()
        print("最后确认：所有数据将被永久清除。")
        confirm2 = input("请输入 RESET ALL（全大写）以确认：").strip()
        if confirm2 != "RESET ALL":
            print("---输入不匹配，已取消---")
            return

        deleted = 0
        for filename in os.listdir(VAULT_FOLDER):
            if filename.endswith(".dat") and filename != "index.dat":
                try:
                    os.remove(os.path.join(VAULT_FOLDER, filename))
                    deleted += 1
                except Exception as e:
                    print(f"---删除 {filename} 失败：{e}---")

        try:
            self.vault.save_index({})
        except Exception as e:
            print(f"---清空索引失败：{e}---")
            return

        print(f"---已恢复出厂设置：删除 {deleted} 条密码，索引已清空---")
        print("---下次启动时，可设置新的主密码---")
        
        self.completed = False
        with open(OPTIONS_FILE, "w") as file:
            json.dump(self.options, file, ensure_ascii=False)

    def _cmd_cloud(self, args):
        if not args:
            print("用法：cloud true / cloud false / cloud backup [gitee|server] / cloud restore [gitee|server] / cloud status")
            return

        action = args[0].lower()
        backend = args[1].lower() if len(args) >= 2 else "server"  # 默认 server

        if action == "true":
            self.options["cloud"] = True
            print("OK.")
        elif action == "false":
            self.options["cloud"] = False
            print("OK.")
        elif action == "backup":
            if backend == "gitee":
                self._cloud_backup_gitee()
            elif backend == "server":
                self._cloud_backup()
            else:
                print(f"未知的云端后端：{backend}")
        elif action == "restore":
            if backend == "gitee":
                self._cloud_restore_gitee()
            elif backend == "server":
                self._cloud_restore()
            else:
                print(f"未知的云端后端：{backend}")
        elif action == "status":
            self._cloud_status()
        else:
            print("用法：cloud true / cloud false / cloud backup [gitee|server] / cloud restore [gitee|server] / cloud status")

    def _cloud_user_name(self):
        """Read the user name from user_name.name, 'cat' is used as the fallback."""
        name_file = os.path.join(get_base_dir(), "user_name.name")
        try:
            with open(name_file, "r", encoding="utf-8") as file:
                user_name = file.read().strip()
        except OSError:
            user_name = ""
        if not user_name:
            print("请先设置用户名！")
            self._cmd_exit(args="")
        return user_name

    def _cloud_dat_files(self):
        """Return the file name of every .dat inside the vault folder (index.dat included)."""
        names = []
        if os.path.isdir(VAULT_FOLDER):
            for file_name in sorted(os.listdir(VAULT_FOLDER)):
                if file_name.endswith(".dat"):
                    names.append(file_name)
        return names

    def _persist_options(self):
        with open(OPTIONS_FILE, "w") as file:
            json.dump(self.options, file, ensure_ascii=False)

    def _cloud_backup(self, exit_mode=False):
        """Upload every .dat in the vault folder to the cloud."""
        user_name = self._cloud_user_name()
        success = 0
        failed = 0
        for file_name in self._cloud_dat_files():
            file_path = os.path.join(VAULT_FOLDER, file_name)
            url = f"{self.CLOUD_URL}/{user_name}/backup/{file_name}/"
            try:
                rest = Save_file.Save(file_path, file_name, user_name, url).save()
                if getattr(rest, "status_code", None) == 200:
                    success += 1
                else:
                    failed += 1
            except Exception as error:
                failed += 1
                print(f"---上传 {file_name} 失败：{error}---")
        if failed == 0 and success > 0:
            self.options["last_backup"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._persist_options()
        if exit_mode:
            if failed:
                print(f"---云端备份有 {failed} 个文件失败（不影响退出）---")
        else:
            print(f"---云端备份完成：成功 {success} 个，失败 {failed} 个---")

    def _cloud_backup_gitee(self):
        """上传所有 .dat 到 Gitee 仓库"""
        user_name = self._cloud_user_name()
        token = self.options.get("gitee_token", "")
        if not token:
            print("---未配置 gitee_token，请在 Options.op 里添加---")
            return

        api = Gitee_api.Gitee_API(
            token,
            self.options.get("gitee_owner", "Interesting_Cat"),
            self.options.get("gitee_repo", "cat-vault-server-side-saving"),
        )

        success = 0
        failed = 0
        for file_name in self._cloud_dat_files():
            file_path = os.path.join(VAULT_FOLDER, file_name)
            try:
                with open(file_path, "rb") as f:
                    content = f.read()
                remote_path = f"{user_name}/{file_name}"
                if api.upload(remote_path, content):
                    success += 1
                else:
                    failed += 1
            except Exception as error:
                failed += 1
                print(f"---上传 {file_name} 失败：{error}---")

        if failed == 0 and success > 0:
            self.options["last_backup"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._persist_options()
        print(f"---Gitee 备份完成：成功 {success} 个，失败 {failed} 个---")


    def _cloud_restore_gitee(self):
        """从 Gitee 仓库下载所有 .dat 覆盖本地"""
        user_name = self._cloud_user_name()
        token = self.options.get("gitee_token", "")
        if not token:
            print("---未配置 gitee_token，请在 Options.op 里添加---")
            return

        api = Gitee_api.Gitee_API(
            token,
            self.options.get("gitee_owner", "Interesting_Cat"),
            self.options.get("gitee_repo", "cat-vault-server-side-saving"),
        )

        # 收集要下载的文件名
        names = {"index.dat"}
        for file_name in self._cloud_dat_files():
            names.add(file_name)
        try:
            if self.vault is not None:
                for file_id in self.vault.load_index():
                    names.add(f"{file_id}.dat")
        except Exception:
            pass

        replaced = 0
        for file_name in sorted(names):
            remote_path = f"{user_name}/{file_name}"
            content = api.download(remote_path)
            if content is None:
                continue
            target = os.path.join(VAULT_FOLDER, file_name)
            with open(target, "wb") as f:
                f.write(content)
            replaced += 1
        print(f"---Gitee 恢复完成：已覆盖 {replaced} 个本地文件---")

    def _cloud_restore(self):
        """Download every known .dat from the cloud and replace the local files."""
        user_name = self._cloud_user_name()
        url = f"{self.CLOUD_URL}/{user_name}/backup/"

        names = {"index.dat"}
        for file_name in self._cloud_dat_files():
            names.add(file_name)
        try:
            if self.vault is not None:
                for file_id in self.vault.load_index():
                    names.add(f"{file_id}.dat")
        except Exception:
            pass

        replaced = 0
        for file_name in sorted(names):
            target = os.path.join(VAULT_FOLDER, file_name)
            before = os.path.getmtime(target) if os.path.isfile(target) else None
            try:
                Get_file.Get(user_name, file_name, url).get()
            except Exception as error:
                print(f"---下载 {file_name} 失败：{error}---")
                continue
            if os.path.isfile(target) and os.path.getmtime(target) != before:
                replaced += 1
        print(f"---云端恢复完成：已覆盖 {replaced} 个本地文件---")

    def _cloud_status(self):
        state = "开启" if self.options.get("cloud", False) else "关闭"
        last_backup = self.options.get("last_backup") or "无备份记录"
        print(f"云端开关：{state}")
        print(f"最近一次备份：{last_backup}")
        print(f"账户：{self._cloud_user_name()}")
        print(f"服务器：{self.CLOUD_URL}")

    def _check_options(self):
        expected = {"cloud", "last_backup", "gitee_token", "gitee_owner", "gitee_repo"}
        extra = set(self.options) - expected
        missing = expected - set(self.options)
        return extra, missing


    def _fix_options(self, extras, missings):
        if extras:
            for extra in extras:
                del self.options[extra]
        for missing in missings:
            if missing == "cloud":
                self.options["cloud"] = True
            elif missing == "last_backup":
                self.options["last_backup"] = ""
            elif missing == "gitee_token":
                self.options["gitee_token"] = ""
            elif missing == "gitee_owner":
                self.options["gitee_owner"] = "Interesting_Cat"
            elif missing == "gitee_repo":
                self.options["gitee_repo"] = "cat-vault-server-side-saving"
            ...  #后期有新的参数，需在此处添加新的补充逻辑
