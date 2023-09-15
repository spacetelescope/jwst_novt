import argparse
import os
import sys
import tempfile
import warnings
from pathlib import Path

try:
    from voila.app import Voila
    from voila.configuration import VoilaConfiguration
except ImportError as err:  # pragma: no cover
    warnings.warn(
        f"Optional dependency `voila` not present: "
        f"jwst_novt.run_notebook functionality will not work. "
        f"Import error: {err}",
        stacklevel=2,
    )
    Voila = None
    VoilaConfiguration = None
    HAS_VOILA = False
else:  # pragma: no cover
    HAS_VOILA = True

from jwst_novt.constants import NOVT_DIR

__all__ = ["main"]


def main(notebook_name, *, serve_only=False):
    """
    Run a NOVT notebook as a Voila application.

    Parameters
    ----------
    notebook_name : str
        The notebook to run. May be either a full path to an
        existing notebook or else the base name of a notebook installed
        in the jwst_novt/notebooks directory.
    serve_only: bool, optional
        If set, the application is served without opening a browser window.
    """
    if not HAS_VOILA:
        sys.exit(1)

    # Patterned on Jdaviz CLI script, simplified and adapted for
    # NOVT purposes
    notebook_name = Path(notebook_name)
    if not notebook_name.is_file():
        notebook_name = NOVT_DIR / "notebooks" / f"{notebook_name}.ipynb"
        if not notebook_name.is_file():
            msg = f"Cannot find notebook {notebook_name.name}"
            raise FileNotFoundError(msg)

    # run a copy of the notebook from a temp directory,
    # but keep track of start directory to reset
    start_dir = Path().absolute()
    nbdir = tempfile.mkdtemp()
    nbname = Path(nbdir) / notebook_name.name

    with notebook_name.open() as f:
        notebook_template = f.read()

    with nbname.open("w") as nbf:
        nbf.write(notebook_template.replace("novt_notebook", "novt_voila"))

    os.chdir(nbdir)
    try:
        Voila.notebook_path = nbname
        VoilaConfiguration.theme = "light"
        VoilaConfiguration.enable_nbextensions = True
        VoilaConfiguration.file_whitelist = [".*"]
        if serve_only:
            Voila.open_browser = False
        sys.exit(Voila().launch_instance(argv=[]))
    finally:
        os.chdir(start_dir)


def _main():  # pragma: no cover
    parser = argparse.ArgumentParser(
        description="Start a NOVT notebook as a Voila application"
    )

    parser.add_argument(
        "-n",
        "--notebook",
        dest="notebook",
        type=str,
        action="store",
        default="novt",
        help="Path to a notebook file or name of a NOVT notebook.",
    )
    parser.add_argument(
        "-s",
        "--serve-only",
        dest="serve_only",
        action="store_true",
        default=False,
        help="Serve the notebook without opening a browser.",
    )
    args = parser.parse_args()
    main(args.notebook, serve_only=args.serve_only)
