import dearpygui.dearpygui as dpg
from GUI_Elements import Logger, Explorer, DataEntry
import logging


def main():
    dpg.create_context()
    dpg.create_viewport(title="Timelapse Generator", width=896, height=600)
    AppLog = logging.getLogger("ISRO")
    AppLog.setLevel(logging.INFO)
    formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")

    with dpg.window(tag="Primary Window"):
        with dpg.group(horizontal=True):
            with dpg.child_window(width=450) as dataWindow:
                DataEntry(parent=dataWindow)
            with dpg.group():
                with dpg.child_window(height=300) as loggerWindow:
                    log = Logger(parent=loggerWindow)
                    log.setFormatter(formatter)
                    AppLog.addHandler(log)
                with dpg.child_window() as explorerWindow:
                    Explorer(parent=explorerWindow)

    def resizeWindows():
        width, height = dpg.get_item_rect_size("Primary Window")
        dpg.configure_item(loggerWindow, height=height / 2)
        dpg.configure_item(dataWindow, width=width / 2)

    with dpg.item_handler_registry(tag="resizeHandler"):
        dpg.add_item_resize_handler(callback=resizeWindows)

    dpg.bind_item_handler_registry("Primary Window", "resizeHandler")
    dpg.setup_dearpygui()
    dpg.set_primary_window("Primary Window", True)
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    main()
