import logging
import pathlib
import re
from itertools import chain

import dearpygui.dearpygui as dpg

from .utils import modal_message

logger = logging.getLogger("GUI.Explorer")


class ImageWindow:
    def __init__(self, directory: pathlib.Path):
        self.image_list = list(
            chain.from_iterable(directory.glob(ext) for ext in ("*.jpg", "*.png"))
        )
        self.image_list.sort(
            key=lambda x: [
                int(c) if c.isdigit() else c for c in re.split(r"(\d+)", str(x))
            ]
        )

        if len(self.image_list) == 0:
            logger.error(f"No *.jpg *.png or *.gif found in {directory}")
            modal_message(
                f"No images ending in .jpg, .png or .gif were found in {directory}."
            )
            return
        self.index = 0

        with dpg.window(
            label="ImageWindow", pos=(20, 100), width=500, height=500, no_title_bar=True
        ) as self.window_id:
            with dpg.group(horizontal=True, parent=self.window_id):
                dpg.add_button(label="Previous", tag=f"previous-{self.window_id}")
                dpg.add_button(label="Next", tag=f"next-{self.window_id}")
                dpg.add_button(label="Close", callback=lambda: self._close())

        with dpg.child_window(
            parent=self.window_id, autosize_x=True, autosize_y=True
        ) as self.image_window:
            width, height, _, data = dpg.load_image(str(self.image_list[self.index]))
            with dpg.texture_registry() as self.registry:
                dpg.add_raw_texture(width, height, data, tag=f"image-{self.window_id}")
            with dpg.plot(
                label=self.image_list[self.index].name,
                parent=self.image_window,
                width=-1,
                height=-1,
                equal_aspects=True,
            ) as self.image:
                # Dummy bar series to trick the scale and zoom out to fit the image
                dpg.add_plot_axis(dpg.mvYAxis, tag=f"y-{self.window_id}")
                dpg.add_bar_series(
                    [-width / 2, 0, width / 2],
                    [0, 0, 0],
                    weight=1,
                    parent=f"y-{self.window_id}",
                )
                dpg.draw_image(
                    f"image-{self.window_id}",
                    (-width / 2, height / 2),
                    (width / 2, -height / 2),
                )

        with dpg.item_handler_registry(tag=f"playHandler-{self.window_id}"):
            dpg.add_item_active_handler(callback=lambda: self._loadTexture(1))
        with dpg.item_handler_registry(tag=f"rewindHandler-{self.window_id}"):
            dpg.add_item_active_handler(callback=lambda: self._loadTexture(-1))

        dpg.bind_item_handler_registry(
            f"next-{self.window_id}", f"playHandler-{self.window_id}"
        )
        dpg.bind_item_handler_registry(
            f"previous-{self.window_id}", f"rewindHandler-{self.window_id}"
        )

    def _loadTexture(self, i):
        if (self.index > 0 and i == -1) or (
            self.index < len(self.image_list) - 1 and i == 1
        ):
            self.index += i
        file = self.image_list[self.index]
        _, _, _, data = dpg.load_image(str(file))
        dpg.set_value(f"image-{self.window_id}", data)
        dpg.configure_item(self.image, label=file.name)

    def _close(self):
        dpg.delete_item(self.window_id)
        dpg.delete_item(f"image-{self.window_id}")
        dpg.delete_item(self.registry)


class Explorer:
    def __init__(self, parent):
        self.window_id = parent
        self.table = None
        dpg.add_button(
            label="Refresh", callback=self._loadDirectories, parent=self.window_id
        )
        self._loadDirectories()

    def _loadDirectories(self):
        imageFolders = []
        folder = pathlib.Path("./Images")
        if folder.is_dir():
            imageFolders = list(folder.iterdir())
        if not imageFolders:
            logger.warning("No image folders were found.")
            dpg.add_text(
                "Make some videos and they will appear here.",
                wrap=0,
                parent=self.window_id,
            )
            return
        if self.table:
            dpg.delete_item(self.table)
        with dpg.table(
            label="",
            parent=self.window_id,
            header_row=False,
            row_background=True,
            borders_innerH=True,
            borders_outerH=True,
            borders_innerV=True,
            borders_outerV=True,
            delay_search=True,
        ) as self.table:
            dpg.add_table_column(width_fixed=True)
            dpg.add_table_column(width_fixed=False)
            dpg.add_table_column(width_fixed=True)
            for index, directory in enumerate(imageFolders):
                with dpg.table_row():
                    dpg.add_text(str(index + 1))
                    dpg.add_text(directory.name)
                    dpg.add_button(
                        label="View",
                        user_data=directory,
                        callback=lambda s, a, u: ImageWindow(u),
                    )
        logger.debug("Refreshed explorer window")
