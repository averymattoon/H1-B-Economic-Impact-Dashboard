'use client';

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { StateMetric } from '@/lib/types';

interface StateChartsProps {
  data: StateMetric[];
}

export default function StateCharts({ data }: StateChartsProps) {
  // Get top 15 states by applications
  const topStates = data
    .sort((a, b) => b.total_applications - a.total_applications)
    .slice(0, 15);

  // Format data for charts
  const applicationsData = topStates.map((item) => ({
    state: item.worksite_state,
    applications: item.total_applications,
  }));

  const wagesData = topStates.map((item) => ({
    state: item.worksite_state,
    avgWage: Math.round(item.avg_annual_wage),
    totalWages: Math.round(item.total_annual_wages / 1000000), // Convert to millions
  }));

  return (
    <div className="space-y-6">
      {/* Applications by State */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">
          Top 15 States by Applications
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={applicationsData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="state" tick={{ fill: '#000000' }} />
            <YAxis tick={{ fill: '#000000' }} />
            <Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #ccc' }} />
            <Legend />
            <Bar dataKey="applications" fill="#8b5cf6" name="Applications" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Total Economic Impact by State */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">
          Total Wages by State (Millions)
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={wagesData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="state" tick={{ fill: '#000000' }} />
            <YAxis tickFormatter={(value) => `$${value}M`} tick={{ fill: '#000000' }} />
            <Tooltip
              contentStyle={{ backgroundColor: 'white', border: '1px solid #ccc' }}
              formatter={(value) => `$${Number(value).toFixed(1)}M`}
            />
            <Legend />
            <Bar dataKey="totalWages" fill="#f59e0b" name="Total Annual Wages" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* State Stats Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <h3 className="text-lg font-semibold text-slate-900 p-6 pb-4">
          State Details
        </h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  State
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Applications
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Employers
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Avg Wage
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Total Wages
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-200">
              {topStates.map((item, index) => (
                <tr key={index} className="hover:bg-slate-50 group">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-900 group-hover:text-black">
                    {item.worksite_state}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 group-hover:text-black">
                    {item.total_applications.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 group-hover:text-black">
                    {item.unique_employers.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 group-hover:text-black">
                    ${Math.round(item.avg_annual_wage).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 group-hover:text-black">
                    ${(item.total_annual_wages / 1000000).toFixed(1)}M
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
