import ipywidgets as ipw
from jdaviz.app import Application
from jdaviz.configs.imviz.helper import Imviz
from jdaviz.core.config import get_configuration

__all__ = ["ViewImage"]


class ViewImage:
    """Widgets to view images and overlays."""

    def __init__(self):
        self.title = "View Image"

        # start imviz viewer with custom configuration
        self.app = Application(self._config())
        self.viz = Imviz(self.app)

        # set up viewer sizing for voila app
        self.style = (
            ".jdaviz__content--not-in-notebook "
            "{min-height: 80vh; max-height: 80vh; "
            "width:100%;"
            "padding-left: 1px !important; "
            "padding-right: 0.5px !important}"
        )

        # widgets to display
        style_html = ipw.HTML(f"<style>{self.style}</style>")
        box_layout = ipw.Layout(
            display="flex", flex_flow="column", align_items="stretch"
        )
        self.widgets = ipw.Box(children=[style_html, self.app], layout=box_layout)

    @staticmethod
    def _config():
        """
        Generate custom configuration for remote viewer.

        Local file imports and new viewer creation are removed from the
        configuration.
        """
        # based on MAST Jdaviz configuration
        cc = get_configuration("imviz")
        cc["settings"]["viewer_spec"] = cc["settings"].get("configuration", "default")
        cc["settings"]["visible"] = {
            "menu_bar": False,
            "toolbar": False,
            "tray": False,
            "tab_headers": False,
        }
        for tool in ["g-data-tools", "g-viewer-creator", "g-image-viewer-creator"]:
            if tool in cc["toolbar"]:
                cc["toolbar"].remove(tool)
        return cc
