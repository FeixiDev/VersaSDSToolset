# -*- coding:utf-8 -*-
import action
import sys


def all_deploy(conf_args):
    """一键执行完成软件安装以及配置、root密码设置、允许以root用户登录、连接IP的设置的功能"""
    install = action.InstallSoftware(conf_args["User password"])
    root_config = action.RootConfig(conf_args["User password"])
    ip_service = action.IpService(conf_args["User password"])
    ssh_service = action.OpenSSHService(conf_args["User password"])
    print("\nPrepare to install software...")
    if install.update_apt():
        print("Start to install openssh-server")
        if install.install_software("openssh-server"):
            print(" Start openssh service")
            if ssh_service.oprt_ssh_service("start"):
                print("Set can be logged as root")
                if root_config.set_root_permit_login():
                    print("Set root password")
                    root_config.set_root_password(conf_args["Root password"])
                    print(" Restart openssh service")
                    ssh_service.oprt_ssh_service("restart")
        print("Start to install network-manager")
        if install.install_software("network-manager"):
            print(" Start to set network-manager config")
            if install.set_nmcli_config():
                print(f"Set {conf_args['IP']} on the {conf_args['Device']}")
                if ip_service.set_local_ip(conf_args['Device'], conf_args['IP'], conf_args['Gateway']):
                    ip_service.up_local_ip_service(conf_args['Device'])
        print("\n")
    else:
        sys.exit()


def set_root_pwd_permit_login(conf_args):
    """root密码设置、允许以root用户登录"""
    ssh_service = action.OpenSSHService(conf_args["User password"])
    root_config = action.RootConfig(conf_args["User password"])
    print("Set can be logged as root")
    if root_config.set_root_permit_login():
        print(" Start to set root password")
        root_config.set_root_password(conf_args["Root password"])
        print(" Start to restart openssh service")
        ssh_service.oprt_ssh_service("restart")
        print("Finish to set root password and can be logged as root")


def set_local_ip(conf_args):
    """连接IP的设置的功能"""
    ip_service = action.IpService(conf_args["User password"])
    print(f"Start to set {conf_args['IP']} on the {conf_args['Device']}")
    ssh_service = action.OpenSSHService(conf_args["User password"])
    if ip_service.set_local_ip(conf_args['Device'], conf_args['IP'], conf_args['Gateway']):
        ip_service.up_local_ip_service(conf_args['Device'])
        print(" Start to restart openssh service")
        ssh_service.oprt_ssh_service("restart")
        print(f"Finish to set {conf_args['IP']} on the {conf_args['Device']}")
