import contextlib

import ipywidgets as ipw
from jdaviz.core.events import SnackbarMessage

from jwst_novt.interact import display as nd
from jwst_novt.interact.utils import ToggleButton

__all__ = ["ShowOverlays"]


class ShowOverlays:
    """Widgets to control showing, hiding, and updating image overlays."""

    def __init__(self, viz, uploaded_data, nirspec=None, nircam=None):
        # internal data
        self.title = "Show Overlays"
        self.viz = viz
        self.viewer = viz.default_viewer
        self.uploaded_data = uploaded_data
        self.nirspec_controls = nirspec
        self.nircam_controls = nircam
        self.instruments = []
        self.catalogs = ["primary", "filler"]
        self.catalog_markers = {}
        self.footprint_patches = {}

        # toggle catalog overlays
        self.catalog_buttons = []
        for name in self.catalogs:
            button = ToggleButton(children=[f"{name.capitalize()} sources"], value=name)
            button.on_event("click", self.toggle_catalog)
            self.catalog_buttons.append(button)

        # watch for changes to uploaded files
        self.uploaded_data.image_file_upload.observe(
            self.clear_overlays, names="file_info"
        )
        self.uploaded_data.observe(self.clear_catalog, names="catalog_file")
        self.uploaded_data.observe(
            self.update_catalog, names=["color_primary", "color_alternate"]
        )

        # watch for changes to update footprint
        if self.nirspec_controls is not None:
            self.instruments.append("NIRSpec")
            self.nirspec_controls.observe(
                self.update_nirspec_footprint,
                names=["ra", "dec", "pa", "color_primary", "alpha"],
            )
        if self.nircam_controls is not None:
            self.instruments.extend(["NIRCam Short", "NIRCam Long"])
            self.nircam_controls.observe(
                self.update_nircam_footprint,
                names=["ra", "dec", "pa", "color_primary", "color_alternate", "alpha"],
            )
            self.nircam_controls.observe(self.update_nircam_dither, names=["dither"])
            self.nircam_controls.observe(
                self.update_nircam_mosaic, names=["mosaic", "mosaic_v2", "mosaic_v3"]
            )

        # toggle footprint overlays
        self.footprint_buttons = []
        for name in self.instruments:
            button = ToggleButton(children=[name], value=name)
            button.on_event("click", self.toggle_footprint)

            # if uploaded data already has a wcs, reset the button state
            if uploaded_data.has_wcs:
                button.reset()

            self.footprint_buttons.append(button)

        # layout widgets
        button_layout = ipw.Layout(
            display="flex", flex_flow="row", justify_content="flex-start"
        )
        self.widgets = ipw.Box(
            children=self.footprint_buttons + self.catalog_buttons, layout=button_layout
        )

    def clear_overlays(self, *args):
        """Remove existing catalog markers when a catalog file is loaded."""
        # clear any old overlays on change in the image file
        for instrument in self.footprint_patches:
            nd.remove_bqplot_patches(
                self.viewer.figure, self.footprint_patches[instrument]
            )
        self.footprint_patches = {}

        for button in self.footprint_buttons:
            if self.uploaded_data.has_wcs:
                button.reset()
            else:
                button.disabled = True

        # also clear catalog
        self.clear_catalog()

    def _load_catalog(self):
        """
        Load catalog from file.

        Returns
        -------
        status : bool
            True if load succeeded, False otherwise
        """
        available = self.uploaded_data.has_wcs and self.uploaded_data.has_catalog
        if not available:
            return False

        status = True
        wcs = self.viewer.state.reference_data.coords
        catalog_file = self.uploaded_data.catalog_file
        if catalog_file is not None:
            if isinstance(catalog_file, str):
                # assume it's a path to a file on disk
                catalog = catalog_file
            else:
                catalog = catalog_file["file_obj"]
            try:
                primary, filler = nd.bqplot_catalog(
                    self.viewer.figure,
                    catalog,
                    wcs,
                    visible=False,
                    colors=[
                        self.uploaded_data.color_primary,
                        self.uploaded_data.color_alternate,
                    ],
                )
            except Exception as err:
                status = False
                msg_text = f"Error reading catalog: {err}"
                msg = SnackbarMessage(msg_text, sender=self, color="warning")
                self.viz.app.hub.broadcast(msg)
            else:
                self.catalog_markers["primary"] = primary
                self.catalog_markers["filler"] = filler
            finally:  # pragma: no cover
                with contextlib.suppress(Exception):
                    catalog.seek(0)
        return status

    def clear_catalog(self, *args):
        """Remove existing catalog markers when a catalog file is loaded."""
        # clear any old markers on change in the catalog file
        if "primary" in self.catalog_markers:
            nd.remove_bqplot_patches(
                self.viewer.figure, [self.catalog_markers["primary"]]
            )
            del self.catalog_markers["primary"]
        if "filler" in self.catalog_markers:
            nd.remove_bqplot_patches(
                self.viewer.figure, [self.catalog_markers["filler"]]
            )
            del self.catalog_markers["filler"]

        # load catalog if it is available
        available = self._load_catalog()

        # enable buttons only if catalog is available
        for button in self.catalog_buttons:
            if available:
                button.reset()
            else:
                button.disabled = True

    def update_catalog(self, *args):
        """Update existing catalog markers when a new color is chosen."""
        # clear any old markers on change in the catalog file
        if "primary" in self.catalog_markers:
            self.catalog_markers["primary"].colors = [self.uploaded_data.color_primary]
        if "filler" in self.catalog_markers:
            self.catalog_markers["filler"].colors = [self.uploaded_data.color_alternate]

    def toggle_catalog(self, button, *args):
        """Toggle catalog visibility."""
        name = button.value
        if button.is_active():
            if name in self.catalog_markers:
                self.catalog_markers[name].visible = True
                button.toggle()
        else:
            button.toggle()
            if name in self.catalog_markers:
                self.catalog_markers[name].visible = False

    def toggle_footprint(self, button, *args):
        """Toggle footprint visibility."""
        if button.is_active():
            if not self.uploaded_data.has_wcs:
                return
            button.toggle()

            if "NIRS" in button.value:
                controls = self.nirspec_controls
            else:
                controls = self.nircam_controls
            self._show_footprint([button.value], controls)
        else:
            button.toggle()
            nd.remove_bqplot_patches(
                self.viewer.figure, self.footprint_patches[button.value]
            )
            del self.footprint_patches[button.value]

    def all_patches(self):
        """Return all patches currently tracked."""
        patches = []
        for patch_set in self.footprint_patches.values():
            for patch in patch_set:
                patches.append(patch)
        for patch in self.catalog_markers.values():
            patches.append(patch)
        return patches

    def _show_footprint(self, instruments, controls):
        """
        Show an instrument footprint.

        Removes any existing patches for the instrument and creates new
        ones from the `controls` configuration.

        Parameters
        ----------
        instruments : list of str
            The instruments to show.
        controls : jwst_novt.interact.ControlInstruments
            Controls widgets associated with the instrument.
        """
        if not self.uploaded_data.has_wcs:
            return
        wcs = self.viewer.state.reference_data.coords
        with nd.hold_all_sync(self.all_patches()):
            for instrument in instruments:
                # any old patches need to be removed first
                if instrument in self.footprint_patches:
                    nd.remove_bqplot_patches(
                        self.viewer.figure, self.footprint_patches[instrument]
                    )

                # make new patches
                if "long" in instrument.lower():
                    color = controls.color_alternate
                else:
                    color = controls.color_primary
                add_mosaic = controls.mosaic == "Yes"
                self.footprint_patches[instrument] = nd.bqplot_footprint(
                    self.viewer.figure,
                    instrument,
                    controls.ra,
                    controls.dec,
                    controls.pa,
                    wcs,
                    color=color,
                    fill_alpha=controls.alpha,
                    dither_pattern=controls.dither,
                    add_mosaic=add_mosaic,
                    mosaic_offset=(controls.mosaic_v2, controls.mosaic_v3),
                )

    def _update_footprint(self, instruments, controls):
        """
        Update an instrument footprint.

        Existing patches for the instrument are updated in place from
        the `controls` configuration.

        Parameters
        ----------
        instruments : list of str
            The instruments to update.
        controls : jwst_novt.interact.ControlInstruments
            Controls widgets associated with the instrument.
        """
        if not self.uploaded_data.has_wcs:
            return
        wcs = self.viewer.state.reference_data.coords
        with nd.hold_all_sync(self.all_patches()):
            for instrument in instruments:
                if instrument in self.footprint_patches:
                    if "long" in instrument.lower():
                        color = controls.color_alternate
                    else:
                        color = controls.color_primary
                    self.footprint_patches[instrument] = nd.bqplot_footprint(
                        self.viewer.figure,
                        instrument,
                        controls.ra,
                        controls.dec,
                        controls.pa,
                        wcs,
                        color=color,
                        fill_alpha=controls.alpha,
                        dither_pattern=controls.dither,
                        add_mosaic=(controls.mosaic == "Yes"),
                        mosaic_offset=(controls.mosaic_v2, controls.mosaic_v3),
                        update_patches=self.footprint_patches.get(instrument),
                    )

    def update_nircam_dither(self, *args):
        """Update NIRCam apertures after a dither pattern change."""
        instruments = []
        for inst in ["NIRCam Short", "NIRCam Long"]:
            if inst in self.footprint_patches:
                instruments.append(inst)
        controls = self.nircam_controls
        self._show_footprint(instruments, controls)

    def update_nircam_footprint(self, *args):
        """Update NIRCam apertures after a center position or angle change."""
        instruments = ["NIRCam Short", "NIRCam Long"]
        controls = self.nircam_controls
        self._update_footprint(instruments, controls)

    def update_nircam_mosaic(self, change):
        """
        Update NIRCam apertures after a mosaic offset change.

        If a mosaic is being created or destroyed, the number of overlays
        changes, and the apertures need to be recreated. Otherwise, the
        apertures are updated in place.
        """
        instruments = []
        for inst in ["NIRCam Short", "NIRCam Long"]:
            if inst in self.footprint_patches:
                instruments.append(inst)
        controls = self.nircam_controls

        if change["name"] == "mosaic":
            self._show_footprint(instruments, controls)
        else:
            self._update_footprint(instruments, controls)

    def update_nirspec_footprint(self, *args):
        """Update NIRSpec apertures in place."""
        instruments = ["NIRSpec"]
        controls = self.nirspec_controls
        self._update_footprint(instruments, controls)
