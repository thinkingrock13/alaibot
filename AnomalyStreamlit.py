#in cmd, run: streamlit run "C:/Users/psacs/Desktop/Subiksha/AlaiBot/alaibot/AnomalyStreamlit.py"

import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt

conn = sqlite3.connect(r'C:\Users\psacs\Desktop\Subiksha\AlaiBot\alaibot\water_quality.db')
df = pd.read_sql_query("SELECT * FROM water_readings", conn)
conn.close()

df['Timestamp'] = pd.to_datetime(df['Timestamp'])
df = df.sort_values('Timestamp')

st.title("Water Quality Anomaly Dashboard")

if st.checkbox("Show only anomalies"):
    df_display = df[df['Anomaly_Status'] != 'Normal']
else:
    df_display = df

st.subheader("Water Quality Data")
st.dataframe(df_display)

parameters = ['pH', 'Turbidity', 'Temperature', 'Chlorine', 'Coagulant_Dosing', 'Flow_Rate']
pcheck = parameters+['flow','Coagulant']
for param in parameters:
    st.subheader(f"{param} Over Time")
    
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(df['Timestamp'], df[param], label=param, color='blue')

    anomaly_indices = df[df['Anomaly_Status'].str.contains(param, case=False, na=False)].index
    
    ax.scatter(df.loc[anomaly_indices, 'Timestamp'], df.loc[anomaly_indices, param], color='red', label='Anomaly', zorder=5)
    
    ax.set_xlabel("Time")
    ax.set_ylabel(param)
    ax.legend()
    ax.grid(True)
    
    st.pyplot(fig)

st.download_button("Download CSV", df.to_csv(index=False), "anomaly_data.csv", "text/csv")
