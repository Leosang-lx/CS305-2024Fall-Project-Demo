import pyaudio
import sounddevice as sd
import queue
import threading

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1  # 单声道
RATE = 48000  # 采样率

# 创建一个队列来存储音频数据
q = queue.Queue()

def callback(in_data, frame_count, time_info, status):
    q.put(in_data)
    return (in_data, pyaudio.paContinue)

# 初始化 PyAudio
p = pyaudio.PyAudio()

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                stream_callback=callback)

# 开始录音
stream.start_stream()

# 在另一个线程中读取音频数据
def read_audio(q):
    while stream.is_active():
        try:
            data = q.get(timeout=1)
            # 发送数据到网络
            send_audio_data(data, audio_type='microphone')
        except queue.Empty:
            pass

# 启动读取线程
audio_thread = threading.Thread(target=read_audio, args=(q,))
audio_thread.start()