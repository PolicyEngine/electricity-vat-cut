"""Distributional, poverty and inequality impacts of the electricity VAT cut.

All functions take a PLAIN ``pandas.DataFrame`` of the baseline household
table (the pipeline strips the microdf MicroDataFrame wrapper first — its
reductions are already weight-aware, so explicit weighted math on it would
double-weight) plus a per-household ``gain`` column, and do every
aggregation with explicit household weights.

Poverty is relative BHC (equivalised HBAI household net income below 60% of
the person-weighted median), with the line held FIXED at its baseline value:
a temporary six-month transfer should not move the poverty line itself.
Deep poverty uses 50% of the same fixed median. Headcounts are
person-weighted (people living in households below the line).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def weighted_mean(values, weights) -> float:
    return float(np.average(np.asarray(values), weights=np.asarray(weights)))


def weighted_median(values, weights) -> float:
    values, weights = np.asarray(values), np.asarray(weights)
    order = np.argsort(values)
    values, weights = values[order], weights[order]
    cumulative = np.cumsum(weights)
    return float(values[np.searchsorted(cumulative, 0.5 * cumulative[-1])])


def weighted_gini(values, weights) -> float:
    values, weights = np.asarray(values, dtype=float), np.asarray(weights, dtype=float)
    order = np.argsort(values)
    values, weights = values[order], weights[order]
    cum_w = np.cumsum(weights)
    cum_vw = np.cumsum(values * weights)
    total_w, total_vw = cum_w[-1], cum_vw[-1]
    # Trapezoidal Lorenz-curve Gini on the weighted distribution.
    lorenz = cum_vw / total_vw
    prev_lorenz = np.concatenate([[0.0], lorenz[:-1]])
    return float(1 - np.sum((weights / total_w) * (lorenz + prev_lorenz)))


def equiv_income_decile(hh: pd.DataFrame) -> np.ndarray:
    """Household decile of baseline equivalised HBAI net income, with
    person-weighted decile boundaries — PolicyEngine's published decile
    convention."""
    equiv = hh["equiv_hbai_household_net_income"].to_numpy()
    people_w = (hh["household_weight"] * hh["household_count_people"]).to_numpy()
    order = np.argsort(equiv)
    cumulative = np.cumsum(people_w[order])
    boundaries = np.interp(np.linspace(0.1, 0.9, 9) * cumulative[-1], cumulative, equiv[order])
    return np.searchsorted(boundaries, equiv, side="right") + 1


def group_table(hh: pd.DataFrame, gain_col: str, group_col) -> list[dict]:
    """Weighted mean gain, gain as % of net income, total £m and household
    count, by group. ``group_col`` is a column name or a precomputed array."""
    groups = hh[group_col] if isinstance(group_col, str) else pd.Series(group_col, index=hh.index)
    rows = []
    for group, g in hh.groupby(groups):
        w = g["household_weight"]
        total = float((g[gain_col] * w).sum())
        net_income = float((g["household_net_income"].clip(lower=0) * w).sum())
        rows.append(
            {
                "group": int(group) if isinstance(group, (int, np.integer)) else str(group),
                "mean_gain": total / float(w.sum()),
                "pct_net_income": 100 * total / net_income if net_income > 0 else None,
                "total_m": total / 1e6,
                "n_households": float(w.sum()),
            }
        )
    return rows


def winners_share(hh: pd.DataFrame, gain_col: str) -> float:
    w = hh["household_weight"]
    return float(((hh[gain_col] > 0) * w).sum() / w.sum())


def poverty_impact(hh: pd.DataFrame, gain_col: str, deep: bool = False) -> dict:
    """Relative BHC poverty (fixed 60%-of-median line; 50% for deep) with the
    six-month gain added to household income, equivalised by each
    household's own baseline equivalisation factor."""
    equiv = hh["equiv_hbai_household_net_income"].to_numpy()
    people_w = (hh["household_weight"] * hh["household_count_people"]).to_numpy()
    # Per-household OECD equivalisation factor, recovered from the model's
    # own income pair; 1.0 where income is non-positive.
    factor = np.where(equiv > 0, hh["hbai_household_net_income"].to_numpy() / equiv, 1.0)
    line = (0.5 if deep else 0.6) * weighted_median(equiv, people_w)
    reformed_equiv = equiv + hh[gain_col].to_numpy() / factor
    base_poor, reformed_poor = equiv < line, reformed_equiv < line
    return {
        "line": line,
        "baseline_rate": float((base_poor * people_w).sum() / people_w.sum()),
        "reformed_rate": float((reformed_poor * people_w).sum() / people_w.sum()),
        "people_out_of_poverty": float(((base_poor & ~reformed_poor) * people_w).sum()),
    }


def inequality_impact(hh: pd.DataFrame, gain_col: str) -> dict:
    """Gini of equivalised HBAI net income, person-weighted, baseline vs
    baseline plus the (equivalised) six-month gain. The change is ~0 —
    reported anyway so the dashboard can say so with a number."""
    equiv = hh["equiv_hbai_household_net_income"].to_numpy().clip(min=0)
    people_w = (hh["household_weight"] * hh["household_count_people"]).to_numpy()
    factor = np.where(
        equiv > 0,
        hh["hbai_household_net_income"].to_numpy().clip(min=0) / np.where(equiv > 0, equiv, 1),
        1.0,
    )
    reformed = equiv + hh[gain_col].to_numpy() / np.where(factor > 0, factor, 1.0)
    return {
        "baseline_gini": weighted_gini(equiv, people_w),
        "reformed_gini": weighted_gini(reformed, people_w),
    }
