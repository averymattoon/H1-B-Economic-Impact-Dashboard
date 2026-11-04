'use client';

import CovidChangeChart, { CovidRow } from './CovidChangeChart';

export default function CovidStateChart({ data }: { data: CovidRow[] }) {
  return (
    <CovidChangeChart data={data} level="state" title="COVID Impact by State" labelWidth={50} />
  );
}
