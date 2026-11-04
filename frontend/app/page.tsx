'use client';

import { useEffect, useState } from 'react';
import { IndustryMetric, StateMetric, ApiResponse } from '@/lib/types';

import IndustryCharts from '@/components/IndustryCharts';
import StateCharts from '@/components/StateCharts';
import StateHeatmap from '@/components/StateHeatmap';
import DashboardFilters from '@/components/DashboardFilters';
import CovidIndustryChart from '@/components/CovidIndustryChart';
import CovidStateChart from '@/components/CovidStateChart';
import ExposureScatterPlot from '@/components/ExposureScatterPlot';
import ExposureTopIndustries from '@/components/ExposureTopIndustries';
import ExposureStateHeatmap from '@/components/ExposureStateHeatmap';
import ExposureMetricsGrid from '@/components/ExposureMetricsGrid';
import EmployerLeaderboard from '@/components/EmployerLeaderBoard';

export default function Dashboard() {
  const [industryData, setIndustryData] = useState<IndustryMetric[]>([]);
  const [stateData, setStateData] = useState<StateMetric[]>([]);
  const [covidData, setCovidData] = useState<any[]>([]);
  const [exposureIndustryData, setExposureIndustryData] = useState<any[]>([]);
  const [exposureStateData, setExposureStateData] = useState<any[]>([]);

  const [employerData, setEmployerData] = useState<any[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'covid' | 'exposure'>('overview');

  const [selectedYear, setSelectedYear] = useState<number>(2024);
  const [selectedIndustry, setSelectedIndustry] = useState<string>('');
  const [selectedState, setSelectedState] = useState<string>('');

  const fetchOverviewData = async () => {
    setLoading(true);
    setError(null);

    try {
      const industryParams = new URLSearchParams();
      if (selectedYear) industryParams.append('year', selectedYear.toString());
      if (selectedIndustry) industryParams.append('industry', selectedIndustry);

      const stateParams = new URLSearchParams();
      if (selectedYear) stateParams.append('year', selectedYear.toString());
      if (selectedState) stateParams.append('state', selectedState);

      const [industryRes, stateRes] = await Promise.all([
        fetch(`/api/industry-metrics?${industryParams.toString()}`),
        fetch(`/api/state-metrics?${stateParams.toString()}`),
      ]);

      const employerParams = new URLSearchParams();
      if (selectedYear) employerParams.append('year', selectedYear.toString());
      if (selectedIndustry) employerParams.append('industry', selectedIndustry);
      employerParams.append('limit', '50');

      const employerRes = await fetch(`/api/employer-metrics?${employerParams.toString()}`);
      if (employerRes.ok) {
        const employerJson = await employerRes.json();
        setEmployerData(employerJson.data || []);
      } else {
        setEmployerData([]);
      }

      if (!industryRes.ok || !stateRes.ok) {
        throw new Error('Failed to fetch overview data');
      }

      const industryJson: ApiResponse<IndustryMetric[]> = await industryRes.json();
      const stateJson: ApiResponse<StateMetric[]> = await stateRes.json();

      setIndustryData(industryJson.data || []);
      setStateData(stateJson.data || []);
    } catch (err) {
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const fetchCovidData = async () => {
    try {
      const res = await fetch('/api/covid-trends');
      if (!res.ok) throw new Error('Failed to fetch COVID trends');

      const json = await res.json();

      if (Array.isArray(json)) {
        setCovidData(json);
      } else if (Array.isArray(json.data)) {
        setCovidData(json.data);
      } else {
        console.error('Unexpected covid-trends response:', json);
        setCovidData([]);
      }
    } catch (err) {
      console.error(err);
      setCovidData([]);
    }
  };

  const fetchExposureData = async () => {
    try {
      const res = await fetch('/api/exposure-scores');
      if (!res.ok) throw new Error('Failed to fetch exposure scores');

      const json = await res.json();
      setExposureIndustryData(json.industries || []);
      setExposureStateData(json.states || []);
    } catch (err) {
      console.error(err);
      setExposureIndustryData([]);
      setExposureStateData([]);
    }
  };

  useEffect(() => {
    fetchOverviewData();
  }, [selectedYear, selectedIndustry, selectedState]);

  useEffect(() => {
    fetchCovidData();
    fetchExposureData();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <header className="bg-white shadow-sm border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-slate-900">
            H-1B Economic Impact Dashboard
          </h1>
          <p className="mt-2 text-sm text-slate-600">
            Analyzing the economic impact of H-1B visa holders on U.S. industries and states
          </p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-6 border-b border-slate-200">
          <nav className="flex space-x-6">
            <button
              onClick={() => setActiveTab('overview')}
              className={`pb-2 font-medium ${activeTab === 'overview'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-slate-500'
                }`}
            >
              Overview
            </button>

            <button
              onClick={() => setActiveTab('covid')}
              className={`pb-2 font-medium ${activeTab === 'covid'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-slate-500'
                }`}
            >
              COVID Trends
            </button>

            <button
              onClick={() => setActiveTab('exposure')}
              className={`pb-2 font-medium ${activeTab === 'exposure'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-slate-500'
                }`}
            >
              Policy Exposure
            </button>
          </nav>
        </div>

        {activeTab === 'overview' && (
          <DashboardFilters
            selectedYear={selectedYear}
            selectedIndustry={selectedIndustry}
            selectedState={selectedState}
            onYearChange={setSelectedYear}
            onIndustryChange={setSelectedIndustry}
            onStateChange={setSelectedState}
            industries={Array.from(
              new Map(
                industryData
                  .filter(
                    d =>
                      typeof d.industry_name === 'string' &&
                      d.industry_name.trim() !== '' &&
                      d.industry_name !== d.industry
                  )
                  .map(d => [d.industry_name, d.industry_name])
              ).entries()
            ).map(([value, label]) => ({ value, label }))}
            states={Array.from(
              new Set(stateData.map(d => d.worksite_state))
            ).filter(Boolean)}
          />
        )}

        {loading && (
          <div className="flex justify-center py-12">
            <div className="animate-spin h-10 w-10 border-b-2 border-blue-600 rounded-full" />
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {!loading && !error && activeTab === 'overview' && (
          <>
            <div className="mb-8">
              <StateHeatmap data={stateData} />
            </div>

            <EmployerLeaderboard data={employerData} />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <IndustryCharts data={industryData} />
              <StateCharts data={stateData} />
            </div>


          </>
        )}

        {!loading && activeTab === 'covid' && (
          <div className="space-y-10">
            <CovidIndustryChart data={covidData} />
            <CovidStateChart data={covidData} />
          </div>
        )}

        {!loading && activeTab === 'exposure' && (
          <div className="space-y-10">
            <ExposureMetricsGrid
              industryData={exposureIndustryData}
              stateData={exposureStateData}
            />

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <ExposureTopIndustries data={exposureIndustryData} />
              <ExposureScatterPlot data={exposureIndustryData} />
            </div>

            <ExposureStateHeatmap data={exposureStateData} />
          </div>
        )}
      </main>
    </div>
  );
}
