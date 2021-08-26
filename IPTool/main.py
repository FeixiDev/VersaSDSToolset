import argparse
import sys
import os
import action

sys.path.append('../')
import utils
import consts
import control


class IPTool():
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog='main')
        self.setup_parser()

    def setup_parser(self):
        subp = self.parser.add_subparsers(metavar='', dest='subargs_vtel')

        self.parser.add_argument('-v',
                                 '--version',
                                 dest='version',
                                 help='Show current version',
                                 action='store_true')

        parser_bonding = subp.add_parser("bonding", aliases=['b', 'bond'], help="Bonding operation")
        # parser_ip = subp.add_parser("ip", help="ip operation")
        subp_bonding = parser_bonding.add_subparsers()

        parser_apply = subp_bonding.add_parser('apply', help='Apply config file')
        parser_apply.add_argument('file', metavar='FILE', action='store', help='YAML file with IP config')

        parser_create = subp_bonding.add_parser('create', aliases=['c'], help='Create bonding')
        parser_create.add_argument('bonding', metavar='BONDING', action='store', help='Bonding name')
        parser_create.add_argument('-n',
                                   '--node',
                                   dest='node',
                                   action='store',
                                   help='Node name')
        parser_create.add_argument('-d',
                                   '--device',
                                   dest='device',
                                   nargs='+',
                                   action='store',
                                   required=True,
                                   help='Device name')
        parser_create.add_argument('-m',
                                   '--mode',
                                   dest='mode',
                                   action='store',
                                   choices=["balance-rr", "active-backup", "balance-xor", "broadcast", "802.3ad", "balance-tlb",
                                            "balance-alb"],
                                   required=True,
                                   help='Bonding mode')
        parser_create.add_argument('-ip',
                                   '--ip',
                                   dest='ip',
                                   action='store',
                                   required=True,
                                   help='Bonding ip')

        parser_delete = subp_bonding.add_parser('delete', aliases=['d', 'del'], help='Delete bonding')
        parser_delete.add_argument('bonding', metavar='BONDING', action='store', help='Bonding name')
        parser_delete.add_argument('-n',
                                   '--node',
                                   dest='node',
                                   action='store',
                                   help='Node name')

        parser_modify = subp_bonding.add_parser('modify', aliases=['m'], help='Modify bonding mode')
        parser_modify.add_argument('bonding', metavar='BONDING', action='store', help='Bonding name')
        parser_modify.add_argument('-n',
                                   '--node',
                                   dest='node',
                                   action='store',
                                   help='Node name')
        parser_modify.add_argument('-m',
                                   '--mode',
                                   dest='mode',
                                   choices=["balance-rr", "active-backup", "balance-xor", "broadcast", "802.3ad", "balance-tlb",
                                            "balance-alb"],
                                   required=True,
                                   help='Bonding mode')

        # Bonding function
        parser_apply.set_defaults(func=self.apply_file)
        parser_delete.set_defaults(func=self.delete_bonding)
        parser_create.set_defaults(func=self.create_bonding)
        parser_modify.set_defaults(func=self.modify_mode)

        self.parser.set_defaults(func=self.main_usage)

    def print_help(self, args):
        self.parser.print_help()

    def main_usage(self, args):
        if args.version:
            print(f'Version: {consts.VERSION}')
        else:
            self.print_help(self.parser)

    def parse(self):  # 调用入口
        args = self.parser.parse_args()
        args.func(args)

    def apply_file(self, args):
        bonding = control.Bonding()
        bonding.create_bonding_by_file(args.file)

    def create_bonding(self, args):
        bonding = control.Bonding()
        bonding.create_bonding(args.node, args.bonding, args.mode, args.device, args.ip)

    def delete_bonding(self, args):
        bonding = control.Bonding()
        bonding.del_bonding(args.node, args.bonding)

    def modify_mode(self, args):
        bonding = control.Bonding()
        bonding.modify_bonding_mode(args.node, args.bonding, args.mode)


def main():
    if os.geteuid() != 0:
        print('This program must be run as root. Aborting.')
        sys.exit()
    try:
        cmd = IPTool()
        cmd.parse()
    except KeyboardInterrupt:
        sys.stderr.write("\nClient exiting (received SIGINT)\n")
    except PermissionError:
        sys.stderr.write("\nPermission denied (log file or other)\n")


if __name__ == '__main__':
    main()