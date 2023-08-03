import asyncio
import logging
from datetime import datetime

import dearpygui.dearpygui as dpg
import httpx

from Timelapse import Downloader

from . import treeselector

logger = logging.getLogger("GUI.Downloader")


class DownloaderWindow:
    def __init__(self, product_selector: treeselector.TreeSelector, parent):
        self.product_selector = product_selector
        self.parent = parent

        now = datetime.now()
        default_date = {
            "year": now.year % 100 + 100,
            "month": now.month - 1,
            "month_day": now.day,
        }
        with dpg.collapsing_header(label="Start Date"):
            dpg.add_date_picker(tag="start", default_value=default_date)
        with dpg.collapsing_header(label="End Date"):
            dpg.add_date_picker(tag="end", default_value=default_date)
        dpg.add_separator()

        with dpg.group():
            dpg.add_button(label="Download", callback=self.run)

    async def download(self):
        name = self.name
        start, end = self.dates
        product = self.product
        if not all((name, start, end, product)):
            logger.error("Download cancelled!")
            return
        logger.info(
            f"Download Settings:\n\tName:\t{name}\n\tStart:\t{start:'%d%b%Y'}\n\tEnd:\t{end:'%d%b%Y'}\n\tProduct:\t{product}"
        )
        async with httpx.AsyncClient() as client:
            downloader = Downloader(client, name, product, start, end)  # type: ignore
            await downloader.run()

    def run(self):
        logger.info("Starting download...")
        asyncio.run(self.download())
        logger.info("Done!")

    @property
    def name(self):
        try:
            name = "_".join(f"{d:%d%b%Y}" for d in self.dates)
            return name
        except treeselector.TreeError:
            return

    @property
    def dates(self):
        data = []
        for d in ("start", "end"):
            val: dict = dpg.get_value(d)
            year = val["year"] + 1900  # years in dpg date picker are measured from 1900
            month = val["month"] + 1
            day = val["month_day"]
            data.append(datetime(year, month, day))
        return data

    @property
    def product(self):
        try:
            return self.product_selector.get_node()
        except treeselector.TreeError as error:
            logger.warning(error)
