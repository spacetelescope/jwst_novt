import pytest
from astropy.time import Time
import numpy as np
import pandas as pd

from novt import timeline as tl


def test_timeline():
    ra = 202.4695898
    dec = 47.1951868

    # default start/end dates should return some data with
    # at least some visible and non-visible periods
    df = tl.timeline(ra, dec)

    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0

    expected_columns = ['Time', 'V3PA', 'NIRSPEC_min_PA', 'NIRSPEC_max_PA',
                        'NIRCAM_min_PA', 'NIRCAM_max_PA']
    for col in expected_columns:
        assert col in df

    not_visible = np.isnan(df['V3PA'])
    assert np.sum(not_visible) > 0
    assert np.sum(~not_visible) > 0


@pytest.mark.parametrize('inst,pa', [('NIRSPEC', 69), ('NIRCAM', 290)])
def test_timeline_instrument_dates(inst, pa):
    ra = 202.4695898
    dec = 47.1951868

    # okay start and end dates
    df = tl.timeline(ra, dec, start_date=Time('2022-01-05'),
                     end_date=Time('2022-01-09'), instrument=inst)
    assert len(df) > 0

    # expected position angle for this date
    visible = ~np.isnan(df['V3PA'])
    assert np.allclose(df[f'{inst}_min_PA'][visible], pa, atol=10)
    assert np.allclose(df[f'{inst}_max_PA'][visible], pa, atol=10)


def test_timeline_errors():
    ra = 202.4695898
    dec = 47.1951868

    # bad start and end dates
    with pytest.raises(ValueError) as err:
        tl.timeline(ra, dec, start_date=Time('2022-01-01'),
                    end_date=Time('2022-01-01'))
    assert 'End date must be later' in str(err)

    with pytest.raises(ValueError) as err:
        tl.timeline(ra, dec, start_date=Time('2020-01-01'))
    assert 'No JWST ephemeris available' in str(err)

    with pytest.raises(ValueError) as err:
        tl.timeline(ra, dec, end_date=Time('2050-01-01'))
    assert 'No JWST ephemeris available' in str(err)
