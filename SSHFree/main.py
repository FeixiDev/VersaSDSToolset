import sys
import time
import operation
import utils
import argparse

sys.path.append('../')
import consts


class ArgparseOperator:
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog='argparse')
        self.setup_parse()

    def setup_parse(self):
        sub_parser = self.parser.add_subparsers()

        self.parser.add_argument('-v',
                                 '--version',
                                 dest='version',
                                 help='Show current version',
                                 action='store_true')

        self.parser.set_defaults(func=self.main_usage)

        parser_free = sub_parser.add_parser("free", aliases=['fe'], help='free_login')

        parser_re_free = sub_parser.add_parser("re", aliases=['re'], help='re_free_login')

        parser_check = sub_parser.add_parser("check", aliases=['c'], help='check_node_passwd_free')

        parser_modify = sub_parser.add_parser("mod", aliases=['m'], help='modify_ssh_config_file')

        parser_free.set_defaults(func=self.func_free_login)
        parser_re_free.set_defaults(func=self.func_re_free_login)
        parser_check.set_defaults(func=self.func_check_node)
        parser_modify.set_defaults(func=self.func_modify_ssh_config)

    def main_usage(self, args):
        if args.version:
            print(f'Version: {consts.VERSION}')
            sys.exit()
        else:
            self.parser.print_help()

    def parser_init(self):
        args = self.parser.parse_args()
        args.func(args)

    def func_free_login(self, args):
        free_login()

    def func_re_free_login(self, args):
        re_free_login()

    def func_check_node(self, args):
        check_node_()

    def func_modify_ssh_config(self, args):
        modify_ssh_config_()
        
def free_login():
    config_info = operation.read_config('vsdssshfree_config.yaml')
    node_list = config_info['node']
    # TODO: 可以使用 concurrent.futures 模块来并行执行循环中的任务，以提高效率
    for z in node_list:
        name = z['name']
        ipaddr = z['ip']
        usname = z['username']
        passwd = z['password']
        ssh_obj = utils.SSHConn(host=ipaddr, username=usname, password=passwd)
        status0 = operation.revise_sshd_config(ssh_obj)
        status1 = operation.check_id_rsa_pub(ssh_obj)
        if status1 is False:
            print(f'{ipaddr} does not have a public key, creating one now')
            status2 = operation.create_id_rsa_pub(ssh_obj)
            time.sleep(2)
            if status2 is False:
                print('Failed to create public key')
                sys.exit()
            else:
                print('Public key created successfully')
        else:
            print(f'{ipaddr} has a public key')

    for i, z in enumerate(node_list):
        name = z['name']
        ipaddr = z['ip']
        usname = z['username']
        passwd = z['password']
        ssh_obj = utils.SSHConn(host=ipaddr, username=usname, password=passwd)
        exec(f'list{i} = {node_list}')
        # exec(f'list{i}.remove({z})')
        print(f'Now distributing public key for {ipaddr}')
        try:
            exec(f'for y in list{i}:'
                 f'    ssh_obj.exec_copy_id_rsa_pub(y["ip"],y["password"])')
            print(f'Public key distribution for {ipaddr} completed')
        except:
            print('Failed to distribute public key, program will exit automatically')
            sys.exit()


def re_free_login():
    config_info = operation.read_config('vsdssshfree_config.yaml')
    node_list = config_info['node']
    for z in node_list:
        name = z['name']
        ipaddr = z['ip']
        usname = z['username']
        passwd = z['password']
        print(f'Now removing password-free operation for {ipaddr}')
        ssh_obj = utils.SSHConn(host=ipaddr, username=usname, password=passwd)
        status0 = operation.check_authorized_keys(ssh_obj)
        try:
            delete_cmd = "rm /root/.ssh/authorized_keys"
            utils.exec_cmd(delete_cmd, ssh_obj)
            print("Password-free operation removed successfully")
        except:
            print("Failed to remove password-free operation")

def check_node_():
    config_info = operation.read_config('vsdssshfree_config.yaml')
    node_list = config_info['node']
    result = operation.check_node(node_list)
    if result:
        print("Node to node password free successful")
    else:
        print("Node to node password free failure")

def modify_ssh_config_():
    config_info = operation.read_config('vsdssshfree_config.yaml')
    node_list = config_info['node']
    result = operation.modify_ssh_config(node_list)
    if result:
        print("modify ssh_config successful")
    else:
        print("modify ssh_config failure")


if __name__ == "__main__":
    cmd = ArgparseOperator()
    cmd.parser_init()
