import control


class NormalIPCommands(object):
    def __init__(self, sub_parser):
        self.subp = sub_parser
        self.setup_parser()

    def setup_parser(self):
        self.parser_normal_ip = self.subp.add_parser("ip", help="Normal IP operation")
        subp_ip = self.parser_normal_ip.add_subparsers()

        parser_create = subp_ip.add_parser('create', aliases=['c'], help='Create IP')
        # parser_create.add_argument('-n',
        #                            '--node',
        #                            dest='node',
        #                            action='store',
        #                            help='Node (IP) for SSH connect')
        # parser_create.add_argument('-p',
        #                            '--password',
        #                            dest='password',
        #                            action='store',
        #                            help='Password for SSH connect')
        parser_create.add_argument('-d',
                                   '--device',
                                   dest='device',
                                   nargs=1,
                                   action='store',
                                   required=True,
                                   help='Device name')
        parser_create.add_argument('-ip',
                                   '--ip',
                                   dest='ip',
                                   action='store',
                                   required=True,
                                   help='Normal ip')
        parser_create.add_argument('-dns',
                                   '--dns',
                                   dest='dns',
                                   action='store',
                                   help='DNS value')
        parser_create.add_argument('-g',
                                   '--gateway',
                                   dest='gateway',
                                   action='store',
                                   help='Gateway value')

        parser_delete = subp_ip.add_parser('delete', aliases=['d', 'del'], help='Delete IP')
        # parser_delete.add_argument('-n',
        #                            '--node',
        #                            dest='node',
        #                            action='store',
        #                            help='Node (IP) for SSH connect')
        # parser_delete.add_argument('-p',
        #                            '--password',
        #                            dest='password',
        #                            action='store',
        #                            help='Password for SSH connect')
        parser_delete.add_argument('-d',
                                   '--device',
                                   dest='device',
                                   nargs=1,
                                   action='store',
                                   required=True,
                                   help='Device name')

        parser_modify = subp_ip.add_parser('modify', aliases=['m', 'mod'], help='Modify IP')
        # parser_modify.add_argument('-n',
        #                            '--node',
        #                            dest='node',
        #                            action='store',
        #                            help='Node (IP) for SSH connect')
        # parser_modify.add_argument('-p',
        #                            '--password',
        #                            dest='password',
        #                            action='store',
        #                            help='Password for SSH connect')
        parser_modify.add_argument('-ip',
                                   '--ip',
                                   dest='ip',
                                   action='store',
                                   required=True,
                                   help='IP that you want to set')
        parser_modify.add_argument('-d',
                                   '--device',
                                   dest='device',
                                   nargs=1,
                                   action='store',
                                   required=True,
                                   help='Device name')
        parser_modify.add_argument('-dns',
                                   '--dns',
                                   dest='dns',
                                   action='store',
                                   help='DNS value')
        parser_modify.add_argument('-g',
                                   '--gateway',
                                   dest='gateway',
                                   action='store',
                                   help='Gateway value')

        parser_create.set_defaults(func=self.create)
        parser_delete.set_defaults(func=self.delete)
        parser_modify.set_defaults(func=self.modify)
        self.parser_normal_ip.set_defaults(func=self.print_normal_help)

    def create(self, args):
        args.node = None
        args.password = None
        conn = control.get_ssh_conn(args.node, args.password)
        normal_ip = control.NormalIP()
        normal_ip.create_ip(conn, args.device, args.ip, args.dns, args.gateway)

    def delete(self, args):
        args.node = None
        args.password = None
        conn = control.get_ssh_conn(args.node, args.password)
        normal_ip = control.NormalIP()
        normal_ip.del_ip(conn, args.device)

    def modify(self, args):
        args.node = None
        args.password = None
        conn = control.get_ssh_conn(args.node, args.password)
        normal_ip = control.NormalIP()
        normal_ip.modify_ip(conn, args.device, args.ip, args.dns, args.gateway)

    def print_normal_help(self, *args):
        self.parser_normal_ip.print_help()
