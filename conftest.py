# Project defaults and fixtures for pytest

import pytest


@pytest.fixture()
def catalog_file(tmp_path):
    filename = tmp_path / 'sources.radec'
    with open(filename, 'w') as fh:
        fh.write('202.42053  47.17906  F  16.58300\n'
                 '202.42514  47.29251  P  16.69000\n'
                 '202.45114  47.14672  F  16.70300\n'
                 '202.48190  47.19670  F  16.71100\n'
                 '202.43707  47.16641  F  17.20600\n'
                 '202.47760  47.20205  F  17.32900\n'
                 '202.48415  47.24812  P  17.52500\n')
    return filename
