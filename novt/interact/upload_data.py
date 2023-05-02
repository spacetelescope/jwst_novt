import warnings

from astropy.io import fits

import ipywidgets as ipw
import ipyvuetify.extra as ve
from traitlets import HasTraits, Any

__all__ = ['UploadData']


class UploadData(HasTraits):
    """
    Widgets to upload user data files.
    """
    catalog_file = Any(None, allow_none=True)

    def __init__(self, viz):
        super().__init__(self)

        # internal data
        self.viz = viz
        self.viewer = viz.default_viewer
        self.image_files = {}

        # make widgets to display
        self.image_label = ipw.Label('Image file (.fits):',
                                     style={'font_weight': 'bold'})
        self.image_file_upload = ve.FileInput(accept='.fits', multiple=True)

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

    def load_image(self, change):
        """
        Watch for newly uploaded or removed files.

        New images are loaded into the viewer. Removed files are removed
        from the viewer. The loaded data remains accessible to the viewer
        and can be manually reloaded by the user if desired.
        """
        # watch for uploaded files
        change.owner.disabled = True
        if len(change['new']) > 0:
            uploaded_files = change.owner.get_files()
            if len(uploaded_files) > 0:
                for uploaded_file in uploaded_files:
                    self.image_files[uploaded_file['name']] = uploaded_file

                    hdul = fits.open(uploaded_file['file_obj'])
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore')
                        self.viz.load_data(
                            hdul, data_label=uploaded_file['name'])
                    hdul.close()
        if len(change['old']) > 0:
            # clear any removed data from viewer
            for old_file in change['old']:
                for data_set in self.viz.app.data_collection:
                    if data_set.label.startswith(old_file['name']):
                        self.viz.app.remove_data_from_viewer(
                            self.viewer.reference_id, data_set.label)
                del self.image_files[old_file['name']]
        change.owner.disabled = False

    def load_catalog(self, change):
        """
        Watch for newly uploaded or removed catalog files.

        Newly uploaded files are set in the `catalog_file`
        traitlet. If files are removed, the traitlet is set to None.
        """
        # watch for uploaded files
        change.owner.disabled = True
        if len(change['new']) > 0:
            uploaded_files = change.owner.get_files()
            if len(uploaded_files) > 0:
                self.catalog_file = uploaded_files[0]
        elif len(change['old']) > 0:
            self.catalog_file = None
        change.owner.disabled = False
