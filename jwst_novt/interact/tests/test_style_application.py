import pytest

try:
    import ipywidgets as ipw

    from jwst_novt.interact import style_application as u
except ImportError:
    ipw = None
    u = None
    HAS_DISPLAY = False
else:
    HAS_DISPLAY = True


@pytest.mark.skipif(not HAS_DISPLAY, reason="Missing optional dependencies")
class TestStyleApplication:
    @pytest.mark.parametrize("context", ["notebook", "voila"])
    def test_init(
        self,
        image_viewer,
        uploaded_data,
        nirspec_controls,
        nircam_controls,
        timeline_controls,
        overlay_controls,
        save_controls,
        context,
    ):
        sa = u.StyleApplication(
            image_viewer,
            uploaded_data,
            nirspec_controls,
            nircam_controls,
            timeline_controls,
            overlay_controls,
            save_controls,
            context=context,
        )
        assert isinstance(sa.widgets, ipw.Widget)
        if context == "notebook":
            # viewer is top-level widget
            assert image_viewer.widgets in sa.widgets.children
        else:
            # viewer is in an accordion tab
            assert image_viewer.widgets not in sa.widgets.children
            viewer_location = sa.widgets.children[-2].children[-1].children
            assert image_viewer.widgets in viewer_location

    def test_link(self, application_style):
        # link between other controls and timeline_controls

        test_values = {
            "ra": 240,
            "dec": -80,
            "color1": "orange",
            "color2": "purple",
            "name": "test",
        }

        # from nirspec
        application_style.nirspec_controls.ra = test_values["ra"]
        assert application_style.timeline_controls.ra == test_values["ra"]
        application_style.nirspec_controls.dec = test_values["dec"]
        assert application_style.timeline_controls.dec == test_values["dec"]
        application_style.nirspec_controls.color_primary = test_values["color1"]
        assert (
            application_style.timeline_controls.nirspec_color == test_values["color1"]
        )

        # from nircam
        application_style.nircam_controls.color_primary = test_values["color2"]
        assert application_style.timeline_controls.nircam_color == test_values["color2"]

        # from uploaded data
        application_style.uploaded_data.image_file_name = test_values["name"]
        assert application_style.timeline_controls.center == test_values["name"]

    def test_update_from_config(self, application_style):
        orig_dec = application_style.nirspec_controls.dec

        # update config in uploaded data
        nrs_config = {
            "ra": 100.0,
            "color_primary": "red",
            "bad": "ignored",
            "dec": "also ignored",
        }
        application_style.uploaded_data.configuration = {"nirspec": nrs_config}

        # nirspec control should be updated
        assert application_style.nirspec_controls.ra == nrs_config["ra"]
        assert (
            application_style.nirspec_controls.color_primary
            == nrs_config["color_primary"]
        )
        assert not hasattr(application_style.nirspec_controls, "bad")
        assert application_style.nirspec_controls.dec == orig_dec

    def test_update_to_config(self, application_style):
        # update control value
        application_style.nirspec_controls.ra = 100.0
        application_style.nirspec_controls.color_primary = "red"

        # config should be updated
        assert application_style.uploaded_data.configuration == {
            "nirspec": {"ra": 100.0, "color_primary": "red"},
            "timeline": {"ra": 100.0},
        }
