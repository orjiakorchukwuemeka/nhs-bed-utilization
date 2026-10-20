import os
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv

# Locate the project folder and load credentials
PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env")

OUTPUT_DIR = PROJECT_DIR / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

queries = {
    "daily_occupancy.csv": """
        SELECT
            b.record_date,
            COUNT(*) FILTER (WHERE b.is_staffed) AS staffed_beds,
            COUNT(*) FILTER (WHERE b.is_occupied) AS occupied_beds,
            ROUND(
                100.0 * COUNT(*) FILTER (WHERE b.is_occupied)
                / NULLIF(COUNT(*) FILTER (WHERE b.is_staffed), 0),
                2
            ) AS occupancy_rate_pct
        FROM fact_bed_daily b
        GROUP BY b.record_date
        ORDER BY b.record_date;
    """,

    "ward_occupancy.csv": """
        SELECT
            w.ward_name,
            COUNT(*) FILTER (WHERE b.is_staffed) AS staffed_bed_days,
            COUNT(*) FILTER (WHERE b.is_occupied) AS occupied_bed_days,
            ROUND(
                100.0 * COUNT(*) FILTER (WHERE b.is_occupied)
                / NULLIF(COUNT(*) FILTER (WHERE b.is_staffed), 0),
                2
            ) AS occupancy_rate_pct
        FROM fact_bed_daily b
        JOIN dim_bed d ON b.bed_id = d.bed_id
        JOIN dim_ward w ON d.ward_id = w.ward_id
        GROUP BY w.ward_name
        ORDER BY occupancy_rate_pct DESC;
    """,

    "admissions_by_ward.csv": """
        SELECT w.ward_name, COUNT(*) AS total_admissions
        FROM fact_admission a
        JOIN dim_ward w ON a.ward_id = w.ward_id
        GROUP BY w.ward_name
        ORDER BY total_admissions DESC;
    """,

    "discharge_destinations.csv": """
        SELECT discharge_destination, COUNT(*) AS total_discharges
        FROM fact_discharge
        GROUP BY discharge_destination
        ORDER BY total_discharges DESC;
    """,

    "discharge_delay_reasons.csv": """
        SELECT delay_reason, COUNT(*) AS total_discharges
        FROM fact_discharge
        GROUP BY delay_reason
        ORDER BY total_discharges DESC;
    """,

    "ward_transfers.csv": """
        SELECT
            fw.ward_name AS from_ward,
            tw.ward_name AS to_ward,
            COUNT(*) AS total_transfers
        FROM fact_patient_flow f
        JOIN dim_ward fw ON f.from_ward_id = fw.ward_id
        JOIN dim_ward tw ON f.to_ward_id = tw.ward_id
        GROUP BY fw.ward_name, tw.ward_name
        ORDER BY total_transfers DESC;
    """
}

connection = None

try:
    connection = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT")
    )

    for filename, query in queries.items():
        df = pd.read_sql_query(query, connection)
        output_path = OUTPUT_DIR / filename
        df.to_csv(output_path, index=False)
        print(f"Exported {filename}: {len(df)} rows")

    print("All analysis exports completed successfully.")

except Exception as error:
    print("Export failed:", error)

finally:
    if connection is not None:
        connection.close()