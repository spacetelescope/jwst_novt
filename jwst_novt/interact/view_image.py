import ipywidgets as ipw
import jdaviz as jd
from jdaviz.configs.imviz.plugins.viewers import ImvizImageView
from jdaviz.core.events import NewViewerMessage

from jwst_novt.constants import VIEWER_NAME

__all__ = ["ViewImage"]


class ViewImage:
    """Widgets to view images and overlays."""

    def __init__(self):
        self.title = "View Image"

        # start the jdaviz app
        self.viz = jd.new_app()

        # Add a jdaviz viewer so that we can pre-populate it in the app
        # without having to first upload an image.
        nv = self.viz._app._on_new_viewer(
            NewViewerMessage(ImvizImageView, data=None, sender=self.viz._app),
            vid=VIEWER_NAME,
            name=VIEWER_NAME,
        )

        nv.toggle_focus_mode(focus=True)

        # set up viewer sizing for voila app
        self.style = (
            ".jdaviz__content--not-in-notebook "
            "{min-height: 80vh; max-height: 80vh; "
            "width:100%;"
            "padding-left: 1px !important; "
            "padding-right: 0.5px !important}"
        )

        # Without a defined height in jdaviz>=5.1, the veiwer scales to
        # very small windows.
        style_html = ipw.HTML(f"<style>{self.style}</style>")
        box_layout = ipw.Layout(
            display="flex", flex_flow="column", align_items="stretch", height="600px"
        )
        self.widgets = ipw.Box(children=[style_html, self.viz._app], layout=box_layout)
