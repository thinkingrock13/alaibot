#cd C:\Users\psacs\AppData\Local\Programs\Python\Python39\Scripts
#streamlit run "C:/Users/psacs/Desktop/Subiksha/AlaiBot/alaibot/gpt_test.py"

import streamlit as st
import openai
import os
from dotenv import load_dotenv
from supabase import create_client

# Load secrets
load_dotenv()

# Updated client usage for OpenAI>=1.0.0
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Supabase connection
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

st.title("💧 Alaibot - Water Treatment Chatbot")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "input" not in st.session_state:
    st.session_state.input = ""

def handle_input():
    user_input = st.session_state.input
    if not user_input:
        return

    # Add user input to chat history
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    try:
        # Call GPT-3.5 using new SDK format
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=st.session_state.chat_history
        )
        reply = response.choices[0].message.content
    except Exception as e:
        reply = f"Error from OpenAI API: {e}"

    st.session_state.chat_history.append({"role": "assistant", "content": reply})

    # Log to Supabase
    try:
        supabase.table("chat_logs").insert({
            "user_input": user_input,
            "bot_response": reply
        }).execute()
    except Exception as e:
        st.error(f"Error logging chat to database: {e}")

    # Clear input field
    st.session_state.input = ""

# Text input with on_change callback
st.text_input("You:", key="input", on_change=handle_input)

# Display chat history
for msg in st.session_state.chat_history:
    role = "You" if msg['role'] == "user" else "Bot"
    st.markdown(f"**{role}:** {msg['content']}")
