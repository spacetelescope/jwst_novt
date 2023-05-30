import pytest
import regions
from astropy.coordinates import SkyCoord

from jwst_novt import footprints as fp


@pytest.mark.parametrize(
    ("instrument", "n_reg"), [("nirspec", 11), ("nircam_short", 9), ("nircam_long", 3)]
)
def test_instrument_footprints(instrument, n_reg):
    ra = 202.4695898
    dec = 47.1951868
    pa = 25.0

    reg_func = getattr(fp, f"{instrument}_footprint")

    reg = reg_func(ra, dec, pa)
    assert len(reg) == n_reg
    assert isinstance(reg, regions.Regions)

    # center point
    assert isinstance(reg[0], regions.PointSkyRegion)
    assert reg[0].center == SkyCoord(ra, dec, unit="deg")

    # other apertures
    for r in reg[1:]:
        assert isinstance(r, regions.PolygonSkyRegion)


@pytest.mark.parametrize(
    ("channel", "dither", "mosaic", "offsets", "n_reg"),
    # n_reg is n_tile * n_dither * n_aperture + 1 center
    [
        ("long", "NONE", False, (0, 0), 2 + 1),
        ("long", "NONE", True, (0, 0), 2 * 2 + 1),
        ("long", "NONE", True, None, 2 * 2 + 1),
        ("long", "NONE", True, (20, 20), 2 * 2 + 1),
        ("long", "FULL3", False, (0, 0), 3 * 2 + 1),
        ("long", "FULL3", True, (20, 20), 2 * 3 * 2 + 1),
        ("long", "FULL3TIGHT", False, (0, 0), 3 * 2 + 1),
        ("long", "FULL3TIGHT", True, (20, 20), 2 * 3 * 2 + 1),
        ("long", "FULL6", False, (0, 0), 6 * 2 + 1),
        ("long", "FULL6", True, (20, 20), 2 * 6 * 2 + 1),
        # mosaics not allowed for 8nirspec
        ("long", "8NIRSPEC", False, (0, 0), 8 * 2 + 1),
        ("long", "8NIRSPEC", True, (20, 20), 8 * 2 + 1),
        ("long", "BAD", False, (0, 0), "error"),
        # short channel has 8 apertures
        ("short", "NONE", False, (0, 0), 8 + 1),
        ("short", "FULL3", True, (20, 20), 2 * 3 * 8 + 1),
        ("short", "8NIRSPEC", True, (20, 20), 8 * 8 + 1),
    ],
)
def test_nircam_dithers(channel, dither, mosaic, offsets, n_reg):
    ra = 202.4695898
    dec = 47.1951868
    pa = 25.0

    if n_reg == "error":
        with pytest.raises(ValueError, match="not recognized"):
            fp.nircam_dither_footprint(
                ra,
                dec,
                pa,
                channel=channel,
                dither_pattern=dither,
                add_mosaic=mosaic,
                mosaic_offset=offsets,
            )
    else:
        reg = fp.nircam_dither_footprint(
            ra,
            dec,
            pa,
            channel=channel,
            dither_pattern=dither,
            add_mosaic=mosaic,
            mosaic_offset=offsets,
        )

        assert len(reg) == n_reg
        assert isinstance(reg, regions.Regions)

        # one center point
        assert isinstance(reg[0], regions.PointSkyRegion)
        assert reg[0].center == SkyCoord(ra, dec, unit="deg")

        # other apertures
        for r in reg[1:]:
            assert isinstance(r, regions.PolygonSkyRegion)


@pytest.mark.parametrize("in_file", [True, False])
def test_source_catalog(catalog_file, catalog_dataframe, in_file):
    if in_file:
        catalog = catalog_file
    else:
        catalog = catalog_dataframe
    primary, filler = fp.source_catalog(catalog)
    assert isinstance(primary, regions.Regions)
    assert isinstance(filler, regions.Regions)

    expected_primary, expected_filler = 2, 5
    assert len(primary) == expected_primary
    assert len(filler) == expected_filler


@pytest.mark.parametrize("in_file", [True, False])
def test_source_catalog_2col(catalog_file_2col, catalog_dataframe_2col, in_file):
    if in_file:
        catalog = catalog_file_2col
    else:
        catalog = catalog_dataframe_2col
    primary, filler = fp.source_catalog(catalog)
    assert isinstance(primary, regions.Regions)
    assert isinstance(filler, regions.Regions)

    expected_primary, expected_filler = 7, 0
    assert len(primary) == expected_primary
    assert len(filler) == expected_filler


def test_source_catalog_errors(tmp_path):
    # empty catalog: raises value error
    bad_cat = tmp_path / "empty.txt"
    bad_cat.write_text("")
    with pytest.raises(ValueError, match="file is empty"):
        fp.source_catalog(str(bad_cat))

    # bad catalog: raises value error for unexpected columns
    bad_cat = tmp_path / "bad_file.txt"
    bad_cat.write_text("bad")
    with pytest.raises(ValueError, match="expected 2"):
        fp.source_catalog(str(bad_cat))
