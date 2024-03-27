# -*- coding: utf-8 -*-
# import paramiko
import datetime
import os
import subprocess
import time
import yaml
import sys
import re
import socket
import logging


def get_host_ip():
    """
    查询本机ip地址
    :return: ip
    """
    # try:
    #     s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #     s.connect(('8.8.8.8', 80))
    #     ip = s.getsockname()[0]
    # finally:
    #     s.close()

    # return ip
    return None 


def exec_cmd(cmd, conn=None):
    if conn:
        result = conn.exec_cmd(cmd)
        log_data = f'{conn._host} - {cmd} - {result}'
        Log().logger.info(log_data)
        return result
    else:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, encoding="utf-8")
        if p.returncode == 0:
            result = p.stdout
            result = result.decode() if isinstance(result, bytes) else result
            log_data = f'localhost - {cmd} - {result}'
            Log().logger.info(log_data)
            return {"st": True, "rt": result}
        else:
            result = p.stderr
            result = result.decode() if isinstance(result, bytes) else result
            log_data = f'localhost - {cmd} - {result}'
            Log().logger.info(log_data)
            return {"st": False, "rt": result}



def check_mode(mode):
    mode_list = ["balance-rr", "active-backup", "balance-xor", "broadcast", "802.3ad", "balance-tlb", "balance-alb"]
    if mode in mode_list:
        return True
    else:
        print(f"{mode} is not in following mode: {', '.join(mode_list)}")
        return False


def check_ip(ip):
    """检查IP格式"""
    re_ip = re.compile(
        r'^((2([0-4]\d|5[0-5]))|[1-9]?\d|1\d{2})(\.((2([0-4]\d|5[0-5]))|[1-9]?\d|1\d{2})){3}$')
    result = re_ip.match(ip)
    if result:
        return True
    else:
        print(f"ERROR in IP format of {ip}, please check.")
        return False



# class SSHConn(object):  # 注释

#     def __init__(self, host, port=22, username=None, password=None, timeout=8):
#         self._host = host
#         self._port = port
#         self._timeout = timeout
#         self._username = username
#         self._password = password
#         self.SSHConnection = None
#         self.ssh_connect()

#     def _connect(self):
#         try:
#             objSSHClient = paramiko.SSHClient()
#             objSSHClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#             objSSHClient.connect(self._host, port=self._port,
#                                  username=self._username,
#                                  password=self._password,
#                                  timeout=self._timeout)
#             # time.sleep(1)
#             # objSSHClient.exec_command("\x003")
#             self.SSHConnection = objSSHClient
#         except:
#             print(f" Failed to connect {self._host}")

#     def ssh_connect(self):
#         self._connect()
#         if not self.SSHConnection:
#             print(f'Connect retry for {self._host} ...')
#             self._connect()
#             if not self.SSHConnection:
#                 sys.exit()

#     def exec_cmd(self, command):
#         if self.SSHConnection:
#             stdin, stdout, stderr = self.SSHConnection.exec_command(command)
#             err = stderr.read()
#             if len(err) > 0:
#                 err = err.decode() if isinstance(err, bytes) else err
#                 return {"st": False, "rt": err}
#             data = stdout.read()
#             if len(data) > 0:
#                 data = data.decode() if isinstance(data, bytes) else data
#                 return {"st": True, "rt": data}

def get_hostname():
    """
    查询本机hostname
    :return:
    """
    # local_hostname = os.popen('hostname').read()
    local_hostname = os.popen('hostname').read().strip('\n')
    return local_hostname


class ConfFile(object):
    def __init__(self, file):
        self.yaml_file = file
        self.config = self.read_yaml()

    def read_yaml(self):
        """读YAML文件"""
        try:
            with open(self.yaml_file, 'r', encoding='utf-8') as f:
                yaml_dict = yaml.safe_load(f)
            return yaml_dict
        except FileNotFoundError:
            print(f"Please check the file name: {self.yaml_file}")
            sys.exit()
        except TypeError:
            print("Error in the type of file name.")
            sys.exit()

    # def update_yaml(self):
    #     """更新文件内容"""
    #     with open(self.yaml_file, 'w', encoding='utf-8') as f:
    #         yaml.dump(self.cluster, f, default_flow_style=False)
    
    def get_config(self):
        for host_config in self.config["bond"]:
            if not check_mode(host_config['mode']):
                print(f"Please check the mode config of {host_config['mode']}")
                sys.exit()
            if not check_ip(host_config['ip']):
                print(f"Please check the ip config of {host_config['mode']}")
                sys.exit()
            if len(host_config["device"]) != 2:
                print(f"Please check the ip config of {host_config['mode']}. Number of bond devices must be 2")
                sys.exit()
        return self.config["bond"]

class Log(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.logger = logging.getLogger()
            cls._instance.logger.setLevel(logging.INFO)
            cls._instance.set_handler()
        return cls._instance

    def set_handler(self):
        now_date = datetime.datetime.now().strftime('%Y-%m-%d')
        existing_log_files = [file for file in os.listdir('.') if file.startswith(f"vsdscoroconf_{now_date}")]

        if existing_log_files:
            file_name = existing_log_files[0]
        else:
            file_name = f"vsdsiptool_{now_date}.log"

        fh = logging.FileHandler(file_name, mode='a')
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)