import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription

async def answer(pc, type, sdp):
    pc.setRemoteDescription(RTCSessionDescription(sdp=sdp, type=type))
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    return pc.localDescription

async def run_client():
    pc = RTCPeerConnection()

    # 这里应该有网络通信逻辑来发送 offer 并接收 answer
    pc.createDataChannel("chat")
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    
    answer_sdp = "服务器返回的 SDP"
    await answer(pc, "answer", answer_sdp)

    # 连接建立后，可以开始发送和接收数据
    # ...

    await asyncio.sleep(3600 * 24)  # keep alive

if __name__ == "__main__":
    asyncio.run(run_client())