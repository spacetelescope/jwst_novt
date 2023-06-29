import datetime

import pytest

try:
    import ipywidgets as ipw

    from jwst_novt.interact import show_timeline as u
except ImportError:
    ipw = None
    u = None
    HAS_DISPLAY = False
else:
    HAS_DISPLAY = True

from jwst_novt.constants import DEFAULT_COLOR


@pytest.mark.skipif(not HAS_DISPLAY, reason="Missing optional dependencies")
class TestShowTimeline:
    def test_init(self):
        # no initial arguments
        st = u.ShowTimeline()
        assert isinstance(st.widgets, ipw.Widget)
        assert st.center is None
        assert st.ra == 0
        assert st.dec == 0

    def test_clear_plot(self, timeline_controls):
        # nothing happens if there's no plot
        timeline_controls._clear_plot()
        assert timeline_controls.figure is None
        assert len(timeline_controls.figure_container.children) == 0

        # show the plot figure
        timeline_controls._show_plot()
        assert timeline_controls.figure is not None
        assert timeline_controls.figure in timeline_controls.figure_container.children
        assert len(timeline_controls.figure.marks) > 0

        # clear it
        timeline_controls._clear_plot()

        # figure still exists but does not contain marks
        assert timeline_controls.figure is not None
        assert len(timeline_controls.figure.marks) == 0

        # container no longer holds figure
        assert len(timeline_controls.figure_container.children) == 0

    @pytest.mark.parametrize("inst", ["NIRSpec", "NIRCam", "NIRSpec, NIRCam"])
    def test_make_timeline(self, timeline_controls, inst):
        timeline_controls.set_instrument.value = inst

        # no effect if plot is closed
        timeline_controls._make_timeline()
        assert timeline_controls.figure is None

        # show plot -- also calls make_timeline
        timeline_controls._show_plot()
        if inst == "NIRSpec":
            n_plot = 2
            assert len(timeline_controls.figure.marks) == n_plot
            assert timeline_controls.figure.marks[0].colors == [DEFAULT_COLOR["V3PA"]]
            assert timeline_controls.figure.marks[1].colors == [DEFAULT_COLOR[inst]]
        elif inst == "NIRCam":
            n_plot = 2
            assert len(timeline_controls.figure.marks) == n_plot
            assert timeline_controls.figure.marks[0].colors == [DEFAULT_COLOR["V3PA"]]
            assert timeline_controls.figure.marks[1].colors == [
                DEFAULT_COLOR["NIRCam Short"]
            ]
        else:
            n_plot = 3
            assert len(timeline_controls.figure.marks) == n_plot
            assert timeline_controls.figure.marks[0].colors == [DEFAULT_COLOR["V3PA"]]
            assert timeline_controls.figure.marks[1].colors == [
                DEFAULT_COLOR["NIRSpec"]
            ]
            assert timeline_controls.figure.marks[2].colors == [
                DEFAULT_COLOR["NIRCam Short"]
            ]

        # modify colors: marks are updated in place
        timeline_controls.nircam_color = "red"
        timeline_controls.nirspec_color = "blue"
        if inst == "NIRSpec":
            assert timeline_controls.figure.marks[1].colors == ["blue"]
        elif inst == "NIRCam":
            assert timeline_controls.figure.marks[1].colors == ["red"]
        else:
            assert timeline_controls.figure.marks[1].colors == ["blue"]
            assert timeline_controls.figure.marks[2].colors == ["red"]

    @pytest.mark.parametrize("start_date", [False, True])
    def test_save_plot(self, timeline_controls, mocker, start_date):
        # set start and end dates if needed
        if not start_date:
            timeline_controls.set_start.value = None
            timeline_controls.set_end.value = None
            date_str = datetime.datetime.now(tz=datetime.timezone.utc).strftime(
                "%Y%m%d"
            )
        else:
            timeline_controls.set_start.value = datetime.date(2022, 1, 5)
            timeline_controls.set_end.value = datetime.date(2022, 1, 9)
            date_str = "20220105-20220109"

        # show the plot to make the figure then clear it
        timeline_controls._show_plot()
        timeline_controls._clear_plot()

        # mock the actual save function
        m1 = mocker.patch.object(timeline_controls.figure, "save_png")

        # nothing happens if plot is not ready
        timeline_controls._save_plot()
        assert m1.call_count == 0

        # show the plot
        timeline_controls._show_plot()

        # save the plot to a default filename
        timeline_controls._save_plot()
        assert m1.call_count == 1
        m1.assert_called_with(filename=f"novt_timeline_{date_str}.png")

    def test_update_colors_no_figure(self, timeline_controls):
        assert timeline_controls.figure is None
        # nothing happens
        timeline_controls._update_colors()
        assert timeline_controls.figure is None
