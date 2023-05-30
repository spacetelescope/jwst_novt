# Project defaults and fixtures for pytest
import numpy as np
import pandas as pd
import pytest
from astropy.io import fits
from astropy.time import Time
from astropy.wcs import WCS


@pytest.fixture()
def catalog_file(tmp_path):
    filename = tmp_path / "sources.radec"
    with filename.open("w") as fh:
        fh.write(
            "202.42053  47.17906  F  16.58300\n"
            "202.42514  47.29251  P  16.69000\n"
            "202.45114  47.14672  F  16.70300\n"
            "202.48190  47.19670  F  16.71100\n"
            "202.43707  47.16641  F  17.20600\n"
            "202.47760  47.20205  F  17.32900\n"
            "202.48415  47.24812  P  17.52500\n"
        )
    return filename


@pytest.fixture()
def catalog_file_2col(tmp_path):
    filename = tmp_path / "sources_2col.radec"
    with filename.open("w") as fh:
        fh.write(
            "202.42053  47.17906\n"
            "202.42514  47.29251\n"
            "202.45114  47.14672\n"
            "202.48190  47.19670\n"
            "202.43707  47.16641\n"
            "202.47760  47.20205\n"
            "202.48415  47.24812\n"
        )
    return filename


@pytest.fixture()
def catalog_dataframe():
    return pd.DataFrame(
        {
            "ra": [
                202.42053,
                202.42514,
                202.45114,
                202.48190,
                202.43707,
                202.47760,
                202.48415,
            ],
            "dec": [
                47.17906,
                47.29251,
                47.14672,
                47.19670,
                47.16641,
                47.20205,
                47.24812,
            ],
            "flag": ["F", "P", "F", "F", "F", "F", "P"],
        }
    )


@pytest.fixture()
def catalog_dataframe_2col():
    return pd.DataFrame(
        {
            "ra": [
                202.42053,
                202.42514,
                202.45114,
                202.48190,
                202.43707,
                202.47760,
                202.48415,
            ],
            "dec": [
                47.17906,
                47.29251,
                47.14672,
                47.19670,
                47.16641,
                47.20205,
                47.24812,
            ],
        }
    )


@pytest.fixture()
def bad_catalog_file(tmp_path):
    filename = tmp_path / "bad.radec"
    filename.write_text("bad\n")
    return filename


@pytest.fixture()
def timeline_data():
    times = [
        Time("2022-01-04"),
        Time("2022-01-05"),
        Time("2022-01-06"),
        Time("2022-01-07"),
        Time("2022-01-08"),
        Time("2022-01-09"),
    ]
    v3pa = [
        np.nan,
        np.nan,
        290.5200764854323,
        289.6925780758301,
        288.8617815873458,
        288.0274449868331,
    ]
    nrs_min = [
        np.nan,
        np.nan,
        63.88394137790897,
        63.04444850978905,
        62.20105233407935,
        61.353514250989974,
    ]
    nrs_max = [
        np.nan,
        np.nan,
        74.3053509929556,
        73.48984704187114,
        72.67165024061228,
        71.85051512267626,
    ]
    nrc_min = [
        np.nan,
        np.nan,
        285.238018577909,
        284.39852570978906,
        283.5551295340793,
        282.7075914509899,
    ]
    nrc_max = [
        np.nan,
        np.nan,
        295.6594281929556,
        294.84392424187115,
        294.02572744061223,
        293.2045923226762,
    ]
    return pd.DataFrame(
        {
            "Time": times,
            "V3PA": v3pa,
            "NIRSPEC_min_PA": nrs_min,
            "NIRSPEC_max_PA": nrs_max,
            "NIRCAM_min_PA": nrc_min,
            "NIRCAM_max_PA": nrc_max,
        }
    )


@pytest.fixture()
def image_2d_wcs():
    return WCS(
        {
            "CTYPE1": "RA---TAN",
            "CUNIT1": "deg",
            "CDELT1": -0.0002777777778,
            "CRPIX1": 1,
            "CRVAL1": 202.4695898,
            "CTYPE2": "DEC--TAN",
            "CUNIT2": "deg",
            "CDELT2": 0.0002777777778,
            "CRPIX2": 1,
            "CRVAL2": 47.1951868,
        }
    )


@pytest.fixture()
def bad_wcs():
    return WCS(
        {"CDELT1": 1, "CRPIX1": 1, "CRVAL1": 1, "CDELT2": 1, "CRPIX2": 1, "CRVAL2": 1}
    )


@pytest.fixture()
def image_file(tmp_path, image_2d_wcs):
    hdul = fits.HDUList(
        fits.PrimaryHDU(np.zeros((10, 10)), header=image_2d_wcs.to_header())
    )
    filename = tmp_path / "image.fits"
    hdul.writeto(str(filename), overwrite=True)
    hdul.close()
    return filename


@pytest.fixture()
def image_file_no_wcs(tmp_path):
    hdul = fits.HDUList(fits.PrimaryHDU(np.zeros((10, 10))))
    filename = tmp_path / "image_no_wcs.fits"
    hdul.writeto(str(filename), overwrite=True)
    hdul.close()
    return filename
