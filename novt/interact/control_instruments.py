import ipywidgets as ipw
from traitlets import HasTraits, Float


class ControlInstruments(HasTraits):
    ra = Float(0.0).tag(sync=True)
    dec = Float(0.0).tag(sync=True)
    pa = Float(0.0).tag(sync=True)

    def __init__(self, instrument, viz):
        super().__init__(self)

        # internal data
        self.instrument = instrument
        self.viz = viz
        self.viewer = viz.default_viewer

        # make control widgets
        self.label = ipw.Label(f'{self.instrument} Configuration:',
                               style={'font_weight': 'bold'})
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

        # set a callback in the viewer to initialize RA/Dec
        # from WCS on data load
        self.viewer.state.add_callback('reference_data', self._set_from_wcs)

        # layout widgets
        button_layout = ipw.Layout(display='flex', flex_flow='row',
                                   justify_content='flex-start', padding='5px')

        self.widgets = ipw.Box(children=[self.label, self.set_ra,
                                         self.set_dec, self.set_pa],
                               layout=button_layout)

    def _wrap_angle(self, change):
        angle = change['new']
        if angle < 0 or angle >= 360:
            angle = (angle + 360) % 360
            self.set_pa.value = angle
        else:
            self.pa = angle

    def _set_from_wcs(self, event):
        if self.viewer.state.reference_data is not None:
            coords = self.viewer.state.reference_data.coords
            if coords is not None:
                ra, dec = coords.wcs.crval
                self.ra = ra
                self.dec = dec
