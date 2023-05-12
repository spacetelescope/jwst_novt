import argparse
import os
import sys
import tempfile
import warnings

try:
    from voila.app import Voila
    from voila.configuration import VoilaConfiguration
except ImportError as err:  # pragma: no cover
    warnings.warn(f'Optional dependency `voila` not present: '
                  f'novt.run_notebook functionality will not work. '
                  f'Import error: {err}')
    Voila = None
    VoilaConfiguration = None
    HAS_VOILA = False
else:  # pragma: no cover
    HAS_VOILA = True

from novt.constants import NOVT_DIR

__all__ = ['main']


def main(notebook_name):
    """
    Run a NOVT notebook as a Voila application.

    Parameters
    ----------
    notebook_name : str
        The notebook to run.  May be either a full path to an
        existing notebook or else the base name of a notebook installed
        in the novt/notebooks directory.
    """
    if not HAS_VOILA:
        sys.exit(1)

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

    with open(notebook_name) as f:
        notebook_template = f.read()

    with open(nbname, 'w') as nbf:
        nbf.write(notebook_template.replace('novt_notebook', 'novt_voila'))

    os.chdir(nbdir)
    try:
        Voila.notebook_path = nbname
        VoilaConfiguration.theme = 'light'
        VoilaConfiguration.enable_nbextensions = True
        VoilaConfiguration.file_whitelist = ['.*']
        sys.exit(Voila().launch_instance(argv=[]))
    finally:
        os.chdir(start_dir)


def _main():  # pragma: no cover
    parser = argparse.ArgumentParser(
        description='Start a NOVT notebook as a Voila application')

    parser.add_argument('-n', '--notebook', dest='notebook', type=str,
                        action='store', default='novt',
                        help='Path to a notebook file or name of a '
                             'NOVT notebook.')
    args = parser.parse_args()
    main(args.notebook)
