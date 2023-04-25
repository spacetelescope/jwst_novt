from astropy import coordinates
import numpy as np
import pandas as pd
import pysiaf
import regions

__all__ = ['nirspec_footprint', 'nircam_short_footprint',
           'nircam_long_footprint', 'nircam_dither_footprint',
           'nircam_mosaic_footprint', 'source_catalog']


def nirspec_footprint(ra, dec, pa):
    """
    Create NIRSpec footprint regions in sky coordinates.

    The MSA center and PA offset angle are determined from the
    NRS_FULL_MSA aperture.  Apertures appearing in the footprint are:

        - NRS_FULL_MSA1
        - NRS_FULL_MSA2
        - NRS_FULL_MSA3
        - NRS_FULL_MSA4
        - NRS_FULL_IFU
        - NRS_FULL_IFU
        - NRS_S400A1_SLIT
        - NRS_S400A1_SLIT
        - NRS_S200A2_SLIT
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

    Returns
    -------
    footprint : regions.Regions
        NIRSpec footprint regions.  MSA center is marked with a Point
        region; all other apertures are marked with Polygon regions.
        Output regions are in sky coordinates.
    """
    # Siaf interface for NIRSpec
    nirspec = pysiaf.Siaf('NIRSpec')

    # Get center and PA offset from MSA full aperture
    msa_full = nirspec.apertures['NRS_FULL_MSA']
    msa_corners = msa_full.corners('tel')
    msa_v2 = np.mean(msa_corners[0])
    msa_v3 = np.mean(msa_corners[1])
    pa_offset = msa_full.V3IdlYAngle

    # Attitude matrix for sky coordinates
    attmat = pysiaf.utils.rotations.attitude(
        msa_v2, msa_v3, ra, dec, pa - pa_offset)

    # Aperture regions
    nrs_regions = [regions.PointSkyRegion(
        coordinates.SkyCoord(ra, dec, unit='deg'))]
    for aperture_name in ['NRS_FULL_MSA1', 'NRS_FULL_MSA2',
                          'NRS_FULL_MSA3', 'NRS_FULL_MSA4',
                          'NRS_FULL_IFU', 'NRS_FULL_IFU',
                          'NRS_S400A1_SLIT', 'NRS_S400A1_SLIT',
                          'NRS_S200A2_SLIT', 'NRS_S200B1_SLIT']:
        aperture = nirspec.apertures[aperture_name]
        aperture.set_attitude_matrix(attmat)
        poly_points = aperture.closed_polygon_points('sky')

        sky_coord = coordinates.SkyCoord(*poly_points, unit='deg')
        reg = regions.PolygonSkyRegion(sky_coord)
        nrs_regions.append(reg)

    nrs_regions = regions.Regions(nrs_regions)
    return nrs_regions


def nircam_short_footprint(ra, dec, pa):
    """
    Create NIRCam short channel footprint regions in sky coordinates.

    The NIRCam center and PA offset angle are determined from the
    NRCALL_FULL aperture.  Apertures appearing in the footprint are:

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

    Returns
    -------
    footprint : regions.Regions
        NIRCam footprint regions.  NIRCam center is marked with a Point
        region; all other apertures are marked with Polygon regions.
        Output regions are in sky coordinates.
    """
    # Siaf interface for NIRCam
    nircam = pysiaf.Siaf('NIRCam')

    # Get center and PA offset from full aperture
    nrc_full = nircam.apertures['NRCALL_FULL']
    nrc_corners = nrc_full.corners('tel', rederive=False)
    nrc_v2 = np.mean(nrc_corners[0])
    nrc_v3 = np.mean(nrc_corners[1])
    pa_offset = nrc_full.V3IdlYAngle

    # Attitude matrix for sky coordinates
    attmat = pysiaf.utils.rotations.attitude(
        nrc_v2, nrc_v3, ra, dec, pa - pa_offset)

    # Aperture regions
    nrc_regions = [regions.PointSkyRegion(
        coordinates.SkyCoord(ra, dec, unit='deg'))]
    for aperture_name in ['NRCA1_FULL', 'NRCA2_FULL',
                          'NRCA3_FULL', 'NRCA4_FULL',
                          'NRCB1_FULL', 'NRCB2_FULL',
                          'NRCB3_FULL', 'NRCB4_FULL']:
        aperture = nircam.apertures[aperture_name]
        aperture.set_attitude_matrix(attmat)
        poly_points = aperture.closed_polygon_points('sky')

        sky_coord = coordinates.SkyCoord(*poly_points, unit='deg')
        reg = regions.PolygonSkyRegion(sky_coord)
        nrc_regions.append(reg)

    nrc_regions = regions.Regions(nrc_regions)
    return nrc_regions


def nircam_long_footprint(ra, dec, pa):
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

    Returns
    -------
    footprint : regions.Regions
        NIRCam footprint regions.  NIRCam center is marked with a Point
        region; all other apertures are marked with Polygon regions.
        Output regions are in sky coordinates.
    """
    # Siaf interface for NIRCam
    nircam = pysiaf.Siaf('NIRCam')

    # Get center and PA offset from full aperture
    nrc_full = nircam.apertures['NRCALL_FULL']
    nrc_corners = nrc_full.corners('tel', rederive=False)
    nrc_v2 = np.mean(nrc_corners[0])
    nrc_v3 = np.mean(nrc_corners[1])
    pa_offset = nrc_full.V3IdlYAngle

    # Attitude matrix for sky coordinates
    attmat = pysiaf.utils.rotations.attitude(
        nrc_v2, nrc_v3, ra, dec, pa - pa_offset)

    # Aperture regions
    nrc_regions = [regions.PointSkyRegion(
        coordinates.SkyCoord(ra, dec, unit='deg'))]
    for aperture_name in ['NRCA5_FULL', 'NRCB5_FULL']:
        aperture = nircam.apertures[aperture_name]
        aperture.set_attitude_matrix(attmat)
        poly_points = aperture.closed_polygon_points('sky')

        sky_coord = coordinates.SkyCoord(*poly_points, unit='deg')
        reg = regions.PolygonSkyRegion(sky_coord)
        nrc_regions.append(reg)

    nrc_regions = regions.Regions(nrc_regions)
    return nrc_regions


def nircam_dither_footprint():
    raise NotImplementedError


def nircam_mosaic_footprint():
    raise NotImplementedError


def source_catalog(catalog_file):
    """
    Create point regions for a source catalog.

    The input catalog is in '.radec' form.  Three whitespace-separated
    columns are expected: RA, Dec, and flag.  RA and Dec must be in degrees.
    The flag may be 'P' for primary source or 'F' for filler.

    Parameters
    ----------
    catalog_file : str
        Path to a .radec catalog file.

    Returns
    -------
    primary_sources, filler_sources : regions.Regions, regions.Regions
        Catalog source regions, returned as 2 separate sets for primary
        and filler sources. All contained regions are Point regions in
        sky coordinates.
    """
    # load the source catalog
    catalog = pd.read_table(catalog_file, names=['ra', 'dec', 'flag'],
                            delim_whitespace=True, usecols=[0, 1, 2])

    filler = (catalog['flag'] == 'F')
    primary = ~filler

    primary_regions = []
    for ra, dec in zip(catalog['ra'][primary], catalog['dec'][primary]):
        primary_regions.append(
            regions.PointSkyRegion(coordinates.SkyCoord(ra, dec, unit='deg')))

    filler_regions = []
    for ra, dec in zip(catalog['ra'][filler], catalog['dec'][filler]):
        filler_regions.append(
            regions.PointSkyRegion(coordinates.SkyCoord(ra, dec, unit='deg')))

    return regions.Regions(primary_regions), regions.Regions(filler_regions)
