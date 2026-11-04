'use client';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Legend,
} from 'recharts';

interface ExposureRow {
  industry: string;
  industry_name: string;
  exposure_score: number;
  volume_share_pct: number;
  wage_mass_share_pct: number;
  hhi_score: number;
  estimated_fee_shock_millions: number;
}

export default function ExposureTopIndustries({ data }: { data: ExposureRow[] }) {
  const chartData = data
    .filter(d => d.industry_name && d.exposure_score)
    .map(d => ({
      industry: d.industry_name,
      exposure: Number(d.exposure_score),
      volume: Number(d.volume_share_pct) * 0.5,
      wageMass: Number(d.wage_mass_share_pct) * 0.4,
      hhi: Number(d.hhi_score) * 0.1,
      feeShock: Number(d.estimated_fee_shock_millions),
    }))
    .sort((a, b) => b.exposure - a.exposure)
    .slice(0, 12);

  if (chartData.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6 text-slate-500">
        No exposure data available.
      </div>
    );
  }

  const getColor = (exposure: number) => {
    if (exposure >= 30) return '#dc2626';
    if (exposure >= 20) return '#ea580c';
    if (exposure >= 10) return '#f59e0b';
    return '#10b981';
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-2">
        Top Industries by Policy Exposure Score
      </h3>
      <p className="text-sm text-slate-500 mb-4">
        Vulnerability to $100K H-1B fee increase. Score = 50% volume + 40% wage mass + 10% HHI.
      </p>
      <div className="h-[480px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical">
            <XAxis
              type="number"
              label={{ value: 'Exposure Score', position: 'insideBottom', offset: -5 }}
            />
            <YAxis
              type="category"
              dataKey="industry"
              width={220}
              interval={0}
              tick={{ fontSize: 11, fill: '#0f172a' }}
            />
            <Tooltip
              content={({ payload }: any) => {
                if (!payload?.[0]) return null;
                const d = payload[0].payload;
                return (
                  <div className="bg-white border border-slate-200 rounded shadow-lg p-3">
                    <p className="font-semibold text-sm mb-2">{d.industry}</p>
                    <p className="text-xs text-slate-600">
                      Exposure Score: <span className="font-medium">{d.exposure.toFixed(1)}</span>
                    </p>
                    <p className="text-xs text-slate-600 mt-1">Components:</p>
                    <p className="text-xs text-slate-500 ml-2">
                      Volume: {d.volume.toFixed(1)}
                    </p>
                    <p className="text-xs text-slate-500 ml-2">
                      Wage Mass: {d.wageMass.toFixed(1)}
                    </p>
                    <p className="text-xs text-slate-500 ml-2">
                      HHI: {d.hhi.toFixed(1)}
                    </p>
                    <p className="text-xs text-slate-600 mt-1">
                      Est. Fee Impact: <span className="font-medium">${d.feeShock.toFixed(1)}M</span>
                    </p>
                  </div>
                );
              }}
            />
            <Bar dataKey="exposure" radius={[0, 4, 4, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getColor(entry.exposure)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 flex justify-center gap-6 text-xs">
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-red-600" />
          Critical (30+)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-orange-600" />
          High (20-30)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-amber-500" />
          Moderate (10-20)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-emerald-500" />
          Low (0-10)
        </span>
      </div>
    </div>
  );
}
