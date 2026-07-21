"""Schema checks on the generated results JSON (skipped when absent)."""

import json
from pathlib import Path

import pytest

RESULTS_PATH = Path(__file__).parent.parent / "data" / "electricity_vat_cut_results.json"

pytestmark = pytest.mark.skipif(
    not RESULTS_PATH.exists(), reason="results JSON not built; run the pipeline first"
)


@pytest.fixture(scope="module")
def data():
    return json.loads(RESULTS_PATH.read_text())


def test_top_level_sections(data):
    for key in (
        "metadata",
        "reform_definition",
        "government_claims",
        "assumptions",
        "external_estimates",
        "official_stats",
        "methods",
        "baseline",
        "reform",
        "poverty",
        "inequality",
    ):
        assert key in data, f"missing top-level section {key!r}"


def test_metadata(data):
    meta = data["metadata"]
    assert meta["year"] >= 2026
    assert "enhanced_frs" in meta["dataset"]
    assert meta["policyengine_version"]


def test_costs_are_consistent(data):
    cost = data["reform"]["cost"]
    assert cost["six_month_uniform_m"] == pytest.approx(cost["full_year_bn"] * 1000 / 2, rel=1e-6)
    assert cost["six_month_winter_m"] > cost["six_month_uniform_m"]


def test_decile_breakdowns(data):
    for key in ("by_decile", "by_equiv_decile"):
        rows = data["reform"][key]
        assert len(rows) == 10
        assert [r["group"] for r in rows] == list(range(1, 11))
    assert len(data["reform"]["by_quintile"]) == 5
    # The equivalised ranking covers every household, so its groups sum to
    # the headline cost exactly (household_income_decile excludes a small
    # unranked decile-"-1" group from the view).
    total = sum(r["total_m"] for r in data["reform"]["by_equiv_decile"])
    assert total == pytest.approx(data["reform"]["cost"]["six_month_uniform_m"], rel=1e-6)


def test_sources_carry_urls(data):
    for entry in data["external_estimates"].values():
        assert entry["url"].startswith("http")
        assert entry["description"]
    for scenario in data["assumptions"]["pass_through_scenarios"]:
        assert scenario["url"].startswith("http")


def test_poverty_and_winners(data):
    poverty = data["poverty"]["bhc_relative"]
    assert 0 < poverty["reformed_rate"] <= poverty["baseline_rate"] < 1
    assert poverty["people_out_of_poverty"] >= 0
    assert 0.5 < data["reform"]["winners_share"] < 1


def test_dashboard_copy_matches(data):
    dashboard_copy = (
        Path(__file__).parent.parent
        / "dashboard"
        / "public"
        / "data"
        / "electricity_vat_cut_results.json"
    )
    assert dashboard_copy.exists()
    assert json.loads(dashboard_copy.read_text()) == data
