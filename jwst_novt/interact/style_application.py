import copy

import ipywidgets as ipw
from traitlets import TraitError

from jwst_novt.constants import CONFIGURABLE
from jwst_novt.interact.utils import read_image

__all__ = ["StyleApplication"]


class StyleApplication:
    """Widgets to lay out and style the default application."""

    def __init__(
        self,
        image_viewer,
        uploaded_data,
        nirspec_controls,
        nircam_controls,
        timeline_controls,
        overlay_controls,
        save_controls,
        context="notebook",
    ):
        # internal data
        self.context = context
        self.title = "JWST NIRSpec Observation Visualization Tool (NOVT)"

        # store all the control widgets
        self.image_viewer = image_viewer
        self.uploaded_data = uploaded_data
        self.nirspec_controls = nirspec_controls
        self.nircam_controls = nircam_controls
        self.timeline_controls = timeline_controls
        self.save_controls = save_controls

        # link timeline controls to other changes in app
        ipw.dlink((self.nirspec_controls, "ra"), (self.timeline_controls, "ra"))
        ipw.dlink((self.nirspec_controls, "dec"), (self.timeline_controls, "dec"))
        ipw.dlink(
            (self.nirspec_controls, "color_primary"),
            (self.timeline_controls, "nirspec_color"),
        )
        ipw.dlink(
            (self.nircam_controls, "color_primary"),
            (self.timeline_controls, "nircam_color"),
        )
        ipw.dlink(
            (self.uploaded_data, "image_file_name"), (self.timeline_controls, "center")
        )

        # link configuration upload to controls
        self.uploaded_data.observe(self.update_from_config, "configuration")

        # link controls to config dict
        self.uploaded_data.observe(self.update_to_config)
        self.nirspec_controls.observe(self.update_to_config)
        self.nircam_controls.observe(self.update_to_config)
        self.timeline_controls.observe(self.update_to_config)
        self.save_controls.observe(self.update_to_config)

        # layouts
        self.row_layout = ipw.Layout(
            display="flex",
            flex_flow="row",
            align_items="center",
            justify_content="space-between",
        )
        self.column_layout = ipw.Layout(
            display="flex", flex_flow="column", align_items="stretch"
        )

        # header banner
        self.jwst_logo = read_image("JWSTlogo.png")
        self.stsci_logo = read_image("STScIlogo.png")
        self.docs_link = (
            "https://jwst-docs.stsci.edu/jwst-other-tools/"
            "nirspec-observation-visualization-tool-help"
        )
        self.header = ipw.Box(
            children=[
                ipw.HTML(
                    f"<h1>{self.title}</h1>"
                    f"<p>For usage information, see the "
                    f'<a style="color: #106ba3" '
                    f'href="{self.docs_link}"'
                    f'target="_blank">NOVT Documentation.</a></p>'
                ),
                ipw.HBox(
                    children=[
                        nirspec_controls.logo,
                        nircam_controls.logo,
                        self.jwst_logo,
                        self.stsci_logo,
                    ]
                ),
            ],
            layout=self.row_layout,
        )

        # footer links
        self.footer = ipw.Box(children=[], layout=self.row_layout)

        children = [
            self.header,
            uploaded_data.widgets,
            nirspec_controls.widgets,
            nircam_controls.widgets,
            timeline_controls.widgets,
            save_controls.widgets,
        ]
        if "notebook" in self.context:
            # in a notebook, display the viewer inline at
            # 100% of cell width
            width = "100%"
            children.extend([overlay_controls.widgets, image_viewer.widgets])
        else:
            # in a web app, collapse the viewer and controls and set
            # width to 95% of viewer width
            width = "95vw"
            viewer_with_controls = ipw.Box(
                children=[overlay_controls.widgets, image_viewer.widgets],
                layout=self.column_layout,
            )
            viewer_tab = ipw.Accordion(
                children=[viewer_with_controls],
                layout=self.column_layout,
                titles=[image_viewer.title],
                selected_index=0,
            )
            children.append(viewer_tab)
        children.append(self.footer)

        # set layout
        self.top_layout = ipw.Layout(
            display="flex",
            flex_flow="column",
            align_items="stretch",
            width=width,
            padding="0px",
            margin="0px",
        )

        self.widgets = ipw.Box(children=children, layout=self.top_layout)

    def update_from_config(self, *args, **kwargs):
        """Update control values from input configuration."""
        config = copy.deepcopy(self.uploaded_data.configuration)

        controls = {
            "nirspec": self.nirspec_controls,
            "nircam": self.nircam_controls,
            "catalog": self.uploaded_data,
            "timeline": self.timeline_controls,
            "save": self.save_controls,
        }
        for section in config:
            for key, value in config[section].items():
                control = controls[section]
                if control.has_trait(key):
                    try:
                        setattr(control, key, value)
                    except (AttributeError, ValueError, TypeError, TraitError):
                        continue

    def update_to_config(self, change):
        """Update configuration dictionary from changed control values."""
        config = self.uploaded_data.configuration
        sections = {
            "nirspec": self.nirspec_controls,
            "nircam": self.nircam_controls,
            "catalog": self.uploaded_data,
            "timeline": self.timeline_controls,
            "save": self.save_controls,
        }
        for section, control in sections.items():
            if change["owner"] is control and change["name"] in CONFIGURABLE[section]:
                # check for whitelisted names
                if section not in config:
                    config[section] = {}
                config[section][change["name"]] = change["new"]
