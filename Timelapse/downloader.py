import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime

import httpx
import product

logger = logging.getLogger("Timelapse.Downloader")

MOSDAC_STRING = "https://mosdac.gov.in/look/"


@dataclass
class ImageURL:
    url_suffix: str
    image_number: int

    @property
    def url(self):
        return MOSDAC_STRING + self.url_suffix


class Downloader:
    """
    > Gets the urls
    > downloads them, based on some parameters that I haven't thought of yet
    > Keeps all the async code in one place, and lets the GUI handle this better,
        instead of the threading horrors that are in place rn.
    """

    def __init__(
        self,
        client: httpx.AsyncClient,
        name: str,
        product: product.Product,
        start_date: datetime,
        end_date: datetime,
        num_workers=25,
    ):
        self.client = client

        self.name = name
        self.product = product
        self.start_date = start_date
        self.end_date = end_date
        self.url_queue = asyncio.Queue()
        self.num_workers = num_workers

    def get_urls(self):
        """
        gets a list of image urls, by calling a MOSDAC enpoint, which is fed to get_images().

        the mosdac endpoint takes in an st_date parameter that is the last date of the images,
        and a count for the number of image URLs, this counts *back* from the end date,
        the number of images can vary for some reason, images can be missing, so just simply estimating
        the count by looking at the time interval between images is not a complete solution
        """

        logger.info("Getting URLs!")
        start_time = self.start_date.strftime("%d%b%Y").upper()
        end_time = self.end_date.strftime("%Y-%m-%d")
        count = (self.end_date - self.start_date).total_seconds() / 1800

        json = {
            "prod": self.product.pattern,
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
            return []
        logger.debug(f"Length of URL Data Received: {len(data)}")

        index = data.find(start_time)
        logger.debug(f"Index of start date: {index}")
        index = 0 if index == -1 else index
        data = data[index:]

        for index, url in enumerate(data.split(",")):
            self.url_queue.put_nowait(ImageURL(url, index + 1))

    async def worker(self):
        while True:
            try:
                await self.download_and_write_one_image()
            except asyncio.CancelledError:
                return

    async def download_and_write_one_image(self):
        url: ImageURL = await self.url_queue.get()
        try:
            response = await self.client.get(url.url)
            filename = url.url_suffix.split("/")[-1]
            with open(
                f"Images/{self.name}/{url.image_number}-{filename}", "wb"
            ) as file:
                file.write(response.content)
        except Exception as exc:
            logger.error(exc)
        finally:
            self.url_queue.task_done()

    async def run(self):
        self.get_urls()
        workers = [asyncio.create_task(self.worker()) for _ in range(self.num_workers)]
        await self.url_queue.join()
        for worker in workers:
            worker.cancel()


async def test(product: product.Product):
    async with httpx.AsyncClient() as client:
        start = datetime(2023, 7, 21)
        end = datetime(2023, 7, 22)
        downloader = Downloader(client, "Test", product, start, end)
        await downloader.run()


if __name__ == "__main__":
    import os

    import anytree

    if os.path.isdir(f"Images/Test"):
        logger.warning(f"Images/Test already exists, the files will be overwritten")
    else:
        os.makedirs(f"Images/Test")

    if os.path.isdir("Videos"):
        pass
    else:
        os.mkdir("Videos")
    logger.info("Folders Created!")

    resolver = anytree.Resolver()
    path = "/Settings/INSAT-3D/IMAGER/Standard(Full Disk)/Shortwave Infrared"
    settings_tree = product.make_settings_tree()
    product = resolver.get(settings_tree, path)
    asyncio.run(test(product))
