// Pre-computed dashboard data exported from Postgres by database/export_static.py.
// The deployed dashboard reads these files instead of querying a database.
import industryMetrics from '@/data/industry_metrics.json';
import stateMetrics from '@/data/state_metrics.json';
import employerMetrics from '@/data/employer_metrics.json';
import covidTrends from '@/data/covid_trends.json';
import exposureScores from '@/data/exposure_scores.json';
import type { IndustryMetric, StateMetric, EmployerMetric } from '@/lib/types';

export const industryData = industryMetrics as IndustryMetric[];
export const stateData = stateMetrics as StateMetric[];
export const employerData = employerMetrics as EmployerMetric[];
export const covidData = covidTrends as Record<string, unknown>[];
export const exposureData = exposureScores as {
  industries: Record<string, unknown>[];
  states: Record<string, unknown>[];
};

// The industry dropdown sends the industry *name*; older links may send the NAICS code.
export const matchesIndustry = (
  row: { industry: string | null; industry_name?: string | null },
  industry: string
) => row.industry === industry || row.industry_name === industry;

export const byApplicationsDesc = (a: { total_applications: number }, b: { total_applications: number }) =>
  b.total_applications - a.total_applications;
