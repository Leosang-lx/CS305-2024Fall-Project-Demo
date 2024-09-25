import socket
import cv2
import numpy as np

# 设置服务器地址和端口
SERVER_IP = "127.0.0.1"
SERVER_PORT = 5005

# 创建一个TCP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((SERVER_IP, SERVER_PORT))
server_socket.listen(1)


def decompress_image(data):
    # 解压JPEG图像数据
    nparr = np.frombuffer(data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("解压缩图像失败")
    return frame


def display_screen(conn):
    while True:
        # 接收数据长度
        data_length = int.from_bytes(conn.recv(4), byteorder='big')
        # 接收数据
        # todo: cannot ensure that recv() can receive data_length bytes each time
        data = conn.recv(data_length)
        frame = decompress_image(data)
        # 显示图像
        if frame.shape[0] > 0 and frame.shape[1] > 0:
            cv2.imshow('Screen Share', frame)
        else:
            raise ValueError("解压缩后的图像尺寸无效")

        # 按'q'键退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


if __name__ == "__main__":
    conn, addr = server_socket.accept()
    print(f"Connected by {addr}")
    display_screen(conn)
    conn.close()
    cv2.destroyAllWindows()