# INSAT-3D Timelapse Generator
<p align='center'>
    <img src="https://github.com/clodman84/ISRO/blob/main/demos/demo1.gif" />
</p>

## How to install
<p align='center'>
    <img src='https://github.com/clodman84/ISRO/blob/main/demos/Interface.png'>
</p>

Download TimeLapse.rar from the [releases](https://github.com/clodman84/ISRO/releases), extract it and run interface.exe

If you are downloading the code directly, run interface.py, make sure that ffmpeg is installed and it is in your system path.

## How it works

The image urls on the [Mosdac Gallery](https://www.mosdac.gov.in/gallery/index.html) follow a pattern, this program
generates the urls and then downloads them. After that it stitches the downloaded images together with ffmpeg to make a video.
