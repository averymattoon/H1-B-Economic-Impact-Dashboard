import { NextRequest, NextResponse } from 'next/server';
import { stateData, byApplicationsDesc } from '@/lib/staticData';
import type { ApiResponse, StateMetric } from '@/lib/types';

export async function GET(request: NextRequest) {
  const sp = request.nextUrl.searchParams;
  const year = sp.get('year');
  const state = sp.get('state');

  const data = stateData
    .filter((r) => !year || r.fiscal_year === Number(year))
    .filter((r) => !state || r.worksite_state === state)
    .sort(byApplicationsDesc);

  const response: ApiResponse<StateMetric[]> = { success: true, data };
  return NextResponse.json(response);
}
