import datetime

import numpy as np
import pandas as pd
import pytest
from astropy.time import Time

from jwst_novt import timeline as tl
from jwst_novt.constants import JWST_MAXIMUM_DATE


def test_timeline():
    ra = 202.4695898
    dec = 47.1951868

    # default start/end dates should return some data with
    # at least some visible and non-visible periods
    timeline_df = tl.timeline(ra, dec)

    assert isinstance(timeline_df, pd.DataFrame)
    assert len(timeline_df) > 0

    expected_columns = [
        "Time",
        "V3PA",
        "NIRSPEC_min_PA",
        "NIRSPEC_max_PA",
        "NIRCAM_min_PA",
        "NIRCAM_max_PA",
    ]
    for col in expected_columns:
        assert col in timeline_df

    not_visible = np.isnan(timeline_df["V3PA"])
    assert np.sum(not_visible) > 0
    assert np.sum(~not_visible) > 0


@pytest.mark.parametrize(("inst", "pa"), [("NIRSPEC", 69), ("NIRCAM", 290)])
def test_timeline_instrument_dates(inst, pa):
    ra = 202.4695898
    dec = 47.1951868

    # okay start and end dates
    timeline_df = tl.timeline(
        ra,
        dec,
        start_date=Time("2022-01-05"),
        end_date=Time("2022-01-09"),
        instrument=inst,
    )
    assert len(timeline_df) > 0

    # expected position angle for this date
    visible = ~np.isnan(timeline_df["V3PA"])
    assert np.allclose(timeline_df[f"{inst}_min_PA"][visible], pa, atol=10)
    assert np.allclose(timeline_df[f"{inst}_max_PA"][visible], pa, atol=10)


def test_timeline_errors():
    ra = 202.4695898
    dec = 47.1951868

    # bad start and end dates
    with pytest.raises(ValueError, match="End date must be later"):
        tl.timeline(ra, dec, start_date=Time("2022-01-01"), end_date=Time("2022-01-01"))

    with pytest.raises(ValueError, match="No JWST ephemeris available"):
        tl.timeline(ra, dec, start_date=Time("2020-01-01"))

    with pytest.raises(ValueError, match="No JWST ephemeris available"):
        tl.timeline(ra, dec, end_date=Time("2050-01-01"))


def test_jwst_maximum_date(mocker):
    expected = datetime.date.fromisoformat(JWST_MAXIMUM_DATE)

    retrieved = tl.jwst_maximum_date()
    assert datetime.date.fromisoformat(retrieved) >= expected

    # trigger an error to check fallback
    mocker.patch.object(tl.requests, "get", side_effect=ValueError("bad request"))
    fallback = tl.jwst_maximum_date()
    assert datetime.date.fromisoformat(fallback) == expected
