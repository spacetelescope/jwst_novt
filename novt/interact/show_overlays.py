import ipywidgets as ipw

from novt import display as nd


class ButtonWithValue(ipw.Button):
    """Button widget with value metadata."""
    def __init__(self, *args, **kwargs):
        self.value = kwargs.pop('value', '')
        super().__init__(*args, **kwargs)


class ShowOverlays(object):
    def __init__(self, viz, uploaded_data, nirspec=None, nircam=None):
        # internal data
        self.viz = viz
        self.viewer = viz.default_viewer
        self.uploaded_data = uploaded_data
        self.nirspec_controls = nirspec
        self.nircam_controls = nircam
        self.instruments = []
        self.catalog_markers = {}
        self.footprint_patches = {}

        # toggle catalog overlay
        self.catalog_show = ipw.Button(description='Show Catalog',
                                       layout=ipw.Layout(width='auto'))
        self.catalog_show.on_click(self.toggle_catalog)

        # watch for changes to catalog file
        self.uploaded_data.observe(self.load_catalog, names='catalog_file')

        # watch for changes to update footprint
        if self.nirspec_controls is not None:
            self.instruments.append('NIRSpec')

            self.nirspec_controls.observe(self.update_nirspec_footprint,
                                          names=['ra', 'dec', 'pa'])
        if self.nircam_controls is not None:
            self.instruments.extend(['NIRCam Long', 'NIRCam Short'])
            self.nircam_controls.observe(self.update_nircam_footprint,
                                         names=['ra', 'dec', 'pa'])
        
        # toggle footprint overlays
        self.footprint_buttons = []
        for name in self.instruments:
            button = ButtonWithValue(
                description=f'Show {name} footprint',
                value=name, layout=ipw.Layout(width='auto'))
            button.on_click(self.toggle_footprint)
            self.footprint_buttons.append(button)

        # layout widgets
        button_layout = ipw.Layout(display='flex', flex_flow='row',
                                   justify_content='flex-start', padding='5px')
        self.widgets = ipw.Box(
            children=self.footprint_buttons + [self.catalog_show],
            layout=button_layout)

    def load_catalog(self, change):
        # clear any old markers on change in the catalog file
        if 'primary' in self.catalog_markers:
            nd.remove_bqplot_patches(
               self.viewer.figure, [self.catalog_markers['primary']])
            del self.catalog_markers['primary']
        if 'filler' in self.catalog_markers:
            nd.remove_bqplot_patches(
               self.viewer.figure, [self.catalog_markers['filler']])
            del self.catalog_markers['filler']
        self.catalog_show.description = 'Show Catalog'

    def toggle_catalog(self, btn):
        # todo - separate into primary and filler catalogs
        # make catalog show/hide button
        if btn.description.startswith('Show'):
            if self.viewer.state.reference_data is not None:
                if ('primary' in self.catalog_markers
                        and 'filler' in self.catalog_markers):
                    self.catalog_markers['primary'].visible = True
                    self.catalog_markers['filler'].visible = True
                    btn.description = 'Hide Catalog'
                else:
                    catalog_file = self.uploaded_data.catalog_file
                    if catalog_file is not None:
                        catalog = catalog_file['file_obj']
                        wcs = self.viewer.state.reference_data.coords
                        try:
                            primary, filler = nd.bqplot_catalog(
                                self.viewer.figure, catalog, wcs, alpha=0.6)
                        except Exception as err:
                            # todo: need error/status handling
                            print(err)
                        else:
                            self.catalog_markers['primary'] = primary
                            self.catalog_markers['filler'] = filler
                            btn.description = 'Hide Catalog'
        else:
            btn.description = 'Show Catalog'
            if 'primary' in self.catalog_markers:
                #nd.remove_bqplot_patches(
                #    self.viewer.figure, [self.catalog_markers['primary']])
                #del self.catalog_markers['primary']
                self.catalog_markers['primary'].visible = False
            if 'filler' in self.catalog_markers:
                #nd.remove_bqplot_patches(
                #    self.viewer.figure, [self.catalog_markers['filler']])
                #del self.catalog_markers['filler']
                self.catalog_markers['filler'].visible = False

    def toggle_footprint(self, btn):
        if btn.description.startswith('Show'):
            if self.viewer.state.reference_data is not None:
                wcs = self.viewer.state.reference_data.coords
                if wcs is not None:
                    btn.description = f'Hide {btn.value} footprint'

                    if 'NIRS' in btn.value:
                        ra = self.nirspec_controls.ra
                        dec = self.nirspec_controls.dec
                        pa = self.nirspec_controls.pa
                    else:
                        ra = self.nircam_controls.ra
                        dec = self.nircam_controls.dec
                        pa = self.nircam_controls.pa
                    self.footprint_patches[btn.value] = nd.bqplot_footprint(
                        self.viewer.figure, btn.value, ra, dec, pa, wcs,
                        fill='inside', alpha=0.6)
        else:
            btn.description = f'Show {btn.value} FOV'
            nd.remove_bqplot_patches(self.viewer.figure,
                                     self.footprint_patches[btn.value])
            del self.footprint_patches[btn.value]

    def _update_footprint(self, instruments, controls):
        if self.viewer.state.reference_data is not None:
            wcs = self.viewer.state.reference_data.coords
            for instrument in instruments:
                if instrument in self.footprint_patches and wcs is not None:
                    self.footprint_patches[instrument] = nd.bqplot_footprint(
                        self.viewer.figure, instrument,
                        controls.ra, controls.dec, controls.pa, wcs,
                        fill='inside', alpha=0.6,
                        update_patches=self.footprint_patches.get(instrument))

    def update_nircam_footprint(self, *args):
        instruments = ['NIRCam Short', 'NIRCam Long']
        controls = self.nircam_controls
        self._update_footprint(instruments, controls)

    def update_nirspec_footprint(self, *args):
        instruments = ['NIRSpec']
        controls = self.nirspec_controls
        self._update_footprint(instruments, controls)
