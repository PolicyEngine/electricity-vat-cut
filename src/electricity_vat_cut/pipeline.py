"""Main pipeline: build the dashboard JSON for the electricity VAT cut.

The baseline runs on the standard policyengine.py stack (per-year certified
Enhanced FRS datasets from ``pe.uk.ensure_datasets``, one
``policyengine.Simulation``). The reform itself is computed arithmetically:
PolicyEngine's native ``vat`` variable spreads a flat 2.5% reduced-rate
share over total consumption rather than electricity-specific spending, so
the household gain is taken directly from the dataset's
``electricity_consumption`` input (LCFS-imputed, NEED-calibrated) as
spending × 5/105 — see :mod:`electricity_vat_cut.formulas` — halved for the
six-month window (with a winter-weighted sensitivity).
"""

from __future__ import annotations

import datetime
import importlib.metadata
import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import sources
from .formulas import vat_component, window_gain
from .impacts import (
    equiv_income_decile,
    group_table,
    inequality_impact,
    poverty_impact,
    weighted_mean,
    winners_share,
)
from .simulations import (
    DATASET,
    ensure_uk_datasets,
    load_electricity_consumption,
    run_baseline,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = REPO_ROOT / "data" / "electricity_vat_cut_results.json"
DASHBOARD_OUTPUT_PATH = (
    REPO_ROOT / "dashboard" / "public" / "data" / "electricity_vat_cut_results.json"
)
DEFAULT_DATA_FOLDER = REPO_ROOT / "data" / "policyengine_datasets"

# Simulation ids double as output-cache filenames (`<id>.h5` beside the
# per-year dataset files), so they are keyed by dataset vintage — a dataset
# upgrade must not silently reuse stale cached outputs.
DATASET_STEM = Path(DATASET.rsplit("@", 1)[0]).stem

OPTIONAL_BREAKDOWNS = {"region": "by_region", "tenure_type": "by_tenure", "country": "by_country"}


def _methods(year: int, winter_share: float) -> dict:
    return {
        "gain_computation": (
            "PolicyEngine UK's native vat variable applies a flat 2.5% "
            "reduced-rate share to total household consumption, so zeroing "
            "the reduced rate in the parameter tree would misattribute the "
            "cut across all reduced-rated spending. Instead, each "
            "household's gain is computed directly from its electricity "
            f"spending in the Enhanced FRS dataset for {year}: observed "
            "spending includes VAT at 5%, so the full-year gain is spending "
            "× 5/105, and the six-month gain is half (uniform) or the "
            f"winter share ({winter_share:.1%} of annual spending in "
            "October-March) as a sensitivity."
        ),
        "electricity_data": (
            "electricity_consumption is a household input in the Enhanced "
            "FRS 2024-25 dataset, imputed from the Living Costs and Food "
            "Survey and calibrated to the National Energy Efficiency Data "
            "framework (NEED), uprated to the analysis year by "
            "policyengine-uk-data. It is populated for about 86% of "
            "households; households with no recorded electricity spending "
            "(e.g. bills in rent, prepayment gaps in the imputation) gain "
            "nothing in the model, so the winners share is below 100%."
        ),
        "pass_through": (
            "The central case assumes 100% pass-through of the VAT cut to "
            "household bills: VAT is charged on the retail bill and the "
            "Ofgem price cap is set net of VAT, so the statutory incidence "
            "passes through mechanically for capped tariffs. 75% and 50% "
            "scenarios scale every household's gain proportionally, as a "
            "sensitivity to supplier or price-cap-timing absorption."
        ),
        "temporary_measure": (
            "The zero rate runs 1 October 2026 to 31 March 2027. Costs and "
            "gains are reported full-year (for comparability) and for the "
            "six-month window: uniform halving as the headline, and a "
            "winter-weighted variant reflecting that domestic electricity "
            "demand is higher in October-March."
        ),
        "poverty": (
            "Relative BHC poverty: people in households whose equivalised "
            "HBAI net income falls below 60% of the person-weighted median "
            "(50% for deep poverty). The line is held FIXED at its baseline "
            "value — a temporary six-month transfer should not move the "
            "poverty line itself. The six-month gain is added to household "
            "income and equivalised with each household's own baseline "
            "equivalisation factor."
        ),
        "no_behavioural_response": (
            "No behavioural response is modelled: electricity demand is "
            "highly price-inelastic in the short run and the cut is 4.8% of "
            "the bill for six months, so any induced consumption (which "
            "would raise the cost slightly) is ignored. Inflation effects "
            "(the government claims about -0.10pp CPI) are also outside the "
            "model."
        ),
        "scope": (
            "The model covers households only. The government's £850m "
            "costing also includes non-VAT-registered small businesses on "
            "domestic relief, charities and care homes, plus comparable "
            "funding for Northern Ireland, and is not OBR-certified — so "
            "the modelled household cost should sit below it."
        ),
    }


def run(
    year: int = 2026,
    data_folder: str | Path | None = None,
    winter_share: float = sources.WINTER_SHARE.value,
    pass_through: list[float] | None = None,
    output_path: Path = OUTPUT_PATH,
) -> dict:
    """Run the pipeline end-to-end and write the results JSON."""
    data_folder = Path(data_folder) if data_folder else DEFAULT_DATA_FOLDER
    pass_through = pass_through or [s.value for s in sources.PASS_THROUGH_SCENARIOS]

    # ── Step 1: certified per-year dataset and baseline simulation ────────
    print(f"Step 1: Ensuring {DATASET} dataset for {year} and running the baseline...")
    datasets = ensure_uk_datasets([year], data_folder)
    sim = run_baseline(datasets[year], sim_id=f"{DATASET_STEM}_electricity_vat_baseline_{year}")
    # MicroDataFrame reductions are weight-aware; drop to a plain DataFrame
    # so every weighted aggregate below is explicit (never double-weighted).
    hh = pd.DataFrame(sim.output_dataset.data.household).copy()

    # ── Step 2: merge electricity spending from the input dataset ─────────
    print("Step 2: Merging electricity_consumption from the input dataset...")
    electricity = load_electricity_consumption(data_folder, year)
    assert len(electricity) == len(hh), "input/output household row mismatch"
    hh["electricity"] = np.nan_to_num(electricity)
    w = hh["household_weight"]
    n_households = float(w.sum())
    share_with_spend = float(((hh["electricity"] > 0) * w).sum() / n_households)
    mean_spend = weighted_mean(hh["electricity"], w)
    print(
        f"    {n_households / 1e6:.1f}m households; mean electricity spend "
        f"£{mean_spend:.0f}/yr; recorded for {share_with_spend:.1%}"
    )

    # ── Step 3: household gains (full-year, uniform 6m, winter 6m) ────────
    print("Step 3: Computing household gains...")
    hh["gain_full_year"] = vat_component(
        hh["electricity"], sources.OLD_VAT_RATE.value, sources.NEW_VAT_RATE.value
    )
    hh["gain_6m"] = window_gain(hh["gain_full_year"], 0.5)
    hh["gain_6m_winter"] = window_gain(hh["gain_full_year"], winter_share)

    # ── Step 4: headline costs, validated against the government claims ───
    print("Step 4: Headline costs...")
    cost_full_year = float((hh["gain_full_year"] * w).sum())
    cost_6m = float((hh["gain_6m"] * w).sum())
    cost_6m_winter = float((hh["gain_6m_winter"] * w).sum())
    claim_m = sources.GOVERNMENT_COST_CLAIM.value
    print(
        f"    Full-year £{cost_full_year / 1e9:.2f}bn | 6m uniform "
        f"£{cost_6m / 1e6:.0f}m | 6m winter £{cost_6m_winter / 1e6:.0f}m "
        f"(government claim £{claim_m}m)"
    )
    assert 0.5 < (cost_6m / 1e6) / claim_m < 1.5, (
        "Modelled six-month cost implausibly far from the government claim; "
        "refusing to write results."
    )

    # ── Step 5: distributional breakdowns ─────────────────────────────────
    print("Step 5: Distributional breakdowns...")
    by_decile = group_table(hh, "gain_6m", "household_income_decile")
    for row, fy in zip(
        by_decile, group_table(hh, "gain_full_year", "household_income_decile"), strict=True
    ):
        row["mean_gain_full_year"] = fy["mean_gain"]
    # PolicyEngine marks households it excludes from the income ranking with
    # decile -1; drop them from the decile view (they remain in every
    # aggregate, and the equivalised-decile ranking covers all households).
    by_decile = [row for row in by_decile if row["group"] >= 1]
    equiv_deciles = equiv_income_decile(hh)
    by_equiv_decile = group_table(hh, "gain_6m", equiv_deciles)
    by_quintile = group_table(hh, "gain_6m", (equiv_deciles + 1) // 2)
    by_quartile = group_table(hh, "gain_6m", (equiv_deciles * 4 + 9) // 10)
    optional = {}
    for column, key in OPTIONAL_BREAKDOWNS.items():
        optional[key] = group_table(hh, "gain_6m", column) if column in hh.columns else None
    def spend_table(group_col) -> list[dict]:
        groups = (
            hh[group_col] if isinstance(group_col, str) else pd.Series(group_col, index=hh.index)
        )
        return [
            {
                "group": int(group) if isinstance(group, (int, np.integer)) else str(group),
                "mean_spend": weighted_mean(g["electricity"], g["household_weight"]),
            }
            for group, g in hh.groupby(groups)
            if not (isinstance(group, (int, np.integer)) and group < 1)
        ]

    baseline_spend_by = {
        "by_decile": spend_table("household_income_decile"),
        "by_quintile": spend_table((equiv_deciles + 1) // 2),
        "by_quartile": spend_table((equiv_deciles * 4 + 9) // 10),
    }
    for column, key in OPTIONAL_BREAKDOWNS.items():
        baseline_spend_by[key] = spend_table(column) if column in hh.columns else None

    # ── Step 6: pass-through scenarios (proportional gain scaling) ────────
    print("Step 6: Pass-through scenarios...")
    scenario_sources = {s.value: s for s in sources.PASS_THROUGH_SCENARIOS}
    pass_through_rows = [
        {
            "rate": rate,
            "cost_6m_m": cost_6m * rate / 1e6,
            "cost_6m_winter_m": cost_6m_winter * rate / 1e6,
            "mean_gain_6m": cost_6m * rate / n_households,
            "description": getattr(scenario_sources.get(rate), "description", None),
            "url": getattr(scenario_sources.get(rate), "url", None),
        }
        for rate in pass_through
    ]

    # ── Step 7: poverty and inequality ────────────────────────────────────
    print("Step 7: Poverty and inequality...")
    poverty = poverty_impact(hh, "gain_6m")
    deep_poverty = poverty_impact(hh, "gain_6m", deep=True)
    inequality = inequality_impact(hh, "gain_6m")
    winners = winners_share(hh, "gain_6m")
    print(
        f"    BHC relative poverty {poverty['baseline_rate']:.3%} -> "
        f"{poverty['reformed_rate']:.3%} "
        f"({poverty['people_out_of_poverty'] / 1e3:.0f}k people out); "
        f"winners {winners:.1%}"
    )

    # ── Step 8: write the results JSON ────────────────────────────────────
    print("Step 8: Writing results JSON...")
    output = {
        "metadata": {
            "generated": datetime.date.today().isoformat(),
            "policyengine_version": importlib.metadata.version("policyengine"),
            "policyengine_uk_version": importlib.metadata.version("policyengine-uk"),
            "dataset": DATASET,
            "year": year,
            "winter_share": winter_share,
        },
        **sources.as_json(),
        "methods": _methods(year, winter_share),
        "baseline": {
            "n_households": n_households,
            "share_with_electricity_spend": share_with_spend,
            "mean_electricity_spend": mean_spend,
            "total_electricity_spend_bn": float((hh["electricity"] * w).sum()) / 1e9,
            "spend_by": baseline_spend_by,
        },
        "reform": {
            "cost": {
                "full_year_bn": cost_full_year / 1e9,
                "six_month_uniform_m": cost_6m / 1e6,
                "six_month_winter_m": cost_6m_winter / 1e6,
            },
            "mean_gain": {
                "full_year": cost_full_year / n_households,
                "six_month_uniform": cost_6m / n_households,
                "six_month_winter": cost_6m_winter / n_households,
            },
            "winners_share": winners,
            "by_decile": by_decile,
            "by_equiv_decile": by_equiv_decile,
            "by_quintile": by_quintile,
            "by_quartile": by_quartile,
            **optional,
            "pass_through": pass_through_rows,
        },
        "poverty": {"bhc_relative": poverty, "bhc_deep": deep_poverty},
        "inequality": inequality,
    }
    for path in (output_path, DASHBOARD_OUTPUT_PATH):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(output, indent=2))
        print(f"    wrote {path}")
    print("Done.")
    return output
