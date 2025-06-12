import  pandas as pd
import sqlite3
df = pd.read_csv('ParameterData.csv')

df['Flow_Change'] = df['Flow_Rate'].diff().abs()
r=[]
i=''
an = ''
def detect_anomaly(row):
    r=[]
    an=''
    if row['pH'] < 6.5 or row['pH'] > 8.5:
        r+=['pH anomaly']
    if row['Turbidity'] > 0.6:
        r+=['High turbidity']
    if row['Temperature'] < 15 or row['Temperature'] > 30:
        r+=['Temperature not optimal']
    if row['Chlorine'] < 0.5 or row['Chlorine'] > 1.5:
        r+=['Chlorine levels not optimal']
    if row['Coagulant_Dosing'] < 8 or row['Coagulant_Dosing'] > 10:
        r+=['Coagulant_Dosing not optimal']
    if row['Flow_Change'] > 10:
        r+=['Sudden change in Flow_Rate']
    for i in range(len(r)):
        if i==(len(r)-1):
            an+=(r[i])
        else:
            an+=(r[i]+", ")
    if an=='':
        an+="Normal"
    return an       

df['Anomaly_Status'] = df.apply(detect_anomaly, axis=1)

conn = sqlite3.connect('water_quality.db')
df.to_sql('water_readings', conn, if_exists='replace', index=False)
