import os

try:
    TwitchKey = os.environ['TwitchKeyDiscursif']
except KeyError:
  print("Exit because 'TwitchKeyDiscursif' not found")
  exit()

#os.system("ffmpeg -f x11grab -s '$INRES' -r '$FPS' -i :0.0 -f pulse -i 0 -f flv -ac 2 -ar $AUDIO_RATE -vcodec libx264 -g $GOP -keyint_min $GOPMIN -b:v $CBR -minrate $CBR -maxrate $CBR -pix_fmt yuv420p -s $OUTRES -preset $QUALITY -tune film -acodec aac -threads $THREADS -strict normal -bufsize $CBR 'rtmp://$SERVER.twitch.tv/app/$STREAM_KEY'")

os.system("ffmpeg"+"-i input.mp4"+" -vcodec libx264 -b:v 5M -acodec aac -b:a 256k -f flv "+TwitchKey)
