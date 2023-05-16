from astropy.nddata import NDData
from astropy.wcs import WCS
import numpy as np
import pytest

try:
    import ipywidgets as ipw
    import jdaviz
    from novt.interact import ControlInstruments, ShowOverlays, UploadData
except ImportError:
    ipw = None
    jdaviz = None
    ControlInstruments, ShowOverlays, UploadData = None, None, None
    HAS_DISPLAY = False
else:
    HAS_DISPLAY = True


@pytest.fixture
def imviz():
    return jdaviz.Imviz()


@pytest.fixture
def loaded_imviz(image_2d_wcs):
    imviz = jdaviz.Imviz()
    arr = np.ones((10, 10))
    ndd = NDData(arr, wcs=image_2d_wcs)
    imviz.load_data(ndd)
    return imviz


@pytest.fixture
def uploaded_data(loaded_imviz):
    return UploadData(loaded_imviz)


@pytest.fixture
def nirspec_controls(loaded_imviz):
    return ControlInstruments('NIRSpec', loaded_imviz)


@pytest.fixture
def nircam_controls(loaded_imviz):
    return ControlInstruments('NIRCam', loaded_imviz)


@pytest.fixture
def overlay_controls(loaded_imviz, uploaded_data,
                     nirspec_controls, nircam_controls, catalog_file):
    ctrl = ShowOverlays(loaded_imviz, uploaded_data, nirspec=nirspec_controls,
                        nircam=nircam_controls)

    # minimum settings to allow overlays to be turned on
    ctrl.uploaded_data.has_wcs = True
    ctrl.uploaded_data.catalog_file = {'file_obj': catalog_file}
    ctrl.uploaded_data.has_catalog = True

    return ctrl
