
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

connection = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    port=os.getenv("DB_PORT")
)

try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM fact_admission;")
        result = cursor.fetchone()[0]
        print(f"Total admissions: {result}")
finally:
    connection.close()