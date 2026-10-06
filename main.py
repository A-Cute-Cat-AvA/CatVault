import Fix_file
import getpass
import Command
import Verify
import os

from Assets.Pictures import TxT

print(TxT.WELCOME)

error = Fix_file.fix_password_folder()
if error == "ERROR":
    input(">>>密码存储文件夹丢失<<<\n>>>密码可能已经丢失，已重新创建空文件夹<<<\n如果你是第一次运行，请忽略\n按任意键继续...")

error = Fix_file.fix_password_index()
if error == "ERROR":
    fix = input(">>>条目名花名册丢失<<<\n>>>密码对应名称可能已经丢失，已重新创建空花名册<<<\n如果你是第一次运行，请忽略\n如需尝试修复，请输YES\n按任意键继续...")
    if fix == "YES":
        input("功能未完善，按任意键继续...")

name_file = os.path.join(Fix_file.get_base_dir(), "user_name.name")
if os.path.isfile(name_file):
    with open(name_file, 'r', encoding="utf-8") as text:
        print(f"{text.read()}欢迎回来！输入help查看帮助")
else:
    print("欢迎使用CatVault命令行，输入help查看帮助")
    name = input("请输入你的名字:")
    with open(name_file, 'w', encoding="utf-8") as text:
        text.write(name)

main_password = getpass.getpass("请输入主密码：")
_is_True = Verify.verify_password(main_password)
number = 4
while (_is_True == "ERROR" or main_password == "") and number > 0:
    number -= 1
    if number <= 0:
        print("输入错误次数过多，已退出程序")
        exit()
    main_password = getpass.getpass(f"主密码错误或不能为空，还剩{number}次机会,请重新输入主密码：")
    _is_True = Verify.verify_password(main_password)

URL = input("请输入你的服务器URL，没有请直接ENTER")

recognition = Command.Command(main_password, URL)
del _is_True
del number
print("OK.")

while True:
    try:
        command = input(">>> ")
    except (EOFError, KeyboardInterrupt):
        print()
        break
    if recognition.recognition(command) is False:
        break
