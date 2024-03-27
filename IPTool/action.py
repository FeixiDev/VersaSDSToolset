# -*- coding: utf-8 -*-
import utils


class IpService(object):
    def __init__(self, conn=None):
        self.conn = conn

    def set_ip(self, device, ip, gateway, dns, netmask=24):
        connection_name = f'vtel_{device}'
        cmd = f"nmcli connection add con-name {connection_name} type ethernet ifname {device} ipv4.addresses {ip}/{netmask} ipv4.gateway {gateway} ipv4.dns {dns} ipv4.method manual ipv6.method ignore"
        result = utils.exec_cmd(cmd, self.conn)
        if result:
            if result["st"]:
                return True

    def get_mode_detail(self, bonding_name):
        cmd = f"cat /proc/net/bonding/{bonding_name}"
        result = utils.exec_cmd(cmd, self.conn)
        return result["rt"]

    def up_ip_service(self, connection_name):
        cmd = f"nmcli connection up id {connection_name}"
        result = utils.exec_cmd(cmd, self.conn)
        if result:
            if result["st"]:
                print(f" Success in up {connection_name}.")
                return True
            else:
                print(f" Failed to up {connection_name}.")
        return False

    # def modify_normal_ip(self, device, new_ip, gateway, netmask=24):
    #     connection_name = f'vtel_{device}'
    #     cmd = f"nmcli connection modify {connection_name} ipv4.address {new_ip}/{netmask} ipv4.gateway {gateway}"
    #     result = utils.exec_cmd(cmd, self.conn)
    #     if result:
    #         if result["st"]:
    #             return True
    #     return False

    def modify_normal_ip(self, device, new_ip, gateway=None, dns=None, netmask=24):
        connection_name = f'vtel_{device}'
        cmd = f"nmcli connection modify {connection_name} ipv4.address {new_ip}/{netmask}"
        if gateway is not None:
            cmd += f" ipv4.gateway {gateway}"
        if dns is not None:
            cmd += f" ipv4.dns {dns}"
        result = utils.exec_cmd(cmd, self.conn)
        if result:
            if result["st"]:
                return True
        return False

    def modify_bond_ip(self, device, new_ip, netmask=24):
        connection_name = f'vtel_{device}'
        cmd = f"nmcli connection modify {connection_name} ipv4.address {new_ip}/{netmask} ipv4.method manual ipv6.method ignore"
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

    def add_bond_options(self, device, option):
        connection_name = f'vtel_{device}'
        cmd = f"nmcli connection modify {connection_name} +bond.options {option}"
        result = utils.exec_cmd(cmd, self.conn)
        if result:
            if result["st"]:
                return True

    def delete_bond_options(self, device, option):
        connection_name = f'vtel_{device}'
        cmd = f"nmcli connection modify {connection_name} -bond.options {option}"
        result = utils.exec_cmd(cmd, self.conn)
        if result:
            if result["st"]:
                return True

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

    def down_connect(self, connection_name):
        cmd = f"nmcli connection down {connection_name}"
        result = utils.exec_cmd(cmd, self.conn)
        if result:
            if result["st"]:
                return True
        return False

    def del_connect(self, name):
        cmd = f"nmcli connection delete {name}"
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
            return result["rt"]

    def get_device_detail(self, bonding_name):
        cmd = f"nmcli device show {bonding_name}"
        result = utils.exec_cmd(cmd, self.conn)
        if result:
            return result["rt"]

    def get_device_status(self):
        cmd = "nmcli device status"
        result = utils.exec_cmd(cmd, self.conn)
        if result:
            return result["rt"]

    def get_bond_ethtool(self, device):
        cmd = f"ethtool {device}"
        result = utils.exec_cmd(cmd, self.conn)
        if result:
            return result["rt"]
