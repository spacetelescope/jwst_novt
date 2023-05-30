import pytest

try:
    import bqplot
    import ipywidgets as ipw

    from jwst_novt.interact import show_overlays as u
except ImportError:
    bqplot = None
    ipw = None
    u = None
    HAS_DISPLAY = False
else:
    HAS_DISPLAY = True

from jwst_novt.constants import DEFAULT_COLOR


@pytest.mark.skipif(not HAS_DISPLAY, reason="Missing optional dependencies")
class TestShowOverlays:
    def test_init(self, imviz, uploaded_data, nirspec_controls, nircam_controls):
        # instruments are both optional
        so = u.ShowOverlays(imviz, uploaded_data, nirspec=nirspec_controls)
        assert isinstance(so.widgets, ipw.Widget)
        assert so.instruments == ["NIRSpec"]

        so = u.ShowOverlays(imviz, uploaded_data, nircam=nircam_controls)
        assert isinstance(so.widgets, ipw.Widget)
        assert so.instruments == ["NIRCam Short", "NIRCam Long"]

        so = u.ShowOverlays(
            imviz, uploaded_data, nirspec=nirspec_controls, nircam=nircam_controls
        )
        assert isinstance(so.widgets, ipw.Widget)
        assert so.instruments == ["NIRSpec", "NIRCam Short", "NIRCam Long"]

        so = u.ShowOverlays(imviz, uploaded_data)
        assert isinstance(so.widgets, ipw.Widget)
        assert so.instruments == []

    def test_init_preloaded(
        self, loaded_imviz, uploaded_data, nirspec_controls, nircam_controls
    ):
        uploaded_data.has_wcs = True
        so = u.ShowOverlays(
            loaded_imviz,
            uploaded_data,
            nirspec=nirspec_controls,
            nircam=nircam_controls,
        )

        # buttons should be pre-enabled
        for btn in so.footprint_buttons:
            assert not btn.disabled

    def test_clear_overlays(self, overlay_controls):
        # show nirspec overlay
        overlay_controls._show_footprint(["NIRSpec"], overlay_controls.nirspec_controls)
        nrs_patches = overlay_controls.footprint_patches["NIRSpec"]
        assert len(nrs_patches) > 1
        assert nrs_patches[0] in overlay_controls.viewer.figure.marks

        # clear overlays - gone from figure and from tracking
        overlay_controls.clear_overlays()
        assert "NIRSpec" not in overlay_controls.footprint_patches
        assert nrs_patches[0] not in overlay_controls.viewer.figure.marks

        # button is reset to enabled if there is a good wcs
        assert not overlay_controls.footprint_buttons[0].disabled

        # it is disabled if not
        overlay_controls.uploaded_data.has_wcs = False
        overlay_controls.clear_overlays()
        assert overlay_controls.footprint_buttons[0].disabled

    def test_load_clear_catalog(self, overlay_controls):
        # load catalog overlay - not visible after load
        overlay_controls._load_catalog()
        cat_markers = overlay_controls.catalog_markers["primary"]
        assert isinstance(cat_markers, bqplot.Scatter)
        assert cat_markers in overlay_controls.viewer.figure.marks
        assert not cat_markers.visible

        # toggle catalog overlay on and off
        overlay_controls.toggle_catalog(overlay_controls.catalog_buttons[0], None, None)
        assert cat_markers.visible
        overlay_controls.toggle_catalog(overlay_controls.catalog_buttons[0], None, None)
        assert not cat_markers.visible

        # clear catalog
        overlay_controls.clear_catalog()
        new_markers = overlay_controls.catalog_markers["primary"]
        assert new_markers is not cat_markers
        assert new_markers in overlay_controls.viewer.figure.marks
        assert cat_markers not in overlay_controls.viewer.figure.marks
        assert not new_markers.visible

        # button is not disabled since catalog is still available
        assert not overlay_controls.catalog_buttons[0].disabled

        # it is disabled after clearing if catalog is not available
        overlay_controls.uploaded_data.has_catalog = False
        overlay_controls.clear_catalog()
        assert overlay_controls.catalog_buttons[0].disabled

    def test_load_catalog_error(self, overlay_controls, bad_catalog_file):
        overlay_controls.uploaded_data.catalog_file = {"file_obj": bad_catalog_file}
        overlay_controls._load_catalog()
        assert "primary" not in overlay_controls.catalog_markers

    def test_update_catalog(self, overlay_controls):
        overlay_controls._load_catalog()
        cat_markers = overlay_controls.catalog_markers["primary"]
        assert cat_markers.colors == [DEFAULT_COLOR["Primary Sources"]]

        # change the color for primary sources
        overlay_controls.uploaded_data.color_primary = "red"

        # callback updates the color in the markers
        assert cat_markers.colors == ["red"]

    @pytest.mark.parametrize("inst", ["NIRSpec", "NIRCam Short", "NIRCam Long"])
    def test_toggle_footprint(self, overlay_controls, inst):
        btn_idx = ["NIRSpec", "NIRCam Short", "NIRCam Long"].index(inst)

        # button for overlay
        button = overlay_controls.footprint_buttons[btn_idx]
        assert button.is_active()

        # toggle footprint on
        overlay_controls.toggle_footprint(button, None, None)
        assert not button.is_active()

        # footprint visible
        patches = overlay_controls.footprint_patches[inst]
        assert len(patches) > 1
        assert patches[0] in overlay_controls.viewer.figure.marks
        assert patches[0].visible

        # toggle footprint off
        overlay_controls.toggle_footprint(button, None, None)
        assert button.is_active()

        # footprint should be removed
        assert inst not in overlay_controls.footprint_patches
        assert patches[0] not in overlay_controls.viewer.figure.marks

        # if no wcs is available, footprint is not created,
        # button stays active
        overlay_controls.uploaded_data.has_wcs = False
        overlay_controls.toggle_footprint(button, None, None)
        assert button.is_active()
        assert inst not in overlay_controls.footprint_patches

    def test_all_patches(self, overlay_controls):
        # no patches yet
        patches = overlay_controls.all_patches()
        assert len(patches) == 0

        # add footprints
        button = overlay_controls.footprint_buttons[0]
        overlay_controls.toggle_footprint(button, None, None)

        expected_patches = 11
        patches = overlay_controls.all_patches()
        assert len(patches) == expected_patches

        # add catalog
        overlay_controls._load_catalog()
        button = overlay_controls.catalog_buttons[0]
        overlay_controls.toggle_catalog(button, None, None)

        # both primary and filler patches returned,
        # even though only one is visible
        patches = overlay_controls.all_patches()
        assert len(patches) == expected_patches + 2

    def test_show_footprint(self, overlay_controls):
        overlay_controls._show_footprint(["NIRSpec"], overlay_controls.nirspec_controls)

        nrs_patches = overlay_controls.footprint_patches["NIRSpec"]
        assert len(nrs_patches) > 1
        assert nrs_patches[0] in overlay_controls.viewer.figure.marks

        # show again: old patches are removed and replaced with new ones
        overlay_controls._show_footprint(["NIRSpec"], overlay_controls.nirspec_controls)

        new_patches = overlay_controls.footprint_patches["NIRSpec"]
        assert len(new_patches) == len(nrs_patches)
        assert new_patches[0] in overlay_controls.viewer.figure.marks
        assert new_patches[0] is not nrs_patches[0]
        assert nrs_patches[0] not in overlay_controls.viewer.figure.marks

        # with no wcs, nothing happens
        overlay_controls.uploaded_data.has_wcs = False
        overlay_controls._show_footprint(["NIRSpec"], overlay_controls.nirspec_controls)
        test_patches = overlay_controls.footprint_patches["NIRSpec"]
        assert test_patches is new_patches
        assert test_patches[0] is new_patches[0]

    @pytest.mark.parametrize("inst", ["NIRSpec", "NIRCam Short", "NIRCam Long"])
    def test_update_footprint(self, overlay_controls, inst):
        if inst == "NIRSpec":
            controls = overlay_controls.nirspec_controls
        else:
            controls = overlay_controls.nircam_controls

        # show footprint initially
        overlay_controls._show_footprint([inst], controls)
        patches = overlay_controls.footprint_patches[inst]
        assert len(patches) > 1
        assert patches[0] in overlay_controls.viewer.figure.marks
        assert patches[0].colors == [DEFAULT_COLOR[inst]]

        # update with new color
        controls.color_primary = "red"
        controls.color_alternate = "blue"
        overlay_controls._update_footprint([inst], controls)

        # patches are updated in place
        new_patches = overlay_controls.footprint_patches[inst]
        assert len(patches) == len(new_patches)
        for i, patch in enumerate(new_patches):
            assert patch is patches[i]
        assert new_patches[0] in overlay_controls.viewer.figure.marks
        if inst == "NIRCam Long":
            assert new_patches[0].colors == ["blue"]
        else:
            assert new_patches[0].colors == ["red"]

        # with no wcs, nothing happens
        overlay_controls.uploaded_data.has_wcs = False
        controls.color_primary = "orange"
        controls.color_alternate = "purple"
        overlay_controls._update_footprint([inst], controls)

        new_patches = overlay_controls.footprint_patches[inst]
        if inst == "NIRCam Long":
            assert new_patches[0].colors == ["blue"]
        else:
            assert new_patches[0].colors == ["red"]

    def test_update_nircam_dither(self, mocker, overlay_controls):
        # show function is called only for currently shown apertures
        m1 = mocker.patch.object(overlay_controls, "_show_footprint")

        # nothing current
        overlay_controls.update_nircam_dither()
        m1.assert_called_with([], overlay_controls.nircam_controls)

        # nircam short shown
        overlay_controls.footprint_patches["NIRCam Short"] = ["test"]
        overlay_controls.update_nircam_dither()
        m1.assert_called_with(["NIRCam Short"], overlay_controls.nircam_controls)

        # long too
        overlay_controls.footprint_patches["NIRCam Long"] = ["test"]
        overlay_controls.update_nircam_dither()
        m1.assert_called_with(
            ["NIRCam Short", "NIRCam Long"], overlay_controls.nircam_controls
        )

    def test_update_nircam_footprint(self, mocker, overlay_controls):
        # update function is called with all nircam instruments,
        # regardless of current state
        m1 = mocker.patch.object(overlay_controls, "_update_footprint")

        # nothing current
        overlay_controls.update_nircam_footprint()
        m1.assert_called_with(
            ["NIRCam Short", "NIRCam Long"], overlay_controls.nircam_controls
        )

        # nircam short shown
        overlay_controls.footprint_patches["NIRCam Short"] = ["test"]
        overlay_controls.update_nircam_footprint()
        m1.assert_called_with(
            ["NIRCam Short", "NIRCam Long"], overlay_controls.nircam_controls
        )

        # long too
        overlay_controls.footprint_patches["NIRCam Long"] = ["test"]
        overlay_controls.update_nircam_footprint()
        m1.assert_called_with(
            ["NIRCam Short", "NIRCam Long"], overlay_controls.nircam_controls
        )

    def test_update_nircam_mosaic(self, mocker, overlay_controls):
        # show is called if mosaic state changes, otherwise update
        m1 = mocker.patch.object(overlay_controls, "_show_footprint")
        m2 = mocker.patch.object(overlay_controls, "_update_footprint")

        overlay_controls.footprint_patches["NIRCam Short"] = ["test"]
        overlay_controls.footprint_patches["NIRCam Long"] = ["test"]

        overlay_controls.update_nircam_mosaic({"name": "mosaic"})
        assert m1.call_count == 1
        assert m2.call_count == 0

        overlay_controls.update_nircam_mosaic({"name": "mosaic_v2"})
        assert m1.call_count == 1
        assert m2.call_count == 1

    def test_update_nirspec_footprint(self, mocker, overlay_controls):
        # update function is called always, regardless of current state
        m1 = mocker.patch.object(overlay_controls, "_update_footprint")

        # nothing current
        overlay_controls.update_nirspec_footprint()
        m1.assert_called_with(["NIRSpec"], overlay_controls.nirspec_controls)

        # nirspec shown
        overlay_controls.footprint_patches["NIRSpec"] = ["test"]
        overlay_controls.update_nirspec_footprint()
        m1.assert_called_with(["NIRSpec"], overlay_controls.nirspec_controls)
