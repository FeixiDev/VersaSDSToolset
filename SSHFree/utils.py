import paramiko
import subprocess
import logging
import sys
import time
import re


def exec_cmd(cmd, conn=None):
    if conn:
        result = conn.exec_cmd(cmd, conn)
    else:
        result = subprocess.getoutput(cmd)
        log_data = f"'localhost' - {cmd} - {result}"
        Log().logger.info(log_data)
        if result:
            result = result.rstrip('\n')
    return result
    
class SSHConn(object):

    def __init__(self, host, port=22, username=None, password=None, timeout=None):
        self._host = host
        self._port = port
        self._timeout = timeout
        self._username = username
        self._password = str(password)
        self.SSHConnection = None
        self.ssh_connect()
        
    def __getitem__(self, key):
        # 根据 key 返回相应的属性值
        if key == 'ip':
            return self._host
        elif key == 'username':
            return self._username
        elif key == 'password':
            return self._password
        else:
            raise KeyError(f"Invalid key: {key}")

    def _connect(self):
        try:
            objSSHClient = paramiko.SSHClient()
            objSSHClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            objSSHClient.connect(self._host, port=self._port,
                                 username=self._username,
                                 password=self._password,
                                 timeout=self._timeout)
            self.SSHConnection = objSSHClient
        except paramiko.AuthenticationException as auth_exception:
            print(f"Authentication failed for {self._host}: {auth_exception}")
            Log().logger.error(f"Authentication failed for {self._host}: {auth_exception}")
        except paramiko.SSHException as ssh_exception:
            print(f"SSH connection failed for {self._host}: {ssh_exception}")
            Log().logger.error(f"SSH connection failed for {self._host}: {ssh_exception}")
        except Exception as e:
            print(f"Failed to connect {self._host}: {e}")
            Log().logger.error(f"Failed to connect {self._host}: {e}")

    def ssh_connect(self):
        self._connect()
        if not self.SSHConnection:
            print(f'Connect retry for {self._host}')
            self._connect()
            if not self.SSHConnection:
                sys.exit()

    def exec_cmd(self, command, conn):
        if self.SSHConnection:
            try:
                stdin, stdout, stderr = self.SSHConnection.exec_command(command)
                #print(f"exec_cmd stdout: {stdout}")
                #print(f"exec_cmd stderr: {stderr}")
                log_data = f"{conn._host} - {command} - {stdout}"
                Log().logger.info(log_data)
                data = stdout.read()

                if len(data) >= 0:
                    data = data.decode() if isinstance(data, bytes) else data
                    # print(f"exec_cmd data: {data.strip()}")
                    if data:
                        return data.strip()
                    else:
                        return True
                err = stderr.read()
            except paramiko.SSHException as ssh_exception:
                error_msg = f"SSH command execution failed: {ssh_exception}"
                Log().logger.error(error_msg)
                return error_msg

            except Exception as e:
                error_msg = f"Error occurred while executing command: {e}"
                Log().logger.error(error_msg)
                return error_msg

    def exec_copy_id_rsa_pub(self, target_ip, passwd):
        try:
            cmd = f'ssh-copy-id -o stricthostkeychecking=no -i /root/.ssh/id_rsa.pub root@{target_ip}'
            conn = self.SSHConnection.invoke_shell()
            conn.keep_this = self.SSHConnection
            # print(cmd)
            Log().logger.info(cmd)
            time.sleep(2)
            conn.send(cmd + '\n')
            time.sleep(2)
            stdout = conn.recv(1024)
            info = stdout.decode()
            result = re.findall(r'Number of key(s) added: 1', info)
            if result == []:
                time.sleep(2)
                if isinstance(passwd, int):
                    passwd = str(passwd)
                conn.send(str(passwd + '\n'))

            time.sleep(1)
            stdout = conn.recv(9999)
        except paramiko.AuthenticationException as auth_exception:
            print(f"Authentication failed: {auth_exception}")
            Log().logger.error(f"Authentication failed: {auth_exception}")
            return False

        except paramiko.SSHException as ssh_exception:
            print(f"SSH connection error: {ssh_exception}")
            Log().logger.error(f"SSH connection error: {ssh_exception}")
            return False

        except Exception as e:
            print(f"Error occurred: {e}")
            Log().logger.error(f"Error occurred: {e}")
            return False

class Log(object):
    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            Log._instance = super().__new__(cls)
            Log._instance.logger = logging.getLogger()
            Log._instance.logger.setLevel(logging.INFO)
            Log.set_handler(Log._instance.logger)
        return Log._instance

    @staticmethod
    def set_handler(logger):
        fh = logging.FileHandler('./vsdssshfree.log', mode='a')
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        fh.setFormatter(formatter)
        logger.addHandler(fh)
