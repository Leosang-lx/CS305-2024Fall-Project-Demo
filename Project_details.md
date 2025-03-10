# Project of Computer Network: Video Conferenece

要求：3到4人

#### 内容概述：完成包括基于P2P以及client-server的实时视频音频共享的视频会议功能

重功能，按点给分

##### 难度

考虑降低其他系同学的上手难度

- 基础部分主要是工作量，控制难度
- 给一些必要的但与网络完全无关的方法
  - 屏幕捕捉，音频捕捉等
  - 给一个简单的基于UDP的传输架构
  - 给出任务分解？
- 与基础部分，拉高bonus部分的难度



##### 基本功能(80)：

Client-Server

- 会议客户端功能(40): 对于最简单的场景，能够演示即可（2C+1S+1M）
  - **不可靠传输**【共享/不共享】【视频：屏幕（摄像头）】以及【音频：媒体音频（麦克风音频）】(20)
  - 
  - 创建会议(5)
  - 加入
  - 退出会议(5)
  - 取消会议(5)
  - **增加**基于可靠传输的应用【文件传输或者文字聊天】
- 会议服务端功能 (40)：管理所有的会议
  - 多人会议(20): >=3
  - 服务端维持多个会议(20): >=2

##### Bonus(110 - 90)

- P2P，模式切换
- 视频音频编码
- 加密
- UI

##### 报告

- 整体实现：分点
- 对于不同的场景，如何选择P2P和Client-Server
- 对于复杂的拓扑架构，在网络结构需要哪些优化

##### Bonus(20+)

- 音画同步
- 服务端/客户端动态负载调整（测试标准？）
  - 复杂的网络条件，脚本控制网络流量以及丢包等
- 性能测试
  - 基于给定测试场景以及最低视频以及音频的分辨率限制，以FPS为性能指标（统一测？）(需要有帧率限制的开关？)
  - 高负载场景：
    - 同时进行多个类型（不同人数）的会议
- 额外的自己实现的功能或者网络传输上的优化

Report

- 

##### 测试

- **主要**是**主观评测项目**（功能是否完成）
- 性能指标
  - 给定场景的FPS
  - 最大支持的会议数以及可服务的客户端数
- 自动化测试（？）
  - 强制要求根据给定命令行输入格式

##### 分工









### 任务细分

- 摄像头、屏幕视频传输
- 设备媒体音频、麦克风音频传输
- 多人会议
- 音画同步*
- 远程控制**
- 文字聊天**
- 文件传输**

### 附加功能

- 增加实现指标；用户、连接数量等，考虑复杂的网络情况



##### 注意

视频声音，相关的功能最好写好给他们

#### 任务分解

##### 视频：

- 摄像头调用、屏幕捕捉，到视频流或者图像
  - opencv？PIL or mss，directx可能需要通过c++调用？

- 视频编码，传输
  - 视频编码*：H.264&AVC，H.265&HEVC，VP8，VP9，AV1等
  - 图像编码：jpg，png等？
  - 传输协议：
    - 最简单的UDP，TCP
    - 流式传输协议：WebRTC，RTSP，RTMP，HLS(HTTP Live Streaming)等

- 视频解码
- 视频显示及窗口组件，多个窗口的叠加以及画幅比例修改
  - opencv，算好位置+mask？


#### 媒体、通话音频

- 设备媒体音频和麦克风调用，转化为音频流
  - pyaudio？sounddevice？pycaw？

- 音频编码，传输
  - 编码：Opus，AAC，Speex等
  - 传输协议

- 音频解码
- 调音与播放：音量设置，麦克风媒体音混合等

#### 传输 & 顶层设计

- 视频与音频对应的传输协议？
- 不同数据分开发送？
- 按照帧/时间发送？
- 如何设置连接？
- 如何管理多个会议室以及不同client？
- 客户端的音频+视频显示

