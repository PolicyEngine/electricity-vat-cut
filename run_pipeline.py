"""Backwards-compatible shim: prefer `python -m electricity_vat_cut` or the
`electricity-vat-cut-build` console script."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from electricity_vat_cut.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
