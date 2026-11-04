'use client';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from 'recharts';

export interface CovidRow {
  level: 'industry' | 'state';
  name: string;
  app_count_2019: number;
  app_count_2020: number | null;
  app_count_2021: number | null;
  pct_change_2019_2020: number | null;
  pct_change_2019_2021: number | null;
}

interface Props {
  data: CovidRow[];
  level: 'industry' | 'state';
  title: string;
  labelWidth: number;
}

const fmt = (n: number | null) => (n == null ? '—' : n.toLocaleString());

export default function CovidChangeChart({ data, level, title, labelWidth }: Props) {
  const chartData = data
    .filter(d => d.level === level && d.pct_change_2019_2020 != null)
    .map(d => ({ ...d, change: Number(d.pct_change_2019_2020) }))
    .sort((a, b) => a.change - b.change);

  if (chartData.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6 text-slate-500">
        No COVID trend data available.
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-sm text-slate-500 mb-4">
        % change in certified H-1B applications, FY2019 → FY2020. Only{' '}
        {level === 'industry' ? 'industries' : 'states'} with at least 1,000 applications in
        FY2019 are shown. Hover a bar for counts and the FY2021 rebound.
      </p>
      <div style={{ height: Math.max(300, chartData.length * 22 + 40) }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical" margin={{ right: 24 }}>
            <XAxis type="number" tickFormatter={v => `${v}%`} />
            <YAxis
              type="category"
              dataKey="name"
              width={labelWidth}
              interval={0}
              tick={{ fontSize: 12 }}
            />
            <ReferenceLine x={0} stroke="#94a3b8" />
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const d = payload[0].payload as CovidRow & { change: number };
                return (
                  <div className="bg-white border border-slate-200 rounded p-3 text-sm shadow">
                    <div className="font-semibold mb-1">{d.name}</div>
                    <div>FY2019: {fmt(d.app_count_2019)}</div>
                    <div>FY2020: {fmt(d.app_count_2020)} ({d.change.toFixed(1)}%)</div>
                    <div>
                      FY2021: {fmt(d.app_count_2021)}
                      {d.pct_change_2019_2021 != null &&
                        ` (${Number(d.pct_change_2019_2021).toFixed(1)}% vs 2019)`}
                    </div>
                  </div>
                );
              }}
            />
            <Bar dataKey="change">
              {chartData.map((d, i) => (
                <Cell key={i} fill={d.change < 0 ? '#dc2626' : '#16a34a'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
