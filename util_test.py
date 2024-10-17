import cv2
import struct
import pyaudio
import socket

# 设置服务器地址和端口
SERVER_IP = "127.0.0.1"
# SERVER_IP = "192.168.1.134"
SERVER_PORT_main = 5005

camera_width, camera_height = 480, 480

seperate_transmission = True

server_port_camera = 5006
server_port_voice = 5007

share_screen = True
share_camera = False
share_audio = False

# 初始化音频
CHUNK = 1024
FORMAT = pyaudio.paInt16  # 采样位宽16bit
CHANNELS = 1  # 声道数
RATE = 44100  # 采样率

data_header_format = 'I'
data_header_size = struct.calcsize(data_header_format)


def send_bytes_tcp(sock: socket.socket, bytes_data):
    header = struct.pack(data_header_format, len(bytes_data))
    res = sock.sendall(header + bytes_data)
    return res


def recv_bytes_tcp(sock: socket.socket):
    header = struct.unpack(data_header_format, sock.recv(data_header_size))
    data_size = header[0]
    data = bytearray(data_size)
    ptr = memoryview(data)
    while data_size:
        nrecv = sock.recv_into(buffer=ptr, nbytes=min(4096, data_size))
        ptr = ptr[nrecv:]
        data_size -= nrecv
    return data

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
# def decompress_image(data):
#     # 解压JPEG图像数据
#     nparr = np.frombuffer(data, np.uint8)
#     frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
#     if frame is None:
#         raise ValueError("解压缩图像失败")
#     return frame


def overlay_camera_on_screen(screen_img, camera_img, position=(0, 0), resize_cam=False):
    """
    Place the camera_img to the screen_img
    参数:
    screen_path (str): 屏幕捕捉图像的文件路径。
    cam_path (str): 摄像头捕捉图像的文件路径。
    position (tuple): 摄像头图像放置的位置 (x, y)。
    resize_cam (bool): 是否根据放置位置自动调整摄像头图像大小以适应屏幕图像。
    """

    if screen_img is None and camera_img is None:
        return None
    elif screen_img is None:
        return camera_img
    elif camera_img is None:
        return screen_img

    x_offset, y_offset = position

    # 如果需要调整摄像头图像大小以适应放置区域
    if resize_cam and (x_offset + camera_img.shape[1] > screen_img.shape[1] or
                       y_offset + camera_img.shape[0] > screen_img.shape[0]):
        # 计算新的尺寸
        new_width = min(camera_img.shape[1], screen_img.shape[1] - x_offset)
        new_height = min(camera_img.shape[0], screen_img.shape[0] - y_offset)
        camera_img = cv2.resize(camera_img, (new_width, new_height))

    # 确保摄像头图像不会超出屏幕图像边界
    if x_offset + camera_img.shape[1] > screen_img.shape[1]:
        x_offset = screen_img.shape[1] - camera_img.shape[1]
    if y_offset + camera_img.shape[0] > screen_img.shape[0]:
        y_offset = screen_img.shape[0] - camera_img.shape[0]

    # 创建ROI并放置摄像头图像
    # roi = screen_img[y_offset:y_offset + camera_img.shape[0],
    #       x_offset:x_offset + camera_img.shape[1]]
    screen_img[y_offset:y_offset + camera_img.shape[0], x_offset:x_offset + camera_img.shape[1]] = camera_img

    # 返回合并后的图像
    return screen_img

# test
# combined_image = overlay_camera_on_screen('screen_capture.png', 'camera_capture.png', (50, 50), True)
# cv2.imshow('Combined Image', combined_image)
# cv2.waitKey(0)
# cv2.destroyAllWindows()
#
# # 如果需要保存结果图像
# cv2.imwrite('combined_image.png', combined_image)
