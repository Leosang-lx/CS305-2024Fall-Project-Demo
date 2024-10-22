from util import *
import threading
import time


class ConferenceClient:
    def __init__(self,):
        """
        建立与服务器的主要连接：仅用于与服务器的通信（保持连接）
        """
        self.is_working = True
        self.server_addr = None  # server addr
        self.on_meeting = False  # status
        self.conns = None  # you may need to maintain multiple conns for a single conference
        self.support_data_types = []  # for some types of data

        self.conference_info = None  # you may need to save and update some conference_info regularly

        self.recv_data = None  # you may need to save received streamd data from other clients in conference


    def init_conf_conn(self,):
        """
        init conns when create or join a conference with necessary conference_info
        """
        pass

    def create_conference(self):
        """
        create a conference: send create-conference request to server and obtain necessary data to
        """
        pass

    def join_conference(self, conference_id):
        """
        join a conference: send join-conference request with given conference_id, and obtain necessary data to
        """
        pass

    def quit_conference(self):
        """
        quit your on-going conference
        """
        pass

    def cancel_conference(self):
        """
        cancel your on-going conference (when you are the conference manager): ask server to close all clients
        """
        pass

    def keep_share(self, data_type, send_conn, capture_function, compress=None, fps_or_frequency=30):
        '''
        keep sharing (capture and send) certain type of data from server or clients (P2P)
        you can create different functions for sharing various types of data
        '''
        pass

    def share_switch(self, data_type):
        '''
        switch for sharing certain type of data (screen, camera, audio, etc.)
        '''
        pass

    def keep_recv(self, recv_conn, decompress=None):
        '''
        keep receiving certain type of data
        '''

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
                print('Recv chunk', len(audio_chunk))
                streamout.write(audio_chunk)
        except Exception as e:
            print('Exception for sock_audio:', e)

    def recv_msg(self):
        try:
            while self.is_working:
                msg = recv_data(self.conference_sock)
                print(msg)
                msg = msg.strip().lower()
                if 'client' in msg and msg.endswith('join the conference'):
                    new_client_id = int(msg.split()[2])
                    self.clients_in_conference.append(new_client_id)
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
        share_audio_thread = threading.Thread(target=self.share, args=('audio', self.stream_socks['audio'], capture_voice, None, 45))

        recv_screen_thread = threading.Thread(target=self.recv_screen, args=(decompress_image,))
        recv_camera_thread = threading.Thread(target=self.recv_camera, args=(decompress_image,))
        recv_audio_thread = threading.Thread(target=self.recv_audio, args=())
        recv_msg_thread = threading.Thread(target=self.recv_msg, args=())

        self.recv_threads = [recv_screen_thread, recv_camera_thread, recv_audio_thread, recv_msg_thread]
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

    def close_conference(self):
        self.close_conf_conns()
        self.close_threads()
        self.clients_in_conference = []

    def start(self):
        """
        根据命令行输入执行指定功能
        """
        while True:
            if not self.on_meeting:
                status = 'Free'
            else:
                status = f'OnMeeting-{self.conference_id}'

            recognized = True
            cmd_input = input(f'({status}) Please enter a operation (enter "?" to help): ').strip().lower()
            fields = cmd_input.split(maxsplit=1)
            if len(fields) == 1:
                if cmd_input in ('?', '？'):
                    print(HELP)
                elif cmd_input == 'create':
                    self.create_conference()
                elif cmd_input == 'quit':
                    self.quit_conference()
                elif cmd_input == 'cancel':
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
                    data_type = fields[1]
                    if data_type in self.share_data.keys():
                        self.share_data[data_type] = not self.share_data[data_type]
                else:
                    recognized = False
            else:
                recognized = False

            if not recognized:
                print(f'[Warn]: Unrecognized cmd_input {cmd_input}')


if __name__ == '__main__':
    client1 = ConferenceClient(SERVER_IP, SERVER_MAIN_PORT)
    client1.start()

