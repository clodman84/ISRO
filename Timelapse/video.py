import logging
import pathlib
import subprocess

logger = logging.getLogger("Timelapse.Video")


class VideoMaker:
    def __init__(self, name: str, directory: pathlib.Path, framerate=24):
        self.name = name
        self.directory = directory
        self.framerate = framerate

    def make_video(self):
        logger.info("Generating Video...")
        args = [
            "ffmpeg",
            "-loglevel",
            "quiet",
            "-stats",
            "-framerate",
            str(self.framerate),
            "-i",
            f"./{self.directory}/%d.jpg",
            "-vf",
            "pad=ceil(iw/2)*2:ceil(ih/2)*2",
            "-vcodec",
            "libx264",
            "-y",
            "-an",
            f"./Videos/{self.name}.mp4",
        ]
        process = subprocess.Popen(args)
        out = process.wait()
        logger.info(f"Done! Exit code - {out}")


if __name__ == "__main__":
    import time

    import anytree

    logging.basicConfig(level=logging.DEBUG)

    resolver = anytree.Resolver()
    path = pathlib.Path(
        "./Images/INSAT-3D/IMAGER/Special/Blended Image/03Aug2023_03Aug2023"
    )
    video = VideoMaker("Test", path)

    a = time.perf_counter()
    video.make_video()
    delta = time.perf_counter() - a

    print(f"Completed in {delta} seconds")
