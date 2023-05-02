import ipywidgets as ipw
from traitlets import HasTraits, Float, Unicode

from novt.constants import NIRCAM_DITHER_OFFSETS, NO_MOSAIC

__all__ = ['ControlInstruments']


class ControlInstruments(HasTraits):
    """
    Widgets to control instrument aperture overlay configuration.
    """
    ra = Float(0.0).tag(sync=True)
    dec = Float(0.0).tag(sync=True)
    pa = Float(0.0).tag(sync=True)
    dither = Unicode('NONE').tag(sync=True)
    mosaic_v2 = Float(0.0).tag(sync=True)
    mosaic_v3 = Float(0.0).tag(sync=True)

    def __init__(self, instrument, viz):
        super().__init__(self)

        # internal data
        self.instrument = instrument
        self.title = f'Configure {instrument} Apertures'
        self.viz = viz
        self.viewer = viz.default_viewer
        self.dither_values = list(NIRCAM_DITHER_OFFSETS.keys())

        # make control widgets
        self.center_label = ipw.Label('Position center and angle',
                                      style={'font_weight': 'bold'})

        # for center and position angle
        self.set_ra = ipw.BoundedFloatText(
            description='RA (deg)', min=0, max=360,
            step=5 / 3600, continuous_update=False,
            style={'description_width': 'initial'})
        self.set_dec = ipw.BoundedFloatText(
            description='Dec (deg)', min=0, max=90,
            step=5 / 3600, continuous_update=False,
            style={'description_width': 'initial'})
        self.set_pa = ipw.FloatText(
            description='PA (deg)',
            step=5, continuous_update=False,
            style={'description_width': 'initial'})

        ipw.link((self.set_ra, 'value'), (self, 'ra'))
        ipw.link((self.set_dec, 'value'), (self, 'dec'))

        # set pa link from self to widget only and directly
        # handle setting from widget input in order to wrap
        # angle properly from widget nudge
        self.set_pa.observe(self._wrap_angle, 'value')
        ipw.dlink((self, 'pa'), (self.set_pa, 'value'))

        # select box and text entry for dither and
        # mosaic patterns (NIRCam only)
        if self.instrument == 'NIRCam':
            self.dither_label = ipw.Label(
                'Dither and mosaic options', style={'font_weight': 'bold'})
            self.set_dither = ipw.Dropdown(
                description='Dither pattern',
                options=self.dither_values,
                style={'description_width': 'initial'})
            ipw.link((self.set_dither, 'value'), (self, 'dither'))
            self.set_dither.observe(self._check_mosaic, 'value')

            self.set_mosaic_v2 = ipw.BoundedFloatText(
                description='Mosaic offset horizontal (arcsec)',
                min=0, max=3600, step=5, continuous_update=False,
                style={'description_width': 'initial'})
            self.set_mosaic_v3 = ipw.BoundedFloatText(
                description='Mosaic offset vertical (arcsec)',
                min=0, max=3600, step=5, continuous_update=False,
                style={'description_width': 'initial'})
            ipw.link((self.set_mosaic_v2, 'value'), (self, 'mosaic_v2'))
            ipw.link((self.set_mosaic_v3, 'value'), (self, 'mosaic_v3'))

        else:
            self.dither_label = None
            self.set_dither = None
            self.set_mosaic_v2 = None
            self.set_mosaic_v3 = None

        # set a callback in the viewer to initialize RA/Dec
        # from WCS on data load
        self.viewer.state.add_callback('reference_data', self._set_from_wcs)

        # layout widgets
        button_layout = ipw.Layout(display='flex', flex_flow='row',
                                   justify_content='flex-start', padding='5px')
        box_layout = ipw.Layout(display='flex', flex_flow='column',
                                align_items='stretch')
        label = ipw.Box(children=[self.center_label],
                        layout=button_layout)
        center_buttons = ipw.Box(children=[self.set_ra,
                                           self.set_dec, self.set_pa],
                                 layout=button_layout)
        children = [label, center_buttons]
        if self.set_dither is not None:
            mosaic_fields = ipw.Box(
                children=[self.set_mosaic_v2,
                          self.set_mosaic_v3],
                layout=button_layout)
            children.extend([self.dither_label, self.set_dither,
                             mosaic_fields])
        box = ipw.Box(children=children, layout=box_layout)
        self.widgets = ipw.Accordion(children=[box], titles=[self.title])

    def _wrap_angle(self, change):
        """Wrap input angles to expected range (0-360)."""
        angle = change['new']
        if angle < 0 or angle >= 360:
            # change angle in widget only:
            # the change will trigger a new call to set the
            # PA trait to the wrapped value
            angle = (angle + 360) % 360
            self.set_pa.value = angle
        else:
            self.pa = angle

    def _set_from_wcs(self, event):
        """Set default RA and Dec from a newly uploaded file."""
        if self.viewer.state.reference_data is not None:
            coords = self.viewer.state.reference_data.coords
            if coords is not None:
                ra, dec = coords.wcs.crval
                self.ra = ra
                self.dec = dec

    def _check_mosaic(self, change):
        """Enable or disable mosaic buttons based on dither value."""
        pattern = change['new']
        if pattern in NO_MOSAIC:
            # this dither pattern does not allow mosaics
            self.set_mosaic_v2.disabled = True
            self.set_mosaic_v3.disabled = True
        else:
            self.set_mosaic_v2.disabled = False
            self.set_mosaic_v3.disabled = False
