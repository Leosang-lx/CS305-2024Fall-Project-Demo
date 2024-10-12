import threading
import asyncio
import time
from config import *
from util import *


class StreamWriters:
    def __init__(self):
        # self.main_writer = None
        self.screen_writer = None
        self.camera_writer = None
        self.audio_writer = None

    def add_writer(self, writer, stream_type):
        if stream_type == 'screen':
            self.screen_writer = writer
        elif stream_type == 'camera':
            self.camera_writer = writer
        elif stream_type == 'audio':
            self.audio_writer = writer

    def conn_is_ready(self):
        return None not in (self.screen_writer, self.camera_writer, self.audio_writer)

    def remove_writer(self, stream_type):
        if stream_type == 'screen':
            self.screen_writer = None
        elif stream_type == 'camera':
            self.camera_writer = None
        elif stream_type == 'audio':
            self.audio_writer = None

    def is_cleared(self):
        return all(s is None for s in (self.screen_writer, self.camera_writer, self.audio_writer))

    # async def close(self):
    #     self.screen_writer.close()
    #     self.camera_writer.close()
    #     self.audio_writer.close()
    #     await self.screen_writer.wait_close()
    #     await self.camera_writer.wait_close()
    #     await self.audio_writer.wait_close()


class ConferenceServer:
    def __init__(self, conference_id, serve_port, creator):
        self.running = False

        self.conference_id = conference_id
        self.serve_port = serve_port
        self.client_id_to_addr = {}

        # self.conf_conns = []
        # self.conference_sock = socket.create_server((SERVER_IP, self.serve_port))
        # self.conference_sock.settimeout(TIMEOUT_SERVER)
        # self.recv_conn_thread = threading.Thread(target=accept_conn, args=[self.conf_conns])
        self.next_client_id = 0

        self.stream_types = ['screen', 'camera', 'audio']
        self.serve_ports = {
            'screen': serve_port + 1,
            'camera': serve_port + 2,
            'audio': serve_port + 3
        }
        # self.clients = {
        #     'screen': set(),
        #     'camera': set(),
        #     'audio': set()
        # }
        self.msg_writers = set()
        self.stream_writers = {
            'screen': set(),
            'camera': set(),
            'audio': set()
        }
        self.max_queue = 1000
        self.forwarding_queue = {
            'screen': asyncio.Queue(self.max_queue),
            'camera': asyncio.Queue(self.max_queue),
            'audio': asyncio.Queue(self.max_queue)
        }
        self.client_writers = {}
        self.servers = {}

        # self.forwarding_server = ConferenceServer(self.serve_port)

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

    # def forwarding_thread(self, recv_sock: socket.socket, send_sock: socket.socket):
    #     while self.running and len(self.msg_sockets) > 1:
    #         if len(self.msg_sockets) > 1:
    #             data, addr = recv_sock.recvfrom(1500)
    #             src = addr[0]
    #             for dest in self.client_id_to_addr.values():
    #                 if src != dest:
    #                     send_sock.sendto(data, (src, self.serve_port + 4))
    #         else:
    #             time.sleep(0.1)

    def gen_client_id(self):
        self.next_client_id += 1
        yield self.next_client_id

    # def join_client(self, joiner):
    #     ip, port = joiner
    #     client_id = next(self.gen_client_id())
    #     self.client_id_to_addr[client_id] = joiner
    #     reply = f'port {self.serve_port} client_id {client_id}'
    #     return reply

    def quit_client(self, ):
        pass

    def cancel_conference(self, ):
        pass

    async def forwarding(self, stream_type):
        recv_queue = self.forwarding_queue[stream_type]
        data_writers = self.stream_writers[stream_type]
        while self.running:
            src_writer, data = await recv_queue.get()
            for writer in data_writers:
                if src_writer != writer:
                    writer.write(data)
                    print(f'Forward {stream_type} data with size {len(data)}')
                    # await writer.drain()

    async def handle_stream(self, reader, writer, stream_type):
        """
        无脑转发收到的数据？：向同一连接同时写入不同数据可能会有问题
        """
        # save writer according to client_id
        first_data = await reader.readline()
        client_id = int(first_data.decode())
        data_writers = self.stream_writers[stream_type]
        data_writers.add(writer)

        client_address = writer.get_extra_info('peername')
        print(f"New {stream_type} connection from {client_address}")

        # if client_id not in self.client_writers.keys():
        #     self.client_writers[client_id] = StreamWriters()
        self.client_writers[client_id].add_writer(writer, stream_type)

        assert isinstance(reader, asyncio.streams.StreamReader)
        try:
            queue = self.forwarding_queue[stream_type]
            assert isinstance(queue, asyncio.Queue)
            while True:
                # read any data
                data = await reader.read(data_header_size)  # 你可以根据实际情况调整缓冲区大小
                data_size = struct.unpack(data_header_format, data)
                data += await reader.readexactly(*data_size)

                print(f'Recv {stream_type} with size {len(data)}')
                # if not data:
                #     break

                await queue.put((writer, data))
                if queue.full():
                    print(f'[Warn]: forwarding queue of {stream_type} data is full')
                # # forwarding
                # for client in data_writers:
                #     if client != writer:  # except myself
                #         client.write(data)
                #         await client.drain()
        except asyncio.CancelledError:
            pass
        finally:
            # 关闭连接并从客户端集合中移除
            print(f"{stream_type} connection closed with {client_id}")
            data_writers.remove(writer)
            self.client_writers[client_id].remove_writer(stream_type)
            writer.close()
            # todo: exception handling
            await writer.wait_closed()

    async def handle_client(self, reader, writer):
        """

        """
        # data = await reader.readline()
        # client_id = int(data.decode())

        # generate client_id and reply
        client_id = next(self.gen_client_id())
        writer.write(gen_bytes(f'client_id {client_id}'))

        client_address = writer.get_extra_info('peername')

        self.client_id_to_addr[client_id] = client_address
        print(f"New msg connection from {client_address}")
        self.msg_writers.add(writer)
        self.client_writers[client_id] = StreamWriters()

        while not self.client_writers[client_id].conn_is_ready():
            await asyncio.sleep(0.1)

        if client_id > 0:
            for writer in self.msg_writers:
                writer.write(gen_bytes(f'[Msg]: client{client_id} join the conference'))

        try:
            while True:
                data = await reader.readline()
                if not data:
                    break

                msg = data.decode()
                pass
                # todo: handle_request_in_meetings(msg)

        except asyncio.CancelledError:
            pass
        finally:
            # 关闭连接并从客户端集合中移除
            print(f"Main connection closed with {client_address}")
            self.msg_writers.remove(writer)
            writer.close()
            await writer.wait_closed()
            # todo: clear user records
            for writer in self.msg_writers:
                writer.write(gen_bytes(f'[Msg]: client{client_id} leave the conference'))

    async def start_receiving(self, host, port, data_type):
        server = await asyncio.start_server(
            lambda r, w: self.handle_stream(r, w, data_type), host, port
        )
        addr = server.sockets[0].getsockname()
        print(f'Serving {data_type} on {addr}')

        self.servers[data_type] = server

        async with server:
            await server.serve_forever()

    async def start_handling(self, host):
        server = await asyncio.start_server(self.handle_client, host, self.serve_port)
        addr = server.sockets[0].getsockname()
        print(f'Serving message on {addr}')

        self.servers['message'] = server
        async with server:
            await server.serve_forever()

    async def start_all_servers(self, host):
        receiving_tasks = [
            self.start_receiving(host, self.serve_ports[stream_type], stream_type) for stream_type in self.stream_types
        ]
        handling_task = self.start_handling(host)
        forwarding_tasks = [
            self.forwarding(stream_type) for stream_type in self.stream_types
        ]

        await asyncio.gather(*receiving_tasks, handling_task, *forwarding_tasks)

    def start(self):
        self.running = True
        # self.recv_conn_thread.start()
        # loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(loop)
        # loop.run_until_complete(self.forwarding_server.start_all_servers(SERVER_IP))
        # asyncio.run(self.start_all_servers(SERVER_IP))  # 试试这个
        asyncio.create_task(self.start_all_servers(SERVER_IP))


class MainServer:
    def __init__(self, server_ip, main_port):
        # self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.server_socket.bind((server_ip, main_port))
        # self.server_socket.listen(1)

        # async server
        self.main_server = None

        self.next_conference_id = 0
        self.max_conference_records = 2

        self.active_clients = None  # self.active_clients[client_addr] = client_socket
        self.managers = {}
        self.conference_clients = {}  # self.conference_clients[conference_id] = list[client_addr]
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
        self.next_conference_id += 1
        if self.next_conference_id < self.max_conference_records:
            yield self.next_conference_id
        else:
            yield None

    def gen_service_port(self, conference_id):
        conf_serve_port = SERVER_MAIN_PORT + 1000 * conference_id
        # for p in ports:
        #     assert
        # todo: 确保这些端口没有被监听，否则要换一个（直接+1）
        # msg_port, screen_port, camera_port, audio_port
        return conf_serve_port

    def handle_creat_conference(self, writer):  # todo: creator这里具体是什么形式
        """
        会议外请求：生成并记录会议号，返回给创建者，并建立数据传输连接
        """
        creator = writer.get_extra_info('peername')
        if self.check_creator(creator):
            # 创建会议
            conference_id = next(self.gen_conference_id())
            if conference_id is None:
                # self.server_socket.sendto('FAIL: no more conference'.encode(), creator)
                reply = 'FAIL: no more conference'
            else:  # 获得conference_id, server记录，分配服务的端口号
                self.conference_clients[conference_id] = [creator]
                port = self.gen_service_port(conference_id)  # 一个port
                # 创建者的client_id是0
                reply = f"conf_id {conference_id} port {port}"

                confMan = ConferenceServer(conference_id, port, creator)
                confMan.start()
                self.conference_managers[conference_id] = confMan

        else:
            # 权限不通过，回复创建申请者创建失败
            # self.server_socket.sendto('FAIL: not a conference manager'.encode(), creator)
            reply = 'FAIL: not a conference manager'
            # pass
        writer.write(gen_bytes(reply))

    def handle_join_conference(self, conference_id, writer):
        """
        会议外请求：
        """
        if conference_id in self.conference_clients.keys():
            # todo: 让conference manager来回复port和client_id
            conference_manager = self.conference_managers[conference_id]
            # todo: joiner包括ip和port，port需要确定（要不这里还是用tcp）
            reply = f'port {conference_manager.serve_port}'
            # self.server_socket.sendto(reply.encode(), joiner)
        else:
            # self.server_socket.sendto('Conference ID Not Found'.encode(), joiner)
            reply = 'Conference ID Not Found'
        writer.write(gen_bytes(reply))

    def handle_unknown(self, writer):
        writer.write(gen_bytes('Unknown command'))

    def handle_exit_conference(self):
        """
        会议内请求
        """
        pass

    def handle_cancel_conference(self):
        """
        会议内请求
        """
        pass

    async def request_handler(self, reader, writer):
        client_addr = writer.get_extra_info('peername')
        print(f"New connection from {client_addr}")

        try:
            while True:
                data = await reader.readline()
                if not data:
                    break
                message = data.decode().strip().lower()

                if message.startswith("create"):
                    self.handle_creat_conference(writer)
                elif message.startswith("join "):
                    assert isinstance(message, str)
                    _, conference_id = message.split(' ', 1)
                    self.handle_join_conference(int(conference_id), writer)
                else:
                    self.handle_unknown(writer)

                # writer.write((reply + '\n').encode())
                await writer.drain()

        except asyncio.IncompleteReadError:
            # conn interrupt
            print(f"Connection with {client_addr} was closed unexpectedly.")
        except Exception as e:
            print(f"An error occurred with {client_addr}: {e}")
        finally:
            # close conn
            print(f"Closing the connection to {client_addr}")
            writer.close()
            await writer.wait_closed()

    async def start_server(self):
        self.main_server = await asyncio.start_server(
            self.request_handler, SERVER_IP, SERVER_MAIN_PORT)
        addr = self.main_server.sockets[0].getsockname()
        print(f'Serving on {addr}')
        await self.main_server.serve_forever()

    def run_in_thread(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.start_server())
        finally:
            loop.close()

    def start(self):
        main_thread = threading.Thread(target=self.run_in_thread)
        main_thread.start()


if __name__ == '__main__':
    server = MainServer(SERVER_IP, SERVER_MAIN_PORT)
    server.start()
