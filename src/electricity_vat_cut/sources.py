"""Single registry of every non-PolicyEngine number used in the analysis.

Policy: modelled quantities come from the PolicyEngine UK simulation at run
time and are never written here. Everything else — the reform definition,
empirical assumptions and external estimates used as anchors or context —
lives in this module with a value, a description, and a source URL, and is
emitted verbatim into the results JSON so the dashboard renders no
hardcoded numbers.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Source:
    value: Any
    description: str
    url: str


# ── Reform definition ────────────────────────────────────────────────────────
# Announced by PM Andy Burnham on 21 July 2026: VAT on domestic electricity
# cut from the 5% reduced rate to 0% for six months.

GOV_ANNOUNCEMENT_URL = (
    "https://www.gov.uk/government/news/"
    "new-pm-cuts-tax-on-household-electricity-bills-to-give-breathing-space-on-cost-of-living"
)

OLD_VAT_RATE = Source(
    value=0.05,
    description="Current VAT reduced rate on domestic fuel and power, in force since 1997.",
    url="https://www.gov.uk/tax-on-shopping/energy-products",
)
NEW_VAT_RATE = Source(
    value=0.0,
    description="Announced VAT rate on domestic electricity during the relief window.",
    url=GOV_ANNOUNCEMENT_URL,
)
REFORM_START = Source(
    value="2026-10-01",
    description="Start of the temporary zero rate on domestic electricity.",
    url=GOV_ANNOUNCEMENT_URL,
)
REFORM_END = Source(
    value="2027-03-31",
    description="End of the temporary zero rate on domestic electricity (six months).",
    url=GOV_ANNOUNCEMENT_URL,
)
WINDOW_YEARS = 0.5  # six months of a full year

# ── Government claims (validation anchors for the modelled figures) ──────────

GOVERNMENT_COST_CLAIM = Source(
    value=850,
    description=(
        "Government's claimed Exchequer cost of the six-month electricity VAT "
        "cut in 2026-27, £m. Covers households plus non-VAT-registered small "
        "businesses on domestic relief, charities and care homes (this model "
        "covers households only), and is not OBR-certified — the OBR forecast "
        "comes at the Budget."
    ),
    url=GOV_ANNOUNCEMENT_URL,
)
GOVERNMENT_PRICE_CAP_CLAIM = Source(
    value=45,
    description=(
        "Government's claimed reduction in the annual price cap for a typical "
        "household, £/year. Annualised: the realised gain over the six-month "
        "window is roughly half (~£22-23)."
    ),
    url=GOV_ANNOUNCEMENT_URL,
)
GOVERNMENT_INFLATION_CLAIM = Source(
    value={"cpi_pp": -0.10, "rpi_pp": -0.14},
    description="Government's claimed impact on CPI and RPI inflation, percentage points.",
    url=GOV_ANNOUNCEMENT_URL,
)

# ── Empirical assumptions (CLI defaults) ─────────────────────────────────────

WINTER_SHARE = Source(
    value=0.575,
    description=(
        "Share of annual household electricity spending falling in "
        "October-March, used for the winter-weighted six-month sensitivity. "
        "Domestic electricity demand is seasonal but far less so than gas; "
        "BEIS/NEED and Elexon load profiles put the winter-half share of "
        "domestic electricity consumption at roughly 55-60%. The uniform "
        "variant uses 0.5."
    ),
    url="https://www.gov.uk/government/collections/national-energy-efficiency-data-need-framework",
)

PASS_THROUGH_SCENARIOS = [
    Source(
        value=1.0,
        description=(
            "Central case: full pass-through of the VAT cut to household "
            "bills. Domestic energy VAT is charged on the retail bill and "
            "most tariffs sit at the Ofgem price cap, which is set net of "
            "VAT, so the statutory incidence passes through mechanically."
        ),
        url="https://www.ofgem.gov.uk/energy-price-cap",
    ),
    Source(
        value=0.75,
        description=(
            "Sensitivity: partial pass-through, if suppliers or the price-cap "
            "mechanics absorb a quarter of the cut (e.g. through tariff "
            "resets timed against the window)."
        ),
        url="https://uk.finance.yahoo.com/news/energy-vat-cut-does-not-075635288.html",
    ),
    Source(
        value=0.50,
        description=(
            "Sensitivity: half pass-through, a lower bound in the "
            "consumption-tax incidence literature for temporary cuts."
        ),
        url="https://uk.finance.yahoo.com/news/energy-vat-cut-does-not-075635288.html",
    ),
]

# ── External estimates and official statistics ───────────────────────────────
# Comparison anchors for the baseline tab. Units vary — each entry flags
# electricity-only vs gas+electricity and full-year vs six-month explicitly.
# More sources will be added as institutions publish formal costings.

EXTERNAL_ESTIMATES = {
    "government_cost_2026_27": Source(
        value=850,
        description=(
            "Government claim: Exchequer cost of the six-month electricity "
            "VAT cut in 2026-27, £m (electricity only, 6-month window; "
            "includes some non-household domestic-relief users; not "
            "OBR-certified)."
        ),
        url=GOV_ANNOUNCEMENT_URL,
    ),
    "government_price_cap_saving": Source(
        value=45,
        description=(
            "Government claim: reduction in the annual price cap for a "
            "typical household, £/year (annualised; realised over the "
            "6-month window ~£22-23). Confirmed informally by the IFS "
            "(Ben Zaranko) and by Cornwall Insight."
        ),
        url=GOV_ANNOUNCEMENT_URL,
    ),
    "ofgem_price_cap_jul_sep_2026": Source(
        value=1862,
        description=(
            "Ofgem price cap, July-September 2026: £1,862/year for a typical "
            "dual-fuel household (old typical-consumption basis; £1,654 on "
            "the new basis). Gas + electricity combined."
        ),
        url="https://www.ofgem.gov.uk/energy-price-cap",
    ),
    "cornwall_insight_oct_2026": Source(
        value=1849,
        description=(
            "Cornwall Insight forecast of the October 2026 price cap, "
            "£1,849/year (old basis), confirming ~£45 off the typical "
            "electricity bill from the VAT cut. Gas + electricity combined."
        ),
        url=(
            "https://www.cornwall-insight.com/press-and-media/press-release/"
            "bills-remain-stable-but-new-forecast-signals-increases-in-april/"
        ),
    ),
    "mse_cap_rise": Source(
        value=0.031,
        description=(
            "MoneySavingExpert: the October 2026 cap was predicted to rise "
            "~3.1%, largely absorbing the six-month gain in cash terms."
        ),
        url="https://uk.finance.yahoo.com/news/energy-vat-cut-does-not-075635288.html",
    ),
    "hmrc_2022_full_removal": Source(
        value=1700,
        description=(
            "HMRC (via 2022 Commons debates): ~£1.7bn/year to remove the 5% "
            "VAT on domestic fuel. NOT directly comparable: gas + electricity "
            "combined, full year, 2022 prices."
        ),
        url="https://commonslibrary.parliament.uk/research-briefings/cdp-2022-0005/",
    ),
    "hmrc_reduced_rate_relief_2024_25": Source(
        value=6500,
        description=(
            "HMRC tax relief statistics (January 2026): £6.5bn cost in "
            "2024-25 of charging domestic fuel at 5% rather than the 20% "
            "standard rate. NOT directly comparable: the 15pp relief, gas + "
            "electricity combined, full year."
        ),
        url="https://www.gov.uk/government/statistics/tax-reliefs/tax-relief-statistics-january-2026",
    ),
    "reform_uk_pledge": Source(
        value=2500,
        description=(
            "Reform UK pledge (March 2026), costed by Pantheon "
            "Macroeconomics: ~£2.5bn/year to scrap VAT AND green levies on "
            "energy bills. NOT directly comparable: gas + electricity, VAT "
            "plus levies, full year."
        ),
        url=(
            "https://www.vatupdate.com/2026/03/17/"
            "reform-uk-pledges-to-scrap-vat-and-green-levies-on-energy-bills-to-cut-costs/"
        ),
    ),
}

OFFICIAL_STATS = {
    "total_household_electricity_spend": {
        "value_bn": 30.8,
        "period_label": "2023",
        "description": (
            "Total UK household expenditure on electricity, £bn (Statista/ONS, "
            "2023). The 5% VAT component of £30.8bn is ~£1.5bn full-year, "
            "~£750m over six months — consistent with the £850m government "
            "claim at 2026 prices."
        ),
        "source": "https://www.statista.com/statistics/496756/household-expenditure-on-electricity-uk/",
    },
    "ons_family_spending_electricity": {
        "value": 816.40,
        "period_label": "FYE 2023",
        "description": (
            "ONS Family Spending: annualised electricity spending per "
            "household, £816.40 in FYE 2023 — compare the model's "
            "LCFS-imputed, NEED-calibrated mean for 2026."
        ),
        "source": "https://www.ons.gov.uk/aboutus/transparencyandgovernance/averagedualfuelhouseholdcosts",
    },
    "ons_households": {
        "value": 28_400_000,
        "description": (
            "Common ONS estimate of UK household numbers (~28.4m). The "
            "Enhanced FRS calibrated household count is higher (~31.3m), "
            "reflecting the policyengine-uk-data calibration targets."
        ),
        "source": "https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/families/bulletins/familiesandhouseholds/latest",
    },
    "commentary": {
        "description": (
            "Sector responses: the End Fuel Poverty Coalition called the cut "
            "'a positive statement of intent' that 'does not address the "
            "scale' of fuel poverty; National Energy Action called it 'the "
            "start we wanted to see'. Commentary cuts both ways: regressive "
            "in cash terms is disputed (the cut is flat in £ but progressive "
            "as a share of income), while excluding gas is criticised even "
            "as electricity-only relief improves heat-pump and EV running "
            "economics."
        ),
        "source": GOV_ANNOUNCEMENT_URL,
    },
}


def as_json() -> dict:
    """Everything above, serialised for the results JSON."""
    return {
        "reform_definition": {
            "old_vat_rate": asdict(OLD_VAT_RATE),
            "new_vat_rate": asdict(NEW_VAT_RATE),
            "start": asdict(REFORM_START),
            "end": asdict(REFORM_END),
            "window_years": WINDOW_YEARS,
            "announcement_url": GOV_ANNOUNCEMENT_URL,
        },
        "government_claims": {
            "cost_2026_27_m": asdict(GOVERNMENT_COST_CLAIM),
            "price_cap_saving_annual": asdict(GOVERNMENT_PRICE_CAP_CLAIM),
            "inflation": asdict(GOVERNMENT_INFLATION_CLAIM),
        },
        "assumptions": {
            "winter_share": asdict(WINTER_SHARE),
            "pass_through_scenarios": [asdict(s) for s in PASS_THROUGH_SCENARIOS],
        },
        "external_estimates": {k: asdict(v) for k, v in EXTERNAL_ESTIMATES.items()},
        "official_stats": OFFICIAL_STATS,
    }
