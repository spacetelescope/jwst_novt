import datetime
import re

import numpy as np
import pandas as pd
import requests
from astropy.time import Time
from jwst_gtvt.constants import URL
from jwst_gtvt.jwst_tvt import Ephemeris

from jwst_novt.constants import JWST_MAXIMUM_DATE, JWST_MINIMUM_DATE

__all__ = ["timeline", "jwst_maximum_date"]


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
    max_date = jwst_maximum_date()
    if end_date > Time(max_date):
        msg = f"No JWST ephemeris available after {max_date}"
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


def jwst_maximum_date():
    """Retrieve the last available date for JWST ephemerides."""
    # attempt to retrieve an ephemeris for a date too far in the future
    start_date = JWST_MINIMUM_DATE
    future_date = "9999-01-01"
    request_url = URL.format(start_date, future_date)
    try:
        # this should return an error message containing the last good date
        ephemeris_request = requests.get(request_url, timeout=10)

        # parse the date from the message
        m = re.match(
            r".*after A\.D\. (\d{4}-[a-zA-Z]+-\d{1,2})", ephemeris_request.text
        )
        dt = m.groups()[0]
        end_date = (
            datetime.datetime.strptime(dt, "%Y-%b-%d")
            .astimezone(datetime.timezone.utc)
            .strftime("%Y-%m-%d")
        )

    except Exception:
        # if the above fails for any reason, fall back to a known good date
        end_date = JWST_MAXIMUM_DATE

    return end_date
