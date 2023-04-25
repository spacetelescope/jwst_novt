from astropy.coordinates import SkyCoord
import pytest
import regions

from novt import footprints as fp


@pytest.mark.parametrize('instrument,n_reg',
                         [('nirspec', 11),
                          ('nircam_short', 9),
                          ('nircam_long', 3)])
def test_instrument_footprints(instrument, n_reg):
    ra = 202.4695898
    dec = 47.1951868
    pa = 25.0

    reg_func = getattr(fp, f'{instrument}_footprint')

    reg = reg_func(ra, dec, pa)
    assert len(reg) == n_reg
    assert isinstance(reg, regions.Regions)

    # center point
    assert isinstance(reg[0], regions.PointSkyRegion)
    assert reg[0].center == SkyCoord(ra, dec, unit='deg')

    # other apertures
    for r in reg[1:]:
        assert isinstance(r, regions.PolygonSkyRegion)


def test_source_catalog(catalog_file):
    primary, filler = fp.source_catalog(catalog_file)
    assert isinstance(primary, regions.Regions)
    assert isinstance(filler, regions.Regions)
    assert len(primary) == 2
    assert len(filler) == 5
