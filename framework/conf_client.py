import sys
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

        # data transmission of meeting
        self.sock_screen = None
        self.sock_camera = None
        self.sock_audio = None
        self.sock_media = None
        self.sock_msg = None

        self.share_screen = False
        self.share_camera = False
        self.share_audio = False
        self.share_media = False

        # output recv data (no cache)
        self.screen_frame = None
        self.camera_frame = None
        self.audio_chunk = None
        self.media_chunk = None

    def recv_msg(self):
        while self.is_working:
            data, addr = self.main_server_sock.recvfrom(1500)
            msg = data.decode()
            print(f'Recv from addr {addr}: {msg}')

    def init_conf_conns(self, port_conference):
        pass

    def create_conference(self):
        """
        创建会议：向服务器发送创建会议请求，并建立该会议对应的服务器传输连接
        """
        msg = f'create'
        self.main_server_sock.sendto(msg.encode(), self.server_addr)
        data, addr = self.main_server_sock.recvfrom(1500)
        # 这里用udp直收后面可能会有bug
        msg = data.decode()
        fields = msg.split(' ')
        if fields[0] == 'Fail':
            print('Server fail to create additional conference')

        elif len(fields) == 4 and fields[0] == 'Conf_id' and fields[2] == 'port':
            # msg = "Conf_id [conference_id] port [conference_port]"
            conference_id = int(fields[1])
            port_conference = int(fields[3])
            self.conference_id = conference_id
            self.init_conf_conns(port_conference)
            print(f'Conference is created with ID: {conference_id}')
        else:
            print(f'Warning from [create]: unknown exception with message from server "{msg}"')

    def join_conference(self, conference_id):
        """
        加入会议：
        """
        msg = f'join {conference_id}'
        self.main_server_sock.sendto(msg.encode(), self.server_addr)
        data, addr = self.main_server_sock.recvfrom(1500)
        # 这里用udp直收后面可能会有bug
        msg = data.decode()
        fields = msg.split(' ')
        if msg == 'Conference ID Not Found':
            print('Invalid Conference ID')
        elif len(fields) == 2 and fields[0] == 'port_conference':
            port_conference = int(fields[1])
            self.init_conf_conns(port_conference)
        else:
            print(f'Warning from [join]: unknown exception with message from server "{msg}"')

    def cancel_conference(self):
        """
        取消会议：作为会议主持人取消会议（具有权限才能够成功执行该方法）向服务器发送取消会议请求
        """
        if self.conference_id is None:
            print('Warning: cannot cancel conference when you are not in one')
            return
        if not self.is_manager:
            print('Warning: cannot cancel conference if you are not a conference manager')
            return

        msg = f'cancel {self.conference_id}'
        self.main_server_sock.sendto(msg.encode(), self.server_addr)

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

