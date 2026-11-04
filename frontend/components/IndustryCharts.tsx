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
import { IndustryMetric } from '@/lib/types';

interface IndustryChartsProps {
  data: IndustryMetric[];
}

export default function IndustryCharts({ data }: IndustryChartsProps) {
  // Get top 10 industries by applications
  const topIndustries = data
    .sort((a, b) => b.total_applications - a.total_applications)
    .slice(0, 10);

  // Helper function to truncate long names
  const truncateName = (name: string, maxLength: number = 15) => {
    if (name.length <= maxLength) return name;
    return name.substring(0, maxLength) + '...';
  };

  // Format data for charts
  const applicationsData = topIndustries.map((item) => {
    const fullName = item.industry_name || item.industry || 'Unknown';
    return {
      industry: truncateName(fullName),
      fullName: fullName, // Keep full name for tooltip
      applications: item.total_applications,
    };
  });

  const wagesData = topIndustries.map((item) => {
    const fullName = item.industry_name || item.industry || 'Unknown';
    return {
      industry: truncateName(fullName),
      fullName: fullName, // Keep full name for tooltip
      avgWage: Math.round(item.avg_annual_wage),
      medianWage: Math.round(item.median_annual_wage),
    };
  });

  return (
    <div className="space-y-6">
      {/* Applications by Industry */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">
          Top 10 Industries by Applications
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={applicationsData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="industry"
              angle={-45}
              textAnchor="end"
              height={100}
              interval={0}
              tick={{ fontSize: 12.5, fill: '#000000' }}
            />
            <YAxis />
            <Tooltip
              contentStyle={{ backgroundColor: 'white', border: '1px solid #ccc' }}
              labelFormatter={(label, payload) => {
                if (payload && payload[0]) {
                  return payload[0].payload.fullName;
                }
                return label;
              }}
            />
            <Legend />
            <Bar dataKey="applications" fill="#3b82f6" name="Applications" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Wages by Industry */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">
          Average & Median Wages by Industry
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={wagesData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="industry"
              angle={-45}
              textAnchor="end"
              height={100}
              interval={0}
              tick={{ fontSize: 12.5, fill: '#000000' }}
            />
            <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
            <Tooltip
              contentStyle={{ backgroundColor: 'white', border: '1px solid #ccc' }}
              formatter={(value) => `$${Number(value).toLocaleString()}`}
              labelFormatter={(label, payload) => {
                if (payload && payload[0]) {
                  return payload[0].payload.fullName;
                }
                return label;
              }}
            />
            <Legend />
            <Bar dataKey="avgWage" fill="#10b981" name="Average Wage" />
            <Bar dataKey="medianWage" fill="#6366f1" name="Median Wage" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Industry Stats Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <h3 className="text-lg font-semibold text-slate-900 p-6 pb-4">
          Industry Details
        </h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Industry
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
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-200">
              {topIndustries.map((item, index) => (
                <tr key={index} className="hover:bg-slate-50 group">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-900 group-hover:text-black">
                    {item.industry_name || item.industry || 'Unknown'}
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
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
