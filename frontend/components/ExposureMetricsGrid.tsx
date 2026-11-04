'use client';

interface ExposureRow {
  exposure_score: number;
  estimated_fee_shock_millions: number;
  total_applications: number;
  hhi_concentration: number;
}

interface ExposureMetricsGridProps {
  industryData: ExposureRow[];
  stateData: ExposureRow[];
}

// Values are in millions of dollars: 477658.9 -> "$477.7B"
const formatMillions = (m: number) =>
  m >= 1_000_000 ? `$${(m / 1_000_000).toFixed(1)}T`
  : m >= 1_000 ? `$${(m / 1_000).toFixed(1)}B`
  : `$${m.toFixed(0)}M`;

export default function ExposureMetricsGrid({ 
  industryData, 
  stateData 
}: ExposureMetricsGridProps) {
  const industryTotalFees = industryData.reduce(
    (sum, d) => sum + Number(d.estimated_fee_shock_millions || 0),
    0
  );
  
  const stateTotalFees = stateData.reduce(
    (sum, d) => sum + Number(d.estimated_fee_shock_millions || 0),
    0
  );

  const avgIndustryExposure = industryData.length > 0
    ? industryData.reduce((sum, d) => sum + Number(d.exposure_score || 0), 0) / industryData.length
    : 0;

  const avgStateExposure = stateData.length > 0
    ? stateData.reduce((sum, d) => sum + Number(d.exposure_score || 0), 0) / stateData.length
    : 0;

  const criticalIndustries = industryData.filter(d => d.exposure_score >= 30).length;
  const criticalStates = stateData.filter(d => d.exposure_score >= 30).length;

  const highHHIIndustries = industryData.filter(d => d.hhi_concentration > 0.15).length;

  const metrics = [
    {
      label: 'Total Policy Impact',
      value: formatMillions(industryTotalFees),
      description: '$100K on every certified application, FY2009–2024 combined',
      color: 'bg-blue-50 text-blue-700 border-blue-200',
    },
    {
      label: 'Avg Industry Exposure',
      value: avgIndustryExposure.toFixed(1),
      description: 'Mean exposure score across industries',
      color: 'bg-purple-50 text-purple-700 border-purple-200',
    },
    {
      label: 'Critical Industries',
      value: criticalIndustries,
      description: 'Industries with exposure ≥ 30',
      color: 'bg-red-50 text-red-700 border-red-200',
    },
    {
      label: 'High Concentration',
      value: highHHIIndustries,
      description: 'Industries with HHI > 0.15',
      color: 'bg-orange-50 text-orange-700 border-orange-200',
    },
    {
      label: 'Avg State Exposure',
      value: avgStateExposure.toFixed(1),
      description: 'Mean exposure score across states',
      color: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    },
    {
      label: 'Critical States',
      value: criticalStates,
      description: 'States with exposure ≥ 30',
      color: 'bg-amber-50 text-amber-700 border-amber-200',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
      {metrics.map((metric, idx) => (
        <div
          key={idx}
          className={`${metric.color} rounded-lg border p-5 transition-all hover:shadow-md`}
        >
          <p className="text-sm font-medium mb-1">{metric.label}</p>
          <p className="text-3xl font-bold mb-1">{metric.value}</p>
          <p className="text-xs opacity-75">{metric.description}</p>
        </div>
      ))}
    </div>
  );
}
