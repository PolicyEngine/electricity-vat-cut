/**
 * Accessors for the electricity_vat_cut_results.json payload.
 *
 * Deliberately no fallbacks: if a field is missing the consumer throws
 * visibly rather than rendering placeholders.
 */

function required(value, name) {
  if (value == null) {
    throw new Error(`results JSON is missing ${name}; re-run the pipeline`);
  }
  return value;
}

export function getReform(data) {
  return required(data.reform, "reform");
}

export function getCost(data) {
  return required(data.reform?.cost, "reform.cost");
}

export function getMeanGain(data) {
  return required(data.reform?.mean_gain, "reform.mean_gain");
}

export function getBaseline(data) {
  return required(data.baseline, "baseline");
}

export function getGovernmentClaims(data) {
  return required(data.government_claims, "government_claims");
}

export function getExternalEstimates(data) {
  return required(data.external_estimates, "external_estimates");
}

export function getAssumptions(data) {
  return required(data.assumptions, "assumptions");
}

export function getPoverty(data) {
  return required(data.poverty, "poverty");
}

export function getMethods(data) {
  return required(data.methods, "methods");
}
