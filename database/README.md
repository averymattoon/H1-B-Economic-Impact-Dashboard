# Database and data pipeline

Setup, the order to run the scripts, and the data-processing notes are in the
[main README](../README.md#rebuilding-the-data-from-scratch).

- `schema.sql`: tables and core materialized views
- `data_cleaning.py`, `clean_all.py`, `fix_cleaned.py`: clean the raw DOL files
- `load_data_fast.py`: bulk loader (run with `PYTHONHASHSEED=0`)
- `employer_metrics.sql`, `COVID_feature.sql`, `company_exposure.sql`: summary views
- `export_static.py`: writes the dashboard's JSON to `frontend/data/`
- `fix_*.sql`, `load_data.py`, `load_remaining_data.py`: earlier versions kept for reference
