import httpx
import asyncio
from datetime import datetime
import os
from subprocess import run
import logging

logger = logging.getLogger("ISRO.Generator")


class TimeLapse:
    def __init__(self, name: str, start_date: datetime, end_date: datetime, prod: str, frame_rate=24):
        self.name = name  # name of the video
        self.prod = prod  # "L1C_ASIA_MER_BIMG","L1C_ASIA_MER_BIMG_KARNATAKA", etc
        self.frame_rate = frame_rate
        self.start = start_date.replace(hour=0)
        self.end = end_date.replace(hour=23)  # time goes forward and the past was the beginning
        self.urls = self.getURLS()
        self.createDir()
        self.fileIndex = 0

    def createDir(self):
        if os.path.isdir(f"Images/{self.name}"):
            logger.warning(f"Images/{self.name} already exists, the file will be overwritten")
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
        smh = '\n'
        start_time = self.start.strftime("%d%b%Y").upper()
        end_time = self.end.strftime("%Y-%m-%d")
        count = (self.end - self.start).seconds / 1800
        count = 48 if count == 0 else count  # potential for having minute-level granularity in the future
        json = {"prod": f"3DIMG_*_{self.prod}_V*.jpg", "st_date": end_time, "count": count}
        logger.debug(f"URL Parameters - \nStart: {start_time}\nEnd: {end_time}\nCount: {count}\nProd: {json['prod']}")

        data = httpx.post("https://www.mosdac.gov.in/gallery/getImage.php", json=json).json()[0]
        logger.debug(f"Length of URL Data Received: {len(data)}")
        index = data.find(start_time)
        logger.debug(f"Index of start date: {index}")
        index = 0 if index == -1 else index
        data = data[index:]
        urls = [mosdacString + url for url in data.split(',')]
        logger.debug(f"Length of URL-list = {len(urls)},\nSample: {smh.join(urls[:2])}")
        logger.info("Received and Parsed URLs!")
        return urls

    async def getImages(self):
        # Breaking the downloads into chunks
        n = 850
        chunks = [self.urls[i * n: (i + 1) * n] for i in range((len(self.urls) + n - 1) // n)]
        for i, chunk in enumerate(chunks):
            while True:
                try:
                    logger.info(f"Downloading Chunk {i + 1}/{len(chunks)}...")
                    async with httpx.AsyncClient(timeout=None) as client:
                        sub_tasks = (client.get(url) for url in chunk)
                        requests = await asyncio.gather(*sub_tasks)

                    requests = [i for i in requests if i.status_code == 200]  # filtering out all failed requests

                    for image in requests:
                        ImageName = f"{self.prod}_{self.fileIndex}.jpg"
                        with open(f"Images/{self.name}/{ImageName}", "wb") as file:
                            file.write(image.content)
                        self.fileIndex += 1

                except httpx.ConnectError:  # random error \_(o_o)_/
                    logger.error("ConnectError encountered, trying again...")
                    continue
                break

    def video(self):
        asyncio.run(self.getImages())
        logger.info('Generating Video...')
        args = ['ffmpeg', '-loglevel', 'quiet', '-stats', '-framerate', str(self.frame_rate), '-i',
                f'./Images/{self.name}/{self.prod}_%d.jpg', '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-vcodec',
                'libx264', '-y', '-an', f'./Videos/{self.name}.mp4']
        run(args=args)
        logger.info('Done!')


# TODO: Get rid of this.
async def preview(date, year, type_, file_name):
    """To get the preview images when the preview button is clicked.
    Copy pasted from https://github.com/clodman84/AternosReborn/blob/master/space.py"""

    minutes = ("00", "59", "30", "29")
    urls = []
    mosdacString = "https://mosdac.gov.in/look/3D_IMG/preview"

    for hour in range(0, 4):
        # increments the time by 30 minutes
        if hour < 10:
            hour = "0" + str(hour)
        else:
            hour = str(hour)
        for minute in minutes:
            time = hour + minute
            url = f"{mosdacString}/{year}/{date}/3DIMG_{date}{year}_{time}_{type_}.jpg"
            urls.append(url)

    async with httpx.AsyncClient(timeout=None) as client:
        tasks = (client.get(url) for url in urls)
        reqs = await asyncio.gather(*tasks)

    for i in reqs:
        if i.status_code == 200:
            with open(f"{file_name}.jpg", "wb") as file:
                file.write(i.content)
            return True

    return False
