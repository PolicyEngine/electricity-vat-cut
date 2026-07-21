"use client";

import { useEffect } from "react";
import { formatPct } from "../lib/formatters";
import { getMethods } from "../lib/dataHelpers";
import SectionHeading from "./SectionHeading";

const METHOD_LABELS = {
  gain_computation: "How the gain is computed",
  electricity_data: "Electricity spending data",
  pass_through: "Pass-through assumption",
  temporary_measure: "The six-month window",
  no_behavioural_response: "No behavioural response",
  scope: "Scope of the costing",
};

export default function MethodologyTab({ data }) {
  // Analysis sections link here with /?tab=methodology#method-<key>; the tab
  // mounts after navigation, so the browser's native hash scroll has already
  // missed and we replay it.
  useEffect(() => {
    const hash = window.location.hash;
    if (hash) {
      document.getElementById(hash.slice(1))?.scrollIntoView();
    }
  }, []);

  const methods = getMethods(data);
  const winterShare = data.assumptions.winter_share;
  const passThrough = data.assumptions.pass_through_scenarios;
  const commentary = data.official_stats.commentary;

  return (
    <div className="space-y-6">
      <section className="section-card">
        <SectionHeading
          title="Computation methods"
          description="Static arithmetic on the PolicyEngine UK baseline: the reform is computed directly from each household's electricity spending, never by editing the VAT parameter tree. Each note below is written by the analysis pipeline alongside the result it describes."
        />
        <div className="grid gap-x-8 gap-y-5 md:grid-cols-2">
          {Object.entries(methods)
            .filter(([key]) => METHOD_LABELS[key])
            .map(([key, text]) => (
              <div key={key} id={`method-${key}`} className="scroll-mt-24">
                <h3 className="text-sm font-semibold text-slate-800">
                  {METHOD_LABELS[key]}
                </h3>
                <p className="mt-1 text-sm leading-6 text-slate-600">{text}</p>
              </div>
            ))}
        </div>
      </section>

      <section className="section-card scroll-mt-24" id="assumptions">
        <SectionHeading title="Key assumptions and their sources" />
        <p className="text-sm leading-6 text-slate-600">
          The winter-weighted sensitivity puts{" "}
          {formatPct(winterShare.value * 100, 1)} of annual electricity spending
          in the October-March window, from{" "}
          <a href={winterShare.url} target="_blank" rel="noreferrer" className="underline">
            BEIS/NEED seasonality
          </a>
          . Pass-through scenarios of{" "}
          {passThrough.map((s) => formatPct(s.value * 100, 0)).join(", ")} scale
          every household&apos;s gain proportionally;{" "}
          <a href={passThrough[0].url} target="_blank" rel="noreferrer" className="underline">
            the central 100% case
          </a>{" "}
          reflects that the Ofgem price cap is set net of VAT, so the statutory
          incidence passes through mechanically for capped tariffs.
        </p>
      </section>

      <section className="section-card">
        <SectionHeading
          title="Price cap context"
          description="The VAT cut lands on top of the Ofgem price cap cycle; the sector figures below frame what households will actually see on bills."
        />
        <ul className="list-disc space-y-1 pl-6 text-sm leading-6 text-slate-600">
          <li>
            <a
              href={data.external_estimates.ofgem_price_cap_jul_sep_2026.url}
              target="_blank"
              rel="noreferrer"
              className="underline"
            >
              Ofgem price cap
            </a>
            , July-September 2026: £
            {Math.round(data.external_estimates.ofgem_price_cap_jul_sep_2026.value)}
            /year for a typical dual-fuel household (old typical-consumption
            basis; £1,654 on the new basis). Gas + electricity combined.
          </li>
          <li>
            <a
              href={data.external_estimates.cornwall_insight_oct_2026.url}
              target="_blank"
              rel="noreferrer"
              className="underline"
            >
              Cornwall Insight
            </a>{" "}
            forecasts the October 2026 cap at £
            {Math.round(data.external_estimates.cornwall_insight_oct_2026.value)}
            /year (old basis) and confirms ~£45 off the typical electricity bill
            from the VAT cut.
          </li>
          <li>
            <a
              href={data.external_estimates.mse_cap_rise.url}
              target="_blank"
              rel="noreferrer"
              className="underline"
            >
              MoneySavingExpert
            </a>{" "}
            notes the October cap was predicted to rise ~
            {formatPct(data.external_estimates.mse_cap_rise.value * 100, 1)},
            largely absorbing the six-month gain in cash terms.
          </li>
        </ul>
      </section>

      <section className="section-card scroll-mt-24" id="model-omissions">
        <SectionHeading title="Model limitations" />
        <ul className="list-disc space-y-1 pl-6 text-sm leading-6 text-slate-600">
          <li>
            PolicyEngine&apos;s native <code>vat</code> variable applies a flat
            2.5% reduced-rate share to total consumption, not
            electricity-specific spending — the reason the gain is computed
            directly from the electricity input rather than by zeroing the
            reduced rate in the parameter tree.
          </li>
          <li>
            Electricity spending is LCFS-imputed and NEED-calibrated; ~14% of
            households have no recorded spend (e.g. bills in rent) and gain
            nothing in the model, so the winners share understates coverage of
            the actual population.
          </li>
          <li>
            Households only: the government&apos;s £850m claim also covers
            non-VAT-registered small businesses, charities and care homes on
            domestic relief, plus comparable funding for Northern Ireland — and
            is not OBR-certified.
          </li>
          <li>
            100% pass-through is assumed centrally; tariff resets timed against
            the window could absorb part of the cut (75%/50% sensitivities).
          </li>
          <li>
            No behavioural response: any induced electricity consumption would
            raise the cost slightly. Inflation effects (~−0.10pp CPI claimed)
            are outside the model.
          </li>
          <li>
            The six-month halving (and the {formatPct(winterShare.value * 100, 1)}{" "}
            winter share) approximates the window from annual spending; actual
            billing cycles and the October price-cap reset are not modelled.
          </li>
        </ul>
        <p className="mt-4 text-sm leading-6 text-slate-600">
          Sector context: {commentary.description}
        </p>
      </section>
    </div>
  );
}
