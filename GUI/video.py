import logging
import pathlib
import re
from itertools import chain

import dearpygui.dearpygui as dpg

from Timelapse import VideoMaker

logger = logging.getLogger("GUI.Video")


class VideoPrompt:
    def __init__(self, directory: pathlib.Path):
        self.directory = directory
        with dpg.mutex():
            with dpg.window(
                modal=True, autosize=True, no_resize=True, no_title_bar=True
            ) as self.window:
                dpg.add_text("Settings")
                dpg.add_separator()

                with dpg.group(horizontal=True):
                    dpg.add_text("Video Name")
                    dpg.add_input_text(tag="name", default_value=self.default_name)
                with dpg.group(horizontal=True):
                    dpg.add_text("Framerate ")
                    dpg.add_input_int(tag="framerate", default_value=24)
                dpg.add_separator(pos=(-1, 70))
                with dpg.group(horizontal=True, tag="button group"):
                    dpg.add_button(label="Create", width=75, callback=self._make_video)
                    dpg.add_button(label="Close", width=75, callback=self._close)
        dpg.split_frame()
        modal_dimensions = dpg.get_item_rect_size(self.window)
        window_dimensions = dpg.get_item_rect_size("Primary Window")
        newPos = [(window_dimensions[i] - modal_dimensions[i]) / 2 for i in range(2)]
        dpg.configure_item(self.window, pos=newPos)

    def _make_video(self):
        dpg.delete_item("button group")
        dpg.add_loading_indicator(parent=self.window)
        VideoMaker(self.name, self.directory, self.framerate).make_video()
        self._close()

    def _close(self):
        dpg.delete_item(self.window)

    @property
    def default_name(self):
        return f"{self.directory.name}"

    @property
    def name(self):
        return dpg.get_value("name") or self.default_name

    @property
    def framerate(self):
        return dpg.get_value("framerate") or 24


class PreviewWindow:
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
            return
        self.index = 0

        with dpg.window(
            label="ImageWindow", pos=(20, 100), width=500, height=500, no_title_bar=True
        ) as self.window_id:
            with dpg.group(horizontal=True, parent=self.window_id):
                dpg.add_button(label="Previous", tag=f"previous-{self.window_id}")
                dpg.add_button(label="Next", tag=f"next-{self.window_id}")
                dpg.add_button(label="Close", callback=self._close)
                dpg.add_button(
                    label="Make Video", callback=lambda: VideoPrompt(directory)
                )

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
            dpg.add_item_active_handler(callback=lambda: self._load_texture(1))
        with dpg.item_handler_registry(tag=f"rewindHandler-{self.window_id}"):
            dpg.add_item_active_handler(callback=lambda: self._load_texture(-1))

        dpg.bind_item_handler_registry(
            f"next-{self.window_id}", f"playHandler-{self.window_id}"
        )
        dpg.bind_item_handler_registry(
            f"previous-{self.window_id}", f"rewindHandler-{self.window_id}"
        )

    def _load_texture(self, i):
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
