import { NextResponse } from 'next/server';
import { covidData } from '@/lib/staticData';

export async function GET() {
  return NextResponse.json(covidData);
}
