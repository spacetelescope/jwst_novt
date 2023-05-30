import pytest

try:
    import ipywidgets as ipw

    from jwst_novt.interact import save_overlays as u
except ImportError:
    ipw = None
    u = None
    HAS_DISPLAY = False
else:
    HAS_DISPLAY = True


@pytest.mark.skipif(not HAS_DISPLAY, reason="Missing optional dependencies")
class TestSaveOverlays:
    def test_init(self, overlay_controls):
        so = u.SaveOverlays(overlay_controls)
        assert isinstance(so.widgets, ipw.Widget)

    @pytest.mark.parametrize("coords", ["pixel coordinates", "sky coordinates"])
    def test_make_regions(self, overlay_controls, catalog_file, bad_wcs, coords):
        so = u.SaveOverlays(overlay_controls)
        so.set_coordinates.value = coords

        # download link starts blank
        assert not so.file_link.url

        # no overlays shown, nothing happens
        so.make_regions()
        assert not so.file_link.url

        # turn on a nirspec overlay
        button = overlay_controls.footprint_buttons[0]
        overlay_controls.toggle_footprint(button, None, None)

        # file link is updated with downloadable data
        so.make_regions()
        assert so.file_link.url.startswith("data:text/plain")
        one_reg = so.file_link.url

        # turn on both nircam overlays: url is longer because it
        # contains more encoded data
        button = overlay_controls.footprint_buttons[1]
        overlay_controls.toggle_footprint(button, None, None)
        button = overlay_controls.footprint_buttons[2]
        overlay_controls.toggle_footprint(button, None, None)

        so.make_regions()
        assert so.file_link.url.startswith("data:text/plain")
        more_reg = so.file_link.url
        assert len(more_reg) > len(one_reg)

        # add catalog overlays too
        overlay_controls._load_catalog()
        for button in overlay_controls.catalog_buttons:
            overlay_controls.toggle_catalog(button, None, None)

        so.make_regions()
        assert so.file_link.url.startswith("data:text/plain")
        even_more_reg = so.file_link.url
        assert len(even_more_reg) > len(more_reg)

        # catalog file can also be a path to a file
        overlay_controls.uploaded_data.catalog_file = str(catalog_file)
        for button in overlay_controls.catalog_buttons:
            overlay_controls.toggle_catalog(button, None, None)

        so.make_regions()
        assert so.file_link.url.startswith("data:text/plain")
        same_reg = so.file_link.url
        assert same_reg == even_more_reg

        # if wcs is bad, nothing happens
        overlay_controls.viewer.state.reference_data.coords = bad_wcs
        so.make_regions()
        assert so.file_link.url == same_reg
        overlay_controls.viewer.state.reference_data = None
        so.make_regions()
        assert so.file_link.url == same_reg

        # link is cleared after clicking on it
        so.file_link.clear_link()
        assert not so.file_link.url

    def test_save_config(self, overlay_controls):
        so = u.SaveOverlays(overlay_controls, allow_configuration=True)
        assert so.save_config_file is not None

        # download link starts blank
        assert not so.config_file_link.url

        # no config set, so nothing happens
        so.make_config()
        assert not so.config_file_link.url

        # add a config value
        so.show_overlays.uploaded_data.configuration = {"nirspec": {"ra": 100.0}}

        # file link is updated with downloadable data
        so.make_config()
        assert so.config_file_link.url.startswith("data:text/plain")
        one_value = so.config_file_link.url

        # add another: url is longer because it
        # contains more encoded data
        so.show_overlays.uploaded_data.configuration["nirspec"]["pa"] = 90.0
        so.make_config()
        assert so.config_file_link.url.startswith("data:text/plain")
        more_values = so.config_file_link.url
        assert len(more_values) > len(one_value)

        # link is cleared after clicking on it
        so.config_file_link.clear_link()
        assert not so.config_file_link.url
