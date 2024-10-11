import pickle
import socket
import struct
import subprocess
import time
import pyaudio
import cv2
import pyautogui
import numpy as np
from PIL import Image
from framework.config import *

FORMAT = pyaudio.paInt16  # 采样位宽16bit
audio = pyaudio.PyAudio()
streamin = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
streamout = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)


# 没有摄像头会报warning
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)


# 这个代码好像没bug
def overlay_camera_images(screen_image, camera_images):
    """
    screen_image: PIL.Image
    camera_images: list[PIL.Image]
    """
    # 确保所有camera images大小一致
    if not all(img.size == camera_images[0].size for img in camera_images):
        raise ValueError("All camera images must have the same size")

    # 获取screen image和camera image的尺寸
    screen_width, screen_height = screen_image.size
    camera_width, camera_height = camera_images[0].size

    # 计算每行能放多少个camera images
    num_cameras_per_row = screen_width // camera_width

    # 如果camera images的数量超过了屏幕宽度，调整camera images的大小
    if len(camera_images) > num_cameras_per_row:
        adjusted_camera_width = screen_width // len(camera_images)
        adjusted_camera_height = (adjusted_camera_width * camera_height) // camera_width
        camera_images = [img.resize((adjusted_camera_width, adjusted_camera_height), Image.LANCZOS) for img in
                         camera_images]
        camera_width, camera_height = adjusted_camera_width, adjusted_camera_height
        num_cameras_per_row = len(camera_images)

    # 创建一个新的image，用于存储结果
    # result_image = screen_image.copy()

    # 按行覆盖camera images
    for i, camera_image in enumerate(camera_images):
        row = i // num_cameras_per_row
        col = i % num_cameras_per_row
        x = col * camera_width
        y = row * camera_height
        screen_image.paste(camera_image, (x, y))

    return screen_image


def capture_screen():
    # 按照当前显示器的分辨率捕获整个屏幕
    img = pyautogui.screenshot()
    return img


def capture_camera():
    # 捕获视频帧
    ret, frame = cap.read()
    if not ret:
        raise Exception('Fail to capture frame from camera')
    return frame


# from PIL import Image
# 测试方法
# for _ in range(600):
#     screen = capture_screen()
#     data = np.asarray(screen)
#     cv2.imshow('image', np.asarray(data))
#     time.sleep(1/60)
# camera = Image.fromarray(np.zeros((500, 500, 3), dtype=np.uint8))
# mix_image = overlay_camera_images(screen, [camera] * 5)
# data = np.asarray(mix_image)
# cv2.imshow('image', np.asarray(mix_image))
# time.sleep(2)


def capture_voice():
    return streamin.read(CHUNK)


def compress_image(img):
    # 转换为numpy数组
    img_np = np.array(img)
    # 转换为BGR（OpenCV默认格式）
    frame = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

    # 使用OpenCV进行JPEG压缩
    result, encoded_image = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    if not result:
        raise ValueError("图像压缩失败")
    return encoded_image.tobytes()


def get_ip_address():
    # windows获取主机名
    hostname = socket.gethostname()

    # 获取与主机名关联的所有 IP 地址
    ip_addresses = socket.gethostbyname_ex(hostname)[2]

    # 通常会返回多个 IP 地址（例如，本地回环地址 127.0.0.1 和实际的网络接口地址）
    # 我们可以过滤掉本地回环地址，只保留实际的网络接口地址
    ip_addresses = [ip for ip in ip_addresses if not ip.startswith("127.") and not ip.startswith("::1")]

    if ip_addresses:
        return ip_addresses  # 返回第一个非本地回环地址
    else:
        return None


data_header_format = 'I'
data_header_size = struct.calcsize(data_header_format)


def gen_bytes(obj):
    data = pickle.dumps(obj)
    data_size = len(data)
    header = struct.pack(data_header_format, data_size)
    return header + data


def send_data(send_socket: socket.socket, obj, waiting=0):
    data = gen_bytes(obj)
    if waiting:
        time.sleep(waiting)
    res = send_socket.sendall(data)
    return res


def recv_data(recv_socket: socket.socket):
    msg = recv_socket.recv(data_header_size, socket.MSG_WAITALL)
    header = struct.unpack(data_header_format, msg)
    data_size = header[0]
    data = bytearray(data_size)
    ptr = memoryview(data)
    while data_size:
        nrecv = recv_socket.recv_into(buffer=ptr, nbytes=min(4096, data_size))
        ptr = ptr[nrecv:]
        data_size -= nrecv
        # recv = recv_socket.recv(min(4096, data_size), MSG_WAITALL)  # deprecated
        # data += recv
        # data_size -= len(recv)
    return pickle.loads(data)


def accept_conn(server_socket: socket, recv_list: list, timeout=None, reply=None):
    while True:
        try:
            conn, addr = server_socket.accept()
            conn.settimeout(timeout)
            recv_list.append((conn, addr[0]))  # only ip
            print(f'Recv connection from {addr}')
            if reply:
                send_data(conn, reply)
        except socket.timeout:
            continue
        except Exception as e:
            print(e)


def is_listening(server_ip, port):
    cmd = f'netstat | find "LISTENING" | find "{server_ip}:{port}"'


def share(send_sock, dest):
    pass
