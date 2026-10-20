CREATE TABLE dim_ward (
    ward_id INTEGER PRIMARY KEY,
    ward_name VARCHAR(100) NOT NULL,
    specialty VARCHAR(100) NOT NULL
);

INSERT INTO dim_ward (ward_id, ward_name, specialty)
VALUES
    (1, 'North Ward', 'General Medicine'),
    (2, 'South Ward', 'Surgery'),
    (3, 'East Ward', 'Orthopaedics'),
    (4, 'West Ward', 'Cardiology'),
    (5, 'Central Ward', 'General Medicine');

	
SELECT *
FROM dim_ward
ORDER BY ward_id;

CREATE TABLE dim_bed (
    bed_id INTEGER PRIMARY KEY,
    ward_id INTEGER NOT NULL REFERENCES dim_ward(ward_id),
    bed_type VARCHAR(50) NOT NULL
);


INSERT INTO dim_bed (bed_id, ward_id, bed_type)
SELECT
    bed_id,
    ((bed_id - 1) / 20) + 1,
    'Standard'
FROM generate_series(1, 100) AS bed_id;


SELECT
    w.ward_name,
    COUNT(b.bed_id) AS total_beds
FROM dim_ward w
JOIN dim_bed b ON w.ward_id = b.ward_id
GROUP BY w.ward_name
ORDER BY w.ward_name;


CREATE TABLE fact_bed_daily (
    bed_id INTEGER NOT NULL REFERENCES dim_bed(bed_id),
    record_date DATE NOT NULL,
    is_staffed BOOLEAN NOT NULL,
    is_occupied BOOLEAN NOT NULL,
    PRIMARY KEY (bed_id, record_date),
    CHECK (is_occupied = FALSE OR is_staffed = TRUE)
);


SELECT
    COUNT(*) AS total_records,
    COUNT(DISTINCT bed_id) AS unique_beds,
    COUNT(DISTINCT record_date) AS unique_dates,
    SUM(CASE WHEN is_occupied THEN 1 ELSE 0 END) AS occupied_records
FROM fact_bed_daily;


CREATE TABLE fact_admission (
    admission_id INTEGER PRIMARY KEY,
    ward_id INTEGER NOT NULL REFERENCES dim_ward(ward_id),
    admission_datetime TIMESTAMP NOT NULL,
    admission_type VARCHAR(50) NOT NULL
);

SELECT
    COUNT(*) AS total_admissions,
    COUNT(DISTINCT admission_id) AS unique_admissions,
    COUNT(*) FILTER (
        WHERE ward_id NOT IN (
            SELECT ward_id FROM dim_ward
        )
    ) AS invalid_ward_ids
FROM fact_admission;


CREATE TABLE fact_discharge (
    discharge_id INTEGER PRIMARY KEY,
    admission_id INTEGER NOT NULL UNIQUE
        REFERENCES fact_admission(admission_id),
    discharge_datetime TIMESTAMP NOT NULL,
    discharge_destination VARCHAR(100) NOT NULL,
    delay_reason VARCHAR(150) NOT NULL
);



SELECT
    COUNT(*) AS total_discharges,
    COUNT(DISTINCT d.admission_id) AS unique_admissions,
    COUNT(*) FILTER (
        WHERE d.discharge_datetime < a.admission_datetime
    ) AS discharges_before_admission
FROM fact_discharge d
JOIN fact_admission a
    ON d.admission_id = a.admission_id;


CREATE TABLE fact_patient_flow (
    event_id INTEGER PRIMARY KEY,
    admission_id INTEGER NOT NULL
        REFERENCES fact_admission(admission_id),
    from_ward_id INTEGER REFERENCES dim_ward(ward_id),
    to_ward_id INTEGER NOT NULL REFERENCES dim_ward(ward_id),
    event_datetime TIMESTAMP NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    CHECK (
        from_ward_id IS NULL
        OR from_ward_id <> to_ward_id
    )
);


SELECT
    COUNT(*) AS total_events,
    COUNT(DISTINCT event_id) AS unique_events,
    COUNT(*) FILTER (
        WHERE f.from_ward_id = f.to_ward_id
    ) AS same_ward_transfers,
    COUNT(*) FILTER (
        WHERE a.admission_id IS NULL
    ) AS invalid_admission_links
FROM fact_patient_flow f
LEFT JOIN fact_admission a
    ON f.admission_id = a.admission_id;


SELECT 'dim_ward' AS table_name, COUNT(*) AS total_records
FROM dim_ward

UNION ALL

SELECT 'dim_bed', COUNT(*)
FROM dim_bed

UNION ALL

SELECT 'fact_bed_daily', COUNT(*)
FROM fact_bed_daily

UNION ALL

SELECT 'fact_admission', COUNT(*)
FROM fact_admission

UNION ALL

SELECT 'fact_discharge', COUNT(*)
FROM fact_discharge

UNION ALL

SELECT 'fact_patient_flow', COUNT(*)
FROM fact_patient_flow;

--Calculating Daily Bed Utilisation by Wards

SELECT
    w.ward_name,
    b.record_date,
    COUNT(*) FILTER (
        WHERE b.is_staffed
    ) AS staffed_beds,
    COUNT(*) FILTER (
        WHERE b.is_occupied
    ) AS occupied_beds,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE b.is_occupied
        )
        / NULLIF(
            COUNT(*) FILTER (WHERE b.is_staffed),
            0
        ),
        2
    ) AS occupancy_rate_pct
FROM fact_bed_daily b
JOIN dim_bed d
    ON b.bed_id = d.bed_id
JOIN dim_ward w
    ON d.ward_id = w.ward_id
GROUP BY
    w.ward_name,
    b.record_date
ORDER BY
    b.record_date,
    w.ward_name;

--Comparing the wards over the full 90-day period

SELECT
    w.ward_name,
    COUNT(*) FILTER (
        WHERE b.is_staffed
    ) AS staffed_bed_days,
    COUNT(*) FILTER (
        WHERE b.is_occupied
    ) AS occupied_bed_days,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE b.is_occupied
        ) / NULLIF(
            COUNT(*) FILTER (WHERE b.is_staffed),
            0
        ),
        2
    ) AS occupancy_rate_pct
FROM fact_bed_daily b
JOIN dim_bed d
    ON b.bed_id = d.bed_id
JOIN dim_ward w
    ON d.ward_id = w.ward_id
GROUP BY w.ward_name
ORDER BY occupancy_rate_pct DESC;

--To find dates with the highest occupancy across all five wards
SELECT
    record_date,
    COUNT(*) FILTER (
        WHERE is_staffed
    ) AS staffed_beds,
    COUNT(*) FILTER (
        WHERE is_occupied
    ) AS occupied_beds,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE is_occupied
        ) / NULLIF(
            COUNT(*) FILTER (WHERE is_staffed),
            0
        ),
        2
    ) AS occupancy_rate_pct
FROM fact_bed_daily
GROUP BY record_date
ORDER BY occupancy_rate_pct DESC
LIMIT 10;

--To find wards that received the most admissions.
SELECT
    w.ward_name,
    COUNT(a.admission_id) AS total_admissions
FROM fact_admission a
JOIN dim_ward w
    ON a.ward_id = w.ward_id
GROUP BY w.ward_name
ORDER BY total_admissions DESC;

--To shows where patients go after discharge
SELECT
    discharge_destination,
    COUNT(*) AS total_discharges
FROM fact_discharge
GROUP BY discharge_destination
ORDER BY total_discharges DESC;

--To estimate how many days patients stayed in hospital before discharge
SELECT
    ROUND(
        AVG(
            EXTRACT(
                EPOCH FROM (
                    d.discharge_datetime - a.admission_datetime
                )
            ) / 86400
        )::numeric,
        2
    ) AS average_length_of_stay_days
FROM fact_discharge d
JOIN fact_admission a
    ON d.admission_id = a.admission_id;

--To identify most recorded reason for discharge delay
SELECT
    delay_reason,
    COUNT(*) AS total_discharges
FROM fact_discharge
GROUP BY delay_reason
ORDER BY total_discharges DESC;

--To analyse patient transfers between wards
SELECT
    fw.ward_name AS from_ward,
    tw.ward_name AS to_ward,
    COUNT(*) AS total_transfers
FROM fact_patient_flow f
JOIN dim_ward fw
    ON f.from_ward_id = fw.ward_id
JOIN dim_ward tw
    ON f.to_ward_id = tw.ward_id
GROUP BY
    fw.ward_name,
    tw.ward_name
ORDER BY total_transfers DESC;

--To identify admissions without matching discharges
SELECT
    COUNT(*) AS total_admissions,
    COUNT(d.discharge_id) AS admissions_with_discharge,
    COUNT(*) - COUNT(d.discharge_id)
        AS admissions_without_discharge
FROM fact_admission a
LEFT JOIN fact_discharge d
    ON a.admission_id = d.admission_id;

--To check patient flow event type
SELECT
    event_type,
    COUNT(*) AS total_events
FROM fact_patient_flow
GROUP BY event_type
ORDER BY total_events DESC;

-- Checking project overall data quality
SELECT 'dim_ward' AS table_name, COUNT(*) AS total_records
FROM dim_ward
UNION ALL
SELECT 'dim_bed', COUNT(*) FROM dim_bed
UNION ALL
SELECT 'fact_bed_daily', COUNT(*) FROM fact_bed_daily
UNION ALL
SELECT 'fact_admission', COUNT(*) FROM fact_admission
UNION ALL
SELECT 'fact_discharge', COUNT(*) FROM fact_discharge
UNION ALL
SELECT 'fact_patient_flow', COUNT(*) FROM fact_patient_flow;

