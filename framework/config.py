"""
字段全部用小写，方法全部用大写
"""

HELP = 'Create         : create an conference\n' \
       'Join [conf_id ]: join a conference with conference ID\n' \
       'Quit           : quit an on-going conference\n' \
       'Cancel         : cancel your on-going conference (only the manager)\n\n'

# SERVER_IP = '127.0.0.1'
SERVER_IP = '192.168.1.134'

SERVER_MAIN_PORT = 8888
TIMEOUT_SERVER = 5
DGRAM_SIZE = 1500

CHUNK = 1024
CHANNELS = 1  # 声道数
RATE = 44100  # 采样率

camera_width, camera_height = 480, 480
