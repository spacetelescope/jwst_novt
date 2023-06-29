import datetime

import ipyvuetify as v
import ipywidgets as ipw
from traitlets import Any, Float, HasTraits, Unicode

from jwst_novt.constants import (
    DEFAULT_COLOR,
    JWST_MINIMUM_DATE,
)
from jwst_novt.interact import display as nd
from jwst_novt.timeline import jwst_maximum_date

__all__ = ["ShowTimeline"]


class ShowTimeline(HasTraits):
    """Widgets to control showing and updating a visibility timeline plot."""

    center = Unicode(None, allow_none=True).tag(sync=True)
    ra = Float(0.0).tag(sync=True)
    dec = Float(0.0).tag(sync=True)
    instrument = Unicode("NIRSpec, NIRCam").tag(sync=True)
    nirspec_color = Unicode(DEFAULT_COLOR["NIRSpec"]).tag(sync=True)
    nircam_color = Unicode(DEFAULT_COLOR["NIRCam Short"]).tag(sync=True)
    start_date = Any(
        datetime.datetime.now(tz=datetime.timezone.utc).date(), allow_none=True
    ).tag(sync=True)
    end_date = Any(
        datetime.datetime.now(tz=datetime.timezone.utc).date()
        + datetime.timedelta(days=365),
        allow_none=True,
    ).tag(sync=True)

    def __init__(self):
        super().__init__()

        self.title = "Show Timeline"

        # bqplot figure to display
        self.figure = None
        self.toolbar = None
        self.figure_container = ipw.VBox()

        # start, end dates
        min_date = datetime.date.fromisoformat(JWST_MINIMUM_DATE)
        max_date = datetime.date.fromisoformat(jwst_maximum_date())

        self.set_start = ipw.DatePicker(
            description="Start date",
            style={"description_width": "initial"},
            min=min_date,
            max=max_date,
            tooltip="Start date for target visibility",
        )
        self.set_end = ipw.DatePicker(
            description="End date",
            style={"description_width": "initial"},
            min=min_date,
            max=max_date,
            tooltip="End date for target visibility",
        )

        ipw.link((self, "start_date"), (self.set_start, "value"))
        ipw.link((self, "end_date"), (self.set_end, "value"))

        # select instrument
        self.set_instrument = ipw.Dropdown(
            description="Instrument",
            options=["NIRSpec, NIRCam", "NIRSpec", "NIRCam"],
            style={"description_width": "initial"},
            tooltip="Instruments to include in plot",
        )
        ipw.link((self, "instrument"), (self.set_instrument, "value"))

        # re-make plot if instrument or dates change
        self.set_start.observe(self._make_timeline, "value")
        self.set_end.observe(self._make_timeline, "value")
        self.set_instrument.observe(self._make_timeline, "value")

        # make/save/close plot
        self.make_plot = v.Btn(
            color="primary", class_="mx-2 my-2", children=["Make timeline plot"]
        )
        self.make_plot.on_event("click", self._show_plot)

        self.save_plot = v.Btn(
            color="primary", class_="mx-2 my-2", children=["Save plot"]
        )
        self.save_plot.on_event("click", self._save_plot)

        self.close_plot = v.Btn(
            color="primary", class_="mx-2 my-2", children=["Close plot"]
        )
        self.close_plot.on_event("click", self._clear_plot)

        # link color changes to plot update
        self.observe(self._update_colors, names=["nirspec_color", "nircam_color"])

        # clear plot if center object changes
        self.observe(self._clear_plot, names=["center"])

        # save plot

        button_layout = ipw.Layout(
            display="flex", flex_flow="row", justify_content="flex-start"
        )
        box_layout = ipw.Layout(
            display="flex", flex_flow="column", align_items="stretch"
        )
        b1 = ipw.Box(
            children=[self.set_start, self.set_end, self.set_instrument],
            layout=button_layout,
        )
        b2 = ipw.Box(
            children=[self.make_plot, self.save_plot, self.close_plot],
            layout=button_layout,
        )
        box = ipw.Box(children=[b1, b2, self.figure_container], layout=box_layout)
        self.widgets = ipw.Accordion(children=[box], titles=[self.title])

    def _clear_plot(self, *args, **kwargs):
        """Clear and hide the current figure."""
        if self.figure is not None:
            nd.clear_bqplot_figure(self.figure)
        self.figure_container.children = []

    def _make_timeline(self, *args, **kwargs):
        """Make a timeline plot."""
        if self.figure is None or len(self.figure_container.children) == 0:
            return

        controls = [self.make_plot, self.save_plot, self.close_plot]
        for control in controls:
            control.disabled = True
        try:
            # check for instrument
            instrument = self.set_instrument.value
            if instrument == "NIRCam":
                colors = [self.nircam_color]
            elif instrument == "NIRSpec":
                colors = [self.nirspec_color]
            else:
                instrument = None
                colors = [self.nirspec_color, self.nircam_color]

            # check for start, end date
            start_date = self.set_start.value
            end_date = self.set_end.value
            if start_date is not None:
                start_date = start_date.strftime("%Y-%m-%d")
            if end_date is not None:
                end_date = end_date.strftime("%Y-%m-%d")

            # original does one position only - use nirspec center
            nd.bqplot_timeline(
                self.figure,
                self.ra,
                self.dec,
                instrument=instrument,
                start_date=start_date,
                end_date=end_date,
                colors=colors,
            )
        finally:
            for control in controls:
                control.disabled = False

    def _save_plot(self, *args, **kwargs):
        """Download a PNG image of the current plot."""
        if self.figure is None or len(self.figure_container.children) == 0:
            return

        start_date = self.set_start.value
        if start_date is None:
            start_date = datetime.datetime.now(tz=datetime.timezone.utc).date()
        filename = f"novt_timeline_{start_date.strftime('%Y%m%d')}"

        end_date = self.set_end.value
        if end_date is not None:
            filename += f"-{end_date.strftime('%Y%m%d')}"
        filename += ".png"

        self.figure.save_png(filename=filename)

    def _show_plot(self, *args, **kwargs):
        """Show the figure window and make a timeline plot."""
        if self.figure is None:
            self.figure, self.toolbar = nd.bqplot_figure(toolbar=True)

        # center toolbar
        self.figure_container.children = [self.figure, self.toolbar]
        self._make_timeline()

    def _update_colors(self, *args, **kwargs):
        """Update colors in the current plot."""
        if self.figure is None:
            return
        instrument = self.set_instrument.value

        if instrument == "NIRCam":
            self.figure.marks[1].colors = [self.nircam_color]
        elif instrument == "NIRSpec":
            self.figure.marks[1].colors = [self.nirspec_color]
        else:
            self.figure.marks[1].colors = [self.nirspec_color]
            self.figure.marks[2].colors = [self.nircam_color]
