"""
Re-parse application dates with the correct day/month order, after all data is loaded.

Why: load_data_fast.py parses each date on its own with pandas' default (month first).
Some source files write dates day-first (30/09/2016). Unambiguous ones are read
correctly, but ambiguous ones like 05/06/2016 get swapped (May 6 instead of June 5).

What this does, per cleaned file and per date column:
  1. Looks at every slash-style date (d/m/yyyy or m/d/yyyy).
  2. Decides the file's order: if some values only make sense day-first
     (first number > 12) and none only make sense month-first, it's day-first.
     If both kinds appear, the column is reported as MIXED and left alone.
  3. Parses the whole column with that explicit format and updates the database
     by app_id. ISO dates (2016-09-30) are already unambiguous and are kept as is.

Run from the database/ folder (it reads ../data and the same .env as the loader):
  python3 fix_dates.py            # report only, changes nothing
  python3 fix_dates.py --apply    # report and update the database
"""
import argparse
import io
import os
import re
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv

DATA_DIR = Path('../data')
DATE_COLS = ['decision_date', 'begin_date', 'end_date']
SLASH = re.compile(r'^\s*(\d{1,2})/(\d{1,2})/(\d{2,4})\s*$')


def detect_order(series: pd.Series):
    """Return 'day', 'month', 'iso', 'mixed' or None for a column of date strings."""
    s = series.dropna().astype(str)
    m = s.str.extract(SLASH)
    m = m.dropna()
    if m.empty:
        return 'iso' if len(s) else None
    a, b = m[0].astype(int), m[1].astype(int)
    day_first_only = ((a > 12) & (b <= 12)).sum()
    month_first_only = ((b > 12) & (a <= 12)).sum()
    if day_first_only and month_first_only:
        return 'mixed'
    if day_first_only:
        return 'day'
    return 'month'


def parse(series: pd.Series, order: str) -> pd.Series:
    s = series.astype('string')
    out = pd.to_datetime(s, format='ISO8601', errors='coerce')  # ISO values
    slash = s.str.match(SLASH, na=False)
    if slash.any():
        fmt = '%d/%m/%Y' if order == 'day' else '%m/%d/%Y'
        out[slash] = pd.to_datetime(s[slash], format=fmt, errors='coerce')
    return out.dt.date


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true', help='write fixes to the database')
    args = ap.parse_args()

    load_dotenv()
    conn = None
    if args.apply:
        conn = psycopg2.connect(host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT', 5432),
                                database=os.getenv('DB_NAME'), user=os.getenv('DB_USER'),
                                password=os.getenv('DB_PASSWORD'))

    for path in sorted(DATA_DIR.glob('cleaned_h1b_*.csv')):
        cols = pd.read_csv(path, nrows=0).columns
        use = ['app_id'] + [c for c in DATE_COLS if c in cols]
        if 'app_id' not in cols or len(use) == 1:
            continue
        df = pd.read_csv(path, usecols=use, dtype=str)
        orders = {c: detect_order(df[c]) for c in use[1:]}
        print(f'{path.name}: ' + ', '.join(f'{c}={o}' for c, o in orders.items()))

        fix_cols = [c for c, o in orders.items() if o == 'day']
        if not fix_cols or not args.apply:
            continue

        fixed = pd.DataFrame({'app_id': df['app_id']})
        for c in fix_cols:
            fixed[c] = parse(df[c], 'day')
        fixed = fixed.dropna(subset=['app_id'])

        with conn.cursor() as cur:
            cur.execute('CREATE TEMP TABLE date_fix (app_id varchar(50), '
                        + ', '.join(f'{c} date' for c in fix_cols) + ') ON COMMIT DROP')
            buf = io.StringIO()
            fixed.to_csv(buf, index=False, header=False)
            buf.seek(0)
            cur.copy_expert(f"COPY date_fix (app_id, {', '.join(fix_cols)}) FROM STDIN WITH CSV", buf)
            sets = ', '.join(f'{c} = f.{c}' for c in fix_cols)
            cur.execute(f'UPDATE applications a SET {sets} FROM date_fix f WHERE a.app_id = f.app_id')
            print(f'   updated {cur.rowcount:,} rows ({", ".join(fix_cols)})')
        conn.commit()

    if conn:
        conn.close()
    if not args.apply:
        print('\nReport only. Run with --apply to update the database.')


if __name__ == '__main__':
    main()
