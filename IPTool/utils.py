# -*- coding: utf-8 -*-
import paramiko
import socket
import os
import subprocess
import yaml
import sys
import re


def exec_cmd(cmd, conn=None):
    if conn:
        result = conn.exec_cmd(cmd)
        return result
    else:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, encoding="utf-8")
        if p.returncode == 0:
            result = p.stdout
            # result = result.decode() if isinstance(result, bytes) else result
            return {"st": True, "rt": result}
        else:
            # print(f"  Failed to execute command: {cmd}")
            # print("  Error message:\n", p.stderr.decode())
            return {"st": False, "rt": p.stderr}


def check_mode(mode):
    mode_list = ["balance-rr", "active-backup", "balance-xor","broadcast", "802.3ad", "balance-tlb", "balance-alb"]
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


class SSHConn(object):

    def __init__(self, host, port=22, username=None, password=None, timeout=8):
        self._host = host
        self._port = port
        self._timeout = timeout
        self._username = username
        self._password = password
        self.SSHConnection = None
        self.ssh_connect()

    def _connect(self):
        try:
            objSSHClient = paramiko.SSHClient()
            objSSHClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            objSSHClient.connect(self._host, port=self._port,
                                 username=self._username,
                                 password=self._password,
                                 timeout=self._timeout)
            # time.sleep(1)
            # objSSHClient.exec_command("\x003")
            self.SSHConnection = objSSHClient
        except:
            print(f" Failed to connect {self._host}")

    def ssh_connect(self):
        self._connect()
        if not self.SSHConnection:
            print(f'Connect retry for {self._host}')
            self._connect()
            if not self.SSHConnection:
                sys.exit()

    def exec_cmd(self, command):
        if self.SSHConnection:
            stdin, stdout, stderr = self.SSHConnection.exec_command(command)
            err = stderr.read()
            if len(err) > 0:
                err = err.decode() if isinstance(err, bytes) else err
                return {"st": False, "rt": err}
            data = stdout.read()
            if len(data) > 0:
                data = data.decode() if isinstance(data, bytes) else data
                return {"st": True, "rt": data}


def get_hostname():
    """
    查询本机hostname
    :return:
    """
    # local_hostname = os.popen('hostname').read()
    local_hostname = os.popen('hostname').read().strip('\n')
    return local_hostname


class ConfFile():
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

    def update_yaml(self):
        """更新文件内容"""
        with open(self.yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(self.cluster, f, default_flow_style=False)

    def get_config(self):
        lst = []
        for host_config in self.config["node"]:
            if check_mode(host_config['mode']) and check_ip(host_config['ip']):
                lst.append(
                    [host_config['hostname'], host_config['bond'], host_config['mode'], host_config['device'],
                     host_config['ip']])
            else:
                print(f"Please check the config of {host_config['hostname']}")
                sys.exit()
        return lst
