import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
from aiortc.contrib.media import MediaPlayer

async def offer(pc, type, sdp):
    pc.setRemoteDescription(RTCSessionDescription(sdp=sdp, type=type))
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    return pc.localDescription

async def run_server():
    pc = RTCPeerConnection()
    
    @pc.on("track")
    def on_track(track):
        print("Track %s received" % track.kind)

    player = MediaPlayer("input.mp4", format="mp4", options={"rtsp_transport": "udp"})
    pc.addTrack(player.audio)
    pc.addTrack(player.video)

    # 这里应该有网络通信逻辑来接收客户端的 offer 并返回 answer
    offer_sdp = "客户端提供的 SDP"
    answer = await offer(pc, "offer", offer_sdp)
    print("Sending answer:\n%s" % answer.sdp)

    await asyncio.sleep(3600 * 24)  # keep alive

if __name__ == "__main__":
    asyncio.run(run_server())