import shutil
import sys
import warnings
from pathlib import Path

try:
    from voila.app import Voila
except ImportError as err:  # pragma: no cover
    warnings.warn(
        f"Optional dependency `voila` not present: "
        f"jwst_novt.serve_novt functionality will not work. "
        f"Import error: {err}",
        stacklevel=2,
    )
    Voila = None
    HAS_VOILA = False
else:  # pragma: no cover
    HAS_VOILA = True

from jwst_novt.constants import NOVT_DIR

__all__ = ["main"]


def main():
    """Serve the main NOVT application from the current directory."""
    if not HAS_VOILA:
        sys.exit(1)

    # get the necessary files
    notebook_file = NOVT_DIR / "notebooks" / "novt_voila.ipynb"
    config_file = NOVT_DIR / "data" / "voila.json"

    # copy the notebook to the current directory
    nbdir = Path().absolute()
    nbname = Path(nbdir) / notebook_file.name
    shutil.copyfile(notebook_file, nbname)

    # copy the voila config to the current directory
    shutil.copyfile(config_file, nbdir / config_file.name)

    # launch voila
    sys.exit(Voila().launch_instance(argv=[nbname.name]))
