import ipywidgets as ipw
from jdaviz.app import PrivateApplication
from jdaviz.configs.deconfigged.helper import App
from jdaviz.configs.default.plugins.viewers import JdavizViewerWindow
from jdaviz.core.config import get_configuration

__all__ = ["ViewImage"]


class ViewImage:
    """Widgets to view images and overlays."""

    def __init__(self):
        self.title = "View Image"

        # start jdaviz app with custom configuration
        self.app = PrivateApplication(self._config())
        self.viz = App(app=self.app)

        # Set the pre-configured viewer as the default viewer
        self.viz._default_viewer = self.viz._app.get_viewer_by_id(
            f"{self.viz._app.config}-0"
        )
        self.viz.default_viewer = JdavizViewerWindow(
            self.viz._default_viewer, app=self.viz._app
        ).user_api

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
        cc = get_configuration("deconfigged")
        cc["settings"]["viewer_spec"] = cc["settings"].get("configuration", "default")
        cc["settings"]["visible"] = {
            "menu_bar": False,
            "toolbar": False,
            "tray": False,
            "tab_headers": False,
        }

        # Configure viewer area with a single imviz-image-viewer
        # so that we can pre-populate it in the app without
        # having to first upload an image.
        viewer = {
            "name": "deconfigged-0",
            "plot": "imviz-image-viewer",
            "reference": "deconfigged-0",
        }
        child = {"container": "row", "viewers": [viewer]}
        cc["viewer_area"] = [{"container": "col", "children": [child]}]

        return cc
