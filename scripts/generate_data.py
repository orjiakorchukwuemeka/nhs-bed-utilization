
from pathlib import Path
import pandas as pd
import numpy as np

# 1. Set a fixed random seed so results are reproducible
rng = np.random.default_rng(42)

# 2. Identify the main project folder
PROJECT_DIR = Path(__file__).resolve().parent.parent

# 3. Define where generated datasets will be saved
RAW_DATA_DIR = PROJECT_DIR / "data" / "raw"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

print("Project folder:", PROJECT_DIR)
print("Raw data folder:", RAW_DATA_DIR)
print("Dataset generation setup is ready.")


# 4. Create a synthetic ward dataset
wards = pd.DataFrame({
    "ward_id": [1, 2, 3, 4, 5],
    "ward_name": [
        "North Ward",
        "South Ward",
        "East Ward",
        "West Ward",
        "Central Ward"
    ],
    "specialty": [
        "General Medicine",
        "Surgery",
        "Orthopaedics",
        "Cardiology",
        "General Medicine"
    ]
})

# 5. Save the dataset as a CSV file
wards.to_csv(RAW_DATA_DIR / "dim_ward.csv", index=False)

# 6. Display the generated data
print("\nWard dataset created successfully.")
print(wards)

# 7. Create a synthetic bed dataset
beds = pd.DataFrame({
    "bed_id": range(1, 101),
    "ward_id": np.repeat([1, 2, 3, 4, 5], 20),
    "bed_type": ["Standard"] * 100
})

# 8. Save the dataset
beds.to_csv(RAW_DATA_DIR / "dim_bed.csv", index=False)

# 9. Display a preview
print("\nBed dataset created successfully.")
print(beds.head())
print("Total beds:", len(beds))

# 10. Generate daily bed-status records for 90 days
dates = pd.date_range("2026-01-01", periods=90, freq="D")

daily_records = pd.MultiIndex.from_product(
    [beds["bed_id"], dates],
    names=["bed_id", "record_date"]
).to_frame(index=False)

# 11. Generate illustrative staffing and occupancy states
daily_records["is_staffed"] = rng.choice(
    [True, False], size=len(daily_records), p=[0.90, 0.10]
)

daily_records["is_occupied"] = (
    daily_records["is_staffed"]
    & (rng.random(len(daily_records)) < 0.80)
)

# 12. Save the dataset
daily_records.to_csv(
    RAW_DATA_DIR / "fact_bed_daily.csv", index=False
)

# 13. Display a preview and validation counts
print("\nDaily bed-status dataset created successfully.")
print(daily_records.head())
print("Total daily records:", len(daily_records))
print("Occupied records:", daily_records["is_occupied"].sum())
# 14. Validate daily bed-status data
print("\n--- Data Quality Checks ---")

print(
    "Duplicate bed-date records:",
    daily_records.duplicated(["bed_id", "record_date"]).sum()
)

print(
    "Occupied but unstaffed beds:",
    (
        daily_records["is_occupied"]
        & ~daily_records["is_staffed"]
    ).sum()
)

print(
    "Missing values:",
    daily_records.isna().sum().sum()
)

print("Validation complete.")

# 15. Generate synthetic admission records
number_of_admissions = 1200

admissions = pd.DataFrame({
    "admission_id": range(1, number_of_admissions + 1),
    "ward_id": rng.integers(1, 6, size=number_of_admissions),
    "admission_datetime": (
        pd.Timestamp("2026-01-01")
        + pd.to_timedelta(
            rng.integers(0, 90 * 24, size=number_of_admissions),
            unit="h"
        )
    ),
    "admission_type": rng.choice(
        ["Emergency", "Elective", "Transfer"],
        size=number_of_admissions,
        p=[0.60, 0.25, 0.15]
    )
})

# 16. Save the admission dataset
admissions.to_csv(
    RAW_DATA_DIR / "fact_admission.csv", index=False
)

# 17. Preview and validate
print("\nAdmission dataset created successfully.")
print(admissions.head())
print("Total admissions:", len(admissions))
print("Missing values:", admissions.isna().sum().sum())
print(
    "Invalid ward IDs:",
    (~admissions["ward_id"].isin(wards["ward_id"])).sum()
)
# 18. Generate synthetic discharge records
discharged_admissions = admissions.sample(
    n=1000, random_state=42
).copy()

discharged_admissions = discharged_admissions.sort_values(
    "admission_id"
).reset_index(drop=True)

discharge_dates = (
    discharged_admissions["admission_datetime"]
    + pd.to_timedelta(
        rng.integers(1, 15, size=1000),
        unit="D"
    )
)

discharges = pd.DataFrame({
    "discharge_id": range(1, 1001),
    "admission_id": discharged_admissions["admission_id"],
    "discharge_datetime": discharge_dates,
    "discharge_destination": rng.choice(
        ["Home", "Care facility", "Another hospital"],
        size=1000,
        p=[0.80, 0.10, 0.10]
    ),
    "delay_reason": rng.choice(
        ["None recorded", "Transport", "Awaiting care package",
         "Medication", "Other"],
        size=1000,
        p=[0.60, 0.12, 0.12, 0.08, 0.08]
    )
})

# 19. Save the discharge dataset
discharges.to_csv(
    RAW_DATA_DIR / "fact_discharge.csv", index=False
)

# 20. Preview and validate
print("\nDischarge dataset created successfully.")
print(discharges.head())
print("Total discharges:", len(discharges))
print(
    "Duplicate admission IDs:",
    discharges["admission_id"].duplicated().sum()
)
print(
    "Invalid admission IDs:",
    (~discharges["admission_id"].isin(
        admissions["admission_id"]
    )).sum()
)
print(
    "Discharges before admissions:",
    (
        discharges["discharge_datetime"].values
        < discharged_admissions["admission_datetime"].values
    ).sum()
)

# 21. Generate synthetic patient-flow events
number_of_events = 600

# Keep only admissions with enough time before discharge
eligible_admissions = admissions.merge(
    discharges[["admission_id", "discharge_datetime"]],
    on="admission_id",
    how="left"
)

eligible_admissions = eligible_admissions[
    eligible_admissions["discharge_datetime"].isna()
    | (
        eligible_admissions["discharge_datetime"]
        > eligible_admissions["admission_datetime"]
        + pd.Timedelta(hours=1)
    )
].copy()

# Sample admissions for the flow events
flow_admissions = eligible_admissions.sample(
    n=number_of_events,
    random_state=24
).reset_index(drop=True)

from_wards = flow_admissions["ward_id"].to_numpy()

# Choose a different destination ward for each event
to_wards = np.array([
    rng.choice([w for w in range(1, 6) if w != source])
    for source in from_wards
])

# Generate a transfer time after admission
event_datetimes = []

for _, row in flow_admissions.iterrows():
    admission_time = row["admission_datetime"]
    discharge_time = row["discharge_datetime"]

    if pd.notna(discharge_time):
        latest_time = discharge_time - pd.Timedelta(hours=1)
    else:
        latest_time = admission_time + pd.Timedelta(hours=72)

    available_hours = max(
        1,
        int((latest_time - admission_time).total_seconds() // 3600)
    )

    hours_after_admission = int(
        rng.integers(1, available_hours + 1)
    )

    event_datetimes.append(
        admission_time + pd.Timedelta(hours=hours_after_admission)
    )

flow_events = pd.DataFrame({
    "event_id": range(1, number_of_events + 1),
    "admission_id": flow_admissions["admission_id"],
    "from_ward_id": from_wards,
    "to_ward_id": to_wards,
    "event_datetime": event_datetimes,
    "event_type": "Ward Transfer"
})

# 22. Save the patient-flow dataset
flow_events.to_csv(
    RAW_DATA_DIR / "fact_patient_flow.csv",
    index=False
)

# 23. Validate patient-flow records
print("\nPatient-flow dataset created successfully.")
print("Total flow events:", len(flow_events))

print(
    "Invalid admission IDs:",
    (~flow_events["admission_id"].isin(
        admissions["admission_id"]
    )).sum()
)

print(
    "Transfers to the same ward:",
    (flow_events["from_ward_id"] == flow_events["to_ward_id"]).sum()
)

print(
    "Events before admission:",
    (
        flow_events.merge(
            admissions[["admission_id", "admission_datetime"]],
            on="admission_id"
        )["event_datetime"]
        <
        flow_events.merge(
            admissions[["admission_id", "admission_datetime"]],
            on="admission_id"
        )["admission_datetime"]
    ).sum()
)

flow_with_discharge = flow_events.merge(
    discharges[["admission_id", "discharge_datetime"]],
    on="admission_id",
    how="inner"
)

print(
    "Events after discharge:",
    (
        flow_with_discharge["event_datetime"]
        >= flow_with_discharge["discharge_datetime"]
    ).sum()
)

print("Patient-flow validation complete.")