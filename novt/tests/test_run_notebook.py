import pytest

from novt import run_notebook as rn


def test_main_no_voila():
    rn.HAS_VOILA = False
    with pytest.raises(SystemExit):
        rn.main('novt')


def test_main_bad_notebook():
    rn.HAS_VOILA = True
    with pytest.raises(FileNotFoundError):
        rn.main('bad')
