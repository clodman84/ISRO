import logging

import dearpygui.dearpygui as dpg

ModalHiddenList = []


def modalMessage(message):
    if message in ModalHiddenList:
        return
    with dpg.mutex():
        with dpg.window(
            modal=True, autosize=True, no_resize=True, no_title_bar=True
        ) as warning:
            dpg.add_text(f"{message}", wrap=200)
            dpg.add_separator()
            dpg.add_checkbox(
                label="Don't show this again.",
                callback=lambda: ModalHiddenList.append(message),
            )
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Okay", width=75, callback=lambda: dpg.delete_item(warning)
                )
    dpg.split_frame()
    modal_dimensions = dpg.get_item_rect_size(warning)
    window_dimensions = dpg.get_item_rect_size("Primary Window")
    newPos = [(window_dimensions[i] - modal_dimensions[i]) / 2 for i in range(2)]
    dpg.configure_item(warning, pos=newPos)


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
            dpg.add_checkbox(
                label="Auto-scroll",
                default_value=True,
                callback=lambda sender: self.auto_scroll(dpg.get_value(sender)),
            )
            dpg.add_button(
                label="Clear",
                callback=lambda: dpg.delete_item(self.filter_id, children_only=True),
            )

        dpg.add_input_text(
            label="Filter (inc, -exc)",
            callback=lambda sender: dpg.set_value(
                self.filter_id, dpg.get_value(sender)
            ),
            parent=self.window_id,
        )
        self.child_id = dpg.add_child_window(
            parent=self.window_id, autosize_x=True, autosize_y=True
        )
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
            modalMessage(message)
        elif level == 50:
            theme = self.critical_theme

        new_log = dpg.add_text(
            message, parent=self.filter_id, filter_key=message, wrap=0
        )
        dpg.bind_item_theme(new_log, theme)
        if self._auto_scroll:
            dpg.set_y_scroll(self.child_id, -1.0)

    def emit(self, record):
        string = self.format(record)
        self._log(string, record.levelno)

    def clear_log(self):
        dpg.delete_item(self.filter_id, children_only=True)
        self.count = 0
