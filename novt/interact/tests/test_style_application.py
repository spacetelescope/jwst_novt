import pytest

try:
    import ipywidgets as ipw
    from novt.interact import style_application as u
except ImportError:
    ipw = None
    u = None
    HAS_DISPLAY = False
else:
    HAS_DISPLAY = True


@pytest.mark.skipif(not HAS_DISPLAY, reason='Missing optional dependencies')
class TestStyleApplication(object):
    @pytest.mark.parametrize('context', ['notebook', 'voila'])
    def test_init(self, image_viewer, uploaded_data, nirspec_controls,
                  nircam_controls, timeline_controls, overlay_controls,
                  save_controls, context):
        sa = u.StyleApplication(image_viewer, uploaded_data, nirspec_controls,
                                nircam_controls, timeline_controls,
                                overlay_controls, save_controls,
                                context=context)
        assert isinstance(sa.widgets, ipw.Widget)
        if context == 'notebook':
            # viewer is top-level widget
            assert image_viewer.widgets in sa.widgets.children
        else:
            # viewer is in an accordion tab
            assert image_viewer.widgets not in sa.widgets.children
            viewer_location = sa.widgets.children[-2].children[-1].children
            assert image_viewer.widgets in viewer_location

    def test_link(self, application_style):
        # link between other controls and timeline_controls

        # from nirspec
        application_style.nirspec_controls.ra = 240
        assert application_style.timeline_controls.ra == 240
        application_style.nirspec_controls.dec = -80
        assert application_style.timeline_controls.dec == -80
        application_style.nirspec_controls.color_primary = 'orange'
        assert application_style.timeline_controls.nirspec_color == 'orange'

        # from nircam
        application_style.nircam_controls.color_primary = 'purple'
        assert application_style.timeline_controls.nircam_color == 'purple'

        # from uploaded data
        application_style.uploaded_data.image_file_name = 'test'
        assert application_style.timeline_controls.center == 'test'
