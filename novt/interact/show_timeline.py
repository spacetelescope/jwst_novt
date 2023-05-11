import ipyvuetify as v
import ipywidgets as ipw
from traitlets import HasTraits, Float, Unicode

from novt.interact import display as nd

__all__ = ['ShowTimeline']


class ShowTimeline(HasTraits):
    center = Unicode(None, allow_none=True).tag(sync=True)
    ra = Float(0.0).tag(sync=True)
    dec = Float(0.0).tag(sync=True)
    nirspec_color = Unicode('red').tag(sync=True)
    nircam_color = Unicode('blue').tag(sync=True)

    def __init__(self):
        super().__init__()

        self.title = 'Show Timeline'

        # bqplot figure to display
        self.figure = None
        self.figure_container = ipw.VBox()

        # start, end dates
        self.set_start = ipw.DatePicker(
            description='Start date',
            style={'description_width': 'initial'})
        self.set_end = ipw.DatePicker(
            description='End date',
            style={'description_width': 'initial'})

        # select instrument
        self.set_instrument = ipw.Dropdown(
            description='Instrument',
            options=['NIRSpec, NIRCam', 'NIRSpec', 'NIRCam'],
            style={'description_width': 'initial'})

        # re-make plot if instrument or dates change
        self.set_start.observe(self._make_timeline, 'value')
        self.set_end.observe(self._make_timeline, 'value')
        self.set_instrument.observe(self._make_timeline, 'value')

        # make/close plot
        self.make_plot = v.Btn(color='primary', class_='mx-2 my-2',
                               children=['Make timeline plot'])
        self.make_plot.on_event('click', self._show_plot)
        self.close_plot = v.Btn(color='primary', class_='mx-2 my-2',
                               children=['Close plot'])
        self.close_plot.on_event('click', self._clear_plot)

        # activate pan/zoom
        # fig.interaction = bqplot.interacts.panzoom(fig.marks)

        # reset limits

        # link color changes to plot update
        self.observe(self._update_colors,
                     names=['nirspec_color', 'nircam_color'])

        # clear plot if center object changes
        self.observe(self._clear_plot, names=['center'])

        # save plot

        button_layout = ipw.Layout(display='flex', flex_flow='row',
                                   justify_content='flex-start')
        box_layout = ipw.Layout(display='flex', flex_flow='column',
                                align_items='stretch')
        b1 = ipw.Box(children=[self.set_start, self.set_end,
                               self.set_instrument],
                     layout=button_layout)
        b2 = ipw.Box(children=[self.make_plot, self.close_plot],
                     layout=button_layout)
        box = ipw.Box(children=[b1, b2, self.figure_container],
                      layout=box_layout)
        self.widgets = ipw.Accordion(children=[box], titles=[self.title])

    def _show_plot(self, *args, **kwargs):
        if self.figure is None:
            self.figure = nd.bqplot_figure()
        self.figure_container.children = [self.figure]
        self._make_timeline()

    def _clear_plot(self, *args, **kwargs):
        if self.figure is not None:
            nd.clear_bqplot_figure(self.figure)
        self.figure_container.children = []

    def _make_timeline(self, *args, **kwargs):
        if self.figure is None or len(self.figure_container.children) == 0:
            return

        self.make_plot.disabled = True
        self.close_plot.disabled = True
        try:
            # check for instrument
            instrument = self.set_instrument.value
            if instrument == 'NIRCam':
                colors = [self.nircam_color]
            elif instrument == 'NIRSpec':
                colors = [self.nirspec_color]
            else:
                instrument = None
                colors = [self.nirspec_color, self.nircam_color]

            # check for start, end date
            start_date = self.set_start.value
            end_date = self.set_end.value
            if start_date is not None:
                start_date = start_date.strftime('%Y-%m-%d')
            if end_date is not None:
                end_date = end_date.strftime('%Y-%m-%d')

            # original does one position only - use nirspec center
            nd.bqplot_timeline(self.figure, self.ra, self.dec,
                               instrument=instrument,
                               start_date=start_date, end_date=end_date,
                               colors=colors)
        finally:
            self.make_plot.disabled = False
            self.close_plot.disabled = False

    def _update_colors(self, *args, **kwargs):
        if self.figure is None:
            return
        instrument = self.set_instrument.value

        if instrument == 'NIRCam':
            self.figure.marks[0].colors = [self.nircam_color]
        elif instrument == 'NIRSpec':
            self.figure.marks[0].colors = [self.nirspec_color]
        else:
            self.figure.marks[0].colors = [self.nirspec_color]
            self.figure.marks[1].colors = [self.nircam_color]
