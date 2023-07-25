import logging
import time

import anytree
import dearpygui.dearpygui as dpg

logger = logging.getLogger("GUI.TreeSelector")


class TreeSelector:
    """
    Takes in any arbitrary tree and then creates a dynamic settings window, that ultimately returns a leaf node.
    """

    def __init__(self, root: anytree.Node, parent):
        self.parent = parent
        self.root = root
        self.selected_node = None
        a = time.perf_counter()
        self._render(root, parent)
        t = time.perf_counter() - a
        logger.debug(f"Tree rendered in {t} seconds")

    def click_callback(self, sender, app_data, user_data):
        self.selected_node = user_data

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
