// Pre-computed dashboard data exported from Postgres by database/export_static.py.
// The deployed dashboard reads these files instead of querying a database.
import industryMetrics from '@/data/industry_metrics.json';
import stateMetrics from '@/data/state_metrics.json';
import employerMetrics from '@/data/employer_metrics.json';
import covidTrends from '@/data/covid_trends.json';
import exposureScores from '@/data/exposure_scores.json';
import type { IndustryMetric, StateMetric, EmployerMetric } from '@/lib/types';

// Several NAICS codes share one industry name (e.g. 5415, 54151 and 541512 are all
// "Computer Systems Design Services": the same industry recorded at different levels of
// detail or under different NAICS editions). Merge them so each industry appears once.
// The merged row keeps the code of its largest component.

type Row = Record<string, unknown>;
const num = (v: unknown) => Number(v ?? 0);

function groupBy<T>(rows: T[], key: (r: T) => string) {
  const groups = new Map<string, T[]>();
  for (const r of rows) {
    const k = key(r);
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k)!.push(r);
  }
  return groups;
}

function mergeIndustryMetrics(rows: IndustryMetric[]): IndustryMetric[] {
  const groups = groupBy(rows, (r) => `${r.fiscal_year}|${r.industry_name ?? r.industry}`);
  return Array.from(groups.values()).map((g) => {
    if (g.length === 1) return g[0];
    const largest = g.reduce((a, b) => (b.total_applications > a.total_applications ? b : a));
    const apps = g.reduce((s, r) => s + r.total_applications, 0);
    const wages = g.reduce((s, r) => s + num(r.total_annual_wages), 0);
    // Wage-weighted average is exact; a merged median can't be computed from summaries,
    // so use an application-weighted average of the component medians.
    const median = g.reduce((s, r) => s + num(r.median_annual_wage) * r.total_applications, 0) / apps;
    return {
      ...largest,
      total_applications: apps,
      unique_employers: g.reduce((s, r) => s + r.unique_employers, 0),
      total_annual_wages: wages,
      avg_annual_wage: wages / apps,
      median_annual_wage: Math.round(median),
    };
  });
}

function mergeExposureIndustries(rows: Row[]): Row[] {
  const groups = groupBy(rows, (r) => String(r.industry_name ?? r.industry));
  return Array.from(groups.values())
    .map((g) => {
      if (g.length === 1) return g[0];
      const largest = g.reduce((a, b) => (num(b.total_applications) > num(a.total_applications) ? b : a));
      const apps = g.reduce((s, r) => s + num(r.total_applications), 0);
      // HHI of the combined industry, assuming each employer files under one code:
      // sum over codes of (code's share of the combined industry)^2 x code's HHI.
      const hhi = g.reduce((s, r) => s + (num(r.total_applications) / apps) ** 2 * num(r.hhi_concentration), 0);
      const volume = g.reduce((s, r) => s + num(r.volume_share_pct), 0);
      const wage = g.reduce((s, r) => s + num(r.wage_mass_share_pct), 0);
      const hhiScore = Math.min(hhi, 0.25) * 100;
      const round2 = (x: number) => Math.round(x * 100) / 100;
      return {
        ...largest,
        total_applications: apps,
        total_wage_mass: g.reduce((s, r) => s + num(r.total_wage_mass), 0),
        employer_count: g.reduce((s, r) => s + num(r.employer_count), 0),
        hhi_concentration: round2(hhi),
        volume_share_pct: round2(volume),
        wage_mass_share_pct: round2(wage),
        hhi_score: round2(hhiScore),
        exposure_score: round2(0.5 * volume + 0.4 * wage + 0.1 * hhiScore),
        estimated_fee_shock_millions: round2((apps * 100000) / 1e6),
      };
    })
    .sort((a, b) => num(b.exposure_score) - num(a.exposure_score));
}

export const industryData = mergeIndustryMetrics(industryMetrics as IndustryMetric[]);
export const stateData = stateMetrics as StateMetric[];
export const employerData = employerMetrics as EmployerMetric[];
export const covidData = covidTrends as Row[];
export const exposureData = {
  industries: mergeExposureIndustries((exposureScores as { industries: Row[] }).industries),
  states: (exposureScores as { states: Row[] }).states,
};

// The industry dropdown sends the industry *name*; older links may send the NAICS code.
export const matchesIndustry = (
  row: { industry: string | null; industry_name?: string | null },
  industry: string
) => row.industry === industry || row.industry_name === industry;

export const byApplicationsDesc = (a: { total_applications: number }, b: { total_applications: number }) =>
  b.total_applications - a.total_applications;
