import threading
import asyncio
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
        if stream_type == 'screen' or 'all':
            self.screen_writer = None
        if stream_type == 'camera' or 'all':
            self.camera_writer = None
        if stream_type == 'audio' or 'all':
            self.audio_writer = None

    def is_cleared(self):
        return all(s is None for s in (self.screen_writer, self.camera_writer, self.audio_writer))

    async def close(self):
        """
        用于服务器主动关闭连接
        """
        if self.screen_writer:
            self.screen_writer.close()
            await self.screen_writer.wait_closed()
        if self.camera_writer:
            self.camera_writer.close()
            await self.camera_writer.wait_closed()
        if self.audio_writer:
            self.audio_writer.close()
            await self.audio_writer.wait_closed()
        self.remove_writer('all')


class ConferenceServer:
    def __init__(self, conference_id, serve_port):
        self.serve_task = None
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

        self.msg_writers = set()
        self.stream_writers = {
            'screen': set(),
            'camera': set(),
            'audio': set()
        }
        self.max_queue = 1000
        self.forwarding_queue = {
            'message': asyncio.Queue(self.max_queue),
            'screen': asyncio.Queue(self.max_queue),
            'camera': asyncio.Queue(self.max_queue),
            'audio': asyncio.Queue(self.max_queue)
        }
        self.client_writers = {}
        self.servers = {}

    def gen_client_id(self):
        self.next_client_id += 1
        yield self.next_client_id

    # def join_client(self, joiner):
    #     ip, port = joiner
    #     client_id = next(self.gen_client_id())
    #     self.client_id_to_addr[client_id] = joiner
    #     reply = f'port {self.serve_port} client_id {client_id}'
    #     return reply

    async def quit_client(self, client_id):
        pass


    async def cancel_conference(self):
        self.running = False
        for client_id, writers in self.client_writers.items():
            await writers.close()
        for msg_writer in self.msg_writers:
            msg_writer.close()
            await msg_writer.wait_close()
        if self.serve_task:
            self.serve_task.cancel()
            try:
                await self.serve_task
            except asyncio.CancelledError:
                print("Main: Task has been cancelled")

    async def forwarding(self, stream_type):
        recv_queue = self.forwarding_queue[stream_type]
        data_writers = self.stream_writers[stream_type]
        while self.running:
            src_writer, data = await recv_queue.get()
            for writer in data_writers:
                if src_writer != writer:
                    writer.write(data)
                    # print(f'Forward {stream_type} data with size {len(data)}')
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
            while self.running:
                # read any data
                data = await reader.read(data_header_size)  # 你可以根据实际情况调整缓冲区大小
                data_size = struct.unpack(data_header_format, data)
                data += await reader.readexactly(*data_size)

                print(f'Recv {stream_type} with size {len(data)}')
                # if not data:
                #     break

                if queue.full():
                    print(f'[Warn]: forwarding queue of {stream_type} data is full')
                await queue.put((writer, data))

                # # 直接转发可能会导致接收端乱序
                # for client in data_writers:
                #     if client != writer:  # except myself
                #         client.write(data)
                #         await client.drain()
        except asyncio.CancelledError or ConnectionResetError:
            print(f"[Msg] Try close {stream_type} connection of {client_id}")
        finally:
            # 关闭连接并从客户端集合中移除
            data_writers.remove(writer)
            if client_id in self.client_writers.keys():
                self.client_writers[client_id].remove_writer(stream_type)

            # todo: exception handling when closing the StreamWriter
            try:
                writer.close()
                await writer.wait_closed()
            except ConnectionResetError:
                print(f'[Msg] {stream_type} connection of {client_id} is closed remotely')

    async def handle_client(self, reader, writer):
        """

        """
        # generate client_id and reply
        client_id = next(self.gen_client_id())
        writer.write(gen_bytes(f'client_id {client_id}'))

        client_address = writer.get_extra_info('peername')
        self.client_id_to_addr[client_id] = client_address
        print(f"New msg connection from {client_address}")
        # self.msg_writers.add(writer)
        self.client_writers[client_id] = StreamWriters()

        while not self.client_writers[client_id].conn_is_ready():
            await asyncio.sleep(0.1)

        if client_id > 0:
            for writer in self.msg_writers:
                writer.write(gen_bytes(f'[Msg]: client{client_id} join the conference'))

        try:
            while self.running:
                data = await reader.readline()
                if not data:
                    break

                msg = data.decode().strip().lower()
                # msg = ''
                # todo: handle_request_in_meetings(msg)
                split_msg = msg.split(maxsplit=1)
                msg_type = split_msg[0]
                if msg_type == 'quit':
                    writer.write(gen_bytes('OK'))
                    raise ConnectionResetError(f'Close connection of client{client_id}')
                if msg_type == 'cancel':
                    if self.manager_id == client_id:
                        writer.write(gen_bytes('OK'))
                        await self.cancel_conference()
                    else:
                        reply = f'[Warn]: Only conference manager can cancel the conference'
                        writer.write(gen_bytes(reply))
                # if msg_type == 'broadcast':
                #     for writer in self.msg_writers:
                #         writer.write()

        # 关闭连接
        except asyncio.CancelledError or ConnectionResetError:
            print(f"Main connection closed with {client_address}")
        finally:
            try:
                # 关闭连接并从客户端集合中移除
                # self.msg_writers.remove(writer)
                if client_id in self.client_id_to_addr.keys():
                    del self.client_id_to_addr[client_id]
                stream_writers = self.client_writers[client_id]
                del self.client_writers[client_id]
                await stream_writers.close()
                # if self.client_writers[client_id].is_cleared():
                writer.close()
                await writer.wait_closed()
            except ConnectionResetError:
                pass
            # notify other clients
            # for writer in self.msg_writers:
            #     writer.write(gen_bytes(f'[Msg]: client{client_id} leave the conference'))

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
        self.serve_task = self.start_all_servers(SERVER_IP)
        asyncio.create_task(self.serve_task)


class MainServer:
    def __init__(self, server_ip, main_port):
        # async server
        self.main_server = None

        self.next_conference_id = 0
        self.max_conference_records = 2

        self.active_clients = None  # self.active_clients[client_addr] = client_socket
        self.managers = {}
        self.conference_clients = {}  # self.conference_clients[conference_id] = list[client_addr]
        self.conference_conns = None
        self.conference_managers = {}  # self.conference_managers[conference_id] = ConferenceManager

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
                reply = 'FAIL: no more conference'
            else:  # 获得conference_id, server记录，分配服务的端口号
                self.conference_clients[conference_id] = [creator]
                port = self.gen_service_port(conference_id)  # 一个port
                # 创建者的client_id是0
                reply = f"conf_id {conference_id} port {port}"

                confMan = ConferenceServer(conference_id, port)
                confMan.start()
                self.conference_managers[conference_id] = confMan

        else:
            # 权限不通过，回复创建申请者创建失败
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
