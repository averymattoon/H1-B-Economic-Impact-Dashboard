'use client';

import CovidChangeChart, { CovidRow } from './CovidChangeChart';

export default function CovidIndustryChart({ data }: { data: CovidRow[] }) {
  return (
    <CovidChangeChart
      data={data}
      level="industry"
      title="COVID Impact by Industry"
      labelWidth={280}
    />
  );
}
