import datetime
import warnings

from astropy.time import Time
import numpy as np
import pandas as pd

try:
    from jwst_gtvt.jwst_tvt import Ephemeris
except ImportError:
    warnings.warn('Missing jwst_gtvt; latest version is required.')
    HAS_GTVT = False
else:
    HAS_GTVT = True

__all__ = ['timeline']


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
    if not HAS_GTVT:
        raise ImportError('Timeline cannot be computed without '
                          'latest `jwst_gtvt`.')

    # default start date to now
    if start_date is None:
        start_date = Time(datetime.datetime.now())

    # default end date to start date + one year
    if end_date is None:
        end_date = start_date + datetime.timedelta(days=365)

    if end_date <= start_date:
        raise ValueError('End date must be later than start date.')

    ephemeris = Ephemeris(start_date=start_date, end_date=end_date)
    ephemeris.get_fixed_target_positions(str(ra), str(dec))

    if instrument is None:
        instruments = ['NIRSpec', 'NIRCam']
    else:
        instruments = [instrument]

    # get the dataframe from the ephemeris
    df = ephemeris.dataframe
    times = Time(df['MJD'], format='mjd').datetime

    # when the specified position is not in the Field of Regard (FOR),
    # set the PA to NaN
    not_visible = ~df['in_FOR']
    df.loc[not_visible, 'V3PA'] = np.nan

    # relevant data for this application is the V3 position angle (PA)
    # and NIRSpec and NIRCam min and max PA
    timeline_data = {'Time': times, 'V3PA': df['V3PA']}
    for instrument in instruments:
        for key in ['min', 'max']:
            col = instrument.upper() + f'_{key}_pa_angle'
            df.loc[not_visible, col] = np.nan
            timeline_data[col.replace('pa_angle', 'PA')] = df[col]

    timeline_df = pd.DataFrame(timeline_data)
    return timeline_df
