"""Simulation construction on the standard policyengine.py stack.

The baseline simulation is built through the ``policyengine`` package (the
policyengine.py wrapper), never by constructing
``policyengine_uk.Microsimulation`` objects directly (the per-year dataset
files that ``ensure_datasets`` writes are not loadable that way):

- ``pe.uk.ensure_datasets`` materialises the published Enhanced FRS 2024-25
  dataset, referenced directly as an ``hf://`` URI (a private-repo token is
  read from ``HUGGING_FACE_TOKEN``), as one per-year dataset file per
  simulated year. Simulations run on those files unmodified: this repo does
  no local reweighting, since calibration belongs upstream in
  policyengine-uk-data.
- ``policyengine.Simulation`` runs the baseline model once, with a
  deterministic id so policyengine.py's output-dataset cache (``<id>.h5``
  beside the input dataset file) lets a re-run skip the simulation.

No reformed simulation is needed: PolicyEngine's native ``vat`` variable
applies a flat 2.5% reduced-rate share of total consumption rather than
electricity-specific spending, so zeroing ``gov.hmrc.vat.reduced_rate``
would misattribute the cut. The pipeline instead computes each household's
gain directly from the dataset's ``electricity_consumption`` input
(LCFS-imputed, NEED-calibrated) — see :mod:`electricity_vat_cut.formulas`.

CRITICAL — ``sim.output_dataset.data.household`` is a microdf
MicroDataFrame whose reductions are already weight-aware; the pipeline
wraps it in ``pd.DataFrame`` before doing any explicit weighted math, or
every aggregate would be double-weighted.
"""

from __future__ import annotations

from pathlib import Path

DATASET = "hf://policyengine/policyengine-uk-data/enhanced_frs_2024_25.h5"

# Variables needed beyond policyengine.py's bundled UK defaults, for the
# regional/tenure/country breakdowns.
EXTRA_VARIABLES = {
    "household": ["region", "tenure_type", "country"],
}


def ensure_uk_datasets(years: list[int], data_folder: str | Path) -> dict[int, object]:
    """Materialise (or load) the published Enhanced FRS dataset for each year.

    Returns a mapping ``{year: PolicyEngineUKDataset}``.
    """
    import policyengine as pe

    datasets = pe.uk.ensure_datasets(
        datasets=[DATASET],
        years=list(years),
        data_folder=str(data_folder),
    )
    return {ds.year: ds for ds in datasets.values()}


def run_baseline(dataset, sim_id: str):
    """Build and run (with output-dataset caching) the baseline
    policyengine.py Simulation."""
    import policyengine as pe

    sim = pe.Simulation(
        id=sim_id,
        dataset=dataset,
        tax_benefit_model_version=pe.uk.model,
        extra_variables=EXTRA_VARIABLES,
    )
    sim.ensure()
    return sim


def load_electricity_consumption(data_folder: str | Path, year: int):
    """The ``electricity_consumption`` input column, aligned to the output
    household table's row order (the per-year input h5 and the simulation
    output share row order and length)."""
    import pandas as pd

    path = Path(data_folder) / f"enhanced_frs_2024_25_year_{year}.h5"
    households = pd.read_hdf(path, "household")
    return households["electricity_consumption"].to_numpy()
