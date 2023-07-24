import logging
import subprocess

import settings

logger = logging.getLogger("Timelapse.Video")


class VideoMaker:
    def __init__(self, name: str, product: settings.Product, framerate=24):
        self.name = name
        self.product = product
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
            f"./Images/{self.name}/%d-{self.product.pattern}",
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
    path = "/Settings/INSAT-3D/IMAGER/Standard(Full Disk)/Shortwave Infrared"
    settings_tree = settings.make_settings_tree()
    prod = resolver.get(settings_tree, path)
    video = VideoMaker("Test", prod)

    a = time.perf_counter()
    video.make_video()
    delta = time.perf_counter() - a

    print(f"Completed in {delta} seconds")
