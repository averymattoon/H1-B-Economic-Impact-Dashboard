'use client';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface CovidRow {
  worksite_state: string | null;
  pct_change_2019_2020: number | null;
}

export default function CovidStateChart({ data }: { data: CovidRow[] }) {
  const stateGroups = new Map<string, number[]>();
  
  data.forEach(d => {
    if (d.worksite_state && d.pct_change_2019_2020 !== null) {
      const state = d.worksite_state;
      const pct = Number(d.pct_change_2019_2020);
      if (!stateGroups.has(state)) {
        stateGroups.set(state, []);
      }
      stateGroups.get(state)!.push(pct);
    }
  });

  const chartData = Array.from(stateGroups.entries())
    .map(([state, pcts]) => {
      const sum = pcts.reduce((a, b) => a + b, 0);
      const avg = sum / pcts.length;
      return {
        worksite_state: state,
        pct_change_2019_2020: avg,
      };
    })
    .sort((a, b) => a.pct_change_2019_2020 - b.pct_change_2019_2020)
    .slice(0, 15);

  if (chartData.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6 text-slate-500">
        No state-level COVID impact data.
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-2">
        COVID Impact by State
      </h3>
      <p className="text-sm text-slate-500 mb-4">
        % change in H-1B applications (2019 → 2020)
      </p>
      <div className="h-[420px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical">
            <XAxis type="number" tickFormatter={v => `${v}%`} />
            <YAxis
              type="category"
              dataKey="worksite_state"
              width={80}
            />
            <Tooltip formatter={(v) => `${Number(v).toFixed(1)}%`} />
            <Bar dataKey="pct_change_2019_2020" fill="#dc2626" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
