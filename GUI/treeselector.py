import logging
import time

import anytree
import dearpygui.dearpygui as dpg

logger = logging.getLogger("GUI.TreeSelector")


class TreeError(Exception):
    pass


class TreeSelector:
    """
    Takes in any arbitrary tree and then creates a dynamic settings window, that ultimately returns a leaf node.
    """

    def __init__(self, root: anytree.Node, parent):
        self.parent = parent
        self.root = root
        self.selected_node = None
        a = time.perf_counter()
        self.status_text = dpg.add_text(
            "Select a product type from the dropdown menu...", parent=parent
        )
        dpg.add_separator()
        self._render(root, parent)
        t = time.perf_counter() - a
        logger.debug(f"Tree rendered in {t} seconds")

    def click_callback(self, sender, app_data, user_data: anytree.Node):
        self.selected_node = user_data
        dpg.set_value(self.status_text, f"Selected Product: {user_data.name}")

    def get_node(self):
        if not self.selected_node:
            raise TreeError(f"Nothing was selected from {self.root.name} tree!")
        return self.selected_node

    def _render(self, root: anytree.Node, parent):
        if root.is_leaf:
            dpg.add_button(
                label=root.name,
                width=450,
                parent=parent,
                user_data=root,
                callback=self.click_callback,
            )
            return
        else:
            new_parent = dpg.add_tree_node(label=root.name, parent=parent)
        for node in root.children:
            self._render(node, parent=new_parent)
