import time
import utils


class IpService(object):
    def __init__(self, node):
        if node == utils.get_hostname() or node is None:
            self.conn = None
        else:
            self.conn = utils.SSHConn(node)

    def set_ip(self, device, ip, gateway, netmask=24):
        connection_name = f'vtel_{device}'
        cmd = f"nmcli connection add con-name {connection_name} type ethernet ifname {device} ipv4.addresses {ip}/{netmask} ipv4.gateway {gateway} ipv4.dns 114.114.114.114 ipv4.method manual"
        result = utils.exec_cmd(cmd, self.conn)
        if result:
            if result["st"]:
                return True
        return False


    def get_mode(self,bonding_name):
        cmd = f"cat /proc/net/bonding/{bonding_name} | grep Bonding"
        result = utils.exec_cmd(cmd,self.conn)
        return result["rt"]


    def up_ip_service(self, connection_name):
        cmd = f"nmcli connection up id {connection_name}"
        result = utils.exec_cmd(cmd, self.conn)
        if result:
            if result["st"]:
                print(f"Success in up {connection_name}.")
                return True
            else:
                print(f"Failed to up {connection_name}.")
        return False

    def modify_ip(self, device, new_ip, gateway, netmask=24):
        connection_name = f'vtel_{device}'
        cmd = f"nmcli connection modify {connection_name} ipv4.address {new_ip}/{netmask} ipv4.dns 114.114.114.114 ipv4.gateway {gateway} ipv4.method manual"
        print(cmd)
        result = utils.exec_cmd(cmd, self.conn)
        if result:
            if result["st"]:
                return True
        return False

    def set_bonding(self, device, type):
        connection_name = f'vtel_{device}'
        cmd = f"nmcli connection add con-name {connection_name} type bond ifname {device} mode {type}"
        result = utils.exec_cmd(cmd, self.conn)
        if result:
            if result["st"]:
                return True
        return False

    def add_bond_slave(self, master, device):
        """add device into the bond connection which has been set"""
        bond_slave = f'vtel_{master}-slave-{device}'
        cmd = f"nmcli connection add con-name {bond_slave} type bond-slave ifname {device} master {master}"
        result = utils.exec_cmd(cmd, self.conn)
        if result:
            if result["st"]:
                return bond_slave

    def delete_bond_slave(self, master, device):
        bond_slave = f'vtel_{master}-slave-{device}'
        cmd = f"nmcli connect delete {bond_slave}"
        utils.exec_cmd(cmd, self.conn)

    def modify_bonding_mode(self, device, mode):
        """
        Note: result of execute command is None, but actually the command has been executed
        """
        connection_name = f'vtel_{device}'
        cmd = f"nmcli connection modify {connection_name} mode {mode}"
        result = utils.exec_cmd(cmd, self.conn)
        if result:
            if result["st"]:
                return True
        return False

    def down_connect(self, connection_name):
        cmd = f"nmcli connection down {connection_name}"
        result = utils.exec_cmd(cmd, self.conn)
        if result:
            if result["st"]:
                return True
        return False

    def del_connect(self, connection_name):
        cmd = f"nmcli connection delete {connection_name}"
        result = utils.exec_cmd(cmd, self.conn)
        if result:
            if result["st"]:
                return True
        return False

    def get_connection(self):
        """get all the connection,return a string"""
        cmd = f"nmcli connection show"
        result = utils.exec_cmd(cmd, self.conn)
        if result:
            if result["st"]:
                return result["rt"]

    def print_mode(self, device):
        cmd = f"cat /proc/net/bonding/{device}"
        result = utils.exec_cmd(cmd, self.conn)
        if result:
            if result["st"]:
                # Bonding Mode: xxx
                print(result["rt"])
                return result["rt"]

    # for bonding modify
    def get_hostname(self):
        cmd = "hostname"
        result = utils.exec_cmd(cmd, self.conn)
        if result:
            if result["st"]:
                return result["rt"]

    def modify_hostname(self, hostname):
        cmd = f'hostnamectl set-hostname {hostname}'
        utils.exec_cmd(cmd, self.conn)

    def get_device_status(self):
        cmd = "nmcli device status"
        result = utils.exec_cmd(cmd, self.conn)
        if result:
            if result["st"]:
                return result["rt"]

    def get_bond_ip(self, bonding_name):
        cmd = f"nmcli device show {bonding_name} | grep IP4.ADDRESS"
        result = utils.exec_cmd(cmd, self.conn)
        if result:
            if result["st"]:
                return result["rt"]

    def modify_hosts_file(self,old_hostname,new_hostname):
        cmd = f"sed -i 's/{old_hostname}$/{new_hostname}/g' /etc/hosts"
        utils.exec_cmd(cmd, self.conn)
