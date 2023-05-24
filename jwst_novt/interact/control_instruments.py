import ipywidgets as ipw
from traitlets import Float, HasTraits, Unicode

from jwst_novt.constants import DEFAULT_COLOR, NIRCAM_DITHER_OFFSETS, NO_MOSAIC
from jwst_novt.interact.utils import read_image

__all__ = ["ControlInstruments"]


class ControlInstruments(HasTraits):
    """Widgets to control instrument aperture overlay configuration."""

    ra = Float(0.0).tag(sync=True)
    dec = Float(0.0).tag(sync=True)
    pa = Float(0.0).tag(sync=True)
    dither = Unicode("NONE").tag(sync=True)
    mosaic = Unicode("No").tag(sync=True)
    mosaic_v2 = Float(0.0).tag(sync=True)
    mosaic_v3 = Float(0.0).tag(sync=True)
    color_primary = Unicode("red").tag(sync=True)
    color_alternate = Unicode("blue").tag(sync=True)
    alpha = Float(0.1).tag(sync=True)

    def __init__(self, instrument, viz):
        super().__init__(self)

        # internal data
        self.instrument = instrument
        self.title = f"Configure {instrument} Apertures"
        self.viz = viz
        self.viewer = viz.default_viewer
        self.dither_values = list(NIRCAM_DITHER_OFFSETS.keys())

        # instrument logo image
        if self.instrument == "NIRCam":
            self.logo = read_image("nircamlogo.png", width="130px")
        else:
            self.logo = read_image("nirspeclogo.png")

        # controls for center and position angle
        five_arcsec = 0.0014
        self.set_ra = ipw.BoundedFloatText(
            description="RA (deg)",
            min=0,
            max=360,
            step=five_arcsec,
            continuous_update=False,
            style={"description_width": "initial"},
            tooltip="Right ascension coordinate for instrument center",
        )
        self.set_dec = ipw.BoundedFloatText(
            description="Dec (deg)",
            min=-90,
            max=90,
            step=five_arcsec,
            continuous_update=False,
            style={"description_width": "initial"},
            tooltip="Declination coordinate for instrument center",
        )
        self.set_pa = ipw.FloatText(
            description="PA (deg)",
            step=5,
            continuous_update=False,
            style={"description_width": "initial"},
            tooltip="Position angle of vertical axis, from North to East",
        )

        ipw.link((self.set_ra, "value"), (self, "ra"))
        ipw.link((self.set_dec, "value"), (self, "dec"))

        # set pa link from self to widget only and directly
        # handle setting from widget input in order to wrap
        # angle properly from widget nudge
        self.set_pa.observe(self._wrap_angle, "value")
        ipw.dlink((self, "pa"), (self.set_pa, "value"))

        # select box and text entry for dither and
        # mosaic patterns (NIRCam only)
        self.set_dither = None
        self.set_mosaic = None
        self.set_mosaic_v2 = None
        self.set_mosaic_v3 = None
        if self.instrument == "NIRCam":
            self._init_dither_widgets()

            # color controls
            self.color_pickers = [
                ipw.ColorPicker(
                    description="Short color",
                    value=DEFAULT_COLOR["NIRCam Short"],
                    style={"description_width": "initial"},
                    tooltip="Color for NIRCam Short overlays",
                ),
                ipw.ColorPicker(
                    description="Long color",
                    value=DEFAULT_COLOR["NIRCam Long"],
                    style={"description_width": "initial"},
                    tooltip="Color for NIRCam Long overlays",
                ),
            ]
            ipw.link((self.color_pickers[0], "value"), (self, "color_primary"))
            ipw.link((self.color_pickers[1], "value"), (self, "color_alternate"))
        else:
            # color controls
            self.color_pickers = [
                ipw.ColorPicker(
                    description="Color",
                    value=DEFAULT_COLOR["NIRSpec"],
                    style={"description_width": "initial"},
                    tooltip="Color for NIRSpec overlays",
                ),
            ]
            ipw.link((self.color_pickers[0], "value"), (self, "color_primary"))

        # fill alpha for overlays
        self.set_alpha = ipw.BoundedFloatText(
            value=0.1,
            description="Fill opacity",
            min=0,
            max=1,
            step=0.1,
            continuous_update=False,
            style={"description_width": "initial"},
            tooltip="Set to 0 for no fill; 1 for opaque overlays",
        )
        ipw.link((self.set_alpha, "value"), (self, "alpha"))

        # set a callback in the viewer to initialize RA/Dec
        # from WCS on data load
        self.viewer.state.add_callback("reference_data", self._set_from_wcs)

        # also call it now in case viewer already has data loaded
        self._set_from_wcs()

        # layout widgets
        row_layout = ipw.Layout(
            display="flex", flex_flow="row", justify_content="flex-start", padding="0px"
        )
        column_layout = ipw.Layout(
            display="flex", flex_flow="column", align_items="stretch"
        )
        center_buttons = ipw.Box(
            children=[self.set_ra, self.set_dec, self.set_pa], layout=row_layout
        )
        appearance_tab = ipw.Accordion(
            children=[
                ipw.Box(
                    children=[*self.color_pickers, self.set_alpha], layout=row_layout
                )
            ],
            titles=["Appearance"],
        )

        children = [center_buttons]
        if self.set_dither is not None:
            mosaic_fields = ipw.Box(
                children=[self.set_mosaic, self.set_mosaic_v2, self.set_mosaic_v3],
                layout=row_layout,
            )
            children.extend([mosaic_fields, self.set_dither])
        position_tab = ipw.Accordion(
            children=[ipw.Box(children=children, layout=column_layout)],
            titles=["Position"],
            selected_index=0,
        )

        children = [position_tab, appearance_tab]
        col = ipw.Box(children=children, layout=column_layout)
        row = ipw.Box(
            children=[self.logo, col],
            layout=ipw.Layout(
                display="flex",
                flex_flow="row",
                justify_content="flex-start",
                align_items="center",
            ),
        )
        self.widgets = ipw.Accordion(children=[row], titles=[self.title])

    def _init_dither_widgets(self):
        """Set up dither widgets for NIRCam."""
        self.set_dither = ipw.Dropdown(
            description="Dither pattern",
            options=self.dither_values,
            style={"description_width": "initial"},
            tooltip="Apply a NIRCam dither pattern",
        )
        ipw.link((self.set_dither, "value"), (self, "dither"))
        self.set_dither.observe(self._check_mosaic_from_dither, "value")

        self.set_mosaic = ipw.Dropdown(
            description="Mosaic",
            options=["No", "Yes"],
            style={"description_width": "initial"},
            tooltip="Apply a two-tile NIRCam mosaic",
        )
        ipw.link((self.set_mosaic, "value"), (self, "mosaic"))
        self.set_mosaic.observe(self._check_mosaic, "value")

        self.set_mosaic_v2 = ipw.BoundedFloatText(
            description="Horizontal offset (arcsec)",
            min=-3600,
            max=3600,
            step=5,
            continuous_update=False,
            style={"description_width": "initial"},
            tooltip="V2 distance between mosaic tile centers",
        )
        self.set_mosaic_v3 = ipw.BoundedFloatText(
            description="Vertical offset (arcsec)",
            min=-3600,
            max=3600,
            step=5,
            continuous_update=False,
            style={"description_width": "initial"},
            tooltip="V3 distance between mosaic tile centers",
        )
        self.set_mosaic_v2.disabled = True
        self.set_mosaic_v3.disabled = True
        ipw.link((self.set_mosaic_v2, "value"), (self, "mosaic_v2"))
        ipw.link((self.set_mosaic_v3, "value"), (self, "mosaic_v3"))

    def _wrap_angle(self, change):
        """Wrap input angles to expected range (0-360)."""
        angle = change["new"]
        ndeg = 360
        if angle < 0 or angle >= ndeg:
            # change angle in widget only:
            # the change will trigger a new call to set the
            # PA trait to the wrapped value
            angle = (angle + ndeg) % ndeg
            self.set_pa.value = angle
        else:
            self.pa = angle

    def _set_from_wcs(self, *args, **kwargs):
        """Set default RA and Dec from a newly uploaded file."""
        if self.viewer.state.reference_data is not None:
            coords = self.viewer.state.reference_data.coords
            if coords is not None:
                ra, dec = coords.wcs.crval
                self.ra = float(ra)
                self.dec = float(dec)

    def _check_mosaic_from_dither(self, change):
        """Enable or disable mosaic buttons based on dither value."""
        pattern = change["new"]
        if pattern in NO_MOSAIC:
            # this dither pattern does not allow mosaics
            self.set_mosaic.disabled = True
            self.set_mosaic_v2.disabled = True
            self.set_mosaic_v3.disabled = True
        elif self.mosaic != "No":
            self.set_mosaic.disabled = False
            self.set_mosaic_v2.disabled = False
            self.set_mosaic_v3.disabled = False
        else:
            self.set_mosaic.disabled = False

    def _check_mosaic(self, change):
        """Set offset state from mosaic choice."""
        mosaic = change["new"]
        if mosaic == "No":
            # turn off mosaic offsets
            self.set_mosaic_v2.disabled = True
            self.set_mosaic_v3.disabled = True
        else:
            self.set_mosaic_v2.disabled = False
            self.set_mosaic_v3.disabled = False
