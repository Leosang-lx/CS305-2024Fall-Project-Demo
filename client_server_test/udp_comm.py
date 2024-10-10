import socket
import struct  # 用于打包/解包二进制数据


# def send_large_data(ip, port, bytes, image_id, buffer_size=1472):
#     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#
#     num_packets = (len(bytes) - 1) // buffer_size + 1
#     packet_format = f"!I{buffer_size}s"  # 图片ID(4字节整数) + 数据块
#
#     for i in range(num_packets):
#         start = i * buffer_size
#         end = min(start + buffer_size, len(bytes))
#         payload = bytes[start:end]
#
#         # 创建包含ID和序列号的数据包
#         packet = struct.pack(packet_format, image_id, i, payload)
#
#         # 发送数据包
#         sock.sendto(packet, (ip, port))
#
#     sock.close()

def send_large_data(dest, data, image_id, client_id, buffer_size=1472):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    data_size = len(data)
    packet_format = f"!HIII{buffer_size}s"  # 客户端ID(4字节整数) + 图片ID(4字节整数) + 数据块
    header_len = struct.calcsize(packet_format)
    left_buffer = buffer_size - header_len
    num_packets = (len(data) + buffer_size - 1) // left_buffer

    for i in range(num_packets):
        start = i * left_buffer
        end = min(start + left_buffer, len(data))
        payload = data[start:end]

        # 创建包含客户端ID、图片ID和序列号的数据包
        packet = struct.pack(packet_format, client_id, image_id, data_size, i, payload)

        # 发送数据包
        sock.sendto(packet, dest)

    sock.close()


# # 假设image_data是你的图像数据，已经被转换为字节串
# client_id = 1  # 假设这是第一个客户端的ID
# image_id = 1  # 假设这是第一张图片的ID
# image_data = b'...'  # 你的图像数据
# send_large_data('127.0.0.1', 12345, image_data, image_id, client_id)

# import socket
# import struct


# def receive_large_data(listen_addr, buffer_size=1472):
#     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     sock.bind(listen_addr)
#
#     expected_packet_count = None  # 预期的数据包总数
#     last_received_image_id = None  # 上一次接收到的图片ID
#
#     # data = bytearray(data_size)
#
#     while True:
#         packet, _ = sock.recvfrom(buffer_size + 8)  # 包含ID和序列号
#         if not packet: break
#
#         # 解包以获取ID、序列号和实际数据
#         # image_id, seq, payload = struct.unpack(f"!HIII{buffer_size}s", packet)
#         client_id, image_id, data_size, i, payload = struct.unpack(f"!HIII{buffer_size}s", packet)
#         if last_received_image_id is None or last_received_image_id != image_id:
#             # 新的图片开始接收
#             last_received_image_id = image_id
#             ptr = memoryview(data)
#
#         # 记录当前数据包
#         packets[seq] = payload
#
#         if expected_packet_count is None:
#             # 根据第一个数据包估算总数量
#             expected_packet_count = (len(payload) + buffer_size - 1) // buffer_size
#
#         # 检查是否所有数据包都已接收
#         if len(packets) == expected_packet_count:
#             break
#
#     # 按照序列号重组数据
#     received_data = b''.join(packets[i] for i in sorted(packets.keys()))
#
#     sock.close()
#     return received_data, last_received_image_id


# 接收数据
# received_image_data, image_id = receive_large_data(12345)
# print(f"Received image with ID {image_id}")