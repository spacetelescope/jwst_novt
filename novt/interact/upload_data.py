import warnings

from astropy.io import fits

import ipywidgets as ipw
import ipyvuetify.extra as ve


class UploadData(object):
    def __init__(self, viz):
        # internal data
        self.viz = viz
        self.viewer = viz.default_viewer
        self.image_file = None
        self.catalog_file = None

        # make widgets to display
        self.image_label = ipw.Label('Image file (.fits):',
                                     style={'font_weight': 'bold'})
        self.image_file_upload = ve.FileInput(accept='.fits', multiple=False)

        self.catalog_label = ipw.Label('Catalog file (.radec):',
                                       style={'font_weight': 'bold'})
        self.catalog_file_upload = ve.FileInput(accept='.radec', multiple=False)

        # layout widgets
        button_layout = ipw.Layout(display='flex', flex_flow='row',
                                   justify_content='flex-start', padding='5px')
        box_layout = ipw.Layout(display='flex', flex_flow='column',
                                align_items='stretch')

        b1 = ipw.Box(children=[self.image_label, self.image_file_upload],
                               layout=button_layout)
        b2 = ipw.Box(children=[self.catalog_label, self.catalog_file_upload],
                               layout=button_layout)
        self.widgets = ipw.Box(children=[b1, b2], layout=box_layout)

        # connect callbacks
        self.image_file_upload.observe(self.load_image, names='file_info')
        self.catalog_file_upload.observe(self.load_catalog, names='file_info')

    def load_image(self, event):
        # watch for uploaded files
        # todo: clear viewer if file removed or replaced
        # todo: consider allowing multiple, eg for mosaicked field
        uploaded_files = event.owner.get_files()
        if len(uploaded_files) > 0:
            uploaded_file = uploaded_files[0]
            self.image_file = uploaded_file

            hdul = fits.open(uploaded_file['file_obj'])
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                self.viz.load_data(hdul, data_label=uploaded_file['name'])
            hdul.close()

    def load_catalog(self, event):
        # watch for uploaded files
        uploaded_files = event.owner.get_files()
        if len(uploaded_files) > 0:
            self.catalog_file = uploaded_files[0]
