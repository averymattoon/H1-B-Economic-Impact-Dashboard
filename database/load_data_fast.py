"""
OPTIMIZED ETL Script: Load H-1B CSV data into PostgreSQL (MUCH FASTER)
Uses bulk operations instead of row-by-row lookups
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
from pathlib import Path
import os
from dotenv import load_dotenv
import argparse

load_dotenv()

def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT', 5432),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

class H1BFastLoader:
    def __init__(self, data_dir='../data'):
        self.data_dir = Path(data_dir)
        self.conn = get_db_connection()
        self.cur = self.conn.cursor()

    def load_csv_files(self, years=None):
        """Load CSV files for specified years"""
        if years:
            files = []
            for year in years:
                year_files = list(self.data_dir.glob(f'cleaned_*{year}*.csv'))
                files.extend(year_files)
        else:
            files = [f for f in self.data_dir.glob('cleaned_*.csv') if f.name != 'combined.csv']

        print(f"Found {len(files)} CSV files to load")

        dfs = []
        for file in sorted(files):
            print(f"  Reading {file.name}...", end='')
            df = pd.read_csv(file, low_memory=False)
            df = self.standardize_column_names(df)
            dfs.append(df)
            print(f" ✓ ({len(df):,} rows)")

        df = pd.concat(dfs, ignore_index=True)
        print(f"\nTotal records: {len(df):,}")
        return df

    def standardize_column_names(self, df):
        """Standardize column names across different CSV formats"""
        rename_map = {
            'case_number': 'app_id',
            'employer_fein': 'emp_id',
            'employer_name': 'emp_name',
            'employer_city': 'emp_city',
            'employer_state': 'emp_state',
            'employer_zip': 'emp_zip',
            'full_time_position': 'full_time'
        }
        df = df.rename(columns=rename_map)

        # Keep code columns as clean text (avoid 541511.0 / 02139.0 from float parsing)
        for col in ['industry', 'emp_id', 'emp_zip', 'worksite_zip', 'soc_code']:
            if col in df.columns:
                df[col] = (df[col].astype('string')
                                  .str.strip()
                                  .str.replace(r'\.0$', '', regex=True)
                                  .replace({'nan': pd.NA, '': pd.NA}))

        # Add missing columns with default values if they don't exist
        if 'emp_id' not in df.columns:
            # Generate emp_id from emp_name if missing
            df['emp_id'] = df['emp_name'].apply(lambda x: str(hash(x))[:15] if pd.notna(x) else None)

        if 'worksite_city' not in df.columns:
            df['worksite_city'] = df.get('emp_city', None)

        if 'worksite_state' not in df.columns:
            df['worksite_state'] = df.get('emp_state', None)

        if 'worksite_zip' not in df.columns:
            df['worksite_zip'] = df.get('emp_zip', None)

        if 'wage_unit' not in df.columns:
            df['wage_unit'] = 'Year'  # Default to annual wage

        if 'visa_class' not in df.columns:
            df['visa_class'] = 'H-1B'

        if 'full_time' not in df.columns:
            df['full_time'] = 'Y'

        if 'employer_address' not in df.columns:
            df['employer_address'] = None

        # Normalize case_status to title case to match check constraint
        if 'case_status' in df.columns:
            df['case_status'] = df['case_status'].str.title()

        return df

    def standardize_wages(self, df):
        """Standardize all wages to annual"""
        print("Standardizing wages to annual...")

        wage_multipliers = {
            'Hour': 2080, 'Week': 52, 'Bi-Weekly': 26, 'Month': 12, 'Year': 1
        }

        df['wage_offer'] = pd.to_numeric(df['wage_offer'], errors='coerce')
        df['annual_wage'] = df.apply(
            lambda row: row['wage_offer'] * wage_multipliers.get(row['wage_unit'], 1)
            if pd.notna(row['wage_offer']) else None, axis=1
        )
        # Treat implausible annual wages as missing (data-entry errors, e.g. annual pay coded as hourly)
        bad = (df['annual_wage'] < 10_000) | (df['annual_wage'] > 5_000_000)
        print(f"  Blanking {bad.sum():,} implausible wages")
        df.loc[bad, ['annual_wage', 'wage_offer']] = None
        return df

    def load_occupations(self, df):
        """Load unique occupations"""
        print("\n=== Loading Occupations ===")
        occupations = df[['soc_code', 'soc_title', 'major_group']].drop_duplicates()
        occupations = occupations[occupations['soc_code'].notna()]

        print(f"Found {len(occupations)} unique occupations")

        insert_query = """
            INSERT INTO occupations (soc_code, soc_title, major_group)
            VALUES (%s, %s, %s)
            ON CONFLICT (soc_code) DO UPDATE
            SET soc_title = EXCLUDED.soc_title, major_group = EXCLUDED.major_group
        """

        data = [(row['soc_code'], row['soc_title'], row['major_group'])
                for _, row in occupations.iterrows()]

        execute_batch(self.cur, insert_query, data, page_size=1000)
        self.conn.commit()
        print(f"✅ Loaded {len(data)} occupations")

    def load_employers(self, df):
        """Load unique employers"""
        print("\n=== Loading Employers ===")
        employers = df[['emp_id', 'emp_name', 'industry', 'employer_address',
                       'emp_city', 'emp_state', 'emp_zip']].drop_duplicates(subset=['emp_id'])
        employers = employers[employers['emp_id'].notna()]

        print(f"Found {len(employers)} unique employers")

        insert_query = """
            INSERT INTO employers (emp_id, emp_name, industry, emp_address, emp_city, emp_state, emp_zip)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (emp_id) DO UPDATE
            SET emp_name = EXCLUDED.emp_name, industry = EXCLUDED.industry
        """

        data = [
            (row['emp_id'], row['emp_name'],
             str(row['industry']) if pd.notna(row['industry']) else None,
             row['employer_address'] if pd.notna(row['employer_address']) else None,
             row['emp_city'] if pd.notna(row['emp_city']) else None,
             row['emp_state'] if pd.notna(row['emp_state']) else None,
             row['emp_zip'] if pd.notna(row['emp_zip']) else None)
            for _, row in employers.iterrows()
        ]

        execute_batch(self.cur, insert_query, data, page_size=1000)
        self.conn.commit()
        print(f"✅ Loaded {len(data)} employers")

    def load_worksite_locations_bulk(self, df):
        """Load worksite locations in bulk (FAST)"""
        print("\n=== Loading Worksite Locations (Bulk) ===")

        worksites = df[['worksite_city', 'worksite_state', 'worksite_zip']].drop_duplicates()
        worksites = worksites.dropna(subset=['worksite_state'])

        print(f"Found {len(worksites)} unique worksites")

        insert_query = """
            INSERT INTO worksite_locations (worksite_city, worksite_state, worksite_zip)
            VALUES (%s, %s, %s)
            ON CONFLICT (worksite_city, worksite_state, worksite_zip) DO NOTHING
        """

        data = [
            (row['worksite_city'] if pd.notna(row['worksite_city']) else None,
             row['worksite_state'],
             row['worksite_zip'] if pd.notna(row['worksite_zip']) else None)
            for _, row in worksites.iterrows()
        ]

        execute_batch(self.cur, insert_query, data, page_size=1000)
        self.conn.commit()
        print(f"✅ Loaded worksite locations")

    def get_site_id_mapping(self):
        """Get all site_ids in one query (FAST)"""
        print("Creating site_id mapping...")

        query = """
            SELECT site_id, worksite_city, worksite_state, worksite_zip
            FROM worksite_locations
        """
        self.cur.execute(query)
        results = self.cur.fetchall()

        # Create lookup dictionary
        site_map = {}
        for site_id, city, state, zip_code in results:
            key = (city, state, zip_code)
            site_map[key] = site_id

        print(f"✅ Mapped {len(site_map)} worksite locations")
        return site_map

    def load_applications_fast(self, df, site_map):
        """Load applications using pre-built site_id mapping (FAST)"""
        print("\n=== Loading Applications (Fast) ===")
        print(f"Total applications to load: {len(df):,}")

        # Add site_id using the mapping (instant!)
        df['site_id'] = df.apply(
            lambda row: site_map.get((
                row['worksite_city'] if pd.notna(row['worksite_city']) else None,
                row['worksite_state'] if pd.notna(row['worksite_state']) else None,
                row['worksite_zip'] if pd.notna(row['worksite_zip']) else None
            )), axis=1
        )

        insert_query = """
            INSERT INTO applications (
                app_id, emp_id, soc_code, site_id,
                case_status, decision_date, received_date, fiscal_year, visa_class,
                job_title, full_time, begin_date, end_date,
                wage_offer, wage_unit, annual_wage
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (app_id) DO NOTHING
        """

        # Process in batches
        batch_size = 5000
        total_loaded = 0

        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            data = []

            for _, row in batch.iterrows():
                if pd.isna(row['app_id']) or pd.isna(row['emp_id']) or pd.isna(row['soc_code']):
                    continue

                data.append((
                    row['app_id'], row['emp_id'], row['soc_code'],
                    int(row['site_id']) if pd.notna(row['site_id']) else None,
                    row['case_status'] if pd.notna(row['case_status']) else 'Certified',
                    pd.to_datetime(row['decision_date']).date() if pd.notna(row['decision_date']) else None,
                    pd.to_datetime(row['received_date']).date() if pd.notna(row['received_date']) else None,
                    int(row['fiscal_year']) if pd.notna(row['fiscal_year']) else None,
                    row['visa_class'] if pd.notna(row['visa_class']) else 'H-1B',
                    row['job_title'] if pd.notna(row['job_title']) else None,
                    row['full_time'] == 'Y' if pd.notna(row['full_time']) else True,
                    pd.to_datetime(row['begin_date']).date() if pd.notna(row['begin_date']) else None,
                    pd.to_datetime(row['end_date']).date() if pd.notna(row['end_date']) else None,
                    float(row['wage_offer']) if pd.notna(row['wage_offer']) else None,
                    row['wage_unit'] if pd.notna(row['wage_unit']) else None,
                    float(row['annual_wage']) if pd.notna(row['annual_wage']) else None
                ))

            execute_batch(self.cur, insert_query, data, page_size=1000)
            self.conn.commit()

            total_loaded += len(data)
            print(f"  Batch {i//batch_size + 1}: {total_loaded:,}/{len(df):,} ({total_loaded/len(df)*100:.1f}%)")

        print(f"✅ Loaded {total_loaded:,} applications")

    def refresh_views(self):
        """Refresh materialized views"""
        print("\n=== Refreshing Materialized Views ===")
        views = ['mv_industry_metrics', 'mv_state_metrics', 'mv_occupation_metrics']
        for view in views:
            print(f"  Refreshing {view}...", end='')
            self.cur.execute(f"REFRESH MATERIALIZED VIEW {view}")
            self.conn.commit()
            print(" ✓")
        print("✅ All views refreshed")

    def verify_data(self):
        """Verify loaded data"""
        print("\n=== Verifying Data ===")
        tables = [('occupations', 'soc_code'), ('employers', 'emp_id'),
                  ('worksite_locations', 'site_id'), ('applications', 'app_id')]
        for table, pk in tables:
            self.cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = self.cur.fetchone()[0]
            print(f"  {table}: {count:,} records")

    def close(self):
        self.cur.close()
        self.conn.close()

def main():
    parser = argparse.ArgumentParser(description='Fast H-1B data loader')
    parser.add_argument('--years', nargs='+', type=int, help='Years to load')
    parser.add_argument('--all', action='store_true', help='Load all data')
    args = parser.parse_args()

    print("="*70)
    print("H1-B FAST DATA LOADER")
    print("="*70)

    loader = H1BFastLoader()

    try:
        # Load CSV
        df = loader.load_csv_files(years=args.years if not args.all else None)
        df = loader.standardize_wages(df)

        # Load dimension tables
        loader.load_occupations(df)
        loader.load_employers(df)
        loader.load_worksite_locations_bulk(df)

        # Get site_id mapping (one query!)
        site_map = loader.get_site_id_mapping()

        # Load applications (fast!)
        loader.load_applications_fast(df, site_map)

        # Refresh views
        loader.refresh_views()

        # Verify
        loader.verify_data()

        print("\n" + "="*70)
        print("✅ DATA LOAD COMPLETE!")
        print("="*70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
    finally:
        loader.close()

if __name__ == "__main__":
    main()
