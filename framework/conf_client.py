import socket

from util import *

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

        # only for short message between this client and server
        self.main_server_sock = None

        self.is_manager = False
        self.conference_id = None

        self.client_name = None
        self.client_id = None

        # data transmission of meeting
        self.stream_ports = {
            'screen': 0,
            'camera': 0,
            'audio': 0
        }

        # UDP
        # self.send_sock = None
        # self.recv_sock = None

        # TCP
        self.conference_sock = None
        self.stream_socks = {
            'screen': None,
            'camera': None,
            'audio': None
        }
        # self.sock_screen = None
        # self.sock_camera = None
        # self.sock_audio = None
        # self.sock_media = None
        # self.sock_msg = None

        self.on_meeting = False
        self.share_screen = True
        self.share_camera = False
        self.share_audio = False
        self.share_data = {
            'screen': False,
            'camera': False,
            'audio': False
        }
        # self.share_media = False

        self.send_threads = None
        self.recv_threads = None

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

    def share_switch(self, data_type):
        if data_type == 'screen':
            self.share_data[data_type] = not self.share_data[data_type]
        elif data_type == 'camera':
            if can_capture_camera:
                self.share_data[data_type] = not self.share_data[data_type]
            else:
                self.share_data[data_type] = False
        elif data_type == 'audio':
            self.share_data[data_type] = not self.share_data[data_type]
        else:
            print(f'[Warn]: sharing {data_type} is unsupported')

    def init_conn(self, port_conference):
        """
        进入会议时，初始化传输连接
        """

        for i, stream_type in enumerate(self.stream_ports.keys()):
            self.stream_ports[stream_type] = port_conference + i + 1
        # client_socket
        try:
            self.conference_sock = socket.create_connection((SERVER_IP, port_conference))
            # self.conference_sock.sendall((self.client_name + '\n').encode())

            reply = recv_data(self.conference_sock)
            fields = reply.split()
            if len(fields) == 2 and fields[0] == 'client_id' and fields[1].isdigit():
                print('[Reply]: Init conference conns')
                self.on_meeting = True
                self.client_id = int(fields[1])
            else:
                # 可能有错误回复
                print(f'[Warn]: unknown response: {reply}')

            time.sleep(1)
            msg = f'{self.client_id}\n'.encode()
            for stream_type in self.stream_socks.keys():
                sock = socket.create_connection((SERVER_IP, self.stream_ports[stream_type]))
                sock.sendall(msg)
                self.stream_socks[stream_type] = sock

        except Exception as e:
            print(e)

        # self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def close_conf_conns(self):
        """
        退出会议时，关闭所有该会议对应的传输连接
        """
        try:
            self.conference_id = None
            if self.conference_sock:
                self.conference_sock.close()
                self.conference_sock = None
            for stream_type in self.stream_socks.keys():
                sock = self.stream_socks[stream_type]
                if sock:
                    sock.close()
                    self.stream_socks[stream_type] = None

        except Exception as e:
            print('Exception in close_conf_conns:', e)

    def send_request(self, request: str):
        # synchronize
        with socket.create_connection(self.server_addr) as request_conn:
            self.main_server_sock = request_conn
            # data = gen_bytes(request)
            request_conn.sendall((request + '\n').encode())
            reply = recv_data(request_conn)
        self.main_server_sock = None
        return reply

    def create_conference(self):
        """
        创建会议：向服务器发送创建会议请求，并建立该会议对应的服务器传输连接
        """
        msg = f'CREATE'
        # self.main_server_sock.sendto(msg.encode(), self.server_addr)
        # data, addr = self.main_server_sock.recvfrom(1500)
        # # 这里用udp直收后面可能会有bug
        reply = self.send_request(msg)

        # msg = data.decode()
        fields = reply.split(' ')
        if fields[0] == 'FAIL:':
            print('[Reply]: server fail to create additional conference')

        elif len(fields) == 4 and fields[0] == 'conf_id' and fields[2] == 'port':
            # msg = "conf_id [conference_id] port [conference_port] client_id [client_id]"
            conference_id = int(fields[1])
            port_conference = int(fields[3])
            # client_id = int(fields[5])

            self.conference_id = conference_id
            # self.client_id = client_id
            self.client_name = f'user{self.client_id}'  # useless

            print(f'[Reply]: conference is created with ID={conference_id}')

            self.init_conn(port_conference)
            print(f'[Reply]: have joined conference with ID={conference_id}')
            self.start_meeting()

        else:
            print(f'[Warn] from CREATE: unknown exception with message from server "{msg}"')

    def join_conference(self, conference_id):
        """
        加入会议：
        """
        msg = f'JOIN {conference_id}'
        # self.main_server_sock.sendto(msg.encode(), self.server_addr)
        # data, addr = self.main_server_sock.recvfrom(1500)
        # reply = data.decode()

        reply = self.send_request(msg)

        # 这里用udp直收后面可能会有bug
        fields = reply.split(' ')
        if reply == 'Conference ID Not Found':
            print('Invalid Conference ID')
        elif len(fields) == 2 and fields[0] == 'port':
            port_conference = int(fields[1])
            self.init_conn(port_conference)
            print(f'[Reply]: have joined conference with ID={conference_id}')
            self.start_meeting()

        else:
            print(f'[Warn] from JOIN: unknown exception with message from server "{reply}"')

    def quit_conference(self):
        if isinstance(self.conference_sock, socket.socket):
            print(f'[Warn]: cannot quit a conference when you are not in one')
            return

        msg = 'QUIT\n'
        self.conference_sock.sendall(msg.encode())
        reply = recv_data(self.conference_sock)
        reply = reply.decode()  # server回复后，关闭服务端对应的socket并删除client记录
        if reply == 'OK':
            self.close_conf_conns()  # 收到回复才关闭连接
            self.close_threads()
        else:
            print(reply)

    def cancel_conference(self):
        """
        取消会议：作为会议主持人取消会议（具有权限才能够成功执行该方法）向服务器发送取消会议请求
        """
        if isinstance(self.conference_sock, socket.socket):
            print('[Warn]: cannot cancel conference when you are not in one')
            return
        if not self.is_manager:  # 一次权限确认，服务端会进行二次确认
            print('[Warn]: only the conference manager can cancel a conference')
            return

        msg = f'CANCEL\n'
        # self.main_server_sock.sendto(msg.encode(), self.server_addr)
        self.conference_sock.sendall(msg.encode())
        reply = recv_data(self.conference_sock)
        reply = reply.decode()  # server回复后，关闭服务端对应的socket并删除client记录
        if reply == 'OK':
            self.close_conf_conns()  # 收到回复才关闭连接
            self.close_threads()
        else:
            print(reply)

    def share(self, data_type: str, share_socket, capture_function, compress=None, fps=10):
        try:
            # share_socket = socket.create_connection((SERVER_IP, port))
            print(f'[Msg] Build connection for {data_type} sharing')

            interval = 1 / (fps + 1)
            send_cnt = 0
            while self.is_working:
                if self.share_data[data_type]:
                    capture_data = capture_function()
                    if compress:
                        capture_data = compress(capture_data)
                    send_data(share_socket, (self.client_id, capture_data))
                    send_cnt += 1
                    print(f'Send {data_type} {send_cnt}')
                    time.sleep(interval)
                else:
                    time.sleep(0.2)

        except Exception as e:
            print(e)

    def recv_screen(self, decompress=None):
        # recv_cnt = 0
        screen_sock = self.stream_socks['screen']
        assert screen_sock is not None
        try:
            while self.is_working:
                client_id, frame = recv_data(screen_sock)
                if decompress:
                    frame = decompress(frame)
                # recv_cnt += 1
                self.screen_frame, self.screen_tag = frame, time.perf_counter()
                # print('Recv screen', recv_cnt)
        except Exception as e:
            print('Exception for sock_screen:', e)

    def recv_camera(self, decompress=None):
        camera_sock = self.stream_socks['camera']
        try:
            while self.is_working:
                client_id, frame = recv_data(camera_sock)
                if decompress:
                    frame = decompress(frame)
                if self.camera_frames is None:
                    self.camera_frames = [None] * 10
                self.camera_frames[client_id] = frame
                self.camera_tag = time.perf_counter()
        except Exception as e:
            print('Exception for sock_camera:', e)

    def recv_audio(self):
        audio_sock = self.stream_socks['audio']
        try:
            while self.is_working:
                client_id, audio_chunk = recv_data(audio_sock)
                streamout.write(audio_chunk)
        except Exception as e:
            print('Exception for sock_audio:', e)

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
                    if self.camera_frames:
                        recv_cameras = [ci for ci in self.camera_frames if ci is not None]
                    else:
                        recv_cameras = None

                    display_frame = overlay_camera_images(self.screen_frame, recv_cameras)
                    cv2.imshow(f'Client{self.client_id}', np.array(display_frame))
                    cv2.waitKey(100)

    def start_meeting(self):
        # self.sock_screen = socket.create_connection((SERVER_IP, self.screen_port))
        # self.sock_camera = socket.create_connection((SERVER_IP, self.camera_port))
        # self.sock_audio = socket.create_connection((SERVER_IP, self.audio_port))

        share_screen_thread = threading.Thread(target=self.share,
                                               args=('screen', self.stream_socks['screen'], capture_screen, compress_image, 10))
        share_camera_thread = threading.Thread(target=self.share,
                                               args=('camera', self.stream_socks['camera'], capture_camera, compress_image, 10))
        share_audio_thread = threading.Thread(target=self.share, args=('audio', self.stream_socks['audio'], capture_voice, 45))

        recv_screen_thread = threading.Thread(target=self.recv_screen, args=(decompress_image,))
        recv_camera_thread = threading.Thread(target=self.recv_camera, args=(decompress_image,))
        recv_audio_thread = threading.Thread(target=self.recv_audio, args=())

        self.recv_threads = [recv_screen_thread, recv_camera_thread, recv_audio_thread]
        self.send_threads = [share_screen_thread, share_camera_thread, share_audio_thread]
        for t in self.recv_threads:
            t.start()

        for t in self.send_threads:
            t.start()

        display_threads = threading.Thread(target=self.display_frames)
        display_threads.start()
        # self.display_frames()

    def close_threads(self):
        """
        关闭所有线程以及socket
        """
        self.is_working = False
        for t in [*self.send_threads, *self.recv_threads]:
            t.join()

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
    # def display_screen(self, fps=10):
    #     interval = 1 / fps
    #     while self.is_working:
    #         frame = capture_screen()
    #         cv2.imshow('Test screenshot', np.asarray(frame))
    #         cv2.waitKey(100)
    #         # time.sleep(interval)
    #
    # def start_display(self):
    #     dis_thread = threading.Thread(target=self.display_screen)
    #     dis_thread.start()


if __name__ == '__main__':
    client1 = ConferenceClient(SERVER_IP, SERVER_MAIN_PORT)
    # client1.start_display()

    client1.create_conference()
    conference_id = client1.conference_id
    if conference_id is not None:
        client2 = ConferenceClient(SERVER_IP, SERVER_MAIN_PORT)
        client2.join_conference(conference_id)
        client3 = ConferenceClient(SERVER_IP, SERVER_MAIN_PORT)
        client3.join_conference(conference_id)

        client1.share_switch('screen')
        client1.share_switch('camera')
        client2.share_switch('camera')
        client3.share_switch('camera')

        time.sleep(10)
        client2.quit_conference()
        client1.cancel_conference()

