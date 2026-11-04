'use client';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

interface CovidRow {
  industry_name: string | null;
  app_count_change_2019_to_2020_pct: number;
}

export default function CovidImpactBarCharts({ data }: { data: CovidRow[] }) {
  const chartData = data
    .filter(d => d.industry_name)
    .map(d => ({
      industry: d.industry_name!,
      change: Number(d.app_count_change_2019_to_2020_pct),
    }));

  if (chartData.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6 text-slate-500">
        No COVID impact data available.
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-2">
        Industries Most Impacted by COVID
      </h3>
      <p className="text-sm text-slate-500 mb-4">
        % change in H-1B applications (2019 → 2020)
      </p>

      <div className="h-[380px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical">
            <XAxis
              type="number"
              tickFormatter={v => `${v}%`}
            />
            <YAxis
              type="category"
              dataKey="industry"
              width={260}
            />
            <Tooltip formatter={(v) => `${Number(v).toFixed(1)}%`} />
            <Bar dataKey="change">
              {chartData.map((_, i) => (
                <Cell key={i} fill="#dc2626" />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
