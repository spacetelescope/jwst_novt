import pytest

from jwst_novt import serve_novt as sn


def test_main_no_voila():
    sn.HAS_VOILA = False
    with pytest.raises(SystemExit):
        sn.main()
