from astropy.nddata import NDData
import numpy as np
import pytest

try:
    import ipywidgets as ipw
    import jdaviz
    from novt.interact import (
        ControlInstruments, SaveOverlays, ShowOverlays, ShowTimeline,
        UploadData, ViewImage, StyleApplication)
except ImportError:
    ipw = None
    jdaviz = None
    ControlInstruments, SaveOverlays, ShowOverlays = None, None, None
    ShowTimeline, UploadData, ViewImage = None, None, None
    StyleApplication = None
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
def image_viewer():
    return ViewImage()


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


@pytest.fixture
def timeline_controls():
    return ShowTimeline()


@pytest.fixture
def save_controls(overlay_controls):
    return SaveOverlays(overlay_controls)


@pytest.fixture
def application_style(image_viewer, uploaded_data, nirspec_controls,
                      nircam_controls, timeline_controls, overlay_controls,
                      save_controls):
    return StyleApplication(
        image_viewer, uploaded_data, nirspec_controls, nircam_controls,
        timeline_controls, overlay_controls, save_controls)
