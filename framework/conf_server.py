import threading
import asyncio
from config import *
from util import *


class ConferenceManager:
    def __init__(self, conference_id, creator, service_posts):
        self.conference_id = conference_id
        self.client_manager = creator
        self.msg_sockets = {}
        self.video_sockets = {}
        self.audio_sockets = {}
        self.loop = None

    async def handle_message(self, reader, writer):
        client_id = len(self.msg_sockets)
        self.msg_sockets[client_id] = writer

        while True:
            data = await reader.readline()
            if not data:
                break
            message = data.decode().strip()
            print(f"Conference {self.conference_id}: Received message from client {client_id}: {message}")
            # 广播消息给所有客户端
            for client_writer in self.msg_sockets.values():
                if client_writer != writer:
                    client_writer.write(data)
                    await client_writer.drain()

        del self.msg_sockets[client_id]
        writer.close()
        await writer.wait_closed()

    async def handle_video_stream(self, reader, writer):
        client_id = len(self.video_sockets)
        self.video_sockets[client_id] = writer

        while True:
            data = await reader.read(1024)
            if not data:
                break
            print(f"Conference {self.conference_id}: Received video data from client {client_id}: {len(data)} bytes")
            # 将视频数据转发给所有其他客户端
            for client_writer in self.video_sockets.values():
                if client_writer != writer:
                    client_writer.write(data)
                    await client_writer.drain()

        del self.video_sockets[client_id]
        writer.close()
        await writer.wait_closed()

    async def handle_audio_stream(self, reader, writer):
        client_id = len(self.audio_sockets)
        self.audio_sockets[client_id] = (reader, writer)

        while True:
            data = await reader.read(1024)
            if not data:
                break
            print(f"Conference {self.conference_id}: Received audio data from client {client_id}: {len(data)} bytes")
            # 将音频数据转发给所有其他客户端
            for other_client_id, (other_reader, other_writer) in self.audio_sockets.items():
                if other_client_id != client_id:
                    other_writer.write(data)
                    await other_writer.drain()

        del self.audio_sockets[client_id]
        writer.close()
        await writer.wait_closed()

    async def start_server(self):
        self.loop = asyncio.get_event_loop()

        # 创建消息传输服务器
        message_server = await asyncio.start_server(self.handle_message, '0.0.0.0', 8888 + self.conference_id * 1000)
        addr = message_server.sockets[0].getsockname()
        print(f'Conference {self.conference_id}: Message server serving on {addr}')

        # 创建视频流传输服务器
        video_server = await asyncio.start_server(self.handle_video_stream, '0.0.0.0', 8889 + self.conference_id * 1000)
        addr = video_server.sockets[0].getsockname()
        print(f'Conference {self.conference_id}: Video stream server serving on {addr}')

        # 创建音频流传输服务器
        audio_server = await asyncio.start_server(self.handle_audio_stream, '0.0.0.0', 8890 + self.conference_id * 1000)
        addr = audio_server.sockets[0].getsockname()
        print(f'Conference {self.conference_id}: Audio stream server serving on {addr}')

        try:
            await asyncio.gather(
                message_server.serve_forever(),
                video_server.serve_forever(),
                audio_server.serve_forever()
            )
        finally:
            message_server.close()
            video_server.close()
            audio_server.close()
            await asyncio.gather(
                message_server.wait_closed(),
                video_server.wait_closed(),
                audio_server.wait_closed()
            )

    def run(self):
        asyncio.run(self.start_server())

# def main():
#     conferences = [ConferenceManager(i) for i in range(5)]  # 假设有5个会议
#
#     threads = []
#     for conference in conferences:
#         thread = threading.Thread(target=conference.run)
#         thread.start()
#         threads.append(thread)
#
#     for thread in threads:
#         thread.join()
#
# if __name__ == '__main__':
#     main()


class ConferenceMainServer:
    def __init__(self, server_ip, main_port):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((server_ip, main_port))
        # self.server_socket.listen(1)

        self.max_conference_records = 10

        self.active_clients = None  # self.active_clients[client_addr] = client_socket
        self.managers = {}
        self.conference_clients = None  # self.conference_clients[conference_id] = list[client_addr]
        self.conference_conns = None
        self.conference_managers = {}  # self.conference_managers[conference_id] = ConferenceManager

    def maintain_active_clients(self):
        """
        维护self.active_clients：新来的加入到里面，主动退出以及意外断开的踢出来
        """
        pass

    def check_creator(self, creator):
        # todo: 权限的二次确认
        return True

    def gen_conference_id(self):
        """
        conference_id starts from 1
        """
        conference_id = 0
        while True:
            conference_id += 1
            if conference_id < self.max_conference_records:
                yield conference_id
            else:
                yield None

    def gen_service_ports(self, conference_id):
        service_port = SERVER_MAIN_PORT + 1000 * conference_id
        # for p in ports:
        #     assert
        # todo: 确保这些端口没有被监听，否则要换一个（直接+1）
        return service_port, service_port + 1, service_port + 2

    def handle_creat_conference(self, creator):  # todo: creator这里具体是什么形式
        """
        生成并记录会议号，返回给创建者，并建立数据传输连接
        """
        if self.check_creator(creator):
            # 创建会议
            conference_id = next(self.gen_conference_id())
            if conference_id is None:
                self.server_socket.sendto('FAIL: no more conference'.encode(), creator)
            else:  # 获得conference_id, server记录，分配服务的端口号
                self.conference_clients[conference_id] = [creator]
                ports = self.gen_service_ports(conference_id)
                # 启动一个conference manager用于服务会议的数据转发
                confMan = ConferenceManager()

        else:
            # 权限不通过，回复创建申请者创建失败
            self.server_socket.sendto('FAIL: not a conference manager'.encode(), creator)
            # pass

    def handle_join_conference(self, client_addr, conference_id):
        pass

    def handle_exit_conference(self):
        pass

    def handle_cancel_conference(self):
        pass

    def request_handler(self):
        while True:
            data, addr = self.server_socket.recvfrom(DGRAM_SIZE)
            request = data.decode()



    def run(self):
        pass
