#cd C:\Users\psacs\AppData\Local\Programs\Python\Python39\Scripts
#streamlit run "C:/Users/psacs/Desktop/Subiksha/AlaiBot/alaibot/alaibot_app.py"
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

# Page config
st.set_page_config(page_title="Alaibot", layout="wide")

# Apply custom water-themed style
st.markdown(
    """
    <style>
    /* Set background color */
    body, .stApp {
        background-color: #e0f7fa;
        font-family: 'Segoe UI', sans-serif;
    }

    /* Header title */
    .st-emotion-cache-10trblm {
        color: #01579b;
        font-size: 36px;
        font-weight: bold;
        text-shadow: 1px 1px 2px #81d4fa;
    }

    /* Chat input text box */
    .stTextInput > div > div > input {
        background-color: #ffffff;
        border: 2px solid #4fc3f7;
        border-radius: 10px;
        color: #0277bd;
    }

    /* Markdown chat roles */
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

    /* Plot headers */
    .stHeadingContainer {
        color: #01579b;
    }

    /* Download button */
    .stDownloadButton button {
        background-color: #4fc3f7;
        color: white;
        border-radius: 10px;
        font-weight: bold;
    }

    /* Make chat auto-scroll */
    .chat-container {
        display: flex;
        flex-direction: column;
        height: 400px;
        overflow-y: auto;
        scroll-behavior: smooth;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar menu
menu = st.sidebar.radio("Navigate", ["Chatbot", "Anomaly Dashboard"])

if menu == "Chatbot":
    st.title("Alaibot - Water Treatment Chatbot")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_input = st.chat_input("You")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=st.session_state.chat_history
            )
            reply = response.choices[0].message.content
        except Exception as e:
            reply = f"OpenAI API Error: {e}"

        st.session_state.chat_history.append({"role": "assistant", "content": reply})

        # Log chat to Supabase
        try:
            supabase.table("chat_logs").insert({
                "user_input": user_input,
                "bot_response": reply
            }).execute()
        except Exception as e:
            st.error(f"Error logging chat to DB: {e}")

    # Display full chat with auto-scroll
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in st.session_state.chat_history:
        role = "You" if msg['role'] == "user" else "Bot"
        bubble_class = "chat-bubble-user" if role == "You" else "chat-bubble-bot"
        st.markdown(f'<div class="{bubble_class}"><b>{role}:</b> {msg["content"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

elif menu == "Anomaly Dashboard":
    st.title("Water Quality Anomaly Dashboard")

    # Fetch data
    response = supabase.table("water_readings").select("*").execute()
    df = pd.DataFrame(response.data)

    if df.empty:
        st.warning("No data found in water_readings table.")
        st.stop()

    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df = df.sort_values('Timestamp')

    show_anomalies_only = st.checkbox("Show only anomalies")

    if show_anomalies_only:
        df = df[df['Anomaly_Status'] != 'Normal']

    st.dataframe(df)

    parameters = ['pH', 'Turbidity', 'Temperature', 'Chlorine', 'Coagulant_Dosing', 'Flow_Rate']
    for param in parameters:
        st.subheader(f"{param} Over Time")
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.plot(df['Timestamp'], df[param], color='blue')

        anomaly_indices = df[df['Anomaly_Status'].str.contains(param, case=False, na=False)].index
        ax.scatter(df.loc[anomaly_indices, 'Timestamp'], df.loc[anomaly_indices, param],
                   color='red', label='Anomaly', zorder=5)

        ax.set_xlabel("Time")
        ax.set_ylabel(param)
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)

    st.download_button("Download CSV", df.to_csv(index=False), "anomaly_data.csv", "text/csv")
