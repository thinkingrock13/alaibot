import sqlite3
import pandas as pd

# Path to your SQLite DB
db_path = "water_quality.db"

# Connect to SQLite DB
conn = sqlite3.connect(db_path)

# Get all table names
tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
print("Tables found:", tables)

# Export each table to CSV (optional)
for table in tables["name"]:
    df = pd.read_sql(f"SELECT * FROM {table}", conn)
    df.to_csv(f"{table}.csv", index=False)
    print(f"Exported {table}.csv")

conn.close()
