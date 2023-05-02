import ipywidgets as ipw

from novt import display as nd

__all__ = ['ShowOverlays']


class ButtonWithValue(ipw.Button):
    """Button widget with value metadata."""
    def __init__(self, *args, **kwargs):
        self.value = kwargs.pop('value', '')
        super().__init__(*args, **kwargs)


class ShowOverlays(object):
    """
    Widgets to control showing, hiding, and updating image overlays.
    """
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
            self.nircam_controls.observe(self.update_nircam_dither,
                                         names=['dither'])
            self.nircam_controls.observe(self.update_nircam_mosaic,
                                         names=['mosaic_v2', 'mosaic_v3'])

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

    def load_catalog(self, *args):
        """
        Remove any existing catalog markers when a new catalog file is loaded.
        """
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
        """Toggle catalog visibility."""
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
                self.catalog_markers['primary'].visible = False
            if 'filler' in self.catalog_markers:
                self.catalog_markers['filler'].visible = False

    def toggle_footprint(self, btn):
        """Toggle footprint visibility."""
        if btn.description.startswith('Show'):
            if self.viewer.state.reference_data is not None:
                wcs = self.viewer.state.reference_data.coords
                if wcs is not None:
                    btn.description = f'Hide {btn.value} footprint'

                    if 'NIRS' in btn.value:
                        controls = self.nirspec_controls
                    else:
                        controls = self.nircam_controls
                    self._show_footprint([btn.value], controls)
        else:
            btn.description = f'Show {btn.value} footprint'
            nd.remove_bqplot_patches(self.viewer.figure,
                                     self.footprint_patches[btn.value])
            del self.footprint_patches[btn.value]

    def _show_footprint(self, instruments, controls):
        """
        Show an instrument footprint.

        Removes any existing patches for the instrument and creates new
        ones from the `controls` configuration.

        Parameters
        ----------
        instruments : list of str
            The instruments to show.
        controls : novt.interact.ControlInstruments
            Controls widgets associated with the instrument.
        """
        if self.viewer.state.reference_data is None:
            return
        wcs = self.viewer.state.reference_data.coords
        if wcs is None:
            return
        with nd.hold_all_sync(self.viewer.figure.marks):
            for instrument in instruments:
                # any old patches need to be removed first
                if instrument in self.footprint_patches:
                    nd.remove_bqplot_patches(
                        self.viewer.figure,
                        self.footprint_patches[instrument])

                # make new patches
                self.footprint_patches[instrument] = nd.bqplot_footprint(
                    self.viewer.figure, instrument,
                    controls.ra, controls.dec, controls.pa, wcs,
                    dither_pattern=controls.dither,
                    mosaic_v2=controls.mosaic_v2,
                    mosaic_v3=controls.mosaic_v3)

    def _update_footprint(self, instruments, controls):
        """
        Update an instrument footprint.

        Existing patches for the instrument are updated in place from
        the `controls` configuration.

        Parameters
        ----------
        instruments : list of str
            The instruments to update.
        controls : novt.interact.ControlInstruments
            Controls widgets associated with the instrument.
        """
        if self.viewer.state.reference_data is None:
            return
        wcs = self.viewer.state.reference_data.coords
        if wcs is None:
            return
        with nd.hold_all_sync(self.viewer.figure.marks):
            for instrument in instruments:
                if instrument in self.footprint_patches:
                    self.footprint_patches[instrument] = nd.bqplot_footprint(
                        self.viewer.figure, instrument,
                        controls.ra, controls.dec, controls.pa, wcs,
                        dither_pattern=controls.dither,
                        mosaic_v2=controls.mosaic_v2,
                        mosaic_v3=controls.mosaic_v3,
                        update_patches=self.footprint_patches.get(instrument))

    def update_nircam_dither(self, *args):
        """Update NIRCam apertures after a dither pattern change."""
        instruments = []
        for inst in ['NIRCam Short', 'NIRCam Long']:
            if inst in self.footprint_patches:
                instruments.append(inst)
        controls = self.nircam_controls
        self._show_footprint(instruments, controls)

    def update_nircam_footprint(self, *args):
        """Update NIRCam apertures after a center position or angle change."""
        instruments = ['NIRCam Short', 'NIRCam Long']
        controls = self.nircam_controls
        self._update_footprint(instruments, controls)

    def update_nircam_mosaic(self, change):
        """
        Update NIRCam apertures after a mosaic offset change.

        If either old or new mosaic values are all zero,
        the number of overlays changes, and the apertures need to
        be recreated. Otherwise, the apertures are updated in place.
        """

        instruments = []
        for inst in ['NIRCam Short', 'NIRCam Long']:
            if inst in self.footprint_patches:
                instruments.append(inst)
        controls = self.nircam_controls

        # if going to/from a mosaic, the overlays need recreation
        # otherwise, they can just be updated
        if change['name'] == 'mosaic_v2':
            other_value = controls.mosaic_v3
        else:
            other_value = controls.mosaic_v2

        # check for all zero values in either old or new state
        if (change['old'] == 0 and other_value == 0) and change['new'] != 0:
            self._show_footprint(instruments, controls)
        elif (change['new'] == 0 and other_value == 0) and change['old'] != 0:
            self._show_footprint(instruments, controls)
        else:
            self._update_footprint(instruments, controls)

    def update_nirspec_footprint(self, *args):
        """Update NIRSpec apertures in place."""
        instruments = ['NIRSpec']
        controls = self.nirspec_controls
        self._update_footprint(instruments, controls)
