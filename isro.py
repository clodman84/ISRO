import asyncio
import logging
import os
import subprocess
from datetime import datetime
from typing import Callable

import httpx

logger = logging.getLogger("ISRO.Generator")


class TimeLapse:
    def __init__(
        self,
        name: str,
        start_date: datetime,
        end_date: datetime,
        prod: str,
        frame_rate=24,
        chunk_size=850,
    ):
        self.name = name  # name of the video
        self.prod = prod  # "L1C_ASIA_MER_BIMG","L1C_ASIA_MER_BIMG_KARNATAKA", etc
        self.frame_rate = frame_rate
        self.chunk_size = chunk_size
        self.start = start_date.replace(
            hour=0
        )  # time goes forward and the past was the beginning, start < end
        self.end = end_date.replace(hour=23)
        self.urls = self.getURLS()
        self.createDir()
        self.fileIndex = 0

    def createDir(self):
        if os.path.isdir(f"Images/{self.name}"):
            logger.warning(
                f"Images/{self.name} already exists, the files will be overwritten"
            )
        else:
            os.makedirs(f"Images/{self.name}")

        if os.path.isdir("Videos"):
            pass
        else:
            os.mkdir("Videos")
        logger.info("Folders Created!")

    def getURLS(self):
        logger.info("Getting URLs!")
        mosdacString = "https://mosdac.gov.in/look/"
        start_time = self.start.strftime("%d%b%Y").upper()
        end_time = self.end.strftime("%Y-%m-%d")
        count = (self.end - self.start).total_seconds() / 1800
        json = {
            "prod": f"3DIMG_*_{self.prod}_V*.jpg",
            "st_date": end_time,
            "count": count,
        }
        logger.debug(
            f"URL Parameters - \n\tStart: {start_time}\n\tEnd: {end_time}\n\tCount: {count}\n\tProd: {json['prod']}"
        )
        try:
            data = httpx.post(
                "https://www.mosdac.gov.in/gallery/getImage.php", json=json
            ).json()[0]
        except httpx.ConnectError as e:
            logger.error(f"{e}. Check your internet connection.")
            return

        logger.debug(f"Length of URL Data Received: {len(data)}")
        index = data.find(start_time)
        logger.debug(f"Index of start date: {index}")
        index = 0 if index == -1 else index
        data = data[index:]
        urls = [mosdacString + url for url in data.split(",")]
        logger.debug(f"Length of URL-list = {len(urls)}\nSample:\n\t{urls[0]}")
        logger.info(f"Received and Parsed {len(urls)} URLs!")
        return urls

    async def getImages(self, proceed: Callable = lambda: True):
        # Breaking the downloads into chunks
        n = self.chunk_size
        chunks = [
            self.urls[i * n : (i + 1) * n] for i in range((len(self.urls) + n - 1) // n)
        ]
        async with httpx.AsyncClient(timeout=None) as client:
            for i, chunk in enumerate(chunks):
                while True:
                    if not proceed():
                        logger.info(
                            f"Image download cancelled! Making video with {i} downloaded chunks."
                        )
                        await client.aclose()
                        return
                    try:
                        logger.info(f"Downloading Chunk {i + 1}/{len(chunks)}...")
                        sub_tasks = (client.get(url) for url in chunk)
                        requests = await asyncio.gather(*sub_tasks)
                        logger.debug(f"Received chunk {i + 1}")
                        requests = [i for i in requests if i.status_code == 200]
                        logger.debug("Failed requests filtered.")
                        self.writeImages(requests)

                    except Exception as e:
                        logger.error(
                            f"{e}, (If the problem persists try reducing your chunk size). Trying again..."
                        )
                    break

    def writeImages(self, imageList):
        for image in imageList:
            ImageName = f"{self.prod}_{self.fileIndex}.jpg"
            logger.debug(f"Writing file {ImageName}")
            with open(f"Images/{self.name}/{ImageName}", "wb") as file:
                file.write(image.content)
            self.fileIndex += 1

    def makeVideo(self):
        logger.info("Generating Video...")
        args = [
            "ffmpeg",
            "-loglevel",
            "quiet",
            "-stats",
            "-framerate",
            str(self.frame_rate),
            "-i",
            f"./Images/{self.name}/{self.prod}_%d.jpg",
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

    def run(self, proceed: Callable, onCompletion: Callable):
        asyncio.run(self.getImages(proceed))
        self.makeVideo()
        onCompletion()
