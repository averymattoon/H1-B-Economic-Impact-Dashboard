import { NextRequest, NextResponse } from 'next/server';
import { industryData, matchesIndustry, byApplicationsDesc } from '@/lib/staticData';
import type { ApiResponse, IndustryMetric } from '@/lib/types';

export async function GET(request: NextRequest) {
  const sp = request.nextUrl.searchParams;
  const year = sp.get('year');
  const industry = sp.get('industry');

  const data = industryData
    .filter((r) => !year || r.fiscal_year === Number(year))
    .filter((r) => !industry || matchesIndustry(r, industry))
    .sort(byApplicationsDesc);

  const response: ApiResponse<IndustryMetric[]> = { success: true, data };
  return NextResponse.json(response);
}
