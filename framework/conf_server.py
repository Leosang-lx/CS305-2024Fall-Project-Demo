import threading
import asyncio
import time

from config import *
from util import *


class DataForwardingServer:
    def __init__(self, conf_serve_port):
        self.stream_types = ['screen', 'camera', 'audio']
        self.serve_ports = {
            'screen': conf_serve_port + 1,
            'camera': conf_serve_port + 2,
            'audio': conf_serve_port + 3
        }
        self.clients = {
            'screen': set(),
            'camera': set(),
            'audio': set()
        }
        self.servers = {}

    async def handle_client(self, reader, writer, data_type):
        self.clients[data_type].add(writer)
        client_address = writer.get_extra_info('peername')
        print(f"New {data_type} connection from {client_address}")

        try:
            while True:
                # 读取客户端发送的数据
                data = await reader.read(1024)  # 你可以根据实际情况调整缓冲区大小
                if not data:
                    break

                # 转发数据给其他所有客户端
                for client in self.clients[data_type]:
                    if client != writer:  # 不转发给自己
                        client.write(data)
                        await client.drain()
        except asyncio.CancelledError:
            pass
        finally:
            # 关闭连接并从客户端集合中移除
            print(f"{data_type} connection closed with {client_address}")
            self.clients[data_type].remove(writer)
            writer.close()
            await writer.wait_closed()

    async def start_server(self, host, port, data_type):
        server = await asyncio.start_server(
            lambda r, w: self.handle_client(r, w, data_type), host, port
        )
        addr = server.sockets[0].getsockname()
        print(f'Serving {data_type} on {addr}')

        self.servers[data_type] = server

        async with server:
            await server.serve_forever()

    async def start_all_servers(self, host):
        tasks = [
            self.start_server(host, self.serve_ports[stream_type], stream_type) for stream_type in self.stream_types
        ]
        await asyncio.gather(*tasks)


class ConferenceManager:
    def __init__(self, conference_id, serve_port, creator):
        self.running = False

        self.conference_id = conference_id
        self.serve_port = serve_port
        self.client_id_to_addr = {0: creator}

        self.conf_conns = []
        self.conference_sock = socket.create_server((SERVER_IP, self.serve_port))

        self.conference_sock.settimeout(TIMEOUT_SERVER)
        self.recv_conn_thread = threading.Thread(target=accept_conn, args=[self.conf_conns])

        self.forwarding_server = DataForwardingServer(self.serve_port)

        # self.client_screen = set()
        # self.client_camera = set()
        # self.client_audio = set()

        # for i, sock in enumerate(self.listen_sockets):
        #     sock.bind((SERVER_IP, self.serve_port + i + 1))
        #
        # self.forwarding_sockets = [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)] * 3
        #
        # self.forwarding_threads = [threading.Thread(target=self.forwarding_thread, args=thread_pair) for thread_pair in
        #                            zip(self.listen_sockets, self.forwarding_sockets)]
        # for forwarding_thread in self.forwarding_threads:
        #     forwarding_thread.start()

    # 启动主事件循环
    # asyncio.run(main())

    def gen_client_id(self):
        client_id = 0
        while True:
            client_id += 1
            yield client_id

    def forwarding_thread(self, recv_sock: socket.socket, send_sock: socket.socket):
        while self.running and len(self.msg_sockets) > 1:
            if len(self.msg_sockets) > 1:
                data, addr = recv_sock.recvfrom(1500)
                src = addr[0]
                for dest in self.client_id_to_addr.values():
                    if src != dest:
                        send_sock.sendto(data, (src, self.serve_port + 4))
            else:
                time.sleep(0.1)

    def join_client(self, joiner):
        ip, port = joiner
        client_id = next(self.gen_client_id())
        self.client_id_to_addr[client_id] = joiner
        reply = f'port {self.serve_port} client_id {client_id}'
        return reply

    def start(self):
        self.running = True
        asyncio.run(self.forwarding_server.start_all_servers(SERVER_IP))


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
        # msg_port, screen_port, camera_port, audio_port
        return service_port, service_port + 1, service_port + 2, service_port + 3

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
                ports = self.gen_service_ports(conference_id)  # 要不就改成一个port
                # 创建者的client_id是0
                reply = f"conf_id {conference_id} port {ports} client_id {0}"
                # todo: 启动一个conference manager用于服务会议的数据转发
                confMan = ConferenceManager(conference_id, ports, creator)
                confMan.start()
                self.conference_managers[conference_id] = confMan
                self.server_socket.sendto(reply, creator)

        else:
            # 权限不通过，回复创建申请者创建失败
            self.server_socket.sendto('FAIL: not a conference manager'.encode(), creator)
            # pass

    def handle_join_conference(self, joiner, conference_id):
        if conference_id in self.conference_clients.keys():
            # todo: 让conference manager来回复port和client_id
            conference_manager = self.conference_managers[conference_id]
            # todo: joiner包括ip和port，port需要确定（要不这里还是用tcp）
            reply = f'port {conference_manager.serve_port}'
            self.server_socket.sendto(reply.encode(), joiner)
        else:
            self.server_socket.sendto('Conference ID Not Found'.encode(), joiner)

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
