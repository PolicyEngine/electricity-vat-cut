"""VAT arithmetic, shared by the pipeline and tests. No PolicyEngine imports.

Weight-preserving: pandas-like inputs (including microdf's MicroSeries) pass
through pandas' own arithmetic, which propagates weights; plain ndarrays and
scalars go through numpy. Never coerce inputs with ``np.asarray`` here — that
would strip MicroSeries weights.
"""

from __future__ import annotations

import numpy as np


def vat_component(spending_incl_vat, old_rate: float = 0.05, new_rate: float = 0.0):
    """Household gain from cutting VAT on observed (VAT-inclusive) spending.

    Observed spending includes VAT at ``old_rate``, so the pre-VAT base is
    ``spending / (1 + old_rate)`` and the gain from moving to ``new_rate``
    is ``spending * (old_rate - new_rate) / (1 + old_rate)`` — for the
    5%-to-0% cut, spending × 5/105.
    """
    if old_rate < 0 or new_rate < 0:
        raise ValueError("VAT rates must be non-negative.")
    if new_rate > old_rate:
        raise ValueError("vat_component measures a cut: new_rate must not exceed old_rate.")
    if np.any(np.less(spending_incl_vat, 0)):
        raise ValueError("spending_incl_vat must be non-negative.")
    return spending_incl_vat * (old_rate - new_rate) / (1 + old_rate)


def window_gain(full_year_gain, window_share: float):
    """Gain realised inside the relief window.

    ``window_share`` is the share of annual spending falling in the window:
    0.5 for a uniform six months, ~0.575 winter-weighted for October-March.
    """
    if not 0 <= window_share <= 1:
        raise ValueError("window_share must lie in [0, 1].")
    return full_year_gain * window_share
