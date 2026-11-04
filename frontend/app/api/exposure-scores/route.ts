import { NextResponse } from 'next/server';
import { exposureData } from '@/lib/staticData';

export async function GET() {
  return NextResponse.json(exposureData);
}
