import asyncio
import logging
import pathlib
from dataclasses import dataclass
from datetime import datetime

import httpx
from aiofile import async_open

from . import settings

logger = logging.getLogger("Timelapse.Downloader")

MOSDAC_STRING = "https://mosdac.gov.in/look/"


def prepare_directories(name: str):
    images = pathlib.Path(f"./Images/{name}")
    if images.exists():
        logger.warning(f"{images} already exists! Files will be overwritten")
    else:
        images.mkdir(parents=True)

    videos = pathlib.Path("./Videos")
    if videos.exists():
        pass
    else:
        videos.mkdir()
    logger.info("Folders Created!")


@dataclass
class ImageURL:
    url_suffix: str
    image_number: int

    @property
    def url(self):
        return MOSDAC_STRING + self.url_suffix


class Downloader:
    """
    Use .run() after instantiating.

    - a queue of urls
    - a worker function that keeps running .download_and_write_one_image() till it's task is cancelled.
    - .download_and_write_one_image() takes one ImageURL from the queue and does what the name suggests.

    The whole program is IO heavy so GET requests and writing to disk are done asynchronously.
    """

    def __init__(
        self,
        client: httpx.AsyncClient,
        name: str,
        product: settings.Product,
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

        self.total_urls = 0
        prepare_directories(f"{self.product.path_string}/{self.name}")

    def get_urls(self):
        """
        Fills up self.url_queue with ImageURLs. The urls are received from
        https://www.mosdac.gov.in/gallery/getImage.php which needs an `st_date` parameter that is the *last* date of
        the images, and a `count` parameter for the number of image URLs, this counts *back* from the end date,
        the number of images per day is inconsistent, we overestimate the `count` and filter out the urls that lie
        outside the desired time frame.
        """

        logger.info("Getting URLs!")
        start_time = self.start_date.strftime("%Y-%m-%d").upper()
        end_time = self.end_date.strftime("%Y-%m-%d")

        if self.end_date == self.start_date:
            count = 48
        else:
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
            return
        except httpx.TimeoutException as e:
            logger.error(f"{e}. Check your internet connection or try again later")
            return

        logger.debug(f"Length of URL Data Received: {len(data)}")

        index = data.find(start_time)
        logger.debug(f"Index of start date: {index}")
        index = 0 if index == -1 else index
        data = data[index:]

        for index, url in enumerate(data.split(",")):
            self.url_queue.put_nowait(ImageURL(url, index + 1))
        self.total_urls = index + 1

    async def worker(self):
        while True:
            try:
                await self.download_and_write_one_image()
            except asyncio.CancelledError:
                return

    async def download_and_write_one_image(self):
        url: ImageURL = await self.url_queue.get()
        logger.debug(f"Working on image {url.image_number}/{self.total_urls}")
        try:
            response = await self.client.get(url.url)
            if response.status_code != 200:
                error_message = (
                    f"{response.status_code} {response.reason_phrase} - {url.url}"
                )
                if response.status_code == 404:
                    logger.warning(error_message)
                else:
                    logger.error(error_message)
            else:
                file_path = pathlib.Path(
                    f"./Images/{self.product.path_string}/{self.name}/{url.image_number}.{self.product.pattern[-3:]}"
                )
                async with async_open(file_path, "wb") as file:
                    await file.write(response.content)
        except Exception as exc:
            logger.warning(f"{exc.__class__.__name__} while working on {url.url}")
        finally:
            self.url_queue.task_done()

    async def run(self):
        self.get_urls()
        workers = [asyncio.create_task(self.worker()) for _ in range(self.num_workers)]
        await self.url_queue.join()
        for worker in workers:
            worker.cancel()


async def test(product: settings.Product):
    async with httpx.AsyncClient() as client:
        start = datetime(2023, 7, 21)
        end = datetime(2023, 7, 22)
        downloader = Downloader(client, "Test", product, start, end)
        await downloader.run()


if __name__ == "__main__":
    import time

    import anytree

    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    resolver = anytree.Resolver()
    path = "/Settings/INSAT-3D/IMAGER/Standard(Full Disk)/Shortwave Infrared"
    settings_tree = settings.make_settings_tree()
    prod = resolver.get(settings_tree, path)

    a = time.perf_counter()
    asyncio.run(test(prod))
    delta = time.perf_counter() - a

    print(f"Completed in {delta} seconds")
