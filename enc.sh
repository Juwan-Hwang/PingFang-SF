set -e
ffmpeg -y -loglevel error -framerate 30 -i frames/f%05d.png -i soundtrack.wav -map 0:v -map 1:a -c:v libx264 -preset slow -crf 15 -pix_fmt yuv420p -profile:v high -tune animation -c:a aac -b:a 192k -ar 48000 -movflags +faststart -shortest PingFang-SF-promo-v120-master.mp4
echo master done
# 2-pass 1080p for README  (video 1600k)
ffmpeg -y -loglevel error -framerate 30 -i frames/f%05d.png -c:v libx264 -preset slow -b:v 1600k -pass 1 -passlogfile p1080 -pix_fmt yuv420p -profile:v high -tune animation -an -f null -
ffmpeg -y -loglevel error -framerate 30 -i frames/f%05d.png -i soundtrack.wav -map 0:v -map 1:a -c:v libx264 -preset slow -b:v 1600k -maxrate 4000k -bufsize 6000k -pass 2 -passlogfile p1080 -pix_fmt yuv420p -profile:v high -tune animation -c:a aac -b:a 192k -ar 48000 -movflags +faststart -shortest PingFang-SF-promo-v120.mp4
echo small done
