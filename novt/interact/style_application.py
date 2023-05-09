import ipywidgets as ipw

from novt.interact.utilities import read_image

__all__ = ['StyleApplication']


class StyleApplication(object):
    """
    Widgets to lay out and style the default application.
    """
    def __init__(self, image_viewer, uploaded_data, nirspec_controls,
                 nircam_controls, overlay_controls, save_controls,
                 context='notebook'):

        # internal data
        self.context = context
        self.title = 'NIRSpec MOS Pre-Imaging Planner'

        # layouts
        self.row_layout = ipw.Layout(
            display='flex', flex_flow='row', align_items='center',
            justify_content='space-between')
        self.column_layout = ipw.Layout(
            display='flex', flex_flow='column', align_items='stretch')

        # header banner
        self.jwst_logo = read_image('JWSTlogo.png')
        self.stsci_logo = read_image('STScIlogo.png')
        self.docs_link = (
            'https://jwst-docs.stsci.edu/jwst-near-infrared-spectrograph/'
            'nirspec-apt-templates/'
            'nirspec-multi-object-spectroscopy-apt-template/'
            'nirspec-observation-visualization-tool-help')
        self.header = ipw.Box(
            children=[ipw.HTML(f'<h1>{self.title}</h1>'
                               f'<p>For usage information, see the '
                               f'<a style="color: #106ba3" '
                               f'href="{self.docs_link}"'
                               f'target="_blank">NOVT Documentation.</a></p>'),
                      ipw.HBox(children=[nirspec_controls.logo,
                                         nircam_controls.logo,
                                         self.jwst_logo, self.stsci_logo])],
            layout=self.row_layout)

        # footer links
        self.footer = ipw.Box(children=[], layout=self.row_layout)

        children = [self.header, uploaded_data.widgets,
                    nirspec_controls.widgets, nircam_controls.widgets,
                    save_controls.widgets]
        if 'notebook' in self.context:
            # in a notebook, display the viewer inline at
            # 100% of cell width
            width = '100%'
            children.extend([overlay_controls.widgets,
                             image_viewer.widgets])
        else:
            # in a web app, collapse the viewer and controls and set
            # width to 95% of viewer width
            width = '95vw'
            viewer_with_controls = ipw.Box(
                children=[overlay_controls.widgets, image_viewer.widgets],
                layout=self.column_layout)
            viewer_tab = ipw.Accordion(
                children=[viewer_with_controls],
                layout=self.column_layout, titles=[image_viewer.title],
                selected_index=0)
            children.append(viewer_tab)
        children.append(self.footer)

        # set layout
        self.top_layout = ipw.Layout(
            display='flex', flex_flow='column', align_items='stretch',
            width=width, padding='0px', margin='0px')

        self.widgets = ipw.Box(children=children, layout=self.top_layout)
