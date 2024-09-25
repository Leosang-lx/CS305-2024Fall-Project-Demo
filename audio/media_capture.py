import pycaw
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
import pyaudio
import wave

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1  # 单声道
RATE = 48000  # 采样率

# 初始化 PyAudio
p = pyaudio.PyAudio()

# 获取默认的音频设备
default_device_id = p.get_default_input_device_info()["index"]

# 打开音频设备
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=default_device_id)

# 开始录音
stream.start_stream()

while stream.is_active():
    data = stream.read(CHUNK)
    # 发送数据到网络
    send_audio_data(data, audio_type='media')