# INSAT-3D Timelapse Generator
<p align='center'>
    <img src="https://github.com/clodman84/ISRO/blob/main/demos/demo1.gif" />
</p>

## How to Use
<p align='center'>
    <img src='https://github.com/clodman84/ISRO/blob/main/demos/Interface.png'>
</p>

1. Install FFMPEG and make sure it is in your system path, this program uses ffmpeg to stitch together the frames.
2. Run interface.py
3. The interface is fairly straightforward, but you can watch the How2Use.mp4 to get an idea

## How it works

The image urls on the [Mosdac Gallery](https://www.mosdac.gov.in/gallery/index.html) follow a pattern, this program
generates the urls and then downloads them. After that it stitches the downloaded images together with ffmpeg to make a video.
