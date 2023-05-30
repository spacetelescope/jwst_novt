import datetime
import warnings

import numpy as np
import pandas as pd
from astropy.time import Time

try:
    from jwst_gtvt.jwst_tvt import Ephemeris
except ImportError:  # pragma: no cover
    warnings.warn("Missing refactored jwst_gtvt; using local copy.", stacklevel=2)
    from jwst_novt.ephemeris.jwst_tvt import Ephemeris

    GTVT_VERSION = "local"
else:  # pragma: no cover
    GTVT_VERSION = "released"

from jwst_novt.constants import JWST_MAXIMUM_DATE, JWST_MINIMUM_DATE

__all__ = ["timeline"]


def timeline(ra, dec, start_date=None, end_date=None, instrument=None):
    """
    Retrieve a visibility timeline for NIRSpec and NIRCam.

    Calls `jwst_gtvt.Ephemeris` for target visibility and position
    angle (PA). PA values for times at which the target is not visible
    are set to NaN.

    Parameters
    ----------
    ra : float
        Instrument center RA in degrees.
    dec : float
        Instrument center Dec in degrees.
    start_date : astropy.time.Time, optional
        If not specified, the current time is used.
    end_date : astropy.time.Time, optional
        If not specified, the start_date plus one year is used.
    instrument : {'NIRSpec', 'NIRCam'}, optional
        If not specified, both NIRSpec and NIRCam data are returned,
        using the same RA and Dec for the instrument center.

    Returns
    -------
    timeline_dataframe : pandas.DataFrame
        Columns are Time (datetime), V3PA (JWST V3 PA),
        {instrument}_min_PA (minimum PA for instrument),
        and {instrument}_max_PA (maximum PA for instrument),
        where instrument may be NIRCAM, NIRSPEC, or both.
    """
    if GTVT_VERSION == "local":  # pragma: no cover
        warnings.warn(
            "Timeline should be computed with the "
            "refactored `jwst_gtvt` package, when available.",
            DeprecationWarning,
            stacklevel=2,
        )

    # default start date to now
    if start_date is None:
        start_date = Time.now()

    # default end date to start date + one year
    if end_date is None:
        end_date = start_date + datetime.timedelta(days=365)

    # check for reasonable values
    if end_date <= start_date:
        msg = "End date must be later than start date."
        raise ValueError(msg)
    if start_date < Time(JWST_MINIMUM_DATE) - datetime.timedelta(days=1):
        msg = f"No JWST ephemeris available prior to {JWST_MINIMUM_DATE}"
        raise ValueError(msg)
    if end_date > Time(JWST_MAXIMUM_DATE):
        msg = f"No JWST ephemeris available after {JWST_MAXIMUM_DATE}"
        raise ValueError(msg)

    ephemeris = Ephemeris(start_date=start_date, end_date=end_date)
    ephemeris.get_fixed_target_positions(str(ra), str(dec))

    if instrument is None:
        instruments = ["NIRSpec", "NIRCam"]
    else:
        instruments = [instrument]

    # get the dataframe from the ephemeris
    ephem = ephemeris.dataframe
    times = Time(ephem["MJD"], format="mjd").datetime

    # when the specified position is not in the Field of Regard (FOR),
    # set the PA to NaN
    not_visible = ~ephem["in_FOR"]
    ephem.loc[not_visible, "V3PA"] = np.nan

    # relevant data for this application is the V3 position angle (PA)
    # and NIRSpec and NIRCam min and max PA
    timeline_data = {"Time": times, "V3PA": ephem["V3PA"]}
    for instrument in instruments:
        for key in ["min", "max"]:
            col = instrument.upper() + f"_{key}_pa_angle"
            ephem.loc[not_visible, col] = np.nan
            timeline_data[col.replace("pa_angle", "PA")] = ephem[col]

    return pd.DataFrame(timeline_data)
