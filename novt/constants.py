"""
Constants for use in standardizing names and generating instrument footprints.
"""
import pathlib

__all__ = ['NOVT_DIR', 'INSTRUMENT_NAMES', 'NIRCAM_DITHER_OFFSETS',
           'NO_MOSAIC', 'DEFAULT_COLOR']


NOVT_DIR = pathlib.Path(__file__).parent.resolve()
"""pathlib.Path : Path to the top-level package directory."""


INSTRUMENT_NAMES = {
    'nirspec': 'NIRSpec',
    'nircam_long': 'NIRCam Long',
    'nircam_short': 'NIRCam Short',
}
"""dict : Capitalized instrument names for display."""


# see JDox article, Table 1:
# https://jwst-docs.stsci.edu/jwst-near-infrared-spectrograph/
#    nirspec-operations/nirspec-mos-operations/
#    nirspec-mos-operations-pre-imaging-using-nircam,
NIRCAM_DITHER_OFFSETS = {
    'NONE': [(0.0, 0.0)],
    'FULL3': [(-58.0, -23.5), (0.0, 0.0), (58.0, 23.5)],
    'FULL3TIGHT': [(-58.0, -7.5), (0.0, 0.0), (58.0, 7.5)],
    'FULL6': [(-72.0, -30.0), (-43.0, -18.0), (-14.0, -6.0),
              (15.0, 6.0), (44.0, 18.0), (73.0, 30.0)],
    '8NIRSPEC': [(-24.6, -64.1), (-24.4, -89.0), (24.6, -88.8), (24.4, -63.9),
                 (24.6, 64.1), (24.4, 89.0), (-24.6, 88.8), (-24.4, 63.9)],
}
"""dict : Dither offset values by pattern name, in telescope coordinates.

V2 offsets are subtracted; V3 offsets are added.
"""


NO_MOSAIC = {'8NIRSPEC'}
"""set : Dither pattern values for which mosaic is not enabled."""


DEFAULT_COLOR = {
    'NIRSpec': '#d62728',  # tab:red
    'NIRCam Long': '#1f77b4',  # tab:blue
    'NIRCam Short': '#2ca02c',  # tab:green
    'Primary Sources': '#ff7f0e',  # tab:orange
    'Filler Sources': '#9467bd',  # tab:purple
    'V3PA': '#7f7f7f'  # tab:gray
}
"""dict : Default colors for instrument footprint overlays.

Values from defaults in matplotlib.colors.TABLEAU_COLORS.
"""
