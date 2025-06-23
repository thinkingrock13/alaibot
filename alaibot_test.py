#cd C:\Users\psacs\AppData\Local\Programs\Python\Python39\Scripts
#streamlit run "C:/Users/psacs/Desktop/Subiksha/AlaiBot/alaibot/alaibot_test.py"
import streamlit as st
import openai
import os
from dotenv import load_dotenv
from supabase import create_client
import pandas as pd
import matplotlib.pyplot as plt

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Connect to Supabase
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Page settings
st.set_page_config(page_title="Alaibot: Water Quality Assistant 💧", layout="wide")
st.title("💧 Alaibot - Water Treatment Chatbot & Anomaly Dashboard")

# --- CHATBOT SECTION ---
st.header("🤖 Chat with Alaibot")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "input" not in st.session_state:
    st.session_state.input = ""

def handle_input():
    user_input = st.session_state.input
    if not user_input:
        return

    st.session_state.chat_history.append({"role": "user", "content": user_input})

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=st.session_state.chat_history
        )
        reply = response.choices[0].message.content
    except Exception as e:
        reply = f"Error from OpenAI API: {e}"

    st.session_state.chat_history.append({"role": "assistant", "content": reply})

    try:
        supabase.table("chat_logs").insert({
            "user_input": user_input,
            "bot_response": reply
        }).execute()
    except Exception as e:
        st.error(f"Error logging chat to database: {e}")

    st.session_state.input = ""

# Chat input
st.text_input("You:", key="input", on_change=handle_input)

# Chat display
for msg in st.session_state.chat_history:
    role = "You" if msg['role'] == "user" else "Bot"
    st.markdown(f"**{role}:** {msg['content']}")

# --- ANOMALY DASHBOARD SECTION ---
st.divider()
st.header("📊 Water Quality Anomaly Dashboard")

# Fetch data from Supabase
response = supabase.table("water_readings").select("*").execute()

if not response.data:
    st.error("No data found in 'water_readings' table.")
    st.stop()

df = pd.DataFrame(response.data)
df['Timestamp'] = pd.to_datetime(df['Timestamp'])
df = df.sort_values('Timestamp')

# Data filter
if st.checkbox("Show only anomalies"):
    df_display = df[df['Anomaly_Status'] != 'Normal']
else:
    df_display = df

# Table
st.subheader("Water Quality Data")
st.dataframe(df_display)

# Reduce font and graph size
plt.rcParams.update({
    'font.size': 6,
    'axes.titlesize': 10,
    'axes.labelsize': 9,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'legend.fontsize': 8
})

# Plot parameters
parameters = ['pH', 'Turbidity', 'Temperature', 'Chlorine', 'Coagulant_Dosing', 'Flow_Rate']
for param in parameters:
    st.subheader(f"{param} Over Time")
    fig, ax = plt.subplots(figsize=(5, 2.5))
    ax.plot(df['Timestamp'], df[param], label=param, color='blue')

    anomaly_indices = df[df['Anomaly_Status'].str.contains(param, case=False, na=False)].index
    ax.scatter(df.loc[anomaly_indices, 'Timestamp'], df.loc[anomaly_indices, param],
               color='red', label='Anomaly', zorder=5)

    ax.set_xlabel("Time")
    ax.set_ylabel(param)
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

# CSV Download
st.download_button("Download CSV", df.to_csv(index=False), "anomaly_data.csv", "text/csv")
