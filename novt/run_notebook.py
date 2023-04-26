import argparse
import os
import pathlib
import shutil
import sys
import tempfile

from voila.app import Voila
from voila.configuration import VoilaConfiguration

__all__ = ['main']

NOVT_DIR = pathlib.Path(__file__).parent.resolve()


def main(notebook_name):
    """
    Run a NOVT notebook as a Voila application.

    Parameters
    ----------
    notebook_name

    Returns
    -------

    """
    # Patterned on Jdaviz CLI script, simplified and adapted for
    # NOVT purposes
    if not os.path.isfile(notebook_name):
        notebook_name = NOVT_DIR / 'notebooks' / f'{notebook_name}.ipynb'
        if not os.path.isfile(notebook_name):
            raise FileNotFoundError(f'Cannot find notebook '
                                    f'{os.path.basename(notebook_name)}')

    # run a copy of the notebook from a temp directory,
    # but keep track of start directory to reset
    start_dir = os.path.abspath('.')
    nbdir = tempfile.mkdtemp()
    nbname = os.path.join(nbdir, os.path.basename(notebook_name))
    shutil.copyfile(notebook_name, nbname)
    os.chdir(nbdir)

    try:
        Voila.notebook_path = nbname
        VoilaConfiguration.enable_nbextensions = True
        VoilaConfiguration.file_whitelist = ['.*']
        sys.exit(Voila().launch_instance(argv=[]))
    finally:
        os.chdir(start_dir)


def _main():
    parser = argparse.ArgumentParser(
        description='Start a NOVT notebook as a Voila application')

    parser.add_argument('-n', '--notebook', dest='notebook', type=str,
                        action='store', default='novt',
                        help='Path to a notebook file or name of a '
                             'NOVT notebook.')
    args = parser.parse_args()
    main(args.notebook)
