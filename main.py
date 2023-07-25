import logging

import dearpygui.dearpygui as dpg

import GUI
import Timelapse


def main():
    dpg.create_context()
    dpg.create_viewport(title="Timelapse Generator", width=896, height=600)
    TimelapseLogger = logging.getLogger("Timelapse")
    GUI_Logger = logging.getLogger("GUI")
    TimelapseLogger.setLevel(logging.DEBUG)
    GUI_Logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")

    with dpg.window(tag="Primary Window"):
        with dpg.menu_bar():
            with dpg.menu(label="Tools"):
                dpg.add_menu_item(
                    label="Show Item Registry", callback=dpg.show_item_registry
                )
                dpg.add_menu_item(
                    label="Show Performance Metrics", callback=dpg.show_metrics
                )
                dpg.add_menu_item(label="Show Debug", callback=dpg.show_debug)

        with dpg.table(
            parent="Primary Window", resizable=True, reorderable=True, hideable=True
        ):
            dpg.add_table_column(label="Logs")
            dpg.add_table_column(label="Product Selector")
            with dpg.table_row():
                with dpg.group():
                    with dpg.child_window(height=300) as logger_window:
                        log = GUI.Logger(parent=logger_window)
                        log.setFormatter(formatter)
                        TimelapseLogger.addHandler(log)
                        GUI_Logger.addHandler(log)
                    with dpg.child_window() as explorer_window:
                        GUI.Explorer(parent=explorer_window)
                with dpg.child_window() as product_selector_window:
                    settings_root = Timelapse.make_settings_tree()
                    GUI.TreeSelector(settings_root, parent=product_selector_window)

    dpg.setup_dearpygui()
    dpg.set_primary_window("Primary Window", True)
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    main()
