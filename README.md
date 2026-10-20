# NHS Bed Utilisation and Patient Flow Analysis

## 1. Project Overview

This project explores hospital bed utilisation, admissions, discharges and patient flow using a fictional, synthetic hospital dataset. It demonstrates how SQL, Python, PostgreSQL and Power BI can be used to organise operational data, investigate performance indicators and communicate findings through reporting.

**Important:** All data in this project is synthetic. It does not contain real patient information or represent actual NHS hospital performance.

## 2. Business Problem

Hospital operational teams need reliable information to understand bed utilisation, ward-level demand, admissions, discharges and patient movement. Clear reporting can help identify patterns, support operational discussions and highlight areas requiring further investigation.

This project demonstrates an analytical approach to these questions using a reproducible data workflow.

## 3. Project Objectives

- Measure daily bed occupancy and staffed bed capacity.
- Compare occupancy rates across five fictional wards.
- Summarise admissions by ward.
- Examine discharge destinations and recorded discharge-delay reasons.
- Analyse recorded ward-transfer events.
- Perform data-quality checks and document analytical limitations.
- Present key indicators in an interactive Power BI dashboard.

## 4. Tools and Technologies

- **Python:** Data generation, processing and report exports.
- **Pandas and NumPy:** Data manipulation and synthetic data preparation.
- **PostgreSQL:** Relational data storage and SQL analysis.
- **SQL:** Aggregation, validation and operational metrics.
- **Power BI:** Dashboard development and visual reporting.
- **Git and GitHub:** Version control and project publication.

## 5. Dataset

The synthetic dataset covers 1 January to 31 March 2026 and includes six CSV files:

| File | Description |
|---|---|
| `dim_ward.csv` | Five fictional hospital wards |
| `dim_bed.csv` | 100 beds allocated across the wards |
| `fact_bed_daily.csv` | 9,000 daily bed-status records |
| `fact_admission.csv` | 1,200 admission records |
| `fact_discharge.csv` | 1,000 discharge records |
| `fact_patient_flow.csv` | 600 patient-flow event records |

## 6. Analytical Findings

Initial SQL analysis produced the following results from the synthetic dataset:

- **Overall bed occupancy:** approximately 79.95%.
- **Highest ward occupancy:** South Ward at 81.11%.
- **Highest recorded daily occupancy:** 94.62% on 9 January 2026.
- **Admissions:** 1,200 records.
- **Recorded discharges:** 1,000 records.
- **Admissions without a recorded discharge:** 200 records.
- **Average length of stay:** 7.79 days, based on the project's recorded admission and discharge dates.

These figures describe the generated dataset only. They should not be interpreted as real hospital performance measures.

## 7. Data Quality and Limitations

The project includes checks for missing or invalid records, ward and bed references, discharge timing, transfer events and table row counts.

A key modelling limitation is that daily bed-status records are not linked to individual admissions or patient-specific bed assignments. The transfer events are also synthetic and do not represent a fully integrated patient journey.

Consequently, this project examines several operational datasets separately. It does not establish causal relationships between admissions, transfers, discharges and daily occupancy.

## 8. Project Structure

```text
nhs_bed_utilisation/
├── data/
│   ├── raw/
│   └── processed/
├── scripts/
├── sql/
├── notebooks/
├── powerbi/
├── reports/
├── README.md
└── data_dictionary.csv
```

## 9. Reproducibility

The workflow uses Python scripts to generate the synthetic dataset, load and query data in PostgreSQL, perform SQL-based analysis and export results for Power BI.

Database credentials are stored in a local `.env` file and should never be published to GitHub. The virtual environment, credentials and other private configuration files must be excluded through `.gitignore`.

## 10. Future Improvements

- Refine the ward occupancy visualisation and dashboard layout.
- Integrate admissions, discharges and bed assignments into a coherent data model.
- Add more robust validation and automated testing.
- Improve the dashboard with clearer operational comparisons and explanatory notes.
- Explore how more realistic data could support bed-management and patient-flow decisions.

## 11. Disclaimer

This is an educational portfolio project using fictional data. It is not an official NHS report, a clinical decision-support system or evidence of actual hospital performance.
