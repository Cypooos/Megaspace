from TwitchStreamers import TwitchStreamer, BufferedTwitchStreamer
import numpy as np
import cv2
import wave
import time

class BufferedTwitchVideoStreamer(BufferedTwitchStreamer):
  def __init__(self,twitchKey,resolution=(1000,640),fps=30.,ffmpegPath="ffmpeg",pipename="",**kwargs):
    super().__init__(twitchKey,resolution,fps,ffmpegPath,pipename,**kwargs)
    self.videosWatchlist = []
    self.activeWave = None
    self.activeWave__sampw = 0
    self.activeWave__nbChan = 0
    self.activeCV2 = None
    self.functVideoFinish = []
    self.functAudioFinish = []

  def OnVideoFinish(self,funct):
    self.functVideoFinish.append(funct)
    return funct

  def resetList(self):
    self.videoWatchlist = []
    self.audioWatchList = []
    # reset instances

  def getVideosList(self):
    return self.videosWatchlist

  def addVideosList(self,path):
    self.videosWatchlist.append(path)
    return self.videosWatchlist
  
  def mainLoop(self):

    ActivePath = self.videosWatchlist[0]
    self.activeCV2 = cv2.VideoCapture(ActivePath)
    self.activeWave = wave.open(".".join(ActivePath.split(".")[:-1])+".wav",'rb')
    self.activeWave__sampw = self.activeWave.getsampwidth()
    self.activeWave__nbChan = self.activeWave.getnchannels()


    print("STARTING")
    try:
      while True:
        if self.videoBuffer.qsize() <30:
          ret, frame = self.activeCV2.read()
          if not ret:
            return AssertionError("End of video file")
          
          frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
          frame = cv2.resize(frame,(self.resolution[1],self.resolution[0]))
          self.feedVideoBuffer(frame)
        if self.audioBuffer.qsize() <30:
          # add audio data elements
          aud = np.random.randn(1024)
          aud = np.column_stack((aud, aud))
          self.feedAudioBuffer(aud)
    except:
      self.endStream()
      print("\n\n\n----------Stream ended----------\n")
      raise



t = BufferedTwitchVideoStreamer("live_519643490_0CFTFk8gZJL9CowkmSE4GgcEaRR0tk?bandwidthtest=true")


@t.OnVideoFinish
def ok(okdoik,qsdqs):
  print("ok")

t.addVideosList("test.mp4")
t.mainLoop()




