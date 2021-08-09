# -*- coding:utf-8 -*-

import subprocess
import os
import time
import paramiko
import yaml

import socket


def exec_cmd(cmd, conn=None):
    if conn:
        result = conn.exec_cmd(cmd)
    else:
        result = subprocess.getoutput(cmd)
    result = result.decode() if isinstance(result, bytes) else result
    if result:
        result = result.rstrip('\n')
    return result



# LINBIT
# cmd("journalctl -u linstor-controller | cat")  # 查看日志命令
# cmd("journalctl -u linstor-controller --since '2021-06-10' --until '2021-06-22 03:00' | cat ")  # 指定时间查看
# cmd("journalctl -u linstor-controller | cat > linstor-controller.log")  # 将日志保存至指定文件


# DRBD
# cmd("dmesg -T | grep drbd")  # 日志查看
# cmd("dmesg -T | grep drbd | cat > drbd.log")  # 将日志保存至指定文件


# CRM
# cat /var/log/pacemaker.log  #查看pacemaker日志命令
# crm_report --from	"$(date	-d "7 days ago" +"%Y-%m-%d	%H:%M:%S")"	/tmp/crm_report_${HOSTNAME}_$(date +"%Y-%m-%d")
# 收集crm_report命令

# tar -jxvf {path}crm.log.tar.bz2 -C {path} #解压


def save_linbit_file(path, ssh_obj=None):
    cmd = f'journalctl -u linstor-controller | cat > {path}/linstor-controller.log'
    exec_cmd(cmd, ssh_obj)


def save_drbd_file(path, ssh_obj=None):
    cmd = f'dmesg -T | grep	drbd | cat > {path}/drbd.log'
    exec_cmd(cmd, ssh_obj)


def save_crm_file(path, ssh_obj=None):
    cmd = f'crm_report --from "$(date -d "7 days ago" +"%Y-%m-%d %H:%M:%S")" {path}/crm.log'
    exec_cmd(cmd, ssh_obj)


def tar_crm_file(path, ssh_obj=None):
    cmd = f"tar -jxvf {path}crm.log.tar.bz2 -C {path}"
    exec_cmd(cmd, ssh_obj)


def get_path(logdir, node, soft):
    path = f'{logdir}/{node}/{soft}/{time.strftime("%Y%m%d_%H%M%S")}/'
    return path


def show_tree(path, ssh_obj=None):
    cmd = f"cd {path} && tree -L 4"
    return exec_cmd(cmd, ssh_obj)


def mkdir(path, ssh_obj=None):
    if not bool(exec_cmd(f'[ -d {path} ] && echo True', ssh_obj)):
        exec_cmd(f"mkdir -p {path}",ssh_obj)


def scp_file(file_source, file_target, ssh_obj=None):
    cmd = f"scp -r {file_source} {file_target}"
    exec_cmd(cmd,ssh_obj)


class SSHConn(object):

    def __init__(self, host, port=22, username=None, password=None, timeout=None):
        self._host = host
        self._port = port
        self._timeout = timeout
        self._username = username
        self._password = password
        self.SSHConnection = None
        self.ssh_connect()

    def _connect(self):
        try:

            objSSHClient = paramiko.SSHClient()  # 创建SSH对象
            objSSHClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 允许连接其他主机
            objSSHClient.connect(self._host, port=self._port,
                                 username=self._username,
                                 password=self._password,
                                 timeout=self._timeout)  # 连接服务器
            # time.sleep(1)
            # objSSHClient.exec_command("\x003")
            self.SSHConnection = objSSHClient
        except:
            pass

    def ssh_connect(self):
        self._connect()
        if not self.SSHConnection:
            print('Connect retry for SAN switch "%s" ...' % self._host)
            self._connect()

    def exec_cmd(self, command):
        if self.SSHConnection:
            stdin, stdout, stderr = self.SSHConnection.exec_command(command)
            data = stdout.read()
            if len(data) > 0:
                # print(data.strip())
                return data
            err = stderr.read()
            if len(err) > 0:
                # 记录一下log
                pass
            #     print('''Excute command "{}" failed on "{}" with error:
            # "{}"'''.format(command, self._host, err.strip()))


class ConfFile():
    def __init__(self):
        self.yaml_file = './config.yaml'
        self.cluster = self.read_yaml()

    def read_yaml(self):
        """读YAML文件"""
        try:
            with open(self.yaml_file, 'r', encoding='utf-8') as f:
                yaml_dict = yaml.safe_load(f)
            return yaml_dict
        except FileNotFoundError:
            print("Please check the file name:", self.yaml_file)
        except TypeError:
            print("Error in the type of file name.")

    def update_yaml(self):
        """更新文件内容"""
        with open(self.yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(self.cluster, f, default_flow_style=False)

    def get_ssh_conn_data(self):
        lst = []
        for node in self.cluster['node']:
            lst.append([node['public_ip'], node['port'], 'root', node['root_password']])
        return lst


class Connect():
    """
    通过ssh连接节点，生成连接对象的列表
    """
    list_ssh = []

    def get_host_ip(self):
        """
        查询本机ip地址
        :return: ip
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        finally:
            s.close()

        return ip

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            Connect._instance = super().__new__(cls)
            Connect._instance.conf_file = ConfFile()
            Connect._instance.cluster = Connect._instance.conf_file.cluster
            Connect.get_ssh_conn(Connect._instance)
        return Connect._instance

    def get_ssh_conn(self):
        local_ip = self.get_host_ip()
        for node in self.cluster['node']:
            if local_ip == node['public_ip']:
                self.list_ssh.append(None)
            else:
                ssh = SSHConn(node['public_ip'], node['port'], 'root', node['root_password'])
                self.list_ssh.append(ssh)





class Console():
    def __init__(self, logfiledir):
        self.logfiledir = logfiledir
        self.conn = Connect()
        self.file_target = self._get_file_target()


    def _get_file_target(self):
        local_ip = self.conn.get_host_ip()
        for node in self.conn.cluster['node']:
            if local_ip == node['public_ip']:
                return f"root@{node['public_ip']}:{self.logfiledir}/"

    def save_linbit_file(self):
        for ssh, node in zip(self.conn.list_ssh, self.conn.cluster['node']):
            linbit_path = get_path(self.logfiledir, node['hostname'], 'LINBIT')
            mkdir(linbit_path, ssh)
            save_linbit_file(linbit_path, ssh)
            if ssh:
                file_source = f"{self.logfiledir}/{node['hostname']}"
                scp_file(file_source, self.file_target,ssh)


    def save_drbd_file(self):
        for ssh, node in zip(self.conn.list_ssh, self.conn.cluster['node']):
            drbd_path = get_path(self.logfiledir, node['hostname'], 'DRBD')
            mkdir(drbd_path, ssh)
            save_drbd_file(drbd_path, ssh)
            if ssh:
                file_source = f"{self.logfiledir}/{node['hostname']}"
                scp_file(file_source, self.file_target,ssh)

    def save_crm_file(self):
        for ssh, node in zip(self.conn.list_ssh, self.conn.cluster['node']):
            crm_path = get_path(self.logfiledir, node['hostname'], 'CRM')
            mkdir(crm_path, ssh)
            save_crm_file(crm_path, ssh)
            tar_crm_file(crm_path, ssh)
            if ssh:
                file_source = f"{self.logfiledir}/{node['hostname']}"
                scp_file(file_source, self.file_target,ssh)

    def show_tree(self):
        # for ssh, node in zip(self.conn.list_ssh, self.conn.cluster['node']):
        #     # print(f"node: {node['hostname']}")
        #     print(show_tree(self.logfiledir, ssh))

        print(show_tree(self.logfiledir))


    def test_scp(self):
        for ssh, node in zip(self.conn.list_ssh, self.conn.cluster['node']):
            if ssh:
                file_source = f"{self.logfiledir}/{node['hostname']}"
                print("file_source:",file_source)
                print("file_target:",self.file_target)
                scp_file(file_source, self.file_target,ssh)







if __name__ == "__main__":
    path = "/home/logfile"
    worker = Console(path)
    worker.save_linbit_file()
    worker.save_drbd_file()
    worker.save_crm_file()
    worker.show_tree()
    # worker.test_scp()


    # 取出数据
    # for ssh in list_ssh_data:
    #     # ssh[0] IP
    #     # ssh[1] 22
    #     # ssh[2] hostname
    #     # ssh[3] password
    #
    #     # 进行ssh连接（实例化ssh对象）
    #     ssh_obj = SSHConn(ssh[0], ssh[1], ssh[2], ssh[3])
    #     # ssh对象拥有exec_cmd的方法，即在连接过去的主机去执行命令
    #     # print(ssh_obj.exec_cmd('pwd'))
    #     ssh_obj.exec_cmd(f"mkdir -p {path}")
    #     node_name = ssh_obj.exec_cmd("hostname").decode().rstrip("\n")
    #     print(f'{node_name} tree:')
    #     print(ssh_obj.exec_cmd(f"cd {path} && tree ").decode())
