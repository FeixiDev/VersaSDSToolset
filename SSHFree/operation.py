import paramiko
import yaml
import utils


def read_config(yaml_name):
    """
    Reads a YAML configuration file and returns its contents as a dictionary.

    Args:
        yaml_name (str): The name of the YAML configuration file.

    Returns:
        dict: The contents of the YAML configuration file as a dictionary.

    Raises:
        FileNotFoundError: If the specified YAML configuration file cannot be found.
        TypeError: If the input is not a string.
    """
    try:
        with open(yaml_name, encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"Configuration file read error, please check the configuration file name: {yaml_name}")
    except TypeError:
        print("Configuration file read error, please check the input type")


def check_id_rsa_pub(ssh_obj):
    """
    Check if the id_rsa.pub file exists in the /root/.ssh directory.

    Args:
        ssh_obj (paramiko.SSHClient): The SSH client object.

    Returns:
        bool: True if the file exists, False otherwise.
    """
    cmd = '[ -f /root/.ssh/id_rsa.pub ] && echo True || echo False'
    result = utils.exec_cmd(cmd, ssh_obj)
    if not isinstance(result, bool):
        result = result.replace(" ", "")
        result = result.replace("\n", "")

        if result == 'False':
            return False
        else:
            return True
    else:
        return result


# def create_id_rsa_pub(ssh_obj):
#     """
#     Create a new SSH key pair in the /root/.ssh directory if it does not exist.

#     Args:
#         ssh_obj (paramiko.SSHClient): The SSH client object.

#     Returns:
#         bool: True if the key pair is created successfully or already exists, False otherwise.
#     """
#     cmd = 'ssh-keygen -f /root/.ssh/id_rsa -N ""'
#     result = utils.exec_cmd(cmd, ssh_obj)
#     if not result:
#         return False
#     else:
#         return True
def create_id_rsa_pub(ssh_obj):
    """
    Create a new SSH key pair in the /root/.ssh directory if it does not exist.

    Args:
        ssh_obj (paramiko.SSHClient): The SSH client object.

    Returns:
        bool: True if the key pair is created successfully or already exists, False otherwise.
    """
    cmd = 'yes | ssh-keygen -f /root/.ssh/id_rsa -N "" -q'
    result = utils.exec_cmd(cmd, ssh_obj)
    # print(f"create_id_rsa_pub result: {result}")
    if not result:
        return False
    else:
        return True


def revise_sshd_config(ssh_obj):
    """
    Modify the sshd_config file to enable public key authentication.

    Args:
        ssh_obj (paramiko.SSHClient): The SSH client object.

    Returns:
        bool: True if the sshd_config file is modified successfully, False otherwise.
    """
    cmd = "sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/g' /etc/ssh/sshd_config"
    utils.exec_cmd(cmd, ssh_obj)
    return True


def check_authorized_keys(ssh_obj):
    """
    Check if the authorized_keys file exists in the /root/.ssh directory.

    Args:
        ssh_obj (paramiko.SSHClient): The SSH client object.

    Returns:
        bool: True if the file exists, False otherwise.
    """
    cmd = '[ -f /root/.ssh/authorized_keys ] && echo True || echo False'
    result = utils.exec_cmd(cmd, ssh_obj)
    result = result.replace(" ", "")
    result = result.replace("\n", "")
    if result == 'False':
        return False
    else:
        return True

def check_node(node_list):
    for z in node_list:
        ipaddr_z = z['ip']
        usname_z = z['username']
        passwd_z = z['password']
        ssh_obj_z = utils.SSHConn(host=ipaddr_z, username=usname_z, password=passwd_z)
        list_ = node_list
        # list_.remove(z)
        for a in list_:
            ipaddr = a['ip']
            usname = a['username']
            passwd = a['password']
            ssh_obj = utils.SSHConn(host=ipaddr, username=usname, password=passwd)

            try:
                # 创建 SSH 客户端对象
                ssh_client = paramiko.SSHClient()

                # 设置自动添加主机密钥
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                # 连接到 ssh_obj_z
                ssh_client.connect(hostname=ssh_obj_z['ip'], username=ssh_obj_z['username'], password=ssh_obj_z['password'])

                # 使用 ssh_obj_z SSH 连接到 ssh_obj
                transport = ssh_client.get_transport()
                dest_addr = (ssh_obj['ip'], 22)  #
                local_addr = (ssh_obj_z['ip'], 22)  
                channel = transport.open_channel("direct-tcpip", dest_addr, local_addr)

                # 使用连接测试对目标节点进行连接
                ssh_session = paramiko.SSHClient()
                ssh_session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_session.connect(hostname=ssh_obj['ip'], username=ssh_obj['username'], password=None, sock=channel)

                # 关闭连接
                ssh_session.close()
                ssh_client.close()

                print(f"从{ssh_obj_z['ip']}到{ssh_obj['ip']}的SSH连接（无密码）成功。")
                
            except paramiko.AuthenticationException as auth_exception:
                log_data = f"Authentication failed from {ssh_obj_z['ip']} to {ssh_obj['ip']}: {auth_exception}"
                print(log_data)
                utils.Log().logger.info(log_data)
                return False
            except paramiko.SSHException as ssh_exception:
                log_data = f"SSH connection failed from {ssh_obj_z['ip']} to {ssh_obj['ip']}: {ssh_exception}"
                print(log_data)
                utils.Log().logger.info(log_data)
                return False
            except Exception as e:
                log_data = f"Error occurred from {ssh_obj_z['ip']} to {ssh_obj['ip']}: {e}"
                print(log_data)
                utils.Log().logger.info(log_data)
                return False
    return True

def modify_ssh_config(nodes):
    for node in nodes:
        buffer = False

        host = node['ip']
        username = node['username']
        password = node['password']

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            ssh.connect(host, username=username, password=password)
            sftp = ssh.open_sftp()
            remote_file = '/etc/ssh/ssh_config'

            # 读取远程文件内容
            with sftp.file(remote_file, 'r') as file:
                lines = file.readlines()

            # 查找并替换特定行
            for i, line in enumerate(lines):
                if line.strip().startswith(b'#   StrictHostKeyChecking ask'):
                    lines[i] = b'StrictHostKeyChecking no\n'
                    log_data = f"{username} 节点 StrictHostKeyChecking no 替换完成"
                    utils.Log().logger.info(log_data)
                    buffer = True
                    break

            # 重新写入文件
            with sftp.file(remote_file, 'w') as file:
                file.writelines(lines)
            if buffer:
                print(f"Replaced StrictHostKeyChecking ask with no on {host}")
            else:
                print(f"{host}: ssh_config is ready")
            ssh.close()
            
        except paramiko.AuthenticationException:
            log_data = f"Authentication failed for {host}"
            print(log_data)
            utils.Log().logger.info(log_data)
            return False
        except paramiko.SSHException as e:
            log_data = f"SSH error occurred: {e}"
            print(log_data)
            utils.Log().logger.info(log_data)
            return False
        except Exception as e:
            log_data = f"Error occurred for {host}: {e}"
            print(log_data)
            utils.Log().logger.info(log_data)
            return False
    return True