import numpy as np
import pytest

try:
    import ipywidgets as ipw

    from jwst_novt.interact import control_instruments as u
except ImportError:
    ipw = None
    u = None
    HAS_DISPLAY = False
else:
    HAS_DISPLAY = True


@pytest.mark.skipif(not HAS_DISPLAY, reason="Missing optional dependencies")
class TestControlInstrument:
    def test_control_nirspec(self, imviz):
        """Test NIRSpec controls."""
        ci = u.ControlInstruments("NIRSpec", imviz)
        assert ci.instrument == "NIRSpec"

        # expected nirspec components
        controls = ["set_ra", "set_dec", "set_pa", "set_alpha", "widgets"]
        for widget in controls:
            assert isinstance(getattr(ci, widget), ipw.Widget)

        assert len(ci.color_pickers) == 1
        assert isinstance(ci.color_pickers[0], ipw.Widget)

        # not expected for nirspec
        not_controls = ["set_dither", "set_mosaic", "set_mosaic_v2", "set_mosaic_v3"]
        for widget in not_controls:
            assert getattr(ci, widget) is None

    def test_control_nircam(self, imviz):
        ci = u.ControlInstruments("NIRCam", imviz)
        assert ci.instrument == "NIRCam"

        # expected nircam components
        controls = [
            "set_ra",
            "set_dec",
            "set_pa",
            "set_alpha",
            "widgets",
            "set_dither",
            "set_mosaic",
            "set_mosaic_v2",
            "set_mosaic_v3",
        ]
        for widget in controls:
            assert isinstance(getattr(ci, widget), ipw.Widget)

        n_inst = 2
        assert len(ci.color_pickers) == n_inst
        assert isinstance(ci.color_pickers[0], ipw.Widget)
        assert isinstance(ci.color_pickers[1], ipw.Widget)

    def test_wrap_angle(self, imviz):
        ci = u.ControlInstruments("test", imviz)
        assert ci.pa == 0
        assert ci.set_pa.value == 0

        expected = 355
        ci._wrap_angle({"new": -5})
        assert ci.pa == expected
        assert ci.set_pa.value == expected

        expected = 5
        ci._wrap_angle({"new": 365})
        assert ci.pa == expected
        assert ci.set_pa.value == expected

        expected = 45
        ci._wrap_angle({"new": 45})
        assert ci.pa == expected
        assert ci.set_pa.value == expected

    def test_set_from_wcs(self, imviz, loaded_imviz):
        ci = u.ControlInstruments("test", imviz)
        assert ci.ra == 0
        assert ci.dec == 0

        # no effect with no wcs
        ci._set_from_wcs()
        assert np.allclose(ci.ra, 0)
        assert np.allclose(ci.dec, 0)

        # if imviz already has data, ra and dec are pre-populated
        ci = u.ControlInstruments("test", loaded_imviz)
        expected_ra, expected_dec = 202.4695898, 47.1951868
        assert ci.ra == expected_ra
        assert ci.dec == expected_dec

        # calling again has no further effect
        ci._set_from_wcs()
        assert np.allclose(ci.ra, 202.4695898)
        assert np.allclose(ci.dec, 47.1951868)

    def test_check_mosaic_from_dither(self, imviz):
        ci = u.ControlInstruments("NIRCam", imviz)

        # check various combos of mosaic on/off and allowed
        ci.mosaic = "No"
        ci._check_mosaic_from_dither({"new": "FULL3"})
        assert not ci.set_mosaic.disabled
        assert ci.set_mosaic_v2.disabled
        assert ci.set_mosaic_v3.disabled

        ci.mosaic = "Yes"
        ci._check_mosaic_from_dither({"new": "FULL3"})
        assert not ci.set_mosaic.disabled
        assert not ci.set_mosaic_v2.disabled
        assert not ci.set_mosaic_v3.disabled

        ci.mosaic = "No"
        ci._check_mosaic_from_dither({"new": "8NIRSPEC"})
        assert ci.set_mosaic.disabled
        assert ci.set_mosaic_v2.disabled
        assert ci.set_mosaic_v3.disabled

        ci.mosaic = "Yes"
        ci._check_mosaic_from_dither({"new": "8NIRSPEC"})
        assert ci.set_mosaic.disabled
        assert ci.set_mosaic_v2.disabled
        assert ci.set_mosaic_v3.disabled

    def test_check_mosaic(self, imviz):
        ci = u.ControlInstruments("NIRCam", imviz)

        # check mosaic on/off
        ci._check_mosaic({"new": "No"})
        assert ci.set_mosaic_v2.disabled
        assert ci.set_mosaic_v3.disabled

        ci._check_mosaic({"new": "Yes"})
        assert not ci.set_mosaic_v2.disabled
        assert not ci.set_mosaic_v3.disabled
