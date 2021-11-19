import sys
import re
import utils
import action
import gevent
import threading
import time
from ssh_authorized import SSHAuthorizeNoMGN
import ctypes
import inspect


# def _async_raise(tid, exctype):
#     """raises the exception, performs cleanup if needed"""
#     tid = ctypes.c_long(tid)
#     if not inspect.isclass(exctype):
#         exctype = type(exctype)
#     res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
#     if res == 0:
#         raise ValueError("invalid thread id")
#     elif res != 1:
#         # """if it returns a number greater than one, you're in trouble,
#         # and you should call it again with exc=NULL to revert the effect"""
#         ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
#         raise SystemError("PyThreadState_SetAsyncExc failed")
#
#
# def stop_thread(thread):
#     _async_raise(thread.ident, SystemExit)

def get_crm_status_by_type(logger, result, resource, type):
    if result:
        if type in ['IPaddr2', 'iSCSITarget', 'portblock', 'iSCSILogicalUnit']:
            re_string = f'{resource}\s*\(ocf::heartbeat:{type}\):\s*(\w*)\s*(\w*)?'
            re_result = utils.re_search(logger, re_string, result, "groups")
            return re_result
        if type == 'FailedActions':
            re_string = "Failed Actions:\s*.*\*\s\w*\son\s(\S*)\s'(.*)'\s.*exitreason='(.*)',\s*.*"
            re_result = utils.re_search(logger, re_string, result, "group")
            return re_result


class Connect(object):
    """
    通过ssh连接节点，生成连接对象的列表
    """
    list_vplx_ssh = []

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            Connect._instance = super().__new__(cls)
            Connect._instance.config = args[0]
            Connect.get_ssh_conn(Connect._instance)
        return Connect._instance

    def get_ssh_conn(self):
        ssh = SSHAuthorizeNoMGN()
        local_ip = utils.get_host_ip()
        vplx_configs = self.config.get_vplx_configs()
        username = "root"
        for vplx_config in vplx_configs:
            if "username" in vplx_config.keys():
                if vplx_config['username'] is not None:
                    username = vplx_config['username']
            if local_ip == vplx_config['public_ip']:
                self.list_vplx_ssh.append(None)
                utils.set_global_dict_value(None, vplx_config['public_ip'])
            else:
                ssh_conn = ssh.make_connect(vplx_config['public_ip'], vplx_config['port'], username,
                                            vplx_config['password'])
                self.list_vplx_ssh.append(ssh_conn)
                utils.set_global_dict_value(ssh_conn, vplx_config['public_ip'])


class QuorumAutoTest(object):
    def __init__(self, config, logger):
        self.config = config
        self.conn = Connect(self.config)
        self.logger = logger
        self.vplx_configs = self.config.get_vplx_configs()

    def ssh_conn_build(self):
        print("Start to build ssh connect")
        ssh = SSHAuthorizeNoMGN()
        ssh.init_cluster_no_mgn('versaplx', self.vplx_configs, self.conn.list_vplx_ssh)

    def install_software(self):
        lst_update = []
        lst_install_spc = []
        lst_install_drbd = []
        lst_install_linstor = []
        for vplx_conn in self.conn.list_vplx_ssh:
            install_obj = action.InstallSoftware(self.logger, vplx_conn)
            lst_update.append(gevent.spawn(install_obj.update_apt))
            lst_install_spc.append(gevent.spawn(install_obj.install_spc))
            lst_install_drbd.append(gevent.spawn(install_obj.install_drbd))
            lst_install_linstor.append(
                gevent.spawn(install_obj.install_software, "linstor-controller linstor-satellite linstor-client"))
        gevent.joinall(lst_update)
        gevent.joinall(lst_install_spc)
        gevent.joinall(lst_install_drbd)
        gevent.joinall(lst_install_linstor)

    def test_drbd_quorum(self):
        sp = "sp_quorum"
        resource = "res_quorum"
        if len(self.conn.list_vplx_ssh) != 3:
            utils.prt_log(self.logger, None, f"Please make sure there are three nodes for this test", 2)
        test_times = self.config.get_test_times()
        use_case = self.config.get_use_case()
        size = self.config.get_resource_size()
        node_list = [vplx_config["hostname"] for vplx_config in self.vplx_configs]
        vtel_conn = None
        if None not in self.conn.list_vplx_ssh:
            vtel_conn = self.conn.list_vplx_ssh[0]
        # utils.prt_log(self.logger, None, f"Start to install software ...", 0)
        # self.install_software()
        # install_obj = action.InstallSoftware(self.logger, vtel_conn)
        # install_obj.update_pip()
        # install_obj.install_vplx()
        # install_obj.get_log()
        stor_obj = action.Stor(self.logger, vtel_conn)
        # utils.prt_log(self.logger, vtel_conn, f"Start to create node ...", 0)
        # for vplx_config in self.vplx_configs:
        #     stor_obj.create_node(vplx_config["hostname"], vplx_config["private_ip"]["ip"])
        # utils.prt_log(self.logger, vtel_conn, f"Start to create storagepool {sp} ...", 0)
        # for vplx_config in self.vplx_configs:
        #     stor_obj.create_sp(vplx_config["hostname"], sp, vplx_config["lvm_device"])
        # diskful_node_list = node_list[:]
        # utils.prt_log(self.logger, vtel_conn, f"Start to create resource {resource} ...", 0)
        # if use_case == 1:
        #     diskless_node = diskful_node_list.pop()
        #     stor_obj.create_diskful_resource(diskful_node_list, sp, size, resource)
        #     stor_obj.create_diskless_resource(diskless_node, resource)
        # if use_case == 2:
        #     stor_obj.create_diskful_resource(diskful_node_list, sp, size, resource)
        # time.sleep(5)
        for i in range(test_times):
            i = i + 1
            utils.set_times(i)
            print(f"Number of test times --- {i}")
            if not stor_obj.check_drbd_quorum(resource):
                utils.prt_log(self.logger, None, f"Abnormal quorum status of {resource}", 1)
                break
            resource_status, peer_resource_status = stor_obj.get_drbd_status(resource)
            if resource_status[1] not in ["UpToDate", "Diskless"]:
                utils.prt_log(self.logger, None, f"Abnormal status of {resource} status", 1)
                break
            for peer_resource_st in peer_resource_status:
                if peer_resource_st[1] not in ["UpToDate", "Diskless"]:
                    utils.prt_log(self.logger, None, f"Abnormal status of {resource} status", 1)
                    break
            stor_obj.primary_drbd(resource)
            time.sleep(5)
            stor_obj.secondary_drbd(resource)
            # device_name = stor_obj.get_device_name(resource)
            # self.test_by_dd(device_name, resource)
            utils.prt_log(self.logger, None, f"Wait 10 minutes...", 0)
            # time.sleep(600)
            time.sleep(60)
        # utils.prt_log(self.logger, vtel_conn, f"Start to delete resource {resource} ...", 0)
        # stor_obj.delete_resource(resource)
        # utils.prt_log(self.logger, vtel_conn, f"Start to delete storagepool {sp} ...", 0)
        # for node in node_list:
        #     stor_obj.delete_sp(node, sp)
        # utils.prt_log(self.logger, vtel_conn, f"Start to delete node ...", 0)
        # for node in node_list:
        #     stor_obj.delete_node(node)

    def test_by_dd(self, device_name, resource):
        # for vplx_conn in self.conn.list_vplx_ssh:
        stor_obj = action.Stor(self.logger, self.conn.list_vplx_ssh[1])
        ip_obj = action.IpService(self.logger, self.conn.list_vplx_ssh[1])
        stor_obj.primary_drbd(resource)
        device = "bond0"
        thread1 = threading.Thread(target=action.dd_operation,
                                   args=(self.logger, device_name, self.conn.list_vplx_ssh[1]))
        thread2 = threading.Thread(target=ip_obj.down_device, args=(device,))
        thread1.start()
        time.sleep(4)
        thread2.start()
        thread2.join()
        thread1.join()
        # stop_thread(thread1)
        ip_obj.up_device(device)
        ip_obj.netplan_apply()
        stor_obj.secondary_drbd(resource)

    def get_log(self, conn):
        log_path = self.config.get_crm_log_path()
        debug_log = action.DebugLog(self.logger, conn)
        utils.prt_log(self.logger, conn, f"Start to collect dmesg file ...", 0)
        debug_log.get_dmesg_file(time, log_path)
        utils.prt_log(self.logger, conn, f"Finished to collect dmesg file ...", 1)


class IscsiTest(object):
    def __init__(self, config, logger):
        self.config = config
        self.conn = Connect(self.config)
        self.logger = logger
        self.vplx_configs = self.config.get_vplx_configs()
        self.node_list = [vplx_config["hostname"] for vplx_config in self.vplx_configs]

    def test_drbd_in_used(self):
        start_time = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        if len(self.conn.list_vplx_ssh) != 3:
            utils.prt_log(self.logger, None, f"Please make sure there are three nodes for this test", 2)
        test_times = self.config.get_test_times()
        device = self.config.get_device()
        target = self.config.get_target()
        resource = self.config.get_resource()
        ip_obj = action.IpService(self.logger, self.conn.list_vplx_ssh[0])
        for i in range(test_times):
            i = i + 1
            utils.set_times(i)
            print(f"Number of test times --- {i}")
            if not self.check_target_lun_status(target, resource,
                                                self.conn.list_vplx_ssh[0]):
                self.collect_crm_report_file(start_time, self.conn.list_vplx_ssh[0])
            if not self.ckeck_drbd_status(resource):
                self.collect_crm_report_file(start_time, self.conn.list_vplx_ssh[0])
            utils.prt_log(self.logger, self.conn.list_vplx_ssh[0], f"Down {device} ...", 0)
            ip_obj.down_device(device)
            time.sleep(40)
            if not self.check_target_lun_status(target, resource, self.conn.list_vplx_ssh[1]):
                ip_obj.up_device(device)
                ip_obj.netplan_apply()
                time.sleep(30)
                self.collect_crm_report_file(start_time, self.conn.list_vplx_ssh[0])
            utils.prt_log(self.logger, self.conn.list_vplx_ssh[0], f"Up {device} ...", 0)
            ip_obj.up_device(device)
            ip_obj.netplan_apply()
            time.sleep(30)
            self.restore_resource(resource)
            utils.prt_log(self.logger, None, f"Wait 10 minutes to restore the original environment", 0)
            time.sleep(600)

    def check_target_lun_status(self, target, resource, conn):
        iscsi_obj = action.Iscsi(self.logger, conn)
        crm_status = iscsi_obj.get_crm_status()
        error_message = get_crm_status_by_type(self.logger, crm_status, None, "FailedActions")
        if error_message:
            print(error_message)
            return False
        init_resource_status = get_crm_status_by_type(self.logger, crm_status, resource, "iSCSILogicalUnit")
        init_target_status = get_crm_status_by_type(self.logger, crm_status, target, "iSCSITarget")
        if init_target_status:
            if init_target_status[0] != 'Started':
                utils.prt_log(self.logger, conn, f"Target status is {init_target_status[0]}", 1)
                return False
        else:
            utils.prt_log(self.logger, conn, f"Can't get status of target {target}", 1)
            return False
        if init_resource_status:
            if init_resource_status[0] != 'Started':
                utils.prt_log(self.logger, conn, f"LUN status is {init_resource_status[0]}", 1)
                return False
        else:
            utils.prt_log(self.logger, conn, f"Can't get status of resource {resource}", 1)
            return False
        if not init_target_status[1] == init_resource_status[1]:
            utils.prt_log(self.logger, conn, f"Target and LUN is not started on the same node", 1)
            return False
        return True

    def ckeck_drbd_status(self, resource):
        for vplx_conn in self.conn.list_vplx_ssh:
            stor_obj = action.Stor(self.logger, vplx_conn)
            resource_status, _ = stor_obj.get_drbd_status(resource)
            if resource_status[1] != "UpToDate" and resource_status[1] != "Diskless":
                utils.prt_log(self.logger, vplx_conn, f"Resource status is {resource_status[1]}", 1)
                return False
        return True

    def restore_resource(self, resource):
        conn = self.conn.list_vplx_ssh[1]
        init_start_node = self.node_list[0]
        iscsi_obj = action.Iscsi(self.logger, conn)
        iscsi_obj.ref_res()
        time.sleep(10)
        utils.prt_log(self.logger, conn, f"Move {resource} back to {init_start_node} ...", 0)
        iscsi_obj.move_res(resource, init_start_node)
        time.sleep(20)
        crm_status = iscsi_obj.get_crm_status()
        resource_status = get_crm_status_by_type(self.logger, crm_status, resource, "iSCSILogicalUnit")
        if resource_status:
            if resource_status[0] != 'Started' or resource_status[1] != init_start_node:
                utils.prt_log(self.logger, conn,
                              f"Failed to move {resource}, status:{resource_status[0]}", 1)
        else:
            utils.prt_log(self.logger, conn, f"Can't get status of resource {resource}", 1)
        iscsi_obj.unmove_res(resource)

    def collect_crm_report_file(self, time, conn):
        crm_log_path = self.config.get_crm_log_path()
        debug_log = action.DebugLog(self.logger, conn)
        utils.prt_log(self.logger, conn, f"Start to collect crm_report...", 0)
        debug_log.get_crm_report_file(time, crm_log_path)
        utils.prt_log(self.logger, conn, f"Finished to collect crm_report and exit testing ...", 2)