import logging
import pathlib

import anytree
import dearpygui.dearpygui as dpg

from .treeselector import TreeSelector
from .video import PreviewWindow

logger = logging.getLogger("GUI.Explorer")


def load_filesystem_tree(path: pathlib.Path, parent: anytree.Node, is_root=False):
    if path.is_file():
        return
    if not is_root:
        parent = anytree.Node(path.name, parent=parent)
    for p in path.iterdir():
        load_filesystem_tree(p, parent)


class Explorer:
    def __init__(self, parent):
        self.window_id = parent
        self.tree_window = None
        dpg.add_button(
            label="Refresh", callback=self._load_directories, parent=self.window_id
        )
        self._load_directories()

    @staticmethod
    def make_image_window(node: anytree.Node):
        directory = pathlib.Path("/".join(n.name for n in node.path))  # type: ignore
        PreviewWindow(directory)

    def _load_directories(self):
        folder = pathlib.Path("./Images")
        if not folder.exists():
            folder.mkdir()
        root = anytree.Node("Images")
        load_filesystem_tree(folder, root, is_root=True)
        if self.tree_window:
            dpg.delete_item(self.tree_window)
        with dpg.child_window(parent=self.window_id) as self.tree_window:
            TreeSelector(root, parent=self.tree_window, callback=self.make_image_window)
        logger.debug("Refreshed explorer window")
