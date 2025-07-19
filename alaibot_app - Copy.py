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
import difflib

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Connect to Supabase
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Page config
st.set_page_config(page_title="Alaibot", layout="wide")

# Apply styling
st.markdown("""<style>
body, .stApp { background-color: #e1f5fe; font-family: 'Segoe UI', sans-serif; }
.st-emotion-cache-10trblm { color: #01579b; font-size: 36px; font-weight: bold; text-shadow: 1px 1px 2px #4fc3f7; }
.stTextInput > div > div > input { background-color: #ffffff; border: 2px solid #0288d1; border-radius: 10px; color: #0277bd; }
.chat-bubble-user, .chat-bubble-bot {
    padding: 10px; border-radius: 15px; margin-bottom: 5px; width: fit-content; max-width: 70%;
}
.chat-bubble-user { background-color: #b3e5fc; align-self: flex-start; }
.chat-bubble-bot { background-color: #81d4fa; align-self: flex-end; }
.chat-container { display: flex; flex-direction: column; height: 400px; overflow-y: auto; scroll-behavior: smooth; }
section[data-testid="stSidebar"] { background-color: #b2ebf2 !important; }
div[data-baseweb="radio"] { font-family: 'Segoe UI', sans-serif; font-size: 18px; color: #01579b; }
div[data-baseweb="radio"] > div { background-color: #e1f5fe; border-radius: 10px; padding: 8px; margin-bottom: 5px; }
div[data-baseweb="radio"] label { color: #01579b !important; font-weight: bold; }
div[data-baseweb="radio"] > div:hover { background-color: #b3e5fc; transition: 0.2s; }
.stDownloadButton button { background-color: #0288d1; color: white; border-radius: 10px; font-weight: bold; }
</style>""", unsafe_allow_html=True)

@st.cache_data
def load_water_data():
    response = supabase.table("water_readings").select("*").execute()
    df = pd.DataFrame(response.data)
    if not df.empty:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df['Anomaly_Status'] = df['Anomaly_Status'].fillna("normal")
        df = df.sort_values('Timestamp')
    return df

water_df = load_water_data()

# Helpers
def wants_graph(text):
    keywords = ['trend', 'show', 'graph', 'readings', 'plot', 'visual']
    return any(k in text.lower() for k in keywords)

def compute_correlation(df, param1, param2):
    try:
        df = df.dropna(subset=[param1, param2])
        return round(df[param1].corr(df[param2]), 3)
    except Exception as e:
        return f"Error computing correlation: {e}"

def extract_query_entities(text):
    param_aliases = {
        'ph': 'pH',
        'turbidity': 'Turbidity',
        'temperature': 'Temperature',
        'chlorine': 'Chlorine',
        'flow rate': 'Flow_Rate',
        'flowrate': 'Flow_Rate',
        'coagulant': 'Coagulant_Dosing',
        'dosing': 'Coagulant_Dosing'
    }
    detected = []
    for word in text.lower().split():
        match = difflib.get_close_matches(word, param_aliases.keys(), n=1, cutoff=0.8)
        if match:
            detected.append(param_aliases[match[0]])

    time_filter = None
    if "yesterday" in text.lower():
        time_filter = datetime.now() - timedelta(days=1)
    elif "last 24" in text.lower():
        time_filter = datetime.now() - timedelta(hours=24)
    elif "week" in text.lower():
        time_filter = datetime.now() - timedelta(days=7)

    return list(set(detected)), time_filter

#For chemical dosing
@st.cache_data(ttl=300)
def fetch_chemical_dosing():
    response = supabase.table("chemical_dosing").select("*").execute()
    data = response.data
    return pd.DataFrame(data) if data else pd.DataFrame()

def format_time(time_str):
    if time_str:
        return datetime.fromisoformat(time_str.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
    return "Not recorded"

def show_chemical_dosing_module():
    st.header("🧪 Chemical Dosing Overview")
    df = fetch_chemical_dosing()
    if df.empty:
        st.warning("No data found in 'chemical_dosing'.")
        return
    df['Scheduled_Time'] = pd.to_datetime(df['Scheduled_Time'])
    df['Actual_Time'] = pd.to_datetime(df['Actual_Time'], errors='coerce')
    df['Time_Diff_Minutes'] = (df['Actual_Time'] - df['Scheduled_Time']).dt.total_seconds() / 60
    st.subheader("📋 Dosing Records")
    st.dataframe(df[['Chemical','Dose_Amount','Dose_Unit','Scheduled_Time','Actual_Time','Notes','Purpose','Time_Diff_Minutes']].sort_values('Scheduled_Time'))
    st.subheader("⚠️ Missed or Delayed Doses")
    missed = df[df['Actual_Time'].isnull()]
    delayed = df[df['Time_Diff_Minutes'] > 30]
    if missed.empty and delayed.empty:
        st.success("✅ All doses are on schedule!")
    else:
        if not missed.empty:
            st.warning("❌ Missed Doses:")
            st.dataframe(missed[['Chemical','Scheduled_Time','Notes']])
        if not delayed.empty:
            st.warning("⏱️ Delayed Doses (>30 min):")
            st.dataframe(delayed[['Chemical','Scheduled_Time','Actual_Time','Time_Diff_Minutes']])
    st.subheader("🗓️ Upcoming Scheduled Doses")
    upcoming = df[df['Scheduled_Time'] > datetime.utcnow()].sort_values('Scheduled_Time').head(5)
    if not upcoming.empty:
        for _, row in upcoming.iterrows():
            st.info(f"🧪 **{row['Chemical']}** at **{format_time(str(row['Scheduled_Time']))}** – {row['Purpose']}")
    else:
        st.info("No upcoming doses found.")
      
# Sidebar
menu = st.sidebar.radio("Navigate", ["Chatbot", "Anomaly Dashboard", "Chemical Dosing"])

if menu == "Chatbot":
    st.title("Alaibot - Water Treatment Chatbot")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_input = st.chat_input("You")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        params, since = extract_query_entities(user_input)
        bot_reply = ""

        if "cause" in user_input.lower() and "anomal" in user_input.lower() and params:
            param = params[0]
            anomalies = water_df[water_df['Anomaly_Status'].str.contains(param, case=False, na=False)]
            if since:
                anomalies = anomalies[anomalies['Timestamp'] >= since]
            if anomalies.empty:
                bot_reply = f"No {param} anomalies found."
            else:
                bot_reply = f"Found {len(anomalies)} {param} anomalies. Potential correlations:\n"
                for op in ['pH', 'Turbidity', 'Temperature', 'Chlorine', 'Flow_Rate', 'Coagulant_Dosing']:
                    if op != param:
                        corr = compute_correlation(anomalies, param, op)
                        bot_reply += f"- {param} vs {op}: correlation = {corr}\n"

        elif "affect" in user_input.lower() and len(params) == 2:
            p1, p2 = params[0], params[1]
            corr = compute_correlation(water_df, p1, p2)
            bot_reply = f"The correlation between {p1} and {p2} is approximately {corr}."
            if wants_graph(user_input):
                fig, ax = plt.subplots(figsize=(6, 4))
                ax.scatter(water_df[p1], water_df[p2], alpha=0.5, color='#0288d1')
                ax.set_xlabel(p1)
                ax.set_ylabel(p2)
                ax.set_title(f"{p1} vs {p2}")
                st.pyplot(fig)

        elif "anomal" in user_input.lower():
            anomaly_rows = water_df[water_df['Anomaly_Status'].str.lower() != 'normal']
            if since:
                anomaly_rows = anomaly_rows[anomaly_rows['Timestamp'] >= since]
            if params:
                param = params[0]
                anomaly_rows = anomaly_rows[anomaly_rows['Anomaly_Status'].str.contains(param, case=False, na=False)]

            if anomaly_rows.empty:
                bot_reply = "No anomalies detected for that parameter or timeframe."
            else:
                bot_reply = f"Found {len(anomaly_rows)} anomalies"
                if params:
                    bot_reply += f" in {param}"
                if since:
                    bot_reply += f" since {since.strftime('%Y-%m-%d %H:%M')}"
                bot_reply += ":\n\n"

                for _, row in anomaly_rows.iterrows():
                    if param in row and pd.notna(row[param]):
                        time_str = row['Timestamp'].strftime('%Y-%m-%d %H:%M')
                        value = round(row[param], 2)
                        bot_reply += f"- {value} at {time_str}\n"

                if params and wants_graph(user_input):
                    st.line_chart(anomaly_rows.set_index('Timestamp')[param])

        elif params and wants_graph(user_input):
            param = params[0]
            plot_df = water_df.copy()
            if since:
                plot_df = plot_df[plot_df['Timestamp'] >= since]
            bot_reply = f"Here’s the trend for {param}:"
            fig, ax = plt.subplots(figsize=(8, 3))
            ax.plot(plot_df['Timestamp'], plot_df[param], color='#0288d1')
            ax.set_title(f"{param} Over Time")
            ax.set_xlabel("Time")
            ax.set_ylabel(param)
            ax.grid(True)
            st.pyplot(fig)

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
        st.warning("No data found.")
        st.stop()

    show_anomalies_only = st.checkbox("Show only anomalies")
    display_df = water_df if not show_anomalies_only else water_df[water_df['Anomaly_Status'].str.lower() != 'normal']
    st.dataframe(display_df)

    for param in ['pH', 'Turbidity', 'Temperature', 'Chlorine', 'Coagulant_Dosing', 'Flow_Rate']:
        st.subheader(f"{param} Over Time")
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.plot(water_df['Timestamp'], water_df[param], color='#0288d1', label='All Data')
        anomalies = water_df[water_df['Anomaly_Status'].str.contains(param, case=False, na=False)]
        ax.scatter(anomalies['Timestamp'], anomalies[param], color='red', label='Anomaly', zorder=5)
        ax.set_xlabel("Time")
        ax.set_ylabel(param)
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)

    st.download_button("Download CSV", display_df.to_csv(index=False), "anomaly_data.csv", "text/csv")

# --- Chemical Dosing Module ---

elif menu == "Chemical Dosing":
    show_chemical_dosing_module()


