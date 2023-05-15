from contextlib import contextmanager

from astropy.wcs import WCS
import pytest

try:
    import ipywidgets as ipw
    from novt.interact import display as u
except ImportError:
    ipw = None
    u = None
    HAS_DISPLAY = False
else:
    HAS_DISPLAY = True


@pytest.fixture
def image_2d_wcs():
    return WCS({'CTYPE1': 'RA---TAN', 'CUNIT1': 'deg',
                'CDELT1': -0.0002777777778,
                'CRPIX1': 1, 'CRVAL1': 202.4695898,
                'CTYPE2': 'DEC--TAN', 'CUNIT2': 'deg',
                'CDELT2': 0.0002777777778,
                'CRPIX2': 1, 'CRVAL2': 47.1951868})


@pytest.mark.skipif(not HAS_DISPLAY, reason='Missing optional dependencies')
class TestDisplay(object):

    def test_hold_all_sync(self, capsys):
        # mock a mark class with a simple context manager for testing
        class MockMark(object):
            def __init__(self, i):
                self.i = i

            @contextmanager
            def hold_sync(self):
                print(f'entered {self.i}')
                yield
                print(f'exited {self.i}')

        # list of mark objects
        marks = [MockMark(i) for i in range(5)]

        # call all hold_sync cms in order
        with u.hold_all_sync(marks):
            print('done')

        # expected output
        expected = ('entered 0\nentered 1\nentered 2\nentered 3\nentered 4\n'
                    'done\n'
                    'exited 4\nexited 3\nexited 2\nexited 1\nexited 0\n')

        capt = capsys.readouterr().out
        assert capt == expected

    def test_bqplot_figure(self):
        ...

    def test_bqplot_footprint(self):
        ...

    def test_bqplot_catalog(self):
        ...

    def test_bqplot_timeline(self):
        ...

    def test_remove_bqplot_patches(self):
        ...

    def test_bqplot_toolbar(self):
        ...
