"""
Post-cleaning fixes for the cleaned_h1b_*.csv files. Run once, after clean_all.py.

1. Wage units: the FY2009 Case Data file uses YR / HR / MTH / WK / BI.
   load_data_fast.py only recognizes Year / Hour / Month / Week / Bi-Weekly and
   treats anything else as an annual wage, so hourly pay would be counted as salary.
   This maps the abbreviations to the full names.

2. Fiscal year: data_cleaning.py derives fiscal_year from the RECEIVED date, so each
   file spills some cases into the prior year (and FY2024 would be missing cases
   received in FY2024 but decided in FY2025). DOL assigns each case to a fiscal year
   by its decision date, which is how the files are organized. This sets fiscal_year
   to the year in the file name so the yearly counts match DOL's own totals.
   Set USE_FILE_FISCAL_YEAR = False to keep the received-date version.

3. Reports any file that has no wage_unit column (FY2010), which needs a fix in
   data_cleaning.py before re-cleaning.

Usage (in the folder with the cleaned files):
  python3 fix_cleaned.py
"""
import re
from pathlib import Path
import pandas as pd

USE_FILE_FISCAL_YEAR = True

UNIT_MAP = {
    'YR': 'Year', 'YEAR': 'Year',
    'HR': 'Hour', 'HOUR': 'Hour',
    'MTH': 'Month', 'MONTH': 'Month',
    'WK': 'Week', 'WEEK': 'Week',
    'BI': 'Bi-Weekly', 'BI-WEEKLY': 'Bi-Weekly', 'BIWEEKLY': 'Bi-Weekly',
}

for path in sorted(Path('.').glob('cleaned_h1b_*.csv')):
    m = re.match(r'cleaned_h1b_(\d{4})', path.name)
    if not m:
        continue
    file_year = int(m.group(1))
    df = pd.read_csv(path, low_memory=False)
    notes = []

    if 'wage_unit' in df.columns:
        before = df['wage_unit'].copy()
        df['wage_unit'] = (df['wage_unit'].astype(str).str.strip().str.upper()
                           .map(UNIT_MAP).where(before.notna(), None))
        unknown = before[df['wage_unit'].isna() & before.notna()].unique()
        if len(unknown):
            notes.append(f'UNRECOGNIZED units left blank: {list(unknown)[:10]}')
    else:
        notes.append('NO wage_unit column: fix data_cleaning.py and re-clean this file')

    if USE_FILE_FISCAL_YEAR:
        moved = (df.get('fiscal_year') != file_year).sum() if 'fiscal_year' in df else len(df)
        df['fiscal_year'] = file_year
        notes.append(f'fiscal_year set to {file_year} ({moved:,} rows changed)')

    df.to_csv(path, index=False)
    print(f'{path.name}: ' + '; '.join(notes))
