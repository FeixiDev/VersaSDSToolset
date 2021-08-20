import sys
import re
import utils
import action


class Bonding():
    def __init__(self, conn=None):
        self.conn = conn

    def create_bonding_by_file(self, file):
        """create bonding via yaml config file"""
        config = utils.ConfFile(file)
        host_config = config.get_config()
        for host in host_config:
            print('-' * 15, host[0], '-' * 15)
            self.create_bonding(host[0], host[1], host[2], host[3], host[4])

    def create_bonding(self, node, bonding_name, mode, device_list, new_ip):
        if not utils.check_ip(new_ip):
            sys.exit()

        bonding = action.IpService(node)
        connection = bonding.get_connection()
        lc_mode = bonding.get_mode(bonding_name)

        cmd = "nmcli connection show"
        if self.check_bonding_exist(f'vtel_{bonding_name}', connection):
            print(f"{bonding_name} already exists.")
            lc_hostname = bonding.get_hostname()
            if not self.check_hostname(lc_hostname,node):
                bonding.modify_hostname(node)
                bonding.modify_hosts_file(lc_hostname,node)

            if not self.check_mode(lc_mode, mode):
                bonding.modify_bonding_mode(bonding_name, mode)
                bonding.up_ip_service(f'vtel_{bonding_name}')
                bonding.print_mode(bonding_name)

            # bond0 的IP不一致
            lc_ip_data = bonding.get_bond_ip(bonding_name)

            if not self.check_bond_ip(new_ip, lc_ip_data):
                gateway = f"{'.'.join(new_ip.split('.')[:3])}.1"
                bonding.modify_ip(bonding_name, new_ip, gateway)
                bonding.up_ip_service(f'vtel_{bonding_name}')

            lc_device_date = bonding.get_device_status()
            for device in device_list:
                if not self.check_device(device,lc_device_date):
                    print(f"没有{device},退出")
                    return

                bonding_slave = f'vtel_{bonding_name}-slave-{device}'
                if not self.check_bonding_slave(bonding_slave, connection):
                    bonding.add_bond_slave(f"{bonding_name}", device)
                    if bonding_slave:
                        bonding.up_ip_service(bonding_slave)
                    else:
                        print(f'Failed to add bond slave about {device}')
                
        else:
            if bonding.set_bonding(bonding_name, mode):
                gateway = f"{'.'.join(new_ip.split('.')[:3])}.1"
                bonding.modify_ip(bonding_name, new_ip, gateway)
            for device in device_list:
                bonding_slave = bonding.add_bond_slave(f"{bonding_name}", device)
                if bonding_slave:
                    bonding.up_ip_service(bonding_slave)
                else:
                    print(f'Failed to add bond slave about {device}')
            bonding.up_ip_service(f'vtel_{bonding_name}')

    def del_bonding(self, node, device):
        bonding_name = f'vtel_{device}'
        bonding = action.IpService(node)
        connection = bonding.get_connection()
        if connection:
            slave_list = self.get_slave_via_bonding_name(bonding_name, connection)
            if slave_list:
                print("Started to delete bonding slave")
                for slave in slave_list:
                    bonding.down_connect(slave)
                    if bonding.del_connect(slave):
                        print(f" Success in deleting {slave}")
                    else:
                        print(f" Failed to delete {slave}")
            if self.check_bonding_exist(bonding_name, connection):
                bonding.down_connect(bonding_name)
                print("Started to delete bonding")
                if bonding.del_connect(bonding_name):
                    print(f" Success in deleting {bonding_name}")
                else:
                    print(f" Failed to delete {bonding_name}")
            else:
                print(f"There is no configuration to delete for {device}.")
        else:
            print("Can't get any configuration")

    def modify_bonding_mode(self, node, device, mode):
        bonding = action.IpService(node)
        bonding.modify_bonding_mode(device, mode)
        bonding.up_ip_service(f'vtel_{device}')
        bonding.print_mode(device)
        # if bonding.down_connect(f'vtel_{device}'):
        #     if bonding.modify_bonding_mode(device, mode):
        #         print(f'Success in modify {device} mode of {mode}')
        # else:
        #     print(f"Failed to modify {device} mode of {mode}")

    def get_slave_via_bonding_name(self, bonding_name, string):
        slave_list = re.findall(f'({bonding_name}-slave-\S*)\s+\S+\s+\S+\s+\S+', string)
        return slave_list

    def check_bonding_exist(self, bonding_name, string):
        bonding_obj = re.search(f'({bonding_name}\S*)\s+\S+\s+bond\s+\S+', string)
        return bonding_obj

    def check_hostname(self, lc_hostname, tg_hostname):
        if lc_hostname == tg_hostname:
            return True

    def check_mode(self, local_mode, conf_mode):
        if conf_mode == 'balance-rr':
            if 'load balancing (round-robin)' in local_mode:
                return True
        elif conf_mode == 'active-backup':
            if 'active-backup' in local_mode:
                return True
        elif conf_mode == 'balance-xor':
            if 'balance-xor' in local_mode:
                return True
        elif conf_mode == 'broadcast':
            if 'broadcast' in local_mode:
                return True
        elif conf_mode == '802.3ad':
            if '802.3ad' in local_mode:
                return True
        elif conf_mode == 'balance-tlb':
            if 'balance-tlb' in local_mode:
                return True
        elif conf_mode == 'balance-alb':
            if 'balance-alb' in local_mode:
                return True

    def check_bond_ip(self, tg_ip, lc_ip_data):
        "Eg. lc_ip_data: IP4.ADDRESS[1]:                         10.203.1.76/24"
        if tg_ip in lc_ip_data:
            return True

    def check_device(self, tg_device, lc_device_data):
        if tg_device in lc_device_data:
            return True

    def check_bonding_slave(self, slave, conect_data):
        if slave in conect_data:
            return True



