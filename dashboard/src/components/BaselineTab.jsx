"use client";

import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { colors } from "../lib/colors";
import { formatCount, formatCurrency, formatGroup, formatMn } from "../lib/formatters";
import { getBaseline, getExternalEstimates } from "../lib/dataHelpers";
import ChartLogo from "./ChartLogo";
import SectionHeading from "./SectionHeading";

const AXIS_STYLE = { fontSize: 12, fill: colors.gray[500] };

const SPEND_DIMENSIONS = [
  { id: "by_quintile", label: "Income quintile" },
  { id: "by_quartile", label: "Income quartile" },
  { id: "by_tenure", label: "Household type" },
  { id: "by_country", label: "Country" },
];

function SourceLink({ href, children }) {
  return (
    <a href={href} target="_blank" rel="noreferrer" className="underline">
      {children}
    </a>
  );
}

export default function BaselineTab({ data }) {
  const baseline = getBaseline(data);
  const external = getExternalEstimates(data);
  const stats = data.official_stats;
  const totalSpendBn = baseline.total_electricity_spend_bn;
  const [spendDim, setSpendDim] = useState("by_quintile");
  const spendDims = SPEND_DIMENSIONS.filter((d) => baseline.spend_by[d.id]);
  const rawSpendRows = baseline.spend_by[spendDim];
  const spendRows =
    typeof rawSpendRows[0]?.group === "string"
      ? [...rawSpendRows]
          .sort((a, b) => b.mean_spend - a.mean_spend)
          .map((r) => ({ ...r, group: formatGroup(r.group) }))
      : rawSpendRows;

  // Comparison rows: modelled figure vs the nearest external number, with
  // the unit mismatches (electricity-only vs gas+electricity, full-year vs
  // 6-month, annualised vs realised) called out row by row.
  const comparisonRows = [
    {
      quantity: "Six-month Exchequer cost",
      model: formatMn(data.reform.cost.six_month_uniform_m),
      external: (
        <>
          <SourceLink href={external.government_cost_2026_27.url}>
            {formatMn(external.government_cost_2026_27.value)}
          </SourceLink>{" "}
          (government, 2026-27)
        </>
      ),
      notes: external.government_cost_2026_27.description,
    },
    {
      quantity: "Annualised gain per typical household",
      model: formatCurrency(data.reform.mean_gain.full_year),
      external: (
        <>
          <SourceLink href={external.government_price_cap_saving.url}>
            {formatCurrency(external.government_price_cap_saving.value)}/yr
          </SourceLink>{" "}
          (government price-cap figure)
        </>
      ),
      notes: external.government_price_cap_saving.description,
    },
    {
      quantity: "Full-year cost of removing the 5% rate entirely",
      model: `£${(totalSpendBn * 5 / 105).toFixed(2)}bn (electricity only, 2026)`,
      external: (
        <>
          <SourceLink href={external.hmrc_2022_full_removal.url}>
            £{(external.hmrc_2022_full_removal.value / 1000).toFixed(1)}bn
          </SourceLink>{" "}
          (HMRC via Commons, 2022)
        </>
      ),
      notes: external.hmrc_2022_full_removal.description,
    },
  ];

  return (
    <div className="space-y-6">
      <div className="pt-2">
        <SectionHeading
          size="lg"
          title="The electricity spending base"
          description="What households spend on electricity in the model, and how that base reconciles with official statistics. The whole reform costing rests on this one input: the VAT cut is worth exactly 5/105 of each household's observed VAT-inclusive spending."
        />
      </div>

      <section className="section-card">
        <SectionHeading
          title="Household electricity spending in the model (2026)"
          description={
            <>
              electricity_consumption in the Enhanced FRS 2024-25 dataset:
              annual household electricity spending imputed from the Living
              Costs and Food Survey and calibrated to the National Energy
              Efficiency Data framework (NEED), uprated to 2026 by
              policyengine-uk-data. Cross-checks:{" "}
              <SourceLink href={stats.total_household_electricity_spend.source}>
                Statista/ONS
              </SourceLink>{" "}
              put total UK household electricity spending at £
              {stats.total_household_electricity_spend.value_bn}bn in{" "}
              {stats.total_household_electricity_spend.period_label};{" "}
              <SourceLink href={stats.ons_family_spending_electricity.source}>
                ONS Family Spending
              </SourceLink>{" "}
              recorded{" "}
              {formatCurrency(stats.ons_family_spending_electricity.value)}{" "}
              annualised per household in{" "}
              {stats.ons_family_spending_electricity.period_label} against the
              model&apos;s {formatCurrency(baseline.mean_electricity_spend)} for
              2026. The calibrated household count (
              {formatCount(baseline.n_households)}) sits above the{" "}
              <SourceLink href={stats.ons_households.source}>
                common ONS estimate
              </SourceLink>{" "}
              of {formatCount(stats.ons_households.value)}, reflecting the
              policyengine-uk-data calibration targets.
            </>
          }
        />
        <table className="data-table">
          <tbody>
            <tr>
              <td>Households (calibrated weights)</td>
              <td>{formatCount(baseline.n_households)}</td>
            </tr>
            <tr>
              <td>Mean annual electricity spend (all households)</td>
              <td>{formatCurrency(baseline.mean_electricity_spend)}</td>
            </tr>
            <tr>
              <td>Total annual household electricity spend</td>
              <td>£{totalSpendBn.toFixed(1)}bn</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section className="section-card">
        <SectionHeading
          title="Electricity spending by group (2026)"
          description="Mean annual spending by group. Spending is fairly flat in £ across income groups, which is what makes the VAT cut progressive as a share of income."
        />
        <div className="mb-4">
          <label className="flex items-center gap-2 text-sm text-slate-700">
            Group by
            <select
              className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm"
              value={spendDim}
              onChange={(e) => setSpendDim(e.target.value)}
            >
              {spendDims.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.label}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="h-[340px] w-full">
          <ResponsiveContainer>
            <BarChart
              data={spendRows}
              margin={{ top: 10, right: 20, bottom: 5, left: 10 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke={colors.border.light} />
              <XAxis
                dataKey="group"
                tick={AXIS_STYLE}
                interval={0}
                angle={spendRows.length > 6 ? -30 : 0}
                textAnchor={spendRows.length > 6 ? "end" : "middle"}
                height={spendRows.length > 6 ? 70 : 30}
              />
              <YAxis
                tick={AXIS_STYLE}
                tickFormatter={(v) => `£${Math.round(v)}`}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip formatter={(v) => `£${Math.round(v)}`} />
              <Bar
                dataKey="mean_spend"
                name="Mean annual electricity spend"
                fill={colors.primary[600]}
                radius={[6, 6, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <ChartLogo />
      </section>

      <div className="pt-2">
        <SectionHeading
          size="lg"
          title="Comparison with external estimates"
          description="Each row pairs a model quantity with the nearest published figure. Units differ across rows — electricity-only vs gas+electricity, full-year vs six-month, annualised vs realised — and the notes flag each mismatch."
        />
      </div>

      <section className="section-card">
        <SectionHeading title="Model versus external figures (2026-27)" />
        <table className="data-table">
          <thead>
            <tr>
              <th>Quantity</th>
              <th>This model</th>
              <th>External figure</th>
              <th>Notes</th>
            </tr>
          </thead>
          <tbody>
            {comparisonRows.map((row) => (
              <tr key={row.quantity}>
                <td>{row.quantity}</td>
                <td>{row.model}</td>
                <td>{row.external}</td>
                <td className="text-xs leading-5 text-slate-500">{row.notes}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
