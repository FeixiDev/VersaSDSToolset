# -*- coding:utf-8 -*-
import subprocess
import os
import re
import sys


def exec_cmd(cmd):
    """subprocess执行命令"""
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    if p.returncode == 0:
        result = p.stdout
        result = result.decode() if isinstance(result, bytes) else result
        # print("result", result)
        return {"st": True, "rt": result}
    else:
        print(f"  Failed to execute command: {cmd}")
        print("  Error message:\n", p.stderr)
        return {"st": False, "rt": p.stderr}


def get_file(path, type=None):
    """通过路径获取路径下的文件名"""
    file_list = []
    if type:
        for file in os.listdir(path):
            if os.path.splitext(file)[1] == f".{type}":
                file_list.append(file)
    else:
        return os.listdir(path)
    return file_list


def guide_check(target, default):
    for i in range(3):
        a = input(f"Input the value of '{target}' (default [{default}]): ")
        if a.strip() == "":
            return default
        elif a.strip() == "exit":
            sys.exit()
        else:
            if target in ["Gateway", "IP"]:
                if check_ip(a):
                    return a
                else:
                    if i < 2:
                        print(f"Please check the format of {target}.Enter again or enter 'exit' to quit")
                    else:
                        print("Three times for error input, exit the program.")
            else:
                return a


def check_ip(ip):
    """检查IP格式"""
    re_ip = re.compile(
        r'^((2([0-4]\d|5[0-5]))|[1-9]?\d|1\d{2})(\.((2([0-4]\d|5[0-5]))|[1-9]?\d|1\d{2})){3}$')
    result = re_ip.match(ip)
    if result:
        return True
