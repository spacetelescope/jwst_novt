import datetime
import re
from contextlib import ExitStack, contextmanager, suppress
from functools import partial

import bqplot
import ipywidgets as ipw
import numpy as np
import pandas as pd
import regions
from astropy import units as u
from astropy.stats import circmean
from astropy.time import Time

from jwst_novt import footprints as fp
from jwst_novt import timeline as tl
from jwst_novt.constants import DEFAULT_COLOR, INSTRUMENT_NAMES

__all__ = [
    "hold_all_sync",
    "bqplot_figure",
    "bqplot_footprint",
    "bqplot_catalog",
    "bqplot_timeline",
    "remove_bqplot_patches",
    "BqplotToolbar",
]


@contextmanager
def hold_all_sync(marks):
    """
    Hold sync for a set of bqplot marks.

    Each mark entry will have its own hold_sync context manager invoked,
    so that syncing is performed only when all changes on the marks are
    complete.

    Parameters
    ----------
    marks : list of bqplot.Mark
        A list of patches to update together.
    """
    with ExitStack() as stack:
        for mark in marks:
            stack.enter_context(mark.hold_sync())
        yield


def bqplot_figure(*, toolbar=False):
    """
    Make a bqplot figure.

    Parameters
    ----------
    toolbar : bool, optional
        If set, a custom toolbar widget is generated, associated
        with the new figure, and returned along with the figure
        instance.

    Returns
    -------
    fig : bqplot.Figure
        An empty top-level bqplot figure.
    tools : BqplotToolbar, optional
        A widget containing controls to reset plot limits and enable pan/zoom
        in x/y, x, or y directions. Returned if `toolbar` is set.
    """
    fig = bqplot.Figure()
    if toolbar:
        tools = BqplotToolbar(fig).widgets
        return fig, tools
    return fig


def bqplot_footprint(
    fig,
    instrument,
    ra,
    dec,
    pa,
    wcs,
    *,
    dither_pattern=None,
    add_mosaic=False,
    mosaic_offset=None,
    color=None,
    visible=True,
    fill="inside",
    alpha=1.0,
    fill_alpha=0.5,
    update_patches=None,
):
    """
    Create an instrument footprint as an overlay in a bqplot figure.

    Overlays are created from sky regions calculated in `jwst_novt.footprints`.
    Sky coordinates are translated to pixel coordinates using the input
    WCS structure. Aperture overlay marks are closed polygon regions
    implemented as `bqplot.Lines`. The center position is marked with a
    single-point `bqplot.Scatter` mark.

    For improved performance, patches may be updated in place by passing
    them in the `update_patches` parameter.  In this case, the number and
    order of marks passed in must match the number and order of regions
    newly generated by the footprints function for the input instrument
    configuration.

    Patches added to the figure remain until they are explicitly
    removed. The `remove_bqplot` function may be used to remove any
    patches no longer needed.

    Parameters
    ----------
    fig : bqplot.Figure
        The bqplot figure to add aperture overlays to.
    instrument : {'NIRSpec', 'NIRCam Short', 'NIRCam Long'}
        The instrument to display.
    ra : float
        RA of instrument center, in degrees.
    dec : float
        Dec of instrument center, in degrees.
    pa : float
        Position angle for instrument, in degrees measured from North
        to central MSA vertical axis in North to East direction.
    wcs : astropy.wcs.WCS
        WCS structure, used to translate sky coordinates to pixel positions
        in the displayed image.
    dither_pattern : str, optional
        Name of the NIRCam dither pattern to apply.  Options are: NONE, FULL3,
        FULL3TIGHT, FULL6, 8NIRSPEC. Ignored if `instrument` is NIRSpec.
    add_mosaic : bool, optional
        If False, mosaic offsets are ignored. Otherwise, a two-tile
        mosaic is computed with window width specified in `mosaic_offset`.
    mosaic_offset : tuple or list, optional
        (V2, V3) offset in telescope coordinates to apply as a two-tile
        mosaic offset.  The offset is specified as a window width around
        the pointing center: the mosaic position will be at the center +/-
        offset / 2. Ignored if `dither_pattern` is 8NIRSPEC or `instrument`
        is NIRSpec or `add_mosaic` is not set.
    color : str, optional
        Color to apply to the aperture footprint. If not specified, default
        colors are applied.
    visible : bool, optional
        If False, the overlay is added to the figure but initially hidden.
    fill : str, optional
        Fill option to pass to `bqplot.Lines`.
    alpha : float, optional
        Opacity setting for the overlay border.
    fill_alpha : float, optional
        Opacity setting for the overlay fill.
    update_patches : list of bqplot.Mark, optional
        If provided, no new patches are created; the marks in `update_patches`
        are updated in place. This option can improve performance, but
        can only be used if the number and type of new patches exactly
        matches the input patches.

    Returns
    -------
    marks : list of bqplot.Mark
        Marks added to the figure.
    """
    # standardize input
    inst = re.sub(r"\s", "_", instrument.strip().lower())
    inst = INSTRUMENT_NAMES[inst]

    dither_pattern = str(dither_pattern).strip().upper()

    # get footprint configuration by instrument
    if color is None:
        color = DEFAULT_COLOR[inst]

    # make regions
    if inst == "NIRSpec":
        regs = fp.nirspec_footprint(ra, dec, pa)
    else:
        # 'NIRCam Short' or 'NIRCam Long'
        channel = inst.split()[-1].lower()
        regs = fp.nircam_dither_footprint(
            ra,
            dec,
            pa,
            channel=channel,
            dither_pattern=dither_pattern,
            add_mosaic=add_mosaic,
            mosaic_offset=mosaic_offset,
        )

    # get scales from figure
    scales = {"x": fig.interaction.x_scale, "y": fig.interaction.y_scale}

    marks = []
    for i, reg in enumerate(regs):
        pixel_region = reg.to_pixel(wcs)
        if isinstance(pixel_region, regions.PointPixelRegion):
            if update_patches is not None:
                mark = update_patches[i]
                with mark.hold_sync():
                    mark.x = [pixel_region.center.x]
                    mark.y = [pixel_region.center.y]
                    mark.colors = [color]
                    mark.default_opacities = [alpha]
            else:
                # instrument center point
                mark = bqplot.Scatter(
                    x=[pixel_region.center.x],
                    y=[pixel_region.center.y],
                    scales=scales,
                    colors=[color],
                    marker="plus",
                )
                mark.default_opacities = [alpha]
        else:
            x_coords = pixel_region.vertices.x
            y_coords = pixel_region.vertices.y
            if update_patches is not None:
                mark = update_patches[i]
                with mark.hold_sync():
                    mark.x = x_coords
                    mark.y = y_coords
                    mark.fill = fill
                    mark.colors = [color]
                    mark.opacities = [alpha]
                    mark.fill_opacities = [fill_alpha]
            else:
                # instrument aperture regions
                mark = bqplot.Lines(
                    x=x_coords,
                    y=y_coords,
                    scales=scales,
                    fill=fill,
                    colors=[color],
                    stroke_width=2,
                    close_path=True,
                    opacities=[alpha],
                    fill_opacities=[fill_alpha],
                )

        mark.visible = visible
        marks.append(mark)

    if update_patches is None:
        fig.marks = fig.marks + marks
    return marks


def bqplot_catalog(
    fig, catalog_file, wcs, *, colors=None, visible=True, fill=False, alpha=1.0
):
    """
    Create a catalog source overlay on a bqplot figure.

    Overlays are created directly from an input catalog file containing
    RA and Dec sky coordinates for primary and filler sources.  The input
    WCS structure is used to convert the coordinates to pixel positions.
    The catalog is implemented as two `bqplot.Scatter` overlays: one for
    the primary sources, and one for the filler sources.

    The input catalog is in '.radec' form.  Three whitespace-separated
    columns are expected: RA, Dec, and flag.  RA and Dec must be in degrees.
    The flag may be 'P' for primary source or 'F' for filler.

    Parameters
    ----------
    fig : bqplot.Figure
        The bqplot figure to add catalog overlays to.
    catalog_file : str
        Path to a .radec catalog file.
    wcs : astropy.wcs.WCS
        WCS structure, used to translate sky coordinates to pixel positions
        in the displayed image.
    colors : list of str, optional
        If provided, must be a 2-element list or tuple of color names for
        primary and filler sources, in that order. If not provided, default
        colors will be assigned.
    visible : bool, optional
        If False, the overlay is added to the figure but initially hidden.
    fill : bool, optional
        Fill option to pass to `bqplot.Scatter`.
    alpha : float, optional
        Opacity setting for the overlay.

    Returns
    -------
    marks : list of bqplot.Mark
        Marks added to the figure.
    """
    if colors is None:
        colors = [DEFAULT_COLOR["Primary Sources"], DEFAULT_COLOR["Filler Sources"]]

    # load the source catalog
    try:
        catalog = pd.read_csv(
            catalog_file,
            names=["ra", "dec", "flag"],
            delim_whitespace=True,
            usecols=[0, 1, 2],
        )
    except ValueError:
        # if the catalog file is a file object, it may need to be rewound
        # before reading again
        with suppress(AttributeError):
            catalog_file.seek(0)

        catalog = pd.read_csv(
            catalog_file, names=["ra", "dec"], delim_whitespace=True, usecols=[0, 1]
        )
        catalog["flag"] = "P"
    finally:
        with suppress(AttributeError):
            catalog_file.seek(0)

    if len(catalog.index) == 0:
        msg = "Catalog file is empty."
        raise ValueError(msg)

    # sort by flag
    filler = catalog["flag"] == "F"
    primary = ~filler

    fill_x, fill_y = wcs.wcs_world2pix(catalog["ra"][filler], catalog["dec"][filler], 0)

    primary_x, primary_y = wcs.wcs_world2pix(
        catalog["ra"][primary], catalog["dec"][primary], 0
    )

    # get scales from figure
    scales = {"x": fig.interaction.x_scale, "y": fig.interaction.y_scale}

    # scatter plot for primary markers
    primary_markers = bqplot.Scatter(
        x=primary_x,
        y=primary_y,
        scales=scales,
        colors=[colors[0]],
        marker="circle",
        fill=fill,
    )
    primary_markers.visible = visible
    primary_markers.default_opacities = [alpha]

    # scatter plot for filler markers
    filler_markers = bqplot.Scatter(
        x=fill_x,
        y=fill_y,
        scales=scales,
        colors=[colors[1]],
        marker="circle",
        fill=fill,
    )
    filler_markers.visible = visible
    filler_markers.default_opacities = [alpha]

    # place catalog markers at the front of the list, so it always appears
    # behind any other overlays
    fig.marks = [filler_markers, primary_markers, *fig.marks]

    return primary_markers, filler_markers


def _average_pa(time_data, min_pa, max_pa, min_time=None, max_time=None, method="mean"):
    """Describe the average PA value within a specified time range."""
    if min_time is not None and max_time is not None:
        in_range = (time_data >= min_time) & (time_data <= max_time)
        all_pa = np.array([min_pa[in_range], max_pa[in_range]]) * u.deg
    else:
        all_pa = np.array([min_pa, max_pa]) * u.deg

    if method == "mode":
        nnan = ~np.isnan(all_pa[0]) | ~np.isnan(all_pa[1])
        if np.sum(nnan) > 0:
            all_pa = circmean(all_pa[:, nnan], axis=0).value
            val, ct = np.unique(np.round(all_pa).astype(int), return_counts=True)
            avg_pa = (val[ct.argmax()] + 360) % 360
        else:
            avg_pa = np.nan
    else:
        nnan = ~np.isnan(all_pa)
        avg_pa = (circmean(all_pa[nnan]).value + 360) % 360

    if np.isnan(avg_pa):
        pa_label = "(not visible)"
    else:
        pa_label = f"Avg. PA: {avg_pa:.0f} deg"
    return pa_label


def bqplot_timeline(
    fig,
    ra,
    dec,
    *,
    start_date=None,
    end_date=None,
    instrument=None,
    show_v3pa=True,
    colors=None,
):
    """
    Plot a visibility timeline in a bqplot figure.

    Visibility and position angle data at the specified target,
    between the start and end dates, is calculated in `jwst_novt.timeline`.
    This calculation retrieves ephemeris data from JPL Horizons, so it
    requires an internet connection to run and may take some time to
    return. The plot will display a temporary message while the
    calculation is running. If no data is returned, it will show an
    error message. If timeline data is returned, the plot will show
    available position angle ranges for the specified instrument(s)
    over the specified dates.

    Parameters
    ----------
    fig : bqplot.Figure
        The bqplot figure to contain the plot.
    ra : float
        RA of instrument center, in degrees.
    dec : float
        Dec of instrument center, in degrees.
    start_date : str, optional
        Start date, specified as YYYY-MM-DD. If not specified, today's
        date is used as default.
    end_date : str, optional
        End date, specified as YYYY-MM-DD. If not specified, the default
        is start_date + 1 year.
    instrument : {'NIRSpec', 'NIRCam'}, optional
        The instrument to display. If not specified, both instruments
        are shown.
    show_v3pa : bool, optional
        If set, the V3 position angle for JWST is shown on the plot,
        as a gray line.
    colors : list or tuple of str, optional
        Colors to apply to the plot. If not specified, default
        colors are applied. If both instruments are requested, colors
        should be specified as (NIRSpec color, NIRCam color).
    """
    # clear figure and set loading message
    clear_bqplot_figure(fig)
    message = bqplot.Label(
        text=["Computing timeline..."], x=[0.5], y=[0.5], align="middle"
    )
    fig.marks = [message]

    if start_date is not None:
        start_date = Time(start_date) - datetime.timedelta(days=1)
    if end_date is not None:
        end_date = Time(end_date)

    # get timeline for NIRSpec and NIRCam at the same position
    if instrument is None:
        instruments = ["NIRSpec", "NIRCam"]
    else:
        instruments = [instrument]
    try:
        timeline_data = tl.timeline(
            ra, dec, start_date=start_date, end_date=end_date, instrument=instrument
        )
    except Exception:
        timeline_data = None

    clear_bqplot_figure(fig)
    title = f"Visibility for {', '.join(instruments)} at RA={ra}, Dec={dec}"
    marks = []
    scales = {"x": bqplot.DateScale(), "y": bqplot.LinearScale()}
    if timeline_data is None:
        message = bqplot.Label(
            text=["No timeline data for input date range."],
            x=[0.5],
            y=[0.5],
            align="middle",
        )
        marks.append(message)
    else:
        # add V3PA line if desired
        if show_v3pa and len(marks) == 0:
            color = DEFAULT_COLOR["V3PA"]
            line = bqplot.Lines(
                x=timeline_data["Time"],
                y=timeline_data["V3PA"],
                scales=scales,
                colors=[color],
                labels=["JWST V3 PA"],
                display_legend=True,
            )
            marks.append(line)

        for i, inst in enumerate(instruments):
            if colors is None:
                color = DEFAULT_COLOR[inst]
            else:
                color = colors[i]

            min_pa = timeline_data[f"{inst.upper()}_min_PA"]
            max_pa = timeline_data[f"{inst.upper()}_max_PA"]
            avg_pa = _average_pa(timeline_data["Time"], min_pa, max_pa)
            line = bqplot.Lines(
                x=timeline_data["Time"],
                y=[min_pa, max_pa],
                scales=scales,
                colors=[color],
                fill="between",
                fill_opacities=[0.5],
                labels=[inst, avg_pa],
                display_legend=True,
            )
            marks.append(line)

            # add a little callback to update the legend with the
            # average PA value in range, when the plot is zoomed
            def _set_pa_label(inst_, line_, *args):
                pa_label = _average_pa(
                    timeline_data["Time"],
                    timeline_data[f"{inst_.upper()}_min_PA"],
                    timeline_data[f"{inst_.upper()}_max_PA"],
                    scales["x"].min,
                    scales["x"].max,
                )
                line_.labels = [inst_, pa_label]

            scales["x"].observe(partial(_set_pa_label, inst, line), names=["max"])

    fig.title = title.rstrip(",")
    fig.legend_location = "top-right"
    fig.marks = marks
    fig.axes = [
        bqplot.Axis(scale=scales["x"], label="Date"),
        bqplot.Axis(
            scale=scales["y"], label="Position Angle (deg)", orientation="vertical"
        ),
    ]


def remove_bqplot_patches(fig, patches):
    """
    Remove patches from a bqplot figure.

    Parameters
    ----------
    fig : bqplot.Figure
        The figure to update.
    patches : list of bqplot.Mark
        The patches to remove.
    """
    marks = fig.marks.copy()
    for patch in patches:
        try:
            marks.remove(patch)
        except ValueError:
            continue
    fig.marks = marks


def clear_bqplot_figure(fig):
    """Clear a bqplot figure."""
    fig.marks = []
    fig.axes = []
    fig.axis_registry = {}


class BqplotToolbar:
    """
    Custom toolbar with reset and zoom controls.

    Pan/zoom controls can be toggled between x-axis only, y-axis only,
    both axes, and no zoom. A reset button (home icon) resets plot limits
    to default.

    After creation, widgets are contained in a VBox layout in the `widgets`
    attribute.
    """

    def __init__(self, fig):
        self.fig = fig

        self.pan_zoom = None
        self.direction = " "
        self.fig.observe(self.set_scales, "axes")

        self.reset_button = ipw.Button(tooltip="Reset plot limits", icon="home")
        self.reset_button.layout.width = "50px"
        self.reset_button.on_click(self.reset_zoom)

        # note: toggle display doesn't seem to work if buttons
        # have identical labels, even if their values and icons
        # are different
        self.mode_buttons = ipw.ToggleButtons(
            options=[("", " "), (" ", "xy"), ("  ", "x"), ("   ", "y")],
            icons=["stop", "arrows", "arrows-h", "arrows-v", "stop"],
            tooltips=[
                "No zoom mode",
                "Scroll to zoom, drag to pan",
                "Pan/zoom in X only",
                "Pan/zoom in Y only",
            ],
            layout=ipw.Layout(align_items="center"),
        )
        self.mode_buttons.style.button_width = "50px"
        self.mode_buttons.observe(self.set_zoom_mode, "value")

        self.widgets = ipw.VBox(
            children=[ipw.HBox([self.reset_button, self.mode_buttons])],
            layout=ipw.Layout(align_items="center"),
        )

    def reset_zoom(self, *args, **kwargs):
        """Reset the plot limits."""
        if len(self.fig.axes) == 0:
            return
        self.fig.axes[0].scale.min = None
        self.fig.axes[0].scale.max = None
        self.fig.axes[1].scale.min = None
        self.fig.axes[1].scale.max = None

    def set_scales(self, *args, **kwargs):
        """Set the axis scales (x, y, or both) in the pan/zoom tool."""
        if len(self.fig.axes) == 0:
            self.mode_buttons.value = " "
            return

        x_scale = self.fig.axes[0].scale
        y_scale = self.fig.axes[1].scale
        if self.pan_zoom is None:
            # note: fig.interaction needs to be set only once -
            # setting to None to turn off interaction disrupts mouse
            # event handling the next time an interaction is set.
            # Turn off interaction directly in the PanZoom
            # instance instead.
            self.pan_zoom = bqplot.interacts.PanZoom()
            self.fig.interaction = self.pan_zoom
        if self.direction == "x":
            self.pan_zoom.scales = {"x": [x_scale]}
            self.pan_zoom.allow_zoom = True
            self.pan_zoom.allow_pan = True
        elif self.direction == "y":
            self.pan_zoom.scales = {"y": [y_scale]}
            self.pan_zoom.allow_zoom = True
            self.pan_zoom.allow_pan = True
        elif self.direction == "xy":
            self.pan_zoom.scales = {"x": [x_scale], "y": [y_scale]}
            self.pan_zoom.allow_zoom = True
            self.pan_zoom.allow_pan = True
        else:
            self.pan_zoom.allow_zoom = False
            self.pan_zoom.allow_pan = False

    def set_zoom_mode(self, *args, **kwargs):
        """Set the zoom mode (x, y, both, or None)."""
        self.direction = self.mode_buttons.value
        self.set_scales()
