#cd C:\Users\psacs\AppData\Local\Programs\Python\Python39\Scripts
#streamlit run "C:/Users/psacs/Desktop/Subiksha/AlaiBot/alaibot/AnomalyStreamlitChatbot.py"

import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

@st.cache_resource
def load_phi2_model():
    tokenizer = AutoTokenizer.from_pretrained("OpenAssistant/phi-2")
    model = AutoModelForCausalLM.from_pretrained("OpenAssistant/phi-2")
    return tokenizer, model

tokenizer = AutoTokenizer.from_pretrained("microsoft/phi-2")
model = AutoModelForCausalLM.from_pretrained("microsoft/phi-2")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

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

st.sidebar.title("Ask AlaiBot")

user_question = st.sidebar.text_input("Ask about any parameter (e.g., 'Why is turbidity high?')")

def generate_response(prompt):
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=150,
        do_sample=True,
        temperature=0.7,
        top_p=0.9,
        pad_token_id=tokenizer.eos_token_id
    )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

if user_question:
    with st.spinner("Thinking..."):
        response = generate_response(user_question)
    st.sidebar.markdown("AlaiBot says:")
    st.sidebar.write(response)
