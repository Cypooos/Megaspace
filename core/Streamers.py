from __future__ import print_function, division
from twitchstream.outputvideo import TwitchBufferedOutputStream
import argparse
import numpy as np
import subprocess
import signal
import threading
import sys
try:
  import Queue as queue
except ImportError:
  import queue
from time import time
import os
import tempfile

"""
class StreamVideo():

  def __init__(self,key,resolution=(430,240),fps=30.,audioDivision=8192,audioBufferSize = 1470):
    self.resolution = resolution
    self.key = key
    self.list = []
    self.fps = fps
    self.videofile = ""
    self.stream = None
    self.audioInstance = None
    self.videoInstance = None
    self.audioDivision = audioDivision
    self.audioBufferSize = audioBufferSize
    self.audioInstance__sampw = None

  def start(self):
    self.stream = TwitchBufferedOutputStream(
      twitch_stream_key=self.key,
      width=self.resolution[0],height=self.resolution[1],
      enable_audio=True,
      fps=self.fps,
      verbose=True)
    
  def readFile(self,path):
    self.videofile = path
    self.videoInstance = cv2.VideoCapture(path)
    self.audioInstance = wave.open(".".join(path.split(".")[:-1])+".wav",'rb')
    self.audioInstance__sampw = self.audioInstance.getsampwidth()
    self.audioInstance__nbChan = self.audioInstance.getnchannels()

  def feedBuffers(self):
    if self.stream.get_video_frame_buffer_state() < 30:
      ret, frame = self.videoInstance.read()
      if not ret:
        return AssertionError("End of video file")
      
      frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
      image = frame.astype('float64')
      image *= 1.0/image.max()
      image = cv2.resize(image,self.resolution)
      self.stream.send_video_frame(image)
  
    if self.stream.get_audio_buffer_state() < 30:
      left_audio = self.convertwav(self.audioInstance.readframes(self.audioBufferSize))[:,0]
      self.stream.send_audio(left_audio, left_audio)

  def addFile(self):
    pass

  def convertwav(self, data):
    data must be the string containing the bytes from the wav file.
    sampwidth = self.audioInstance__sampw
    nchannels = self.audioInstance__nbChan
    num_samples, remainder = divmod(len(data), sampwidth * nchannels)

    if sampwidth == 3:
      a = np.empty((num_samples, nchannels, 4), dtype=np.uint8)
      raw_bytes = np.frombuffer(data, dtype=np.uint8)
      a[:, :, :sampwidth] = raw_bytes.reshape(-1, nchannels, sampwidth)
      a[:, :, sampwidth:] = (a[:, :, sampwidth - 1:sampwidth] >> 7) * 255
      result = a.view('<i4').reshape(a.shape[:-1]).astype('float32') 
    else:
      # 8 bit samples are stored as unsigned ints; others as signed ints.
      dt_char = 'u' if sampwidth == 1 else 'i'
      a = np.frombuffer(data, dtype='<%s%d' % (dt_char, sampwidth))
      result = a.reshape(-1, nchannels).astype('float32') 
    result /= self.audioDivision
    return result
"""


class Streamer():

  def __init__(self,RTMPlink,resolution=(640,480),fps=30.,ffmpegPath="ffmpeg",pipename="",**kwargs):
    self.kwargs = kwargs # store it for later

    self.RTMPLink = RTMPlink

    self.resolution = resolution
    self.fps = fps

    self.ffmpegProcess = None
    self.ffmpegPath = ffmpegPath

    self.videoPipe = None
    self.audioPipe = None
    
    self._resetFFMPEG()


  def _killFFMPEG(self):
    if self.ffmpegProcess is not None:
      try:
        self.ffmpegProcess.send_signal(signal.SIGINT)
      except OSError:
        pass 

  def _resetFFMPEG(self):

    if self.ffmpegProcess is not None:
      try:
        self.ffmpegProcess.send_signal(signal.SIGINT)
      except OSError:
        pass 

    pipename = self.kwargs.get("pipename","")
    if self.videoPipe is None:
      self.videoPipe = tempfile.NamedTemporaryFile(prefix=pipename, suffix="__video")
    if self.audioPipe is None:
      self.audioPipe = tempfile.NamedTemporaryFile(prefix=pipename, suffix="__audio")

    self._killFFMPEG()

    command = []
    command.extend([ # VIDEO INPUT PARAMS
      self.ffmpegPath,
      '-loglevel', 'verbose',
      '-f', 'rawvideo',
      '-s', '%dx%d' % self.resolution,
      ])
    command.extend(['-i', self.videoPipe.name])

    command.extend([ # AUDIO INPUT PARAMS
      '-f', 's16le'])
    command.extend(['-i', self.audioPipe.name])
    
    command.extend([ # VIDEO CODECS
    ])
    
    command.extend([ # AUDIO CODECS
    ])

    command.extend([ # MAPPING
      '-map', '0:v', '-map', '1:a',
    ])
    command.extend([]) # THREAD

    command.extend(['-f', 'flv', self.RTMPLink]) # OUTPUT

    devnullpipe = open("/dev/null", "w")     # Throw away stream
    self.ffmpegProcess = subprocess.Popen(command,stdin=subprocess.PIPE,stderr=None,stdout=None)

  def __enter__(self):
    return self

  def __exit__(self, type, value, traceback):
    self.endStream()
    
  def feedVideoPipe(self,image): # array of uint8 0-255 shape [h,w,3]. 3 -> RGB
    if self.videoPipe is None:
      pipename = self.kwargs.get("pipename","")
      self.videoPipe = tempfile.NamedTemporaryFile(prefix=pipename, suffix="__video")

    assert image.shape == (self.resolution[0], self.resolution[1], 3)

    #image = np.clip(255*image, 0, 255).astype('uint8')
    try:
      self.videoPipe.write(image.tostring())
    except ValueError:
      raise

  def feedAudioPipe(self,audio): # array int16 -32767:32767 shape[X,2]

    if self.audioPipe is None:
      pipename = self.kwargs.get("pipename","")
      self.audioPipe = tempfile.NamedTemporaryFile(prefix=pipename, suffix="__audio")

    try:
      self.audioPipe.write(audio.tostring())
    except ValueError:
      raise

  def endStream(self):
    self._killFFMPEG()
    self.audioPipe.close()
    self.videoPipe.close()
    self.audioPipe = None
    self.videoPipe = None

      
class BufferedStreamer(Streamer):

  def __init__(self,*args,**kwargs):

    super().__init__(*args,**kwargs)

    self.videoBuffer = queue.PriorityQueue()
    self.audioBuffer = queue.PriorityQueue()

    self.audioRate = kwargs.get("audioRate",44100)

    self.lastFrame = np.ones((self.resolution[0],self.resolution[1],3))
    x = np.sin(np.linspace(0.0, 10*np.pi, int(self.audioRate/self.fps) + 1)[:-1])
    x = np.clip(32767*x, -32767, 32767).astype('int16')
    self.lastAudio = np.column_stack((x,x))

    self.videoFrameCount = 0
    self.audioFrameCount = 0
    
    self.audioTimer = threading.Timer(0.0,self.feedAudioPipe)
    self.audioTimer.daemon = True # Otherwise can't stop program lol
    self.audioTimer.start()
    self.videoTimer = threading.Timer(0.0,self.feedVideoPipe)
    self.videoTimer.daemon = True # Otherwise can't stop program lol
    self.videoTimer.start()
  
  def feedVideoPipe(self):
    difference = time()
    try:
      t,frame = self.videoBuffer.get_nowait()
    except (IndexError, queue.Empty):
      print("Frame taken from last")
      frame = self.lastFrame
    else:
      self.lastFrame = frame
    try:
      super().feedVideoPipe(frame)
    except ValueError:
      return

    timeWait = 1./self.fps-(time()-difference)
    self.videoTimer = threading.Timer(timeWait,self.feedVideoPipe)
    self.videoTimer.daemon = True # Otherwise can't stop program lol
    self.videoTimer.start()

  def feedAudioPipe(self):
    difference = time()
    try:
      Audio = self.audioBuffer.get_nowait()[1]
    except (IndexError, queue.Empty):
      Audio = self.lastAudio
    else:
      self.lastAudio = Audio

    try:
      #print(Audio)
      super().feedAudioPipe(Audio)
    except ValueError:
      return

    timewait = len(Audio) / self.audioRate-(time()-difference)
    self.audioTimer = threading.Timer(timewait,self.feedVideoPipe)
    self.audioTimer.daemon = True # Otherwise can't stop program lol
    self.audioTimer.start()

  def feedVideoBuffer(self, frame):
    self.videoFrameCount +=1
    self.videoBuffer.put((self.videoFrameCount,frame))
  
  def feedAudioBuffer(self,audio):
    self.audioFrameCount += 1
    self.audioBuffer.put((self.audioFrameCount,audio))

  def getVideoBufferLength(self):
    return self.videoBuffer.qsize()

  def getAudioBufferLength(self):
    return self.audioBuffer.qsize()

  def endStream(self):
    self.videoTimer.cancel()
    self.audioTimer.cancel()
    super().endStream()
