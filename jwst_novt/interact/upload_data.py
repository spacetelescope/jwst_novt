import warnings

import ipyvuetify.extra as ve
import ipywidgets as ipw
import yaml
from astropy.io import fits
from jdaviz.core.events import SnackbarMessage
from traitlets import Any, Bool, Dict, HasTraits, Unicode

from jwst_novt.constants import DEFAULT_COLOR

__all__ = ["UploadData"]


class UploadData(HasTraits):
    """Widgets to upload user data files."""

    image_file_name = Unicode(None, allow_none=True).tag(sync=True)
    catalog_file = Any(None, allow_none=True).tag(sync=True)
    color_primary = Unicode("orange").tag(sync=True)
    color_alternate = Unicode("purple").tag(sync=True)
    has_wcs = Bool(default_value=False).tag(sync=True)
    has_catalog = Bool(default_value=False).tag(sync=True)
    configuration = Dict({}).tag(sync=True)

    def __init__(self, viz, *, allow_configuration=False):
        super().__init__(self)

        # internal data
        self.title = "Upload Data"
        self.viz = viz
        self.viewer = viz.default_viewer
        self.image_files = {}
        self.allow_data_replace = False

        # make widgets to display
        self.image_label = ipw.Label(
            "Image file (.fits):",
            style={"font_weight": "bold"},
            layout=ipw.Layout(width="150px"),
            tooltip="FITS image for display, with associated WCS, in the "
            "primary or SCI extension",
        )
        self.image_file_upload = ve.FileInput(
            accept=".fits", multiple=False, layout=ipw.Layout(width="500px")
        )

        self.catalog_label = ipw.Label(
            "Catalog file (.radec):",
            style={"font_weight": "bold"},
            layout=ipw.Layout(width="150px"),
            tooltip="Text file with 2 columns (RA, Dec), "
            "or 3 (RA, Dec, Flag), "
            "where Flag is 'P' for primary or 'F' for filler sources",
        )
        self.catalog_file_upload = ve.FileInput(
            accept=".radec", multiple=False, layout=ipw.Layout(width="500px")
        )

        if allow_configuration:
            self.config_label = ipw.Label(
                "Config file (.yaml):",
                style={"font_weight": "bold"},
                layout=ipw.Layout(width="150px"),
                tooltip="YAML file specifying field values for NOVT configuration.",
            )
            self.config_file_upload = ve.FileInput(
                accept=".yaml", multiple=False, layout=ipw.Layout(width="500px")
            )
        else:
            self.config_label = None
            self.config_file_upload = None

        self.color_pickers = [
            ipw.ColorPicker(
                description="Primary source color",
                value=DEFAULT_COLOR["Primary Sources"],
                style={"description_width": "initial"},
                tooltip="Color for primary source catalog overlays",
            ),
            ipw.ColorPicker(
                description="Filler source color",
                value=DEFAULT_COLOR["Filler Sources"],
                style={"description_width": "initial"},
                tooltip="Color for filler source catalog overlays",
            ),
        ]
        ipw.link((self.color_pickers[0], "value"), (self, "color_primary"))
        ipw.link((self.color_pickers[1], "value"), (self, "color_alternate"))

        # layout widgets
        button_layout = ipw.Layout(
            display="flex",
            flex_flow="row",
            align_items="center",
            justify_content="flex-start",
            padding="0px",
        )
        box_layout = ipw.Layout(
            display="flex", flex_flow="column", align_items="stretch"
        )

        b1 = ipw.Box(
            children=[self.image_label, self.image_file_upload], layout=button_layout
        )
        b2 = ipw.Box(
            children=[self.catalog_label, self.catalog_file_upload],
            layout=button_layout,
        )
        children = [b1, b2]
        if allow_configuration:
            b3 = ipw.Box(
                children=[self.config_label, self.config_file_upload],
                layout=button_layout,
            )
            children.append(b3)

        appearance_tab = ipw.Accordion(
            children=[ipw.Box(children=self.color_pickers, layout=button_layout)],
            titles=["Appearance"],
        )
        children.append(appearance_tab)

        box = ipw.Box(children=children, layout=box_layout)
        self.widgets = ipw.Accordion(children=[box], titles=[self.title])

        # connect callbacks
        self.image_file_upload.observe(self.load_image, names="file_info")
        self.catalog_file_upload.observe(self.load_catalog, names="file_info")
        if allow_configuration:
            self.config_file_upload.observe(self.load_config, names="file_info")

    def _load_hdul_in_viz(self, uploaded_file):
        """
        Load a FITS file into Imviz.

        Parameters
        ----------
        uploaded_file : dict-like
            File structure corresponding to uploaded data in
            the FileInput widget.
        """
        hdul = None
        try:
            hdul = fits.open(uploaded_file["file_obj"])
            self.viz.load_data(hdul, data_label=uploaded_file["name"])

            wcs = self.viewer.state.reference_data.coords
            if wcs is None or not wcs.has_celestial:
                msg_text = (
                    "No WCS associated with image. "
                    "Overlay functions will not be "
                    "available."
                )
                msg = SnackbarMessage(msg_text, sender=self, color="warning")
                self.viz.app.hub.broadcast(msg)
            else:
                self.has_wcs = True
                self.image_file_name = uploaded_file["name"]
        except Exception as err:
            msg_text = f"Error loading image: {err}"
            msg = SnackbarMessage(msg_text, sender=self, color="warning")
            self.viz.app.hub.broadcast(msg)
        finally:
            if hdul is not None:
                hdul.close()

    def load_image(self, change):
        """
        Watch for newly uploaded or removed files.

        New images are loaded into the viewer. Removed files are removed
        from the viewer. The loaded data remains accessible to the viewer
        and can be manually reloaded by the user if desired.

        Due to limited support for data removal in Imviz, the UI currently
        supports uploading only one image per session. After a successful
        upload, the file input field is disabled. If desired, this behavior
        can be changed by setting the `allow_data_replace` attribute to True.
        If set, data can be removed from the viewer and replaced with a new
        image, but the old data will not necessarily be released from memory.
        """
        self.has_wcs = False
        self.image_file_name = None

        # watch for uploaded files
        change["owner"].disabled = True
        if len(change["old"]) > 0:
            # clear any removed data from viewer
            for old_file in change["old"]:
                for data_set in self.viz.app.data_collection:
                    if data_set.label.startswith(old_file["name"]):
                        self.viz.app.remove_data_from_viewer(
                            self.viewer.reference_id, data_set.label
                        )
                        self.viz.app.data_collection.remove(data_set)
                del self.image_files[old_file["name"]]
        if len(change["new"]) > 0:
            uploaded_files = change["owner"].get_files()
            if len(uploaded_files) > 0:
                for uploaded_file in uploaded_files:
                    self.image_files[uploaded_file["name"]] = uploaded_file
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        self._load_hdul_in_viz(uploaded_file)
        if self.allow_data_replace or len(self.image_files) == 0:
            change["owner"].disabled = False

    def load_catalog(self, change):
        """
        Watch for newly uploaded or removed catalog files.

        Newly uploaded files are set in the `catalog_file`
        traitlet. If files are removed, the traitlet is set to None.
        """
        self.has_catalog = False

        # watch for uploaded files
        change["owner"].disabled = True
        if len(change["new"]) > 0:
            uploaded_files = change["owner"].get_files()
            if len(uploaded_files) > 0:
                self.has_catalog = True
                self.catalog_file = uploaded_files[0]
        elif len(change["old"]) > 0:
            self.catalog_file = None
        change["owner"].disabled = False

    def load_config(self, change):
        """
        Watch for newly uploaded or removed configuration files.

        Newly uploaded files are immediately read in to the configuration
        traitlet. If files are removed, the traitlet is set to None.
        """
        # watch for new files
        change["owner"].disabled = True
        if len(change["new"]) > 0:
            uploaded_files = change["owner"].get_files()
            if len(uploaded_files) > 0:
                try:
                    new_config = yaml.safe_load(uploaded_files[0]["file_obj"])
                    self.configuration = new_config
                except Exception as err:
                    msg_text = f"Error loading configuration: {err}"
                    msg = SnackbarMessage(msg_text, sender=self, color="warning")
                    self.viz.app.hub.broadcast(msg)

        change["owner"].disabled = False
