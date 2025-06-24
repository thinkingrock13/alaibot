#cd C:\Users\psacs\AppData\Local\Programs\Python\Python39\Scripts
#streamlit run "C:/Users/psacs/Desktop/Subiksha/AlaiBot/alaibot/alaibot_app - Copy.py"

import streamlit as st
import openai
import os
from dotenv import load_dotenv
from supabase import create_client
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Connect to Supabase
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Page config
st.set_page_config(page_title="Alaibot", layout="wide")

# Apply updated blue water-themed style
st.markdown("""
<style>
body, .stApp {
    background-color: #e1f5fe;
    font-family: 'Segoe UI', sans-serif;
}
.st-emotion-cache-10trblm {
    color: #01579b;
    font-size: 36px;
    font-weight: bold;
    text-shadow: 1px 1px 2px #4fc3f7;
}
.stTextInput > div > div > input {
    background-color: #ffffff;
    border: 2px solid #0288d1;
    border-radius: 10px;
    color: #0277bd;
}
.chat-bubble-user {
    background-color: #b3e5fc;
    padding: 10px;
    border-radius: 15px;
    margin-bottom: 5px;
    width: fit-content;
    max-width: 70%;
    align-self: flex-start;
}
.chat-bubble-bot {
    background-color: #81d4fa;
    padding: 10px;
    border-radius: 15px;
    margin-bottom: 5px;
    width: fit-content;
    max-width: 70%;
    align-self: flex-end;
}
.chat-container {
    display: flex;
    flex-direction: column;
    height: 400px;
    overflow-y: auto;
    scroll-behavior: smooth;
}
section[data-testid="stSidebar"] {
    background-color: #b2ebf2 !important;
}
div[data-baseweb="radio"] {
    font-family: 'Segoe UI', sans-serif;
    font-size: 18px;
    color: #01579b;
}
div[data-baseweb="radio"] > div {
    background-color: #e1f5fe;
    border-radius: 10px;
    padding: 8px;
    margin-bottom: 5px;
}
div[data-baseweb="radio"] label {
    color: #01579b !important;
    font-weight: bold;
}
div[data-baseweb="radio"] > div:hover {
    background-color: #b3e5fc;
    transition: 0.2s;
}
.stDownloadButton button {
    background-color: #0288d1;
    color: white;
    border-radius: 10px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_water_data():
    response = supabase.table("water_readings").select("*").execute()
    df = pd.DataFrame(response.data)
    if not df.empty:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df = df.sort_values('Timestamp')
    return df

water_df = load_water_data()

# Helpers
def wants_graph(text):
    keywords = ['trend', 'show', 'graph', 'readings']
    return any(k in text.lower() for k in keywords)

def compute_correlation(df, param1, param2):
    try:
        df = df.dropna(subset=[param1, param2])
        return round(df[param1].corr(df[param2]), 3)
    except Exception as e:
        return f"Error computing correlation: {e}"

def extract_query_entities(text):
    parameters = ['pH', 'Turbidity', 'Temperature', 'Chlorine', 'Flow_Rate', 'Coagulant_Dosing']
    detected = [p for p in parameters if p.lower() in text.lower()]
    time_filter = None
    if "yesterday" in text.lower():
        time_filter = datetime.now() - timedelta(days=1)
    elif "last 24" in text.lower():
        time_filter = datetime.now() - timedelta(hours=24)
    elif "week" in text.lower():
        time_filter = datetime.now() - timedelta(days=7)
    return detected, time_filter

# Sidebar
menu = st.sidebar.radio("Navigate", ["Chatbot", "Anomaly Dashboard"])

if menu == "Chatbot":
    st.title("Alaibot - Water Treatment Chatbot")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_input = st.chat_input("You")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        params, since = extract_query_entities(user_input)
        bot_reply = ""

        # Handle root cause diagnosis for anomalies with correlations
        if "cause" in user_input.lower() and "anomal" in user_input.lower() and params:
            param = params[0]
            anomalies = water_df[water_df['Anomaly_Status'].str.contains(param, case=False, na=False)]
            if since:
                anomalies = anomalies[anomalies['Timestamp'] >= since]
            if anomalies.empty:
                bot_reply = f"No {param} anomalies found in that timeframe."
            else:
                bot_reply = f"Found {len(anomalies)} {param} anomalies.\n\nPotential correlations:\n"
                for op in ['pH', 'Turbidity', 'Temperature', 'Chlorine', 'Flow_Rate', 'Coagulant_Dosing']:
                    if op != param:
                        corr = compute_correlation(anomalies, param, op)
                        bot_reply += f"- {param} vs {op}: correlation = {corr}\n"

        # Handle cross-parameter correlation questions (e.g., Does temperature affect pH anomalies?)
        elif "affect" in user_input.lower() and len(params) == 2:
            p1, p2 = params[0], params[1]
            corr = compute_correlation(water_df, p1, p2)
            bot_reply = f"The correlation between {p1} and {p2} is approximately {corr}."
            if wants_graph(user_input):
                fig, ax = plt.subplots(figsize=(6, 4))
                ax.scatter(water_df[p1], water_df[p2], alpha=0.5, color='#0288d1')
                ax.set_xlabel(p1)
                ax.set_ylabel(p2)
                ax.set_title(f"{p1} vs {p2} Correlation")
                st.pyplot(fig)

        # Handle queries about anomalies in a time frame, even without graph keywords
        elif "anomal" in user_input.lower() and since:
            anomaly_rows = water_df[water_df['Anomaly_Status'].str.lower() != 'normal']
            anomaly_rows = anomaly_rows[anomaly_rows['Timestamp'] >= since]
            if anomaly_rows.empty:
                bot_reply = "No anomalies detected in the selected timeframe."
            else:
                bot_reply = f"Found {len(anomaly_rows)} anomalies in the selected timeframe."

        # Show anomaly graphs if requested explicitly
        elif "anomaly" in user_input.lower() and wants_graph(user_input):
            anomaly_rows = water_df[water_df['Anomaly_Status'].str.lower() != 'normal']
            if since:
                anomaly_rows = anomaly_rows[anomaly_rows['Timestamp'] >= since]
            if anomaly_rows.empty:
                bot_reply = "No anomalies detected in the selected timeframe."
            else:
                bot_reply = f"Found {len(anomaly_rows)} anomalies. Displaying pH anomaly chart..."
                st.line_chart(anomaly_rows.set_index('Timestamp')['pH'])

        # Show parameter trend graphs if requested
        elif params and wants_graph(user_input):
            param = params[0]
            data_to_plot = water_df.copy()
            if since:
                data_to_plot = data_to_plot[data_to_plot['Timestamp'] >= since]
            bot_reply = f"Here's the trend for {param}"
            fig, ax = plt.subplots(figsize=(8, 3))
            ax.plot(data_to_plot['Timestamp'], data_to_plot[param], color='#0288d1')
            ax.set_title(f"{param} Over Time")
            ax.set_xlabel("Time")
            ax.set_ylabel(param)
            ax.grid(True)
            st.pyplot(fig)

        # Fallback to OpenAI GPT-3.5 turbo for other questions
        else:
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=st.session_state.chat_history
                )
                bot_reply = response.choices[0].message.content
            except Exception as e:
                bot_reply = f"OpenAI API Error: {e}"

        st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})

        try:
            supabase.table("chat_logs").insert({
                "user_input": user_input,
                "bot_response": bot_reply
            }).execute()
        except Exception as e:
            st.error(f"Error logging chat to DB: {e}")

    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in st.session_state.chat_history:
        role = "You" if msg['role'] == "user" else "Bot"
        bubble_class = "chat-bubble-user" if role == "You" else "chat-bubble-bot"
        st.markdown(f'<div class="{bubble_class}"><b>{role}:</b> {msg["content"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

elif menu == "Anomaly Dashboard":
    st.title("Water Quality Anomaly Dashboard")

    if water_df.empty:
        st.warning("No data found in water_readings table.")
        st.stop()

    show_anomalies_only = st.checkbox("Show only anomalies")
    display_df = water_df if not show_anomalies_only else water_df[water_df['Anomaly_Status'].str.lower() != 'normal']
    st.dataframe(display_df)

    for param in ['pH', 'Turbidity', 'Temperature', 'Chlorine', 'Coagulant_Dosing', 'Flow_Rate']:
        st.subheader(f"{param} Over Time")
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.plot(water_df['Timestamp'], water_df[param], color='#0288d1', label='All Data')
        anomaly_points = water_df[water_df['Anomaly_Status'].str.contains(param, case=False, na=False)]
        ax.scatter(anomaly_points['Timestamp'], anomaly_points[param],
                   color='red', label='Anomaly', zorder=5)
        ax.set_xlabel("Time")
        ax.set_ylabel(param)
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)

    st.download_button("Download CSV", display_df.to_csv(index=False), "anomaly_data.csv", "text/csv")
