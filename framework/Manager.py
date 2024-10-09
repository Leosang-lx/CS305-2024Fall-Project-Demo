import asyncio
import threading
import socket


class ConferenceManager:
    def __init__(self, conference_id):
        self.conference_id = conference_id
        self.msg_sockets = {}
        self.video_sockets = {}
        self.audio_sockets = {}
        self.loop = None

    async def handle_message(self, reader, writer):
        client_id = len(self.msg_sockets)
        self.msg_sockets[client_id] = (reader, writer)

        while True:
            data = await reader.readline()
            if not data:
                break
            message = data.decode().strip()
            print(f"Conference {self.conference_id}: Received message from client {client_id}: {message}")
            # 广播消息给所有客户端
            for other_client_id, (other_reader, other_writer) in self.msg_sockets.items():
                if other_client_id != client_id:
                    other_writer.write(data)
                    await other_writer.drain()

        del self.msg_sockets[client_id]
        writer.close()
        await writer.wait_closed()

    async def handle_video_stream(self, reader, writer):
        client_id = len(self.video_sockets)
        self.video_sockets[client_id] = (reader, writer)

        while True:
            data = await reader.read(1024)
            if not data:
                break
            print(f"Conference {self.conference_id}: Received video data from client {client_id}: {len(data)} bytes")
            # 将视频数据转发给所有其他客户端
            for other_client_id, (other_reader, other_writer) in self.video_sockets.items():
                if other_client_id != client_id:
                    other_writer.write(data)
                    await other_writer.drain()

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


# 主函数
def main():
    conferences = [ConferenceManager(i) for i in range(5)]  # 假设有5个会议

    threads = []
    for conference in conferences:
        thread = threading.Thread(target=conference.run)
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()


if __name__ == '__main__':
    main()
