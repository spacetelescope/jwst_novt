from contextlib import contextmanager, ExitStack
import re

import bqplot
import pandas as pd
import regions

from novt import footprints as fp
from novt.constants import INSTRUMENT_NAMES, DEFAULT_COLOR


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


def bqplot_footprint(figure, instrument, ra, dec, pa, wcs,
                     dither_pattern='NONE',
                     mosaic_v2=0.0, mosaic_v3=0.0,
                     color=None, visible=True, fill='inside',
                     alpha=0.5, update_patches=None):
    inst = re.sub(r'\s', '_', instrument.strip().lower())
    inst = INSTRUMENT_NAMES[inst]

    # get footprint configuration by instrument
    if color is None:
        color = DEFAULT_COLOR[inst]

    # make regions
    if inst == 'NIRSpec':
        regs = fp.nirspec_footprint(ra, dec, pa)
    else:
        # 'NIRCam Short' or 'NIRCam Long'
        channel = inst.split()[-1].lower()
        regs = fp.nircam_dither_footprint(
            ra, dec, pa, channel=channel,
            dither_pattern=dither_pattern,
            mosaic_v2=mosaic_v2, mosaic_v3=mosaic_v3)

    # get scales from figure
    scales = {'x': figure.interaction.x_scale, 'y': figure.interaction.y_scale}

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
                mark = bqplot.Scatter(x=[pixel_region.center.x],
                                      y=[pixel_region.center.y],
                                      scales=scales, colors=[color],
                                      marker='plus')
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
                    mark.fill_opacities = [alpha]
            else:
                # instrument aperture regions
                mark = bqplot.Lines(x=x_coords, y=y_coords, scales=scales,
                                    fill=fill, colors=[color], stroke_width=2,
                                    close_path=True, opacities=[alpha],
                                    fill_opacities=[alpha])

        mark.visible = visible
        marks.append(mark)

    if update_patches is None:
        figure.marks = figure.marks + marks
    return marks


def bqplot_catalog(figure, catalog_file, wcs,
                   colors=None, visible=True, fill=False, alpha=1.0):
    if colors is None:
        colors = ['red', 'yellow']

    # load the source catalog
    catalog = pd.read_table(catalog_file, names=['ra', 'dec', 'flag'],
                            delim_whitespace=True, usecols=[0, 1, 2])

    # sort by flag
    filler = (catalog['flag'] == 'F')
    primary = ~filler

    fill_x, fill_y = wcs.wcs_world2pix(
        catalog['ra'][filler], catalog['dec'][filler], 0)

    primary_x, primary_y = wcs.wcs_world2pix(
        catalog['ra'][primary], catalog['dec'][primary], 0)

    # get scales from figure
    scales = {'x': figure.interaction.x_scale, 'y': figure.interaction.y_scale}

    # scatter plot for primary markers
    primary_markers = bqplot.Scatter(
        x=primary_x, y=primary_y, scales=scales, colors=[colors[0]],
        marker='circle', fill=fill)
    primary_markers.visible = visible
    primary_markers.default_opacities = [alpha]

    # scatter plot for filler markers
    filler_markers = bqplot.Scatter(
        x=fill_x, y=fill_y, scales=scales, colors=[colors[1]],
        marker='circle', fill=fill)
    filler_markers.visible = visible
    filler_markers.default_opacities = [alpha]

    # place catalog markers at the front of the list, so it always appears
    # behind any other overlays
    figure.marks = [primary_markers, filler_markers] + figure.marks

    return primary_markers, filler_markers


def remove_bqplot_patches(figure, patches):
    marks = figure.marks.copy()
    for patch in patches:
        marks.remove(patch)
    figure.marks = marks
