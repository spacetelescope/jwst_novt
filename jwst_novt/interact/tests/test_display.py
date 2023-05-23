from contextlib import contextmanager

import pytest
from astropy.time import Time
from astropy.wcs import WCS

try:
    import bqplot
    import ipywidgets as ipw

    from jwst_novt.interact import display as u
except ImportError:
    bqplot = None
    ipw = None
    u = None
    HAS_DISPLAY = False
else:
    HAS_DISPLAY = True

from jwst_novt.constants import DEFAULT_COLOR


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


@pytest.mark.skipif(not HAS_DISPLAY, reason="Missing optional dependencies")
class TestDisplay:
    def test_hold_all_sync(self, capsys):
        # mock a mark class with a simple context manager for testing
        class MockMark:
            def __init__(self, i):
                self.i = i

            @contextmanager
            def hold_sync(self):
                print(f"entered {self.i}")
                yield
                print(f"exited {self.i}")

        # list of mark objects
        marks = [MockMark(i) for i in range(5)]

        # call all hold_sync cms in order
        with u.hold_all_sync(marks):
            print("done")

        # expected output
        expected = (
            "entered 0\nentered 1\nentered 2\nentered 3\nentered 4\n"
            "done\n"
            "exited 4\nexited 3\nexited 2\nexited 1\nexited 0\n"
        )

        capt = capsys.readouterr().out
        assert capt == expected

    def test_bqplot_figure(self):
        fig = u.bqplot_figure(toolbar=False)
        assert isinstance(fig, bqplot.Figure)

        fig, tb = u.bqplot_figure(toolbar=True)
        assert isinstance(fig, bqplot.Figure)
        assert isinstance(tb, ipw.Widget)

    def test_bqplot_footprint(self, loaded_imviz):
        ra = 202.4695898
        dec = 47.1951868
        pa = 25.0
        fig = loaded_imviz.default_viewer.figure
        wcs = loaded_imviz.default_viewer.state.reference_data.coords
        fp_marks = u.bqplot_footprint(fig, "nirspec", ra, dec, pa, wcs)

        # should return 11 patches for nirspec
        expected_patches = 11
        assert isinstance(fp_marks, list)
        assert len(fp_marks) == expected_patches

        # color is default for nirspec if not specified
        assert fp_marks[0].colors == [DEFAULT_COLOR["NIRSpec"]]

        # if patches are passed, they are updated in place
        new_marks = u.bqplot_footprint(
            fig,
            "nirspec",
            ra,
            dec,
            pa,
            wcs,
            update_patches=fp_marks,
            color="red",
            fill_alpha=0.5,
        )
        assert len(new_marks) == expected_patches
        for i, mark in enumerate(new_marks):
            assert mark is fp_marks[i]
            assert mark.colors == ["red"]
            if i > 0:
                assert isinstance(mark, bqplot.Lines)
                assert mark.fill_opacities == [0.5]
            else:
                assert isinstance(mark, bqplot.Scatter)

    def test_bqplot_footprint_mosaic(self, loaded_imviz):
        ra = 202.4695898
        dec = 47.1951868
        pa = 25.0
        fig = loaded_imviz.default_viewer.figure
        wcs = loaded_imviz.default_viewer.state.reference_data.coords
        fp_marks = u.bqplot_footprint(
            fig, "nircam long", ra, dec, pa, wcs, add_mosaic=False
        )

        # should return 3 patches for nircam long, no mosaic
        expected_patches = 3
        assert isinstance(fp_marks, list)
        assert len(fp_marks) == expected_patches

        # with mosaic, should return 5 patches
        fp_marks = u.bqplot_footprint(
            fig,
            "nircam long",
            ra,
            dec,
            pa,
            wcs,
            add_mosaic=True,
            mosaic_offset=(10, 10),
        )
        assert isinstance(fp_marks, list)
        assert len(fp_marks) == 2 * (expected_patches - 1) + 1

        # with mosaic + 3 dither, should return 13 patches
        fp_marks = u.bqplot_footprint(
            fig,
            "nircam long",
            ra,
            dec,
            pa,
            wcs,
            add_mosaic=True,
            mosaic_offset=(10, 10),
            dither_pattern="FULL3",
        )
        assert isinstance(fp_marks, list)
        assert len(fp_marks) == 2 * 3 * (expected_patches - 1) + 1

    def test_bqplot_catalog(self, loaded_imviz, catalog_file):
        fig = loaded_imviz.default_viewer.figure
        wcs = loaded_imviz.default_viewer.state.reference_data.coords

        # test catalog: 2 primary, 5 filler sources
        cat_marks = u.bqplot_catalog(fig, catalog_file, wcs)

        # primary, filler marked with one scatter plot each
        expected_marks = 2
        assert len(cat_marks) == expected_marks
        for mark in cat_marks:
            assert isinstance(mark, bqplot.Scatter)
        assert cat_marks[0].colors == [DEFAULT_COLOR["Primary Sources"]]
        assert cat_marks[1].colors == [DEFAULT_COLOR["Filler Sources"]]

        # colors can be specified
        cat_marks = u.bqplot_catalog(fig, catalog_file, wcs, colors=["red", "blue"])
        assert cat_marks[0].colors == ["red"]
        assert cat_marks[1].colors == ["blue"]

    def test_bqplot_catalog_errors(self, loaded_imviz, tmp_path, catalog_file_2col):
        fig = loaded_imviz.default_viewer.figure
        wcs = loaded_imviz.default_viewer.state.reference_data.coords

        # empty catalog: raises value error
        bad_cat = tmp_path / "empty.txt"
        bad_cat.write_text("")
        with pytest.raises(ValueError, match="file is empty"):
            u.bqplot_catalog(fig, str(bad_cat), wcs)

        # bad catalog: raises value error for unexpected columns
        bad_cat = tmp_path / "bad_file.txt"
        bad_cat.write_text("bad")
        with pytest.raises(ValueError, match="expected 2"):
            u.bqplot_catalog(fig, str(bad_cat), wcs)

        # two columns instead of three: reads okay,
        # all sources assigned primary flag
        marks = u.bqplot_catalog(fig, catalog_file_2col, wcs)
        n_marks, n_pri, n_fill = 2, 7, 0
        assert len(marks) == n_marks
        assert marks[0].x.size == n_pri
        assert marks[1].x.size == n_fill

    @pytest.mark.parametrize(
        ("inst", "mean_value", "mode_value"),
        [("NIRSpec", 68, 67), ("NIRCam", 289, 290)],
    )
    def test_average_pa(self, timeline_data, inst, mean_value, mode_value):
        inst = inst.upper()

        label = u._average_pa(
            timeline_data["Time"],
            timeline_data[f"{inst}_min_PA"],
            timeline_data[f"{inst}_max_PA"],
        )
        assert label == f"Avg. PA: {mean_value} deg"

        # mode
        label = u._average_pa(
            timeline_data["Time"],
            timeline_data[f"{inst}_min_PA"],
            timeline_data[f"{inst}_max_PA"],
            method="mode",
        )
        assert label == f"Avg. PA: {mode_value} deg"

        # not visible in restricted range
        label = u._average_pa(
            timeline_data["Time"],
            timeline_data[f"{inst}_min_PA"],
            timeline_data[f"{inst}_max_PA"],
            method="mode",
            min_time=Time("2022-01-04"),
            max_time=Time("2022-01-05"),
        )
        assert label == "(not visible)"

    @pytest.mark.parametrize("inst", [None, "NIRSpec", "NIRCam"])
    def test_bqplot_timeline(self, inst):
        ra = 202.4695898
        dec = 47.1951868
        fig = bqplot.Figure()
        u.bqplot_timeline(fig, ra, dec, instrument=inst, show_v3pa=False)

        if inst is None:
            n_inst = 2
            assert len(fig.marks) == n_inst
            assert fig.marks[0].colors == [DEFAULT_COLOR["NIRSpec"]]
            assert fig.marks[1].colors == [DEFAULT_COLOR["NIRCam"]]
        elif inst == "NIRSpec":
            assert len(fig.marks) == 1
            assert fig.marks[0].colors == [DEFAULT_COLOR["NIRSpec"]]
        else:
            assert len(fig.marks) == 1
            assert fig.marks[0].colors == [DEFAULT_COLOR["NIRCam"]]

    @pytest.mark.parametrize(
        ("inst", "v3pa", "n_plot"),
        [
            (None, False, 2),
            (None, True, 3),
            ("NIRSpec", False, 1),
            ("NIRSpec", True, 2),
            ("NIRCam", False, 1),
            ("NIRCam", True, 2),
        ],
    )
    def test_bqplot_timeline_colors(self, inst, v3pa, n_plot):
        ra = 202.4695898
        dec = 47.1951868
        fig = bqplot.Figure()
        colors = ["red", "blue"]
        u.bqplot_timeline(fig, ra, dec, instrument=inst, show_v3pa=v3pa, colors=colors)

        assert len(fig.marks) == n_plot
        for i, mark in enumerate(fig.marks):
            assert isinstance(mark, bqplot.Lines)
            if v3pa and i == 0:
                assert mark.colors == [DEFAULT_COLOR["V3PA"]]
            elif inst is None:
                assert mark.colors == [colors[i - v3pa]]
            else:
                assert mark.colors == [colors[0]]

    @pytest.mark.parametrize("inst", [None, "NIRCam", "NIRSpec"])
    def test_bqplot_timeline_no_data(self, mocker, inst):
        ra = 202.4695898
        dec = 47.1951868
        fig = bqplot.Figure()

        # time is out of range -- just shows an error message
        u.bqplot_timeline(
            fig,
            ra,
            dec,
            start_date="2020-01-01",
            end_date="2020-02-01",
            instrument=inst,
        )
        assert len(fig.marks) == 1
        assert isinstance(fig.marks[0], bqplot.Label)

        # same if any error is raised in the timeline function
        mocker.patch.object(u.tl, "timeline", side_effect=ValueError("bad"))
        u.bqplot_timeline(fig, ra, dec, start_date="2020-01-01", end_date="2020-02-01")
        assert len(fig.marks) == 1
        assert isinstance(fig.marks[0], bqplot.Label)

    def test_bqplot_timeline_label_callback(self):
        ra = 202.4695898
        dec = 47.1951868
        fig = bqplot.Figure()
        u.bqplot_timeline(
            fig,
            ra,
            dec,
            instrument="NIRSpec",
            show_v3pa=False,
            start_date="2022-01-05",
            end_date="2022-01-09",
        )
        assert fig.marks[0].labels == ["NIRSpec", "Avg. PA: 68 deg"]

        # label is updated when figure axis range changes
        fig.axes[0].scale.min = Time("2022-01-03").to_datetime()
        fig.axes[0].scale.max = Time("2022-01-04").to_datetime()
        assert fig.marks[0].labels == ["NIRSpec", "(not visible)"]

    def test_remove_bqplot_patches(self):
        # add some marks to a figure
        fig = bqplot.Figure()
        scatter = bqplot.Scatter(x=[1, 2, 3], y=[3, 4, 5])
        line = bqplot.Lines(x=[1, 2, 3], y=[3, 4, 5])
        fig.marks = [scatter, line]
        n_marks = 2
        assert len(fig.marks) == n_marks

        # only the scatter plot is removed
        u.remove_bqplot_patches(fig, [scatter])
        assert len(fig.marks) == 1
        assert scatter not in fig.marks
        assert line in fig.marks

        # nothing happens if it is removed again or an empty list is passed
        u.remove_bqplot_patches(fig, [scatter])
        assert len(fig.marks) == 1
        u.remove_bqplot_patches(fig, [])
        assert len(fig.marks) == 1

        # the line can also be removed
        u.remove_bqplot_patches(fig, [line])
        assert len(fig.marks) == 0

    def test_clear_bqplot_figure(self):
        # add some marks to a figure
        fig = bqplot.Figure()
        scatter = bqplot.Scatter(x=[1, 2, 3], y=[3, 4, 5])
        line = bqplot.Lines(x=[1, 2, 3], y=[3, 4, 5])
        fig.marks = [scatter, line]
        n_marks = 2
        assert len(fig.marks) == n_marks

        u.clear_bqplot_figure(fig)
        assert len(fig.marks) == 0

    def test_bqplot_toolbar(self):
        fig = bqplot.Figure()
        scales = {"x": bqplot.LinearScale(), "y": bqplot.LinearScale()}
        line = bqplot.Lines(x=[1, 2, 3], y=[3, 4, 5], scales=scales)
        fig.marks = [line]

        # toolbar for figure
        tb = u.BqplotToolbar(fig)
        # widgets are in the widgets attribute, which is a
        # layout box at the top level
        assert isinstance(tb.widgets, ipw.Box)

        # nothing happens if zoom is set while axes are not set in
        # the figure yet
        assert len(fig.axes) == 0
        tb.mode_buttons.value = "x"
        assert tb.direction == " "
        assert fig.interaction is None

        # same for reset function
        tb.reset_zoom()

        # after axes are set, set zoom mode to 'x'
        fig.axes = [
            bqplot.Axis(scale=scales["x"]),
            bqplot.Axis(scale=scales["y"], orientation="vertical"),
        ]
        n_marks = 2
        assert len(fig.axes) == n_marks

        tb.mode_buttons.value = "x"
        assert tb.direction == "x"
        assert fig.interaction == tb.pan_zoom
        assert isinstance(tb.pan_zoom, bqplot.PanZoom)
        assert tb.pan_zoom.allow_zoom
        assert tb.pan_zoom.allow_pan
        assert tb.pan_zoom.scales == {"x": [scales["x"]]}

        # now reset will restore scale limits to default
        scales["x"].min = 1
        assert scales["x"].min == 1
        tb.reset_zoom()
        assert scales["x"].min is None

        # changing direction back to none turns off pan/zoom features but
        # does not clear interaction
        tb.mode_buttons.value = " "
        assert isinstance(tb.pan_zoom, bqplot.PanZoom)
        assert not tb.pan_zoom.allow_zoom
        assert not tb.pan_zoom.allow_pan
        assert tb.pan_zoom.scales == {"x": [scales["x"]]}

        # back to y or xy allows interaction again
        tb.mode_buttons.value = "y"
        assert isinstance(tb.pan_zoom, bqplot.PanZoom)
        assert tb.pan_zoom.allow_zoom
        assert tb.pan_zoom.allow_pan
        assert tb.pan_zoom.scales == {"y": [scales["y"]]}

        tb.mode_buttons.value = "xy"
        assert isinstance(tb.pan_zoom, bqplot.PanZoom)
        assert tb.pan_zoom.allow_zoom
        assert tb.pan_zoom.allow_pan
        assert tb.pan_zoom.scales == {"x": [scales["x"]], "y": [scales["y"]]}
