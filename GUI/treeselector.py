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
        self.resolver = anytree.Resolver()
        a = time.perf_counter()
        self._render(root, parent)
        t = time.perf_counter() - a
        logger.info(f"Tree rendered in {t} seconds")

    def _render(self, root: anytree.Node, parent):
        if root.is_leaf:
            new_parent = dpg.add_tree_node(label=root.name, parent=parent, leaf=True)
            return
        else:
            new_parent = dpg.add_tree_node(label=root.name, parent=parent)
        for node in root.children:
            self._render(node, parent=new_parent)
