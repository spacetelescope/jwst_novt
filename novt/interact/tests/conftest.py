from astropy.nddata import NDData
from astropy.wcs import WCS
import numpy as np
import pytest

try:
    import ipywidgets as ipw
    import jdaviz
    from novt.interact import control_instruments as u
except ImportError:
    ipw = None
    jdaviz = None
    u = None
    HAS_DISPLAY = False
else:
    HAS_DISPLAY = True


@pytest.fixture
def imviz():
    return jdaviz.Imviz()


@pytest.fixture
def image_2d_wcs():
    return WCS({'CTYPE1': 'RA---TAN', 'CUNIT1': 'deg',
                'CDELT1': -0.0002777777778,
                'CRPIX1': 1, 'CRVAL1': 202.4695898,
                'CTYPE2': 'DEC--TAN', 'CUNIT2': 'deg',
                'CDELT2': 0.0002777777778,
                'CRPIX2': 1, 'CRVAL2': 47.1951868})


@pytest.fixture
def loaded_imviz(image_2d_wcs):
    imviz = jdaviz.Imviz()
    arr = np.ones((10, 10))
    ndd = NDData(arr, wcs=image_2d_wcs)
    imviz.load_data(ndd)
    return imviz
