import { NextRequest, NextResponse } from 'next/server';
import { employerData, matchesIndustry, byApplicationsDesc } from '@/lib/staticData';
import type { ApiResponse, EmployerMetric } from '@/lib/types';

// export_static.py keeps the top 50 employers per year and per industry, so 50 is the max.
const MAX_LIMIT = 50;

export async function GET(request: NextRequest) {
  const sp = request.nextUrl.searchParams;
  const year = sp.get('year');
  const industry = sp.get('industry');
  const limit = Math.min(parseInt(sp.get('limit') || '20', 10) || 20, MAX_LIMIT);

  const data = employerData
    .filter((r) => !year || r.fiscal_year === Number(year))
    .filter((r) => !industry || matchesIndustry(r, industry))
    .sort(byApplicationsDesc)
    .slice(0, limit);

  const response: ApiResponse<EmployerMetric[]> = { success: true, data };
  return NextResponse.json(response);
}
