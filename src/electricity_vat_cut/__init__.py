"""Electricity VAT cut analysis.

Models the temporary VAT cut on domestic electricity (5% to 0%, 1 October
2026 to 31 March 2027) announced by PM Andy Burnham, using the PolicyEngine
UK microsimulation baseline and the Enhanced FRS electricity spending
imputation.
"""

from .formulas import vat_component, window_gain

__all__ = [
    "run",
    "vat_component",
    "window_gain",
]


def __getattr__(name: str):
    # `run` pulls in the PolicyEngine stack, which only the [simulation]
    # extra installs; import it lazily so the pure-arithmetic tests run
    # without it.
    if name == "run":
        from .pipeline import run

        return run
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
