import pandas as pd
import numpy as np

def clean_h1b_dataset(input_file, output_file='large_cleaned_h1b_test_2024.csv'):
    """
    Clean H-1B dataset from any year (2008-2024) with flexible column mapping.
    Handles different column name formats across years.
    """

    print(f"Reading dataset from {input_file}...")
    df = pd.read_excel(input_file) if input_file.endswith('.xlsx') else pd.read_csv(input_file, low_memory=False)
    print(f"Original dataset: {len(df)} rows, {len(df.columns)} columns")

    # FY2009 Case Data format: translate program codes and old DOT occupation codes
    if 'PROGRAM_DESIGNATION' in df.columns and 'VISA_CLASS' not in df.columns:
        df['VISA_CLASS'] = df['PROGRAM_DESIGNATION'].map(
            {'R': 'H-1B', 'S': 'H-1B1 Singapore', 'C': 'H-1B1 Chile', 'A': 'E-3 Australian'})
    if 'OCCUPATIONAL_CODE' in df.columns and 'SOC_CODE' not in df.columns:
        codes = pd.to_numeric(df['OCCUPATIONAL_CODE'], errors='coerce').astype('Int64')
        df['SOC_CODE'] = ('DOT-' + codes.astype(str).str.zfill(3)).where(codes.notna(), None)

    # Define column mappings (list of possible names for each field)
    column_mappings = {
        'app_id': ['CASE_NUMBER', 'LCA_CASE_NUMBER', 'CASE_NO'],
        'case_status': ['CASE_STATUS', 'STATUS', 'APPROVAL_STATUS'],
        'decision_date': ['DECISION_DATE', 'DOL_DECISION_DATE', 'Decision_Date'],
        'received_date': ['RECEIVED_DATE', 'CASE_SUBMITTED', 'LCA_CASE_SUBMIT', 'SUBMITTED_DATE'],
        'visa_class': ['VISA_CLASS', 'PROGRAM'],
        'soc_code': ['SOC_CODE', 'LCA_CASE_SOC_CODE', 'JOB_CODE'],
        'soc_title': ['SOC_TITLE', 'SOC_NAME', 'LCA_CASE_SOC_NAME', 'OCCUPATIONAL_TITLE'],
        'job_title': ['JOB_TITLE', 'LCA_CASE_JOB_TITLE'],
        'emp_name': ['EMPLOYER_NAME', 'LCA_CASE_EMPLOYER_NAME', 'NAME'],
        'emp_id': ['EMPLOYER_FEIN'],
        'industry': ['NAICS_CODE', 'LCA_CASE_NAICS_CODE'],
        'emp_city': ['EMPLOYER_CITY', 'LCA_CASE_EMPLOYER_CITY', 'CITY'],
        'emp_state': ['EMPLOYER_STATE', 'LCA_CASE_EMPLOYER_STATE', 'STATE'],
        'emp_zip': ['EMPLOYER_POSTAL_CODE', 'LCA_CASE_EMPLOYER_POSTAL_CODE', 'POSTAL_CODE'],
        'employer_address': ['EMPLOYER_ADDRESS1', 'EMPLOYER_ADDRESS', 'LCA_CASE_EMPLOYER_ADDRESS', 'ADDRESS1'],
        'worksite_city': ['WORKSITE_CITY', 'LCA_CASE_WORKLOC1_CITY', 'CITY_1', 'WORK_LOCATION_CITY1'],
        'worksite_state': ['WORKSITE_STATE', 'LCA_CASE_WORKLOC1_STATE', 'STATE_1', 'WORK_LOCATION_STATE1'],
        'worksite_zip': ['WORKSITE_POSTAL_CODE'],
        'wage_offer': ['WAGE_RATE_OF_PAY_FROM', 'WAGE_RATE_OF_PAY_FROM_1', 'LCA_CASE_WAGE_RATE_FROM', 'WAGE_RATE_1'],
        'wage_unit': ['WAGE_UNIT_OF_PAY', 'WAGE_UNIT_OF_PAY_1', 'LCA_CASE_WAGE_RATE_UNIT', 'RATE_PER_1', 'PW_UNIT_1'],
        'full_time': ['FULL_TIME_POSITION', 'FULL_TIME_POS'],
        'begin_date': ['BEGIN_DATE', 'EMPLOYMENT_START_DATE', 'LCA_CASE_EMPLOYMENT_START_DATE', 'PERIOD_OF_EMPLOYMENT_START_DATE'],
        'end_date': ['END_DATE', 'EMPLOYMENT_END_DATE', 'LCA_CASE_EMPLOYMENT_END_DATE', 'PERIOD_OF_EMPLOYMENT_END_DATE']
    }

    # Function to find the first matching column name
    def find_column(possible_names, df_columns):
        for name in possible_names:
            if name in df_columns:
                return name
        return None

    # Map actual columns found in the dataset
    print("\nMapping columns...")
    actual_columns = {}
    for standard_name, possible_names in column_mappings.items():
        found = find_column(possible_names, df.columns)
        if found:
            actual_columns[found] = standard_name
            print(f"  ✓ Found '{standard_name}' as '{found}'")
        else:
            print(f"  ✗ Could not find '{standard_name}'")

    # Step 1: Filter for H-1B visa class
    print("\nFiltering for H-1B visa types...")
    visa_col = find_column(column_mappings['visa_class'], df.columns)
    if visa_col:
        # Handle different H-1B notations
        df = df[df[visa_col].astype(str).str.upper().str.contains('H-1B|H1B', na=False)].copy()
        print(f"After visa filter: {len(df)} rows")
    else:
        print("Warning: VISA_CLASS column not found, skipping visa filter")

    # Step 2: Filter for Certified/Approved applications
    print("\nFiltering for Certified/Approved applications...")
    status_col = find_column(column_mappings['case_status'], df.columns)
    if status_col:
        df = df[df[status_col].astype(str).str.upper().isin(['CERTIFIED'])].copy()
        print(f"After status filter: {len(df)} rows")
    else:
        print("Warning: STATUS column not found, skipping status filter")

    # Step 3: Select and rename columns
    print("\nExtracting available columns...")
    available_cols = [col for col in actual_columns.keys() if col in df.columns]
    df_clean = df[available_cols].copy()
    df_clean = df_clean.rename(columns=actual_columns)

    # Step 4: Add derived columns
    print("\nAdding derived columns...")

    # Extract major group from SOC code (first 2 digits)
    if 'soc_code' in df_clean.columns:
        df_clean['major_group'] = df_clean['soc_code'].astype(str).str.replace('-', '').str[:2]

    # Calculate fiscal year from received date or decision date
    date_col = None
    if 'received_date' in df_clean.columns:
        date_col = 'received_date'
    elif 'decision_date' in df_clean.columns:
        date_col = 'decision_date'

    if date_col:
        df_clean[date_col] = pd.to_datetime(df_clean[date_col], errors='coerce')
        df_clean['fiscal_year'] = df_clean[date_col].apply(
            lambda x: x.year if pd.notna(x) and x.month < 10 else (x.year + 1 if pd.notna(x) else None)
        )
        # Convert date back to string for CSV
        df_clean[date_col] = df_clean[date_col].dt.strftime('%Y-%m-%d')

    # Clean wage data - remove dollar signs and convert to numeric
    if 'wage_offer' in df_clean.columns:
        df_clean['wage_offer'] = df_clean['wage_offer'].astype(str).str.replace('$', '').str.replace(',', '')
        df_clean['wage_offer'] = pd.to_numeric(df_clean['wage_offer'], errors='coerce')

    # Reorder columns in a logical way (only include columns that exist)
    preferred_order = [
        'case_number', 'case_status', 'visa_class', 'decision_date', 'received_date', 'fiscal_year',
        'employer_fein', 'employer_name', 'industry', 'employer_address',
        'employer_city', 'employer_state', 'employer_zip',
        'worksite_city', 'worksite_state', 'worksite_zip',
        'job_title', 'soc_code', 'soc_title', 'major_group',
        'wage_offer', 'wage_unit', 'full_time', 'begin_date', 'end_date'
    ]

    # Only include columns that exist
    final_columns = [col for col in preferred_order if col in df_clean.columns]
    # Add any remaining columns not in preferred order
    remaining = [col for col in df_clean.columns if col not in final_columns]
    final_columns.extend(remaining)

    df_clean = df_clean[final_columns]

    # Step 5: Save to CSV
    print(f"\nSaving cleaned data to {output_file}...")
    df_clean.to_csv(output_file, index=False)

    # Summary statistics
    print("\n" + "="*60)
    print("CLEANING SUMMARY")
    print("="*60)
    print(f"Total records: {len(df_clean):,}")
    print(f"Columns retained: {len(df_clean.columns)}")
    if 'employer_name' in df_clean.columns:
        print(f"Unique employers: {df_clean['employer_name'].nunique():,}")
    if 'soc_code' in df_clean.columns:
        print(f"Unique occupations (SOC codes): {df_clean['soc_code'].nunique():,}")
    if 'fiscal_year' in df_clean.columns:
        print(f"Fiscal years: {sorted(df_clean['fiscal_year'].dropna().unique().astype(int).tolist())}")
    print(f"\nFile saved: {output_file}")
    print("="*60)

    return df_clean


if __name__ == "__main__":
    # Usage example
    input_file = "LCA_Disclosure_Data_FY2024_Q4.xlsx"  # input file
    output_file = "large_cleaned_h1b_test_2024.csv"
    df_cleaned = clean_h1b_dataset(input_file, output_file)
    print("\nData cleaning completed successfully!")
