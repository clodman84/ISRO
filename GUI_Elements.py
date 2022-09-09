import dearpygui.dearpygui as dpg
import os
import logging
from glob import glob
import re
from datetime import datetime
import threading
import isro
import asyncio

logger = logging.getLogger("ISRO.GUI")
ModalHiddenList = []


def modalMessage(message):
    if message in ModalHiddenList:
        return
    with dpg.mutex():
        with dpg.window(modal=True, autosize=True, no_resize=True, no_title_bar=True) as warning:
            dpg.add_text(f"{message}", wrap=200)
            dpg.add_separator()
            dpg.add_checkbox(label="Don't show this again.", callback=lambda: ModalHiddenList.append(message))
            with dpg.group(horizontal=True):
                dpg.add_button(label="Okay", width=75, callback=lambda: dpg.delete_item(warning))
    dpg.split_frame()
    modal_dimensions = dpg.get_item_rect_size(warning)
    window_dimensions = dpg.get_item_rect_size("Primary Window")
    newPos = [(window_dimensions[i] - modal_dimensions[i]) / 2 for i in range(2)]
    dpg.configure_item(warning, pos=newPos)


class DataEntry:
    def __init__(self, parent):
        self.window_id = parent
        self.thread_running = False
        dpg.add_input_text(label="Video Name", width=300, tag="name")

        types = ("L1C_ASIA_MER_BIMG", "L1C_ASIA_MER_BIMG_KARNATAKA", "L1C_SGP_3D_IR1", "L1C_SGP_DMP", "L1C_SGP_NMP",
                 "L1C_ASIA_MER_RGB", "L1C_SGP_RGB", "L1B_STD_IR1", "L1B_STD_IR2", "L1B_STD_MIR", "L1B_STD_WV",
                 "L1B_STD_VIS", "L1B_STD_SWIR", "L1B_STD_BT_IR1_TEMP")
        dpg.add_combo(types, label="Product", tag="product", width=300)
        with dpg.tooltip(dpg.last_item()):
            dpg.add_text("This is the type of image you want to generate.")

        dpg.add_input_int(label="Framerate", tag="framerate", width=300, default_value=24)
        dpg.add_input_int(label="Chunk Size", tag="chunk_size", width=300, default_value=850)
        with dpg.tooltip(dpg.last_item()):
            dpg.add_text("The number of images that will be downloaded in parallel. "
                         "Higher is faster, lower is more stable")
        dpg.add_separator()

        now = datetime.now()
        default_date = {"year": now.year % 100 + 100, "month": now.month - 1, "month_day": now.day}
        with dpg.collapsing_header(label="Start Date", default_open=True):
            dpg.add_date_picker(tag="start", default_value=default_date)
        with dpg.collapsing_header(label="End Date", default_open=True):
            dpg.add_date_picker(tag="end", default_value=default_date)
        dpg.add_separator()

        with dpg.group(horizontal=True):
            dpg.add_button(label="Run", callback=self.run, width=80)
            with dpg.tooltip(dpg.last_item()):
                dpg.add_text("Click to make generate timelapse.")

            dpg.add_button(label="Preview", callback=self.preview, width=80)
            with dpg.tooltip(dpg.last_item()):
                dpg.add_text("Click to view the first and last image of the timelapse.")

            dpg.add_button(label="Terminate", callback=lambda: None, width=80, show=False, tag="terminate")
            with dpg.tooltip(dpg.last_item()):
                dpg.add_text("Click to terminate image download.")

    def validate(self):
        valid = [False, False, False, False]  # [name, dates, prod, chunk_size], True if the values are valid
        if self.name != '':
            valid[0] = True
        else:
            logger.error("Name cannot be empty.")

        dates = self.dates
        if dates[0] > dates[1]:
            logger.error("The timelapse cannot start before the end date.")
        elif dates[0] > datetime.now():
            logger.error("The timelapse cannot start in the future.")
        else:
            valid[1] = True

        if self.prod != '':
            valid[2] = True
        else:
            logger.error("Please select a product.")

        if self.chunk_size > 0:
            valid[3] = True
        else:
            logger.error("Chunk size cannot be zero.")

        if all(valid):
            logger.info("All inputs are valid!")
            return True
        else:
            modalMessage("Something is wrong with the values you entered.\n\nCheck the logs on the right.")
            return False

    def get_settings(self):
        return self.name, *self.dates, self.prod, self.framerate, self.chunk_size

    def run(self):
        if self.thread_running:
            logger.error("A video is already being made...")
            return

        if not self.validate():
            return
        video = isro.TimeLapse(*self.get_settings())
        vid_thread = threading.Thread(target=video.video, args=(lambda: self.thread_running,))
        self.thread_running = True
        vid_thread.daemon = True
        vid_thread.start()

        def terminate_process():
            if vid_thread.is_alive():
                logger.debug("Terminating Process...")
                self.thread_running = False
                vid_thread.join()
            dpg.hide_item("terminate")

        dpg.show_item("terminate")
        dpg.configure_item("terminate", callback=terminate_process)

    def preview(self):
        if not self.validate():
            return
        images = isro.TimeLapse("Preview", *self.get_settings()[1:])
        images.urls = [images.urls[1], images.urls[-1]]
        asyncio.run(images.getImages(lambda: True))
        ImageWindow(".\\Images\\Preview\\")

    @property
    def name(self):
        return '_'.join(dpg.get_value("name").split())  # don't want to have any spaces in the name

    @property
    def dates(self):
        data = []
        for d in ("start", "end"):
            val: dict = dpg.get_value(d)
            year = val["year"] + 1900  # years are measured from 1900
            month = val["month"] + 1
            day = val["month_day"]
            data.append(datetime(year, month, day))
        return data

    @property
    def prod(self):
        return dpg.get_value("product")

    @property
    def framerate(self):
        return dpg.get_value("framerate")

    @property
    def chunk_size(self):
        return dpg.get_value("chunk_size")


class ImageWindow:
    def __init__(self, directory):
        self.image_list = sorted(glob(f"{directory}*.jpg"))
        self.image_list.sort(key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
        if len(self.image_list) == 0:
            logger.error(f"No .jpg found in {directory}")
            modalMessage(f"No images ending in .jpg were found in {directory}, perhaps you moved them.")
            return
        self.index = 0

        with dpg.window(label='ImageWindow', pos=(20, 100), width=500, height=500, no_title_bar=True) as self.window_id:
            with dpg.group(horizontal=True, parent=self.window_id):
                dpg.add_button(label="Previous", callback=lambda: self._loadTexture(-1))
                dpg.add_button(label="Next", callback=lambda: self._loadTexture(1))
                dpg.add_button(label="Play", tag=f'play-{self.window_id}')
                dpg.add_button(label="Rewind", tag=f'rewind-{self.window_id}')
                dpg.add_button(label="Close", callback=lambda: self._close())

        with dpg.child_window(parent=self.window_id, autosize_x=True, autosize_y=True) as self.image_window:
            width, height, channels, data = dpg.load_image(self.image_list[self.index])
            with dpg.texture_registry() as self.registry:
                dpg.add_raw_texture(width, height, data, tag=f"image-{self.window_id}")
            with dpg.plot(label=self.image_list[self.index], parent=self.image_window, width=-1, height=-1,
                          equal_aspects=True) as self.image:
                # Dummy bar series to trick the scale and zoom out to fit the image
                dpg.add_plot_axis(dpg.mvYAxis, tag=f'y-{self.window_id}')
                dpg.add_bar_series([-width / 2, 0, width / 2], [0, 0, 0], weight=1, parent=f"y-{self.window_id}")
                dpg.draw_image(f"image-{self.window_id}", (-width / 2, height / 2), (width / 2, -height / 2))

        with dpg.item_handler_registry(tag=f"playHandler-{self.window_id}"):
            dpg.add_item_active_handler(callback=lambda: self._loadTexture(1))
        with dpg.item_handler_registry(tag=f"rewindHandler-{self.window_id}"):
            dpg.add_item_active_handler(callback=lambda: self._loadTexture(-1))

        dpg.bind_item_handler_registry(f'play-{self.window_id}', f'playHandler-{self.window_id}')
        dpg.bind_item_handler_registry(f'rewind-{self.window_id}', f'rewindHandler-{self.window_id}')

    def _loadTexture(self, i):
        if (self.index > 0 and i == -1) or (self.index < len(self.image_list) - 1 and i == 1):
            self.index += i
        filename = self.image_list[self.index]
        _, _, _, data = dpg.load_image(filename)
        dpg.set_value(f'image-{self.window_id}', data)
        dpg.configure_item(self.image, label=filename)

    def _close(self):
        dpg.delete_item(self.window_id)
        dpg.delete_item(f"image-{self.window_id}")
        dpg.delete_item(self.registry)


class Explorer:
    def __init__(self, parent):
        self.window_id = parent
        dpg.add_button(label='Refresh', callback=lambda: self._loadDirectories(), parent=self.window_id)
        imageFolders = []
        if os.path.isdir('.\\Images'):
            imageFolders = os.listdir('.\\Images')
        if not imageFolders:
            dpg.delete_item('ExpWindow')
            logger.warning("No image folders were found.")
            with dpg.child_window(parent=self.window_id, autosize_x=True, autosize_y=True, tag='ExpWindow'):
                dpg.add_text("Make some videos and they will appear here.", wrap=0)
            return

        with dpg.child_window(parent=self.window_id, autosize_x=True, autosize_y=True, tag='ExpWindow') as window:
            with dpg.table(label=None, parent=window, header_row=False, row_background=True,
                           borders_innerH=True, borders_outerH=True, borders_innerV=True, borders_outerV=True,
                           delay_search=True) as self.table:
                dpg.add_table_column(width_fixed=True)
                dpg.add_table_column(width_fixed=False)
                dpg.add_table_column(width_fixed=True)
                for index, directory in enumerate(imageFolders):
                    with dpg.table_row():
                        dpg.add_text(str(index + 1))
                        dpg.add_text(directory)
                        dpg.add_button(label='View', user_data=directory,
                                       callback=lambda s, a, u: ImageWindow(f".\\Images\\{u}\\"))

    def _loadDirectories(self):
        imageFolders = []
        if os.path.isdir('.\\Images'):
            imageFolders = os.listdir('.\\Images')
        if not imageFolders:
            dpg.delete_item('ExpWindow')
            logger.warning("No image folder were found.")
            with dpg.child_window(parent=self.window_id, autosize_x=True, autosize_y=True, tag='ExpWindow'):
                dpg.add_text("Make some videos and they will appear here.", wrap=0)
            return

        dpg.delete_item(self.table)
        with dpg.table(label=None, parent="ExpWindow", header_row=False, row_background=True, borders_innerH=True,
                       borders_outerH=True, borders_innerV=True, borders_outerV=True, delay_search=True) as self.table:
            dpg.add_table_column(width_fixed=True)
            dpg.add_table_column(width_fixed=False)
            dpg.add_table_column(width_fixed=True)
            for index, directory in enumerate(imageFolders):
                with dpg.table_row():
                    dpg.add_text(str(index + 1))
                    dpg.add_text(directory)
                    dpg.add_button(label='View', user_data=directory,
                                   callback=lambda s, a, u: ImageWindow(f".\\Images\\{u}\\"))


class Logger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.log_level = 0
        self._auto_scroll = True
        self.filter_id = None
        self.count = 0
        self.flush_count = 1000
        self.window_id = parent

        with dpg.group(horizontal=True, parent=self.window_id):
            dpg.add_checkbox(label="Auto-scroll", default_value=True,
                             callback=lambda sender: self.auto_scroll(dpg.get_value(sender)))
            dpg.add_button(label="Clear", callback=lambda: dpg.delete_item(self.filter_id, children_only=True))

        dpg.add_input_text(label="Filter (inc, -exc)",
                           callback=lambda sender: dpg.set_value(self.filter_id, dpg.get_value(sender)),
                           parent=self.window_id)
        self.child_id = dpg.add_child_window(parent=self.window_id, autosize_x=True, autosize_y=True)
        self.filter_id = dpg.add_filter_set(parent=self.child_id)

        with dpg.theme() as self.debug_theme:
            with dpg.theme_component(0):
                dpg.add_theme_color(dpg.mvThemeCol_Text, (64, 128, 255, 255))

        with dpg.theme() as self.info_theme:
            with dpg.theme_component(0):
                dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255, 255))

        with dpg.theme() as self.warning_theme:
            with dpg.theme_component(0):
                dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 0, 255))

        with dpg.theme() as self.error_theme:
            with dpg.theme_component(0):
                dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 0, 0, 255))

        with dpg.theme() as self.critical_theme:
            with dpg.theme_component(0):
                dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 0, 0, 255))

    def auto_scroll(self, value):
        self._auto_scroll = value

    def _log(self, message, level):
        """Different theme for each level"""
        if level < self.log_level:
            return

        self.count += 1

        if self.count > self.flush_count:
            self.clear_log()

        theme = self.info_theme
        if level == 10:
            theme = self.debug_theme
        elif level == 20:
            pass
        elif level == 30:
            theme = self.warning_theme
        elif level == 40:
            theme = self.error_theme
        elif level == 50:
            theme = self.critical_theme

        new_log = dpg.add_text(message, parent=self.filter_id, filter_key=message, wrap=0)
        dpg.bind_item_theme(new_log, theme)
        if self._auto_scroll:
            dpg.set_y_scroll(self.child_id, -1.0)

    def emit(self, record):
        string = self.format(record)
        self._log(string, record.levelno)

    def clear_log(self):
        dpg.delete_item(self.filter_id, children_only=True)
        self.count = 0
