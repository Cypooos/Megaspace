from Streamers import Streamer, BufferedStreamer

class TwitchStreamer(Streamer):
  def __init__(self,twitchKey,resolution=(640,480),fps=30.,ffmpegPath="ffmpeg",pipename="",**kwargs):
    super().__init__("rtmp://live-cdg.twitch.tv/app/%s" % twitchKey,resolution,fps,ffmpegPath,pipename,**kwargs)

# Rajouter le chat par la suite +
# autres interaction comme dons etc

class BufferedTwitchStreamer(BufferedStreamer):
  def __init__(self,twitchKey,resolution=(640,480),fps=30.,ffmpegPath="ffmpeg",pipename="",**kwargs):
    super().__init__("rtmp://live-cdg.twitch.tv/app/%s" % twitchKey,resolution,fps,ffmpegPath,pipename,**kwargs)

# Rajouter le chat par la suite +
# autres interaction comme dons etc