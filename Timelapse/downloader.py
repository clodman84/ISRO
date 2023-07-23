import logging
from datetime import datetime

import httpx

logger = logging.getLogger("Timelapse.Downloader")


class Product:
    """
    > Builds the product, at the end of the day this amounts to just a string, the whole "3D_IMG" thing.
    """

    def __init__(self):
        ...


class Downloader:
    """
    > Gets the urls
    > downloads them, based on some parameters that I haven't thought of yet
    > Keeps all the async code in one place, and lets the GUI handle this better,
        instead of the threading horrors that are in place rn.
    """

    def __init__(
        self, product: str, start_date: datetime, end_date: datetime, chunk_size=850
    ):
        self.product = product
        self.start_date = start_date
        self.end_date = end_date
        self.chunk_size = chunk_size
        self.urls = self.get_urls()

    def get_urls(self) -> list:
        """
        gets a list of image urls, by calling a MOSDAC enpoint, which is fed to get_images().

        the mosdac endpoint takes in an st_date parameter that is the last date of the images,
        and a count for the number of image URLs, this counts *back* from the end date,
        the number of images can vary for some reason, images can be missing, so just simply estimating
        the count by looking at the time interval between images is not a complete solution
        """

        logger.info("Getting URLs!")
        mosdac_string = "https://mosdac.gov.in/look/"
        start_time = self.start_date.strftime("%d%b%Y").upper()
        end_time = self.end_date.strftime("%Y-%m-%d")
        count = (self.end_date - self.start_date).total_seconds() / 1800

        json = {
            "prod": f"3DIMG_*_{self.product}_V*.jpg",
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
        urls = [mosdac_string + url for url in data.split(",")]
        logger.debug(f"Length of URL-list = {len(urls)}\nSample:\n\t{urls[0]}")
        logger.info(f"Received and Parsed {len(urls)} URLs!")
        return urls

    async def get_images(self):
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
