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
import { formatBn, formatCurrency, formatGroup, formatMn, formatPct } from "../lib/formatters";
import { getCost, getGovernmentClaims, getMeanGain, getReform } from "../lib/dataHelpers";
import ChartLogo from "./ChartLogo";
import SectionHeading from "./SectionHeading";

const AXIS_STYLE = { fontSize: 12, fill: colors.gray[500] };

const RANKINGS = [
  { id: "by_quintile", label: "Income quintile" },
  { id: "by_quartile", label: "Income quartile" },
  { id: "by_tenure", label: "Household type" },
  { id: "by_country", label: "Country" },
];

const METRICS = [
  {
    id: "mean_gain",
    label: "Mean gain (£)",
    name: "Mean six-month gain per household",
    money: true,
    format: (v) => `£${Number(v).toFixed(0)}`,
  },
  {
    id: "pct_net_income",
    label: "% of net income",
    name: "Gain as a share of net income",
    money: false,
    format: (v) => `${Number(v).toFixed(2)}%`,
  },
  {
    id: "total_m",
    label: "Total (£m)",
    name: "Total six-month gain",
    money: true,
    format: (v) => `£${Number(v).toFixed(0)}m`,
  },
];

function MetricCard({ label, value, note }) {
  return (
    <div className="metric-card">
      <p className="text-sm font-semibold leading-snug text-slate-700">
        {label}
      </p>
      <p className="mt-1 text-3xl font-bold">{value}</p>
      {note && (
        <p className="mt-2 border-t border-slate-100 pt-2 text-xs leading-5 text-slate-500">
          {note}
        </p>
      )}
    </div>
  );
}

function SourceLink({ href, children }) {
  return (
    <a href={href} target="_blank" rel="noreferrer" className="underline">
      {children}
    </a>
  );
}

function DecileChart({ rows, dataKey, name, money, formatValue }) {
  return (
    <>
      <div className="h-[340px] w-full">
        <ResponsiveContainer>
          <BarChart data={rows} margin={{ top: 10, right: 20, bottom: 5, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={colors.border.light} />
            <XAxis
              dataKey="group"
              tick={AXIS_STYLE}
              interval={0}
              angle={rows.length > 6 && typeof rows[0]?.group === "string" ? -30 : 0}
              textAnchor={rows.length > 6 && typeof rows[0]?.group === "string" ? "end" : "middle"}
              height={rows.length > 6 && typeof rows[0]?.group === "string" ? 70 : 30}
            />
            <YAxis
              tick={AXIS_STYLE}
              tickFormatter={formatValue}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip formatter={(v) => formatValue(v)} />
            <Bar
              dataKey={dataKey}
              name={name}
              fill={money ? colors.primary[600] : colors.primary[400]}
              radius={[6, 6, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <ChartLogo />
    </>
  );
}

export default function ReformTab({ data }) {
  const reform = getReform(data);
  const cost = getCost(data);
  const meanGain = getMeanGain(data);
  const claims = getGovernmentClaims(data);
  const [ranking, setRanking] = useState("by_quintile");
  const [metricId, setMetricId] = useState("mean_gain");
  const rankings = RANKINGS.filter((r) => reform[r.id]);
  const metric = METRICS.find((m) => m.id === metricId);
  const rawRows = reform[ranking];
  // Categorical groups (household type, region, country) have no natural
  // order — sort bars by the displayed metric, largest first.
  const rows =
    typeof rawRows[0]?.group === "string"
      ? [...rawRows]
          .sort((a, b) => (b[metricId] ?? 0) - (a[metricId] ?? 0))
          .map((r) => ({ ...r, group: formatGroup(r.group) }))
      : rawRows;
  const winterShare = data.assumptions.winter_share;
  const quintiles = reform.by_quintile;
  const bottomPct = quintiles[0].pct_net_income;
  const topPct = quintiles[quintiles.length - 1].pct_net_income;
  const progressivityRatio = bottomPct / topPct;

  return (
    <div className="space-y-6">
      <div className="pt-2">
        <SectionHeading
          size="lg"
          title="The reform"
          description={`VAT on domestic electricity falls from the ${formatPct(
            data.reform_definition.old_vat_rate.value * 100,
            0,
          )} reduced rate to ${formatPct(
            data.reform_definition.new_vat_rate.value * 100,
            0,
          )} between ${data.reform_definition.start.value} and ${
            data.reform_definition.end.value
          }. Each household's gain is the VAT component of its observed electricity spending (spending × 5/105), realised over the six-month window and assumed fully passed through to bills in the central case. Gas is unchanged.`}
        />
      </div>


      <section className="section-card">
        <SectionHeading
          title="Headline results (2026-27)"
          description="Each card notes the nearest government claim; the modelled household cost should sit below the £850m claim, which also covers non-household users on domestic relief."
        />
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            label="Six-month Exchequer cost (uniform window)"
            value={formatMn(cost.six_month_uniform_m)}
            note={
              <>
                Winter-weighted: {formatMn(cost.six_month_winter_m)}. Compare
                the{" "}
                <SourceLink href={claims.cost_2026_27_m.url}>
                  government claim
                </SourceLink>{" "}
                of {formatMn(claims.cost_2026_27_m.value)} (includes small
                businesses, charities and care homes; not OBR-certified).
              </>
            }
          />
          <MetricCard
            label="Mean full-year-equivalent gain per household"
            value={formatCurrency(meanGain.full_year)}
            note={
              <>
                Realised over six months: {formatCurrency(meanGain.six_month_uniform)}{" "}
                (uniform). Compare the{" "}
                <SourceLink href={claims.price_cap_saving_annual.url}>
                  government price-cap figure
                </SourceLink>{" "}
                of {formatCurrency(claims.price_cap_saving_annual.value)}/year
                for a typical household.
              </>
            }
          />
          <MetricCard
            label="Relative gain, lowest vs highest income fifth"
            value={`${progressivityRatio.toFixed(1)}×`}
            note={`The bottom income quintile gains ${bottomPct.toFixed(
              2,
            )}% of net income over the window against ${topPct.toFixed(
              2,
            )}% for the top quintile — flat in cash, progressive in proportion.`}
          />
          <MetricCard
            label="Cost if made permanent"
            value={formatBn(cost.full_year_bn)}
            note="Full-year equivalent at 2026 spending levels. Extending the cut past March 2027 — a live question for the autumn Budget — would cost roughly this every year, before any induced electricity demand."
          />
        </div>
      </section>

      <details className="section-card group">
        <summary className="cursor-pointer text-base font-semibold text-slate-900">
          What exactly changes, for whom, and when
          <span className="ml-2 text-sm font-normal text-slate-500 group-open:hidden">
            (expand)
          </span>
        </summary>
        <table className="data-table mt-4">
          <tbody>
            <tr>
              <td className="font-medium">What changes</td>
              <td>
                The VAT rate charged on domestic electricity bills falls from
                the {formatPct(data.reform_definition.old_vat_rate.value * 100, 0)}{" "}
                reduced rate to{" "}
                {formatPct(data.reform_definition.new_vat_rate.value * 100, 0)}.
                Gas, green levies and standing-charge policy are unchanged.
              </td>
            </tr>
            <tr>
              <td className="font-medium">Who is affected</td>
              <td>
                All households paying electricity bills (directly or via a
                capped tariff). The government says the relief also extends to
                non-VAT-registered small businesses, charities and care homes
                on domestic-rate supply; this dashboard models households only.
              </td>
            </tr>
            <tr>
              <td className="font-medium">From when to when</td>
              <td>
                {data.reform_definition.start.value} to{" "}
                {data.reform_definition.end.value} — six months, covering the
                October price-cap period and the winter.
              </td>
            </tr>
          </tbody>
        </table>
      </details>

      <section className="section-card">
        <SectionHeading
          title="Gain by income group (2026-27)"
          description="Flat in cash terms — every income group gains roughly the same £ amount — and progressive as a share of net income, since electricity is a larger budget share for lower-income households. Six-month window, uniform halving, 100% pass-through."
        />
        <div className="mb-4 flex flex-wrap gap-4">
          <label className="flex items-center gap-2 text-sm text-slate-700">
            Group by
            <select
              className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm"
              value={ranking}
              onChange={(e) => setRanking(e.target.value)}
            >
              {rankings.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.label}
                </option>
              ))}
            </select>
          </label>
          <label className="flex items-center gap-2 text-sm text-slate-700">
            Metric
            <select
              className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm"
              value={metricId}
              onChange={(e) => setMetricId(e.target.value)}
            >
              {METRICS.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.label}
                </option>
              ))}
            </select>
          </label>
        </div>
        <h3 className="mb-2 text-sm font-semibold text-slate-800">
          {metric.name}
        </h3>
        <DecileChart
          rows={rows}
          dataKey={metric.id}
          name={metric.name}
          money={metric.money}
          formatValue={metric.format}
        />
      </section>

      <section className="section-card">
        <SectionHeading
          title="Pass-through scenarios (2026-27)"
          description="The central case passes 100% of the VAT cut through to bills (the Ofgem price cap is set net of VAT). Lower pass-through scales every household's gain proportionally."
        />
        <table className="data-table">
          <thead>
            <tr>
              <th>Pass-through</th>
              <th>Six-month cost to households (uniform)</th>
              <th>Six-month cost (winter-weighted)</th>
              <th>Mean six-month gain</th>
            </tr>
          </thead>
          <tbody>
            {reform.pass_through.map((row) => (
              <tr key={row.rate} className={row.rate === 1 ? "font-semibold" : ""}>
                <td>
                  {formatPct(row.rate * 100, 0)}
                  {row.rate === 1 ? " (central)" : ""}
                  {row.url ? (
                    <>
                      {" "}
                      <SourceLink href={row.url}>source</SourceLink>
                    </>
                  ) : null}
                </td>
                <td>{formatMn(row.cost_6m_m)}</td>
                <td>{formatMn(row.cost_6m_winter_m)}</td>
                <td>{formatCurrency(row.mean_gain_6m)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="section-card">
        <SectionHeading
          title="Winter weighting sensitivity (2026-27)"
          description={
            <>
              The relief window is October-March, when electricity use is
              higher than the annual average. The headline halves annual
              spending uniformly; the sensitivity applies the{" "}
              <a href="?tab=methodology#assumptions" className="underline">
                winter-share assumption
              </a>{" "}
              of {formatPct(winterShare.value * 100, 1)} of annual spending in
              the window.
            </>
          }
        />
        <table className="data-table">
          <thead>
            <tr>
              <th>Variant</th>
              <th>Window share of annual spend</th>
              <th>Six-month cost</th>
              <th>Mean gain per household</th>
            </tr>
          </thead>
          <tbody>
            <tr className="font-semibold">
              <td>Uniform (headline)</td>
              <td>{formatPct(50, 0)}</td>
              <td>{formatMn(cost.six_month_uniform_m)}</td>
              <td>{formatCurrency(meanGain.six_month_uniform)}</td>
            </tr>
            <tr>
              <td>Winter-weighted</td>
              <td>{formatPct(winterShare.value * 100, 1)}</td>
              <td>{formatMn(cost.six_month_winter_m)}</td>
              <td>{formatCurrency(meanGain.six_month_winter)}</td>
            </tr>
            <tr>
              <td>Full-year equivalent (context)</td>
              <td>{formatPct(100, 0)}</td>
              <td>{formatBn(cost.full_year_bn)}</td>
              <td>{formatCurrency(meanGain.full_year)}</td>
            </tr>
          </tbody>
        </table>
      </section>

    </div>
  );
}
