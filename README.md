# Temporary VAT cut on domestic electricity (5% to 0%)

**Live dashboard: [electricity-vat-cut.vercel.app/uk/electricity-vat-cut](https://electricity-vat-cut.vercel.app/uk/electricity-vat-cut)**

Data pipeline and dashboard estimating the fiscal cost and distributional
impact of the temporary VAT cut on domestic electricity — from the 5%
reduced rate to 0% for six months, 1 October 2026 to 31 March 2027 —
announced by PM Andy Burnham on 21 July 2026. Built on the
[PolicyEngine UK](https://policyengine.org) microsimulation baseline and the
Enhanced FRS 2024-25 electricity spending imputation (LCFS-imputed,
NEED-calibrated).

## Headline results (2026, households only)

| Result | Value |
| --- | --- |
| Six-month cost (uniform) | ~£670m (government claim: £850m, incl. non-households) |
| Six-month cost (winter-weighted, 57.5% of annual spend) | ~£770m |
| Full-year-equivalent cost | ~£1.34bn |
| Mean full-year gain per household | ~£43 (government price-cap figure: £45/yr) |
| Households gaining | ~87% (the rest have no recorded electricity spend) |
| Gain by income group (6 months) | Flat in £ across quintiles (~£17-25); progressive as % of net income (0.08% bottom quintile → 0.02% top quintile, a 3.8× relative gain) |
| People out of relative BHC poverty (fixed line, 6 months) | ~14k |

The reform is not modelled by changing PolicyEngine's VAT parameters: the
native `vat` variable spreads a flat 2.5% reduced-rate share over total
consumption rather than electricity-specific spending. Each household's gain
is instead computed directly as electricity spending × 5/105 (the VAT
component of observed VAT-inclusive spending), halved for the six-month
window, with a winter-weighted sensitivity. 100% pass-through to bills is
the central case, with 75%/50% sensitivities.

Every number on the dashboard comes from the results JSON; every
non-PolicyEngine assumption and external estimate carries a value,
description and source URL in `src/electricity_vat_cut/sources.py`.

## Quick start

```bash
uv venv --python 3.13
source .venv/bin/activate
uv pip install -e ".[simulation,dev]"

# HUGGING_FACE_TOKEN required for the enhanced-FRS microdata
python -m electricity_vat_cut --year 2026

# options (defaults shown)
python -m electricity_vat_cut \
  --year 2026 \
  --data-folder data/policyengine_datasets \
  --winter-share 0.575 \
  --pass-through 1.0 0.75 0.5
```

Outputs `data/electricity_vat_cut_results.json` and a copy under
`dashboard/public/data/` for the dashboard.

## Dashboard

```bash
cd dashboard
bun install
bun run dev
```

Next.js (App Router) + Recharts + Tailwind, PolicyEngine design system
tokens. Three tabs: the reform results (costs vs the government claims,
gain by income quintile/quartile, household type and country, pass-through and winter sensitivities), a baseline tab
reconciling the model's electricity spending base with external estimates,
and a methodology page with the method notes the pipeline writes alongside
the results.

## Tests

```bash
pytest  # pure-Python VAT arithmetic + schema checks; no microdata needed
```

Linting and the dashboard build run in CI on every pull request.

## Key caveats

- Households only: the government's £850m costing also covers
  non-VAT-registered small businesses, charities and care homes on domestic
  relief, plus comparable funding for Northern Ireland — and is not
  OBR-certified.
- Electricity spending is imputed from the LCFS and calibrated to NEED;
  ~14% of households have no recorded spend and gain nothing in the model.
- 100% pass-through is assumed centrally; the October 2026 price-cap rise
  (~3.1% predicted) may absorb much of the gain in cash terms.
- No behavioural response (electricity demand is short-run price-inelastic)
  and no inflation channel (government claims ~−0.10pp CPI).
- The winter-weighted window share (57.5%) is an assumption from BEIS/NEED
  seasonality, not a statutory parameter.
