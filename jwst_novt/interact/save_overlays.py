import ipywidgets as ipw
import ipyvuetify as v
import regions
from traitlets import HasTraits, Unicode
import yaml

from jwst_novt import footprints as fp
from jwst_novt.interact.utils import FileDownloadLink

__all__ = ['SaveOverlays']


class SaveOverlays(HasTraits):
    """
    Widgets to save currently displayed overlay regions.
    """
    coordinates = Unicode('pixel coordinates').tag(sync=True)
    region_filename = Unicode('novt_overlays.ds9').tag(sync=True)
    config_filename = Unicode('novt_config.yaml').tag(sync=True)

    def __init__(self, show_overlays, allow_configuration=False):
        super().__init__()

        # internal data
        self.title = 'Save Data'
        self.region_formats = ['ds9']
        self.coord_options = ['pixel coordinates', 'sky coordinates']
        self.show_overlays = show_overlays

        # make widgets to display
        self.set_format = ipw.Dropdown(
            description='Region file format', options=self.region_formats,
            style={'description_width': 'initial'},
            tooltip='Text file format for overlay description')
        self.set_coordinates = ipw.Dropdown(
            options=self.coord_options,
            style={'description_width': 'initial'},
            tooltip='Coordinate system for overlay description')
        self.set_filename = ipw.Text(
            description='Region file name',
            style={'description_width': 'initial'},
            layout=ipw.Layout(width='300px'),
            tooltip='File name to assign to downloaded region file')

        ipw.link((self, 'coordinates'), (self.set_coordinates, 'value'))
        ipw.link((self, 'region_filename'), (self.set_filename, 'value'))

        # save buttons: one to make region file and update link to download,
        # another to trigger download
        # (both at once is not currently possible)
        self.make_file = v.Btn(color='primary', class_='mx-2 my-2',
                               children=['Make region file'])
        self.file_link = FileDownloadLink(value='Download')
        self.save_file = v.Btn(
            class_='mx-2 my-2', children=[self.file_link])

        self.make_file.on_event('click', self.make_regions)
        self.save_file.on_event('click', self.file_link.clear_link)

        if allow_configuration:
            self.set_config_filename = ipw.Text(
                description='Config file name',
                style={'description_width': 'initial'},
                layout=ipw.Layout(width='300px'),
                tooltip='File name to assign to downloaded configuration file')
            ipw.link((self, 'config_filename'),
                     (self.set_config_filename, 'value'))

            self.make_config_file = v.Btn(color='primary', class_='mx-2 my-2',
                                          children=['Make config file'])
            self.config_file_link = FileDownloadLink(value='Download')
            self.save_config_file = v.Btn(
                class_='mx-2 my-2', children=[self.config_file_link])

            self.make_config_file.on_event('click', self.make_config)
            self.save_config_file.on_event('click',
                                           self.config_file_link.clear_link)
        else:
            self.set_config_filename = None
            self.make_config_file = None
            self.config_file_link = None
            self.save_config_file = None

        # layout widgets
        button_layout = ipw.Layout(
            display='flex', flex_flow='row', align_items='center',
            justify_content='flex-start', padding='0px')
        box_layout = ipw.Layout(
            display='flex', flex_flow='column', align_items='stretch')

        b1 = ipw.Box(children=[self.set_format, self.set_coordinates],
                     layout=button_layout)
        b2 = ipw.Box(children=[
            self.set_filename, self.make_file, self.save_file],
            layout=button_layout)
        children = [b1, b2]

        if allow_configuration:
            b3 = ipw.Box(children=[
                self.set_config_filename, self.make_config_file,
                self.save_config_file],
                layout=button_layout)
            children.append(b3)

        box = ipw.Box(children=children,
                      layout=box_layout)
        self.widgets = ipw.Accordion(children=[box], titles=[self.title])

    def make_regions(self, *args, **kwargs):
        """
        Save regions to a local file.

        Returns
        -------
        all_regions : regions.Regions
            All created astropy regions. Instrument sets are tagged.
            Colors are set in the style metadata.
        """
        try:
            wcs = self.show_overlays.viewer.state.reference_data.coords
        except AttributeError:
            return
        if not wcs.has_celestial:
            return

        if self.set_coordinates.value.startswith('pixel'):
            coord = 'pixel'
        else:
            coord = 'sky'
        file_format = self.set_format.value

        all_regions = []
        colors = {}
        markers = {}
        for instrument in self.show_overlays.footprint_patches:
            markers[instrument] = 'cross'
            if instrument == 'NIRSpec':
                controls = self.show_overlays.nirspec_controls
                colors[instrument] = controls.color_primary

                ra = controls.ra
                dec = controls.dec
                pa = controls.pa
                regs = fp.nirspec_footprint(ra, dec, pa)
            else:
                # 'NIRCam Short' or 'NIRCam Long'
                channel = instrument.split()[-1].lower()
                controls = self.show_overlays.nircam_controls
                if channel == 'long':
                    colors[instrument] = controls.color_alternate
                else:
                    colors[instrument] = controls.color_primary

                ra = controls.ra
                dec = controls.dec
                pa = controls.pa
                dither_pattern = controls.dither
                add_mosaic = (controls.mosaic == 'Yes')
                mosaic_offset = (controls.mosaic_v2, controls.mosaic_v3)
                regs = fp.nircam_dither_footprint(
                    ra, dec, pa, channel=channel,
                    dither_pattern=dither_pattern,
                    add_mosaic=add_mosaic,
                    mosaic_offset=mosaic_offset)

            for region in regs:
                region.meta['tag'] = [instrument]
                region.style = {'color': colors[instrument]}
                if coord == 'pixel':
                    region = region.to_pixel(wcs)
                all_regions.append(region)

        cat_file = self.show_overlays.uploaded_data.catalog_file
        cat_markers = self.show_overlays.catalog_markers
        cat_colors = [self.show_overlays.uploaded_data.color_primary,
                      self.show_overlays.uploaded_data.color_alternate,]
        test_catalogs = [p.visible for p in cat_markers.values()]
        if any(test_catalogs) and cat_file is not None:
            primary, filler = [], []
            if isinstance(cat_file, str):
                # assume it is a file name
                primary, filler = fp.source_catalog(cat_file)
            else:
                try:
                    primary, filler = fp.source_catalog(cat_file['file_obj'])
                finally:  # pragma: no cover
                    try:
                        cat_file['file_obj'].seek(0)
                    except Exception:
                        pass

            if 'primary' in cat_markers and cat_markers['primary'].visible:
                colors['primary'] = cat_colors[0]
                markers['primary'] = 'circle'
                for region in primary:
                    region.meta['tag'] = ['primary']
                    region.style = {'color': colors['primary']}
                    if coord == 'pixel':
                        region = region.to_pixel(wcs)
                    all_regions.append(region)
            if 'filler' in cat_markers and cat_markers['filler'].visible:
                colors['filler'] = cat_colors[1]
                markers['filler'] = 'circle'
                for region in filler:
                    region.meta['tag'] = ['filler']
                    region.style = {'color': colors['filler']}
                    if coord == 'pixel':
                        region = region.to_pixel(wcs)
                    all_regions.append(region)

        all_regions = regions.Regions(all_regions)
        if len(all_regions) > 0:
            region_text = all_regions.serialize(format=file_format)

            # patch color and marker into text, based on tag
            # (regions package does not yet serialize style)
            for inst, value in colors.items():
                region_text = region_text.replace(
                    f'tag={{{inst}}}',
                    f'tag={{{inst}}} color={value} point={markers[inst]}')

            filename = self.set_filename.value
            self.file_link.edit_link(filename, region_text)

        return all_regions

    def make_config(self, *args, **kwargs):
        """
        Save current configuration to a local file.

        Returns
        -------
        config : dict
            Configuration data in dictionary form.
        """
        config = self.show_overlays.uploaded_data.configuration
        if len(config) == 0:
            return

        config_str = yaml.dump(config)
        filename = self.set_config_filename.value
        self.config_file_link.edit_link(filename, config_str)

        return config
