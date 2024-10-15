import pickle
import socket
import struct
import subprocess
import time
from io import BytesIO

import pyaudio
import cv2
import pyautogui
import numpy as np
from PIL import Image, ImageGrab
from framework.config import *

FORMAT = pyaudio.paInt16  # 采样位宽16bit
audio = pyaudio.PyAudio()
streamin = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
streamout = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)

# 没有摄像头会报warning
cap = cv2.VideoCapture(0)
if cap.isOpened():
    can_capture_camera = True
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)
else:
    can_capture_camera = False

my_screen_size = pyautogui.size()


def resize_image_to_fit_screen(image, my_screen_size):
    screen_width, screen_height = my_screen_size

    original_width, original_height = image.size

    aspect_ratio = original_width / original_height

    if screen_width / screen_height > aspect_ratio:
        # 如果屏幕的宽高比大于图像的宽高比，则按高度缩放
        new_height = screen_height
        new_width = int(new_height * aspect_ratio)
    else:
        # 否则，按宽度缩放
        new_width = screen_width
        new_height = int(new_width / aspect_ratio)

    # 调整图像大小
    resized_image = image.resize((new_width, new_height), Image.LANCZOS)

    return resized_image


# 好像没bug了
def overlay_camera_images(screen_image, camera_images):
    """
    screen_image: PIL.Image
    camera_images: list[PIL.Image]
    """
    if screen_image is None and camera_images is None:
        print('[Warn]: cannot display when screen and camera are both None')
        return None
    if screen_image is not None:
        screen_image = resize_image_to_fit_screen(screen_image, my_screen_size)

    if camera_images is not None:
        # 确保所有camera images大小一致
        if not all(img.size == camera_images[0].size for img in camera_images):
            raise ValueError("All camera images must have the same size")

        # 获取screen image和camera image的尺寸
        screen_width, screen_height = my_screen_size if screen_image is None else screen_image.size
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

        # 如果没有屏幕数据，则创建一个容器
        if screen_image is None:
            display_image = Image.fromarray(np.zeros((camera_width, my_screen_size[1], 3), dtype=np.uint8))
        else:
            display_image = screen_image
        # 按行覆盖camera images
        for i, camera_image in enumerate(camera_images):
            row = i // num_cameras_per_row
            col = i % num_cameras_per_row
            x = col * camera_width
            y = row * camera_height
            display_image.paste(camera_image, (x, y))

        return display_image
    else:
        return screen_image


def capture_screen():
    # 按照当前显示器的分辨率捕获整个屏幕
    # img = pyautogui.screenshot()
    img = ImageGrab.grab()
    return img


def capture_camera():
    # 捕获视频帧
    ret, frame = cap.read()
    if not ret:
        raise Exception('Fail to capture frame from camera')
    return Image.fromarray(frame)


def capture_voice():
    return streamin.read(CHUNK)


def compress_image(image, format='JPEG', quality=85):
    """
    压缩图像并输出为字节。

    :param image: PIL.Image, 输入图像
    :param format: str, 输出格式 ('JPEG', 'PNG', 'WEBP' 等)
    :param quality: int, 压缩质量 (0-100), 默认为 85
    :return: bytes, 压缩后的图像字节
    """
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format=format, quality=quality)
    img_byte_arr = img_byte_arr.getvalue()

    return img_byte_arr


def decompress_image(image_bytes):
    """
    将压缩后的图像字节解压缩并转换为 PIL.Image对象。
    :param image_bytes: bytes, 压缩后的图像字节
    :return: PIL.Image, 解压缩后的图像
    """
    img_byte_arr = BytesIO(image_bytes)
    image = Image.open(img_byte_arr)

    return image


# def compress_image(img):
#     # 转换为numpy数组
#     img_np = np.array(img)
#     # 转换为BGR（OpenCV默认格式）
#     frame = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
#
#     # 使用OpenCV进行JPEG压缩
#     result, encoded_image = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
#     if not result:
#         raise ValueError("图像压缩失败")
#     return encoded_image.tobytes()
#
#
# def decompress_image(data):
#     # 解压JPEG图像数据
#     nparr = np.frombuffer(data, np.uint8)
#     frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
#     if frame is None:
#         raise ValueError("解压缩图像失败")
#     return frame


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
