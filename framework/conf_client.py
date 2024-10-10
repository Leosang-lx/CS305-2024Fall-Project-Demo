import socket

from config import *
from util import *


class ConferenceClient:
    def __init__(self, server_ip: str, server_port_main: int):
        """
        建立与服务器的主要连接：仅用于与服务器的通信（保持连接）
        """
        self.server_addr = (server_ip, server_port_main)
        self.ip = get_ip_address()
        self.is_working = True
        # try:
        # only for short message between this client and server
        self.main_server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.main_server_sock.connect((server_ip, server_port_main))

        # except Exception as e:
        #     print(e)
        #     sys.exit(0)
        # print(f'Connected to server:{server_addr}')

        # meeting status
        # self.on_meeting = False
        self.is_manager = False
        self.conference_id = None

        self.client_name = None
        self.client_id = None

        # data transmission of meeting
        self.screen_port = -1
        self.camera_port = -1
        self.audio_port = -1

        self.sock_screen = None
        self.sock_camera = None
        self.sock_audio = None
        # self.sock_media = None
        # self.sock_msg = None

        self.share_screen = False
        self.share_camera = False
        self.share_audio = False
        # self.share_media = False

        # output recv data (no cache)
        self.screen_frame = None
        self.camera_frame = None
        self.audio_chunk = None
        # self.media_chunk = None

    # def recv_msg(self):
    #     while self.is_working:
    #         data, addr = self.main_server_sock.recvfrom(1500)
    #         msg = data.decode()
    #         print(f'Recv from addr {addr}: {msg}')

    def init_conf_conns(self, ports_conference):
        """
        进入会议时，初始化传输连接
        """
        self.screen_port, self.camera_port, self.audio_port = ports_conference
        # client_socket
        self.sock_screen = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


    def close_conf_conns(self):
        """
        退出会议时，关闭所有该会议对应的传输连接
        """
        pass

    def create_conference(self):
        """
        创建会议：向服务器发送创建会议请求，并建立该会议对应的服务器传输连接
        """
        msg = f'CREATE'
        self.main_server_sock.sendto(msg.encode(), self.server_addr)
        data, addr = self.main_server_sock.recvfrom(1500)
        # 这里用udp直收后面可能会有bug
        msg = data.decode()
        fields = msg.split(' ')
        if fields[0] == 'FAIL:':
            print('[Reply]: server fail to create additional conference')

        elif len(fields) == 6 and fields[0] == 'conf_id' and fields[2] == 'port' and fields[4] == 'client_id':
            # msg = "conf_id [conference_id] port [conference_port] client_id [client_id]"
            conference_id = int(fields[1])
            ports_conference = (int(i) for i in fields[3].split(','))
            client_id = int(fields[5])
            self.conference_id = conference_id
            self.init_conf_conns(ports_conference)
            self.client_id = client_id
            self.client_name = f'user{self.client_id}'
            print(f'[Reply]: conference is created with ID={conference_id}')

        else:
            print(f'[Warn] from CREATE: unknown exception with message from server "{msg}"')

    def join_conference(self, conference_id):
        """
        加入会议：
        """
        msg = f'JOIN {conference_id}'
        self.main_server_sock.sendto(msg.encode(), self.server_addr)

        data, addr = self.main_server_sock.recvfrom(1500)
        # 这里用udp直收后面可能会有bug
        reply = data.decode()
        fields = reply.split(' ')
        if reply == 'Conference ID Not Found':
            print('Invalid Conference ID')
        elif len(fields) == 2 and fields[0] == 'port_conference':
            port_conference = int(fields[1])
            self.init_conf_conns(port_conference)
        else:
            print(f'[Warn] from JOIN: unknown exception with message from server "{reply}"')

    def quit_conference(self):
        if self.conference_id is None:
            print(f'[Warn]: cannot quit a conference when you are not in one')
            return

        msg = 'QUIT'
        self.main_server_sock.sendto(msg.encode(), self.server_addr)
        data, addr = self.main_server_sock.recvfrom(DGRAM_SIZE)
        reply = data.decode()  # server回复后，关闭服务端对应的socket并删除client记录
        if reply == 'OK':
            self.close_conf_conns()  # 收到回复才关闭连接

    def cancel_conference(self):
        """
        取消会议：作为会议主持人取消会议（具有权限才能够成功执行该方法）向服务器发送取消会议请求
        """
        if self.conference_id is None:
            print('[Warn]: cannot cancel conference when you are not in one')
            return
        if not self.is_manager:  # 一次权限确认，服务端会进行二次确认
            print('[Warn]: only the conference manager can cancel a conference')
            return

        msg = f'CANCEL {self.conference_id}'
        self.main_server_sock.sendto(msg.encode(), self.server_addr)
        # todo: 发送给服务器后，服务器关闭通知其他会议内其他全部client，并关闭会议内所有client用于传输的socket
        pass

    def output(self):
        """
        根据收到的视频帧以及音频节进行输出
        """
        pass

    def close(self):
        """
        关闭所有线程以及socket
        """
        pass

    def start(self):
        """
        根据命令行输入执行指定功能
        """
        pass

