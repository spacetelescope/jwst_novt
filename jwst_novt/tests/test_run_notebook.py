import pytest

from jwst_novt import run_notebook as rn


def test_main_no_voila():
    rn.HAS_VOILA = False
    with pytest.raises(SystemExit):
        rn.main("jwst_novt")


def test_main_bad_notebook():
    rn.HAS_VOILA = True
    with pytest.raises(FileNotFoundError):
        rn.main("bad")
