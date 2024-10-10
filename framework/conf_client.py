import socket
import threading
import pickle
from config import *
from util import *


import asyncio
import threading
import time

# class Sender:
#     def __init__(self, host, client_id, screen_port, camera_port, audio_port):
#         self.host = host
#         self.client_id = client_id
#         self.share_switch = {
#             'screen': False,
#             'camera': False,
#             'audio': False
#         }
#         self.ports = {
#             'screen': screen_port,
#             'camera': camera_port,
#             'audio': audio_port
#         }
#         self.senders = {}
#         self.running = True
#
#     async def send_data(self, data_type, capture_function, interval):
#         reader, writer = await asyncio.open_connection(self.host, self.ports[data_type])
#         while self.running:
#             if self.share_switch[data_type]:
#                 # 发送数据
#                 captured_data = capture_function()
#                 data_to_send = self.client_id, captured_data
#                 writer.write(pickle.dumps(data_to_send))
#                 await writer.drain()
#                 await asyncio.sleep(interval)
#             else:
#                 await asyncio.sleep(0.2)
#
#     def start_senders(self):
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#
#         # 假设视频数据发送频率为30 FPS (1/30秒)，音频为44.1 kHz (1024/44100秒)，控制命令为1 Hz (1秒)
#         self.senders['screen'] = loop.create_task(self.send_data('video', capture_screen, 1/30))
#         self.senders['camera'] = loop.create_task(self.send_data('control', capture_camera, 1))
#         self.senders['audio'] = loop.create_task(self.send_data('audio', capture_voice, 1024/44100))
#
#         try:
#             loop.run_forever()
#         except KeyboardInterrupt:
#             pass
#         finally:
#             for task in self.senders.values():
#                 task.cancel()
#             loop.run_until_complete(asyncio.gather(*[task for task in self.senders.values()], return_exceptions=True))
#             loop.close()
#
#
# # def run_sender():
# #     sender = Sender('127.0.0.1', 8888, 8889, 8890)
# #     sender.start_senders()
#
# # 启动发送线程
# # sender_thread = threading.Thread(target=run_sender)
# # sender_thread.start()
#
# frame = {
#         'video': None,
#         'audio': None,
#         'control': None
#         }
# tag = {
#         'video': None,
#         'audio': None,
#         'control': None
#         }
#
#
# class Receiver:
#     def __init__(self, host, video_port, audio_port, control_port):
#         self.host = host
#         self.ports = {
#             'video': video_port,
#             'audio': audio_port,
#             'control': control_port
#         }
#         self.receivers = {}
#
#     async def receive_data(self, data_type):
#         pass
#         # global frame
#         # reader, writer = await asyncio.open_connection(self.host, self.ports[data_type])
#         # while True:
#         #     # 接收数据
#         #     data = await reader.readexactly(data_header_size)  # 你可以根据实际情况调整缓冲区大小
#         #     data_size = struct.unpack(data_header_format, data)
#         #     data = await reader.readexactly(data_size)
#         #     client_id, frame_data = pickle.loads(data)
#             # for
#             # if not data:
#             #     break
#             # print(f"Received {data_type}: {data}")
#
#     def start_receivers(self):
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#
#         # 启动接收任务
#         self.receivers['video'] = loop.create_task(self.receive_data('video'))
#         self.receivers['audio'] = loop.create_task(self.receive_data('audio'))
#         self.receivers['control'] = loop.create_task(self.receive_data('control'))
#
#         try:
#             loop.run_forever()
#         except KeyboardInterrupt:
#             pass
#         finally:
#             for task in self.receivers.values():
#                 task.cancel()
#             loop.run_until_complete(asyncio.gather(*[task for task in self.receivers.values()], return_exceptions=True))
#             loop.close()
#
# def run_receiver():
#     receiver = Receiver('127.0.0.1', 8888, 8889, 8890)
#     receiver.start_receivers()
#
# # 启动接收线程
# receiver_thread = threading.Thread(target=run_receiver)
# receiver_thread.start()


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

        # UDP
        # self.send_sock = None
        # self.recv_sock = None

        # TCP
        self.conference_sock = None
        self.sock_screen = None
        self.sock_camera = None
        self.sock_audio = None
        # self.sock_media = None
        # self.sock_msg = None

        self.on_meeting = False
        self.share_screen = False
        self.share_camera = False
        self.share_audio = False
        # self.share_media = False

        self.send_thread = None
        self.recv_thread = None

        # output recv data (no cache)
        self.screen_frame = None
        self.camera_frames = None
        self.audio_chunk = None
        # self.media_chunk = None

    # def recv_msg(self):
    #     while self.is_working:
    #         data, addr = self.main_server_sock.recvfrom(1500)
    #         msg = data.decode()
    #         print(f'Recv from addr {addr}: {msg}')

    def init_conf(self, port_conference):
        """
        进入会议时，初始化传输连接
        """

        self.screen_port, self.camera_port, self.audio_port = port_conference + 1, port_conference + 2, port_conference + 3,
        # client_socket
        try:
            self.conference_sock = socket.create_connection((SERVER_IP, port_conference))
            self.sock_screen = socket.create_connection((SERVER_IP, self.screen_port))
            self.sock_camera = socket.create_connection((SERVER_IP, self.camera_port))
            self.sock_audio = socket.create_connection((SERVER_IP, self.audio_port))

        except Exception as e:
            print(e)

        # self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        reply = recv_data(self.conference_sock)
        if reply == 'OK':
            print('[Reply] Init conference conns')
            self.on_meeting = True
        else:
            # 可能有错误回复
            pass

    def close_conf_conns(self):
        """
        退出会议时，关闭所有该会议对应的传输连接
        """
        self.conference_id = None
        self.conference_sock.close()
        self.conference_sock = None

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
            port_conference = int(fields[3])
            client_id = int(fields[5])

            self.conference_id = conference_id
            self.client_id = client_id
            self.client_name = f'user{self.client_id}'  # useless

            print(f'[Reply]: conference is created with ID={conference_id}')

            self.init_conf(port_conference)
            self.start_sharing()

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
        elif len(fields) == 2 and fields[0] == 'port':
            port_conference = int(fields[1])
            self.init_conf(port_conference)
            self.start_sharing()

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

    def share(self, data_type: str, share_socket, capture_function, fps=10):
        try:
            # share_socket = socket.create_connection((SERVER_IP, port))
            print(f'[Msg] Build connection for {data_type} sharing')

            interval = 1 / (fps + 1)

            while self.is_working:
                if self.share_screen:
                    capture_data = capture_function()
                    send_data(share_socket, (self.client_id, capture_data))
                    time.sleep(interval)
                else:
                    time.sleep(0.2)

        except Exception as e:
            print(e)

    def recv_screen(self):
        while self.is_working:
            client_id, frame = recv_data(self.sock_screen)
            self.screen_frame, self.screen_tag = frame, time.perf_counter()

    def recv_camera(self):
        while self.is_working:
            client_id, frame = recv_data(self.sock_camera)
            if self.camera_frames is None:
                self.camera_frames = [None] * 10
            self.camera_frames[client_id] = frame
            self.camera_tag = time.perf_counter()

    def recv_audio(self):
        while self.is_working:
            client_id, audio_chunk = recv_data(self.sock_audio)
            streamout.write(audio_chunk)

    def display_frames(self):
        """
        根据收到的视频帧以及音频节进行输出
        """
        last_screen_tag = None
        last_camera_tag = None
        while self.is_working:
            if self.screen_frame is None and self.camera_frames is None:
                time.sleep(0.1)
            else:
                update_screen = False
                update_camera = False
                if self.screen_frame is not None:
                    # screen_tag, screen_frame = recv_screen
                    if last_screen_tag is None or self.screen_tag != last_screen_tag:
                        last_screen_tag = self.screen_tag
                        update_screen = True
                if self.camera_frames is not None:
                    # camera_tag, camera_frames = recv_camera
                    if last_camera_tag is None or self.camera_tag != last_camera_tag:
                        last_camera_tag = self.camera_tag
                        update_camera = True
                if update_screen or update_camera:
                    display_frame = overlay_camera_on_screen(self.screen_frame, self.camera_frames)
                    cv2.imshow('Recv Frames', display_frame)

    def start_meeting(self):
        self.sock_screen = socket.create_connection((SERVER_IP, self.screen_port))
        self.sock_camera = socket.create_connection((SERVER_IP, self.camera_port))
        self.sock_audio = socket.create_connection((SERVER_IP, self.audio_port))

        share_screen_thread = threading.Thread(target=self.share, args=('screen', self.sock_screen, capture_screen, 10))
        share_camera_thread = threading.Thread(target=self.share, args=('camera', self.sock_camera, capture_camera, 10))
        share_audio_thread = threading.Thread(target=self.share, args=('audio', self.sock_audio, capture_audio, 45))

        recv_screen_thread = threading.Thread(target=self.recv_screen, args=())
        recv_camera_thread = threading.Thread(target=self.recv_camera, args=())
        recv_audio_thread = threading.Thread(target=self.recv_audio, args=())

        recv_threads = [recv_screen_thread, recv_camera_thread, recv_audio_thread]
        share_threads = [share_screen_thread, share_camera_thread, share_audio_thread]
        for t in recv_threads:
            t.start()

        for t in share_threads:
            t.start()

        self.display_frames()

    def close(self):
        """
        关闭所有线程以及socket
        """
        pass

    def start(self):
        """
        根据命令行输入执行指定功能
        """
        while True:
            if self.conference_sock is None:
                status = 'Free'
            else:
                status = f'OnMeeting-{self.conference_id}'

            recognized = True
            operation = input(f'({status}) Please enter letter (enter "?" to help)').strip().lower()
            fields = operation.split(' ')
            if len(fields) == 1:
                if operation in ('?', '？'):
                    print(HELP)
                elif operation == 'create':
                    self.create_conference()
                elif operation == 'quit':
                    self.quit_conference()
                elif operation == 'cancel':
                    self.cancel_conference()
                else:
                    recognized = False
            elif len(fields) == 2:
                if fields[0] == 'join':
                    input_conf_id = fields[1]
                    if input_conf_id.isdigit():
                        self.join_conference(input_conf_id)
                    else:
                        print('[Warn]: Input conference ID must be digital form')
                elif fields[0] == 'switch':
                    pass
                else:
                    recognized = False
            else:
                recognized = False

            if not recognized:
                print(f'[Warn]: Unrecognized operation {operation}')


if __name__ == '__main__':
    client = ConferenceClient(SERVER_IP, SERVER_MAIN_PORT)
    client.star

