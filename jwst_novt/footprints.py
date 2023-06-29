import numpy as np
import pandas as pd
import pysiaf
import regions
from astropy import coordinates

from jwst_novt.constants import NIRCAM_DITHER_OFFSETS, NO_MOSAIC

__all__ = [
    "nirspec_footprint",
    "nircam_short_footprint",
    "nircam_long_footprint",
    "nircam_dither_footprint",
    "source_catalog",
]


def nirspec_footprint(ra, dec, pa, *, include_center=True, apertures=None):
    """
    Create NIRSpec footprint regions in sky coordinates.

    The MSA center and PA offset angle are determined from the
    NRS_FULL_MSA aperture.  Apertures appearing in the footprint are,
    by default:

        - NRS_FULL_MSA1
        - NRS_FULL_MSA2
        - NRS_FULL_MSA3
        - NRS_FULL_MSA4
        - NRS_FULL_IFU
        - NRS_S200A1_SLIT
        - NRS_S200A2_SLIT
        - NRS_S400A1_SLIT
        - NRS_S1600A1_SLIT
        - NRS_S200B1_SLIT


    Parameters
    ----------
    ra : float
        RA of NIRSpec MSA center, in degrees.
    dec : float
        Dec of NIRSpec MSA center, in degrees.
    pa : float
        Position angle for NIRSpec, in degrees measured from North
        to central MSA vertical axis in North to East direction.
    include_center : bool, optional
        If set, the center is marked with a Point region. If not,
        only the apertures are included in the output.
    apertures : list of str, optional
        If set, only the specified apertures are returned.

    Returns
    -------
    footprint : regions.Regions
        NIRSpec footprint regions.  MSA center is marked with a Point
        region; all other apertures are marked with Polygon regions.
        Output regions are in sky coordinates.
    """
    if apertures is None:
        apertures = [
            "NRS_FULL_MSA1",
            "NRS_FULL_MSA2",
            "NRS_FULL_MSA3",
            "NRS_FULL_MSA4",
            "NRS_FULL_IFU",
            "NRS_S200A1_SLIT",
            "NRS_S200A2_SLIT",
            "NRS_S400A1_SLIT",
            "NRS_S1600A1_SLIT",
            "NRS_S200B1_SLIT",
        ]

    # Siaf interface for NIRSpec
    nirspec = pysiaf.Siaf("NIRSpec")

    # Get center and PA offset from MSA full aperture
    msa_full = nirspec.apertures["NRS_FULL_MSA"]
    msa_corners = msa_full.corners("tel")
    msa_v2 = np.mean(msa_corners[0])
    msa_v3 = np.mean(msa_corners[1])
    pa_offset = msa_full.V3IdlYAngle

    # Attitude matrix for sky coordinates
    attmat = pysiaf.utils.rotations.attitude(msa_v2, msa_v3, ra, dec, pa - pa_offset)

    # Aperture regions
    nrs_regions = []
    if include_center:
        nrs_regions.append(
            regions.PointSkyRegion(coordinates.SkyCoord(ra, dec, unit="deg"))
        )
    for aperture_name in apertures:
        aperture = nirspec.apertures[aperture_name]
        aperture.set_attitude_matrix(attmat)
        poly_points = aperture.closed_polygon_points("sky")

        sky_coord = coordinates.SkyCoord(*poly_points, unit="deg")
        reg = regions.PolygonSkyRegion(sky_coord)
        nrs_regions.append(reg)

    return regions.Regions(nrs_regions)


def nircam_short_footprint(
    ra, dec, pa, *, v2_offset=0.0, v3_offset=0.0, include_center=True, apertures=None
):
    """
    Create NIRCam short channel footprint regions in sky coordinates.

    The NIRCam center and PA offset angle are determined from the
    NRCALL_FULL aperture.  Apertures appearing in the footprint are,
    by default:

        - NRCA1_FULL
        - NRCA2_FULL
        - NRCA3_FULL
        - NRCA4_FULL
        - NRCB1_FULL
        - NRCB2_FULL
        - NRCB3_FULL
        - NRCB4_FULL

    Parameters
    ----------
    ra : float
        RA of NIRCam center, in degrees.
    dec : float
        Dec of NIRCam center, in degrees.
    pa : float
        Position angle for NIRCam, in degrees measured from North
        to central vertical axis in North to East direction.
    v2_offset : float, optional
        Additional V2 offset in telescope coordinates to apply to instrument
        center, as from a dither pattern.
    v3_offset : float, optional
        Additional V3 offset in telescope coordinates to apply to instrument
        center, as from a dither pattern.
    include_center : bool, optional
        If set, the center is marked with a Point region. If not,
        only the apertures are included in the output.
    apertures : list of str, optional
        If set, only the specified apertures are returned.

    Returns
    -------
    footprint : regions.Regions
        NIRCam footprint regions.  NIRCam center is marked with a Point
        region; all other apertures are marked with Polygon regions.
        Output regions are in sky coordinates.
    """
    if apertures is None:
        apertures = [
            "NRCA1_FULL",
            "NRCA2_FULL",
            "NRCA3_FULL",
            "NRCA4_FULL",
            "NRCB1_FULL",
            "NRCB2_FULL",
            "NRCB3_FULL",
            "NRCB4_FULL",
        ]

    # Siaf interface for NIRCam
    nircam = pysiaf.Siaf("NIRCam")

    # Get center and PA offset from full aperture
    nrc_full = nircam.apertures["NRCALL_FULL"]
    nrc_corners = nrc_full.corners("tel", rederive=False)
    nrc_v2 = np.mean(nrc_corners[0]) - v2_offset
    nrc_v3 = np.mean(nrc_corners[1]) + v3_offset
    pa_offset = nrc_full.V3IdlYAngle

    # Attitude matrix for sky coordinates
    attmat = pysiaf.utils.rotations.attitude(nrc_v2, nrc_v3, ra, dec, pa - pa_offset)

    # Aperture regions
    nrc_regions = []
    if include_center:
        nrc_regions.append(
            regions.PointSkyRegion(coordinates.SkyCoord(ra, dec, unit="deg"))
        )

    for aperture_name in apertures:
        aperture = nircam.apertures[aperture_name]
        aperture.set_attitude_matrix(attmat)
        poly_points = aperture.closed_polygon_points("sky")

        sky_coord = coordinates.SkyCoord(*poly_points, unit="deg")
        reg = regions.PolygonSkyRegion(sky_coord)
        nrc_regions.append(reg)

    return regions.Regions(nrc_regions)


def nircam_long_footprint(
    ra, dec, pa, *, v2_offset=0.0, v3_offset=0.0, include_center=True, apertures=None
):
    """
    Create NIRCam long channel footprint regions in sky coordinates.

    The NIRCam center and PA offset angle are determined from the
    NRCALL_FULL aperture.  Apertures appearing in the footprint are:

        - NRCA5_FULL
        - NRCB5_FULL

    Parameters
    ----------
    ra : float
        RA of NIRCam center, in degrees.
    dec : float
        Dec of NIRCam center, in degrees.
    pa : float
        Position angle for NIRCam, in degrees measured from North
        to central vertical axis in North to East direction.
    v2_offset : float, optional
        Additional V2 offset in telescope coordinates to apply to instrument
        center, as from a dither pattern.
    v3_offset : float, optional
        Additional V3 offset in telescope coordinates to apply to instrument
        center, as from a dither pattern.
    include_center : bool, optional
        If set, the center is marked with a Point region. If not,
        only the apertures are included in the output.
    apertures : list of str, optional
        If set, only the specified apertures are returned.

    Returns
    -------
    footprint : regions.Regions
        NIRCam footprint regions.  NIRCam center is marked with a Point
        region; all other apertures are marked with Polygon regions.
        Output regions are in sky coordinates.
    """
    if apertures is None:
        apertures = ["NRCA5_FULL", "NRCB5_FULL"]

    # Siaf interface for NIRCam
    nircam = pysiaf.Siaf("NIRCam")

    # Get center and PA offset from full aperture
    nrc_full = nircam.apertures["NRCALL_FULL"]
    nrc_corners = nrc_full.corners("tel", rederive=False)
    nrc_v2 = np.mean(nrc_corners[0]) - v2_offset
    nrc_v3 = np.mean(nrc_corners[1]) + v3_offset
    pa_offset = nrc_full.V3IdlYAngle

    # Attitude matrix for sky coordinates
    attmat = pysiaf.utils.rotations.attitude(nrc_v2, nrc_v3, ra, dec, pa - pa_offset)

    # Aperture regions
    nrc_regions = []
    if include_center:
        nrc_regions.append(
            regions.PointSkyRegion(coordinates.SkyCoord(ra, dec, unit="deg"))
        )
    for aperture_name in apertures:
        aperture = nircam.apertures[aperture_name]
        aperture.set_attitude_matrix(attmat)
        poly_points = aperture.closed_polygon_points("sky")

        sky_coord = coordinates.SkyCoord(*poly_points, unit="deg")
        reg = regions.PolygonSkyRegion(sky_coord)
        nrc_regions.append(reg)

    return regions.Regions(nrc_regions)


def nircam_dither_footprint(
    ra,
    dec,
    pa,
    *,
    dither_pattern="NONE",
    channel="long",
    add_mosaic=False,
    mosaic_offset=None,
    include_center=True,
    apertures=None,
):
    """
    Dither and/or mosaic the NIRCam aperture footprint.

    Parameters
    ----------
    ra : float
        RA of NIRCam center, in degrees.
    dec : float
        Dec of NIRCam center, in degrees.
    pa : float
        Position angle for NIRCam, in degrees measured from North
        to central vertical axis in North to East direction.
    dither_pattern : str, optional
        Name of the dither pattern to apply.  Options are: NONE, FULL3,
        FULL3TIGHT, FULL6, 8NIRSPEC.
    channel : {'short', 'long'}, optional
        The NIRCam channel to generate aperture footprints for.
    add_mosaic : bool, optional
        If False, mosaic offsets are ignored. Otherwise, a two-tile
        mosaic is computed with window width specified in `mosaic_offset`.
    mosaic_offset : tuple or list, optional
        (V2, V3) offset in telescope coordinates to apply as a two-tile
        mosaic offset.  The offset is specified as a window width around
        the pointing center: the mosaic position will be at the center +/-
        offset / 2. Ignored if `dither_pattern` is 8NIRSPEC or `instrument`
        is NIRSpec or `add_mosaic` is not set.
    include_center : bool, optional
        If set, the center is marked with a Point region. If not,
        only the apertures are included in the output.
    apertures : list of str, optional
        If set, only the specified apertures are returned.

    Returns
    -------
    footprint : regions.Regions
        NIRCam footprint regions.  NIRCam center is marked with a Point
        region; all other apertures are marked with Polygon regions.
        Output regions are in sky coordinates.
    """
    pattern = dither_pattern.strip().upper()
    if pattern not in NIRCAM_DITHER_OFFSETS:
        msg = (
            f"Dither pattern {dither_pattern} not recognized. "
            f"Options are: {list(NIRCAM_DITHER_OFFSETS.keys())}."
        )
        raise ValueError(msg)
    dither_offsets = NIRCAM_DITHER_OFFSETS[pattern]

    if channel.strip().lower() == "short":
        footprint_func = nircam_short_footprint
    else:
        footprint_func = nircam_long_footprint

    if pattern in NO_MOSAIC:
        add_mosaic = False
    if mosaic_offset is None:
        mosaic_offset = (0.0, 0.0)

    # note: if offsets are 0 but add_mosaic is set, two
    # footprint tiles are still created
    if add_mosaic:
        center_offset = [
            (mosaic_offset[0] / 2, -mosaic_offset[1] / 2),
            (-mosaic_offset[0] / 2, mosaic_offset[1] / 2),
        ]
    else:
        center_offset = [(0, 0)]

    dithers = []
    for mosaic_position in center_offset:
        for offset in dither_offsets:
            v2 = offset[0] + mosaic_position[0]
            v3 = offset[1] + mosaic_position[1]
            reg_list = footprint_func(
                ra,
                dec,
                pa,
                v2_offset=v2,
                v3_offset=v3,
                include_center=include_center,
                apertures=apertures,
            )
            # include center only once
            include_center = False

            for reg in reg_list:
                dithers.append(reg)

    return regions.Regions(dithers)


def source_catalog(catalog_file):
    """
    Create point regions for a source catalog.

    The input catalog is in '.radec' form.  Three whitespace-separated
    columns are expected: RA, Dec, and flag.  RA and Dec must be in degrees.
    The flag may be 'P' for primary source or 'F' for filler.

    Note that this method produces a single region for each source.
    It is suitable for saving to DS9 region files, for example, but
    for display purposes, it may be faster to make a scatter plot out
    of all sources at once, directly from the catalog.  See
    `jwst_novt.display.bqplot_catalog` for an example.

    Parameters
    ----------
    catalog_file : str or pandas.DataFrame
        Path to a .radec catalog file or a DataFrame containing columns
        'ra', 'dec', and optionally, 'flag'.

    Returns
    -------
    primary_sources, filler_sources : regions.Regions, regions.Regions
        Catalog source regions, returned as 2 separate sets for primary
        and filler sources. All contained regions are Point regions in
        sky coordinates.
    """
    # load the source catalog
    if isinstance(catalog_file, pd.DataFrame):
        catalog = catalog_file
        if "flag" not in catalog:
            catalog["flag"] = "P"
    else:
        try:
            catalog = pd.read_csv(
                catalog_file,
                names=["ra", "dec", "flag"],
                delim_whitespace=True,
                usecols=[0, 1, 2],
            )
        except ValueError:
            # try again with two columns
            catalog = pd.read_csv(
                catalog_file, names=["ra", "dec"], delim_whitespace=True, usecols=[0, 1]
            )
            catalog["flag"] = "P"

    if len(catalog.index) == 0:
        msg = "Catalog file is empty."
        raise ValueError(msg)

    filler = catalog["flag"] == "F"
    primary = ~filler

    primary_regions = []
    for ra, dec in zip(catalog["ra"][primary], catalog["dec"][primary]):
        primary_regions.append(
            regions.PointSkyRegion(coordinates.SkyCoord(ra, dec, unit="deg"))
        )

    filler_regions = []
    for ra, dec in zip(catalog["ra"][filler], catalog["dec"][filler]):
        filler_regions.append(
            regions.PointSkyRegion(coordinates.SkyCoord(ra, dec, unit="deg"))
        )

    return regions.Regions(primary_regions), regions.Regions(filler_regions)
