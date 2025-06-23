from supabase import create_client, Client
import pandas as pd

url = "https://ywpwlanvcsqvkhglreks.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl3cHdsYW52Y3NxdmtoZ2xyZWtzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk5NDY2MTksImV4cCI6MjA2NTUyMjYxOX0.wSFxVZCyj-FnXlzipo9dH_uXg453_odlf9oUi5OHLEM"
supabase: Client = create_client(url, key)

# Example: upload data from CSV
df = pd.read_csv("water_readings.csv")
data = df.to_dict(orient="records")

for row in data:
    supabase.table("water_readings").insert(row).execute()
