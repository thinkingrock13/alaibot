import sqlite3
import pandas as pd

df = pd.read_csv("ParameterData.csv")
conn = sqlite3.connect("water_quality.db")
df.to_sql("water_readings", conn, if_exists='append', index=False)
conn.close()
