import sys
sys.path.append("/opt/miniconda3/lib/python3.12/site-packages")
from openai import OpenAI 
import time
from dotenv import load_dotenv
import os
import streamlit as st
from PIL import Image

load_dotenv()

client = OpenAI(api_key=os.getenv("api_key"))
assistant_id = os.getenv("assistant_key")

if "start_chat" not in st.session_state:
    st.session_state.start_chat = False
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "language" not in st.session_state:
    st.session_state.language = None

st.set_page_config(page_title="AmicAI")

@st.cache_resource
def load_logo():
    return Image.open("logo.png")

img = load_logo()
st.sidebar.image(img)  # Cached and stable logo

language = st.sidebar.selectbox("Select your language:", ["English", "Slovenian"])
st.session_state.language = language

# Set a dynamic placeholder based on the selected language
placeholder_text = (
    "Describe the conflict or situation you want to talk about."
    if st.session_state.language == "English"
    else "Opiši konflikt oz. situacijo, o kateri želiš spregovoriti."
)

if st.sidebar.button("Start Chat"):
    st.session_state.start_chat = True
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

st.title("AmicAI")
if language == "English":
    st.subheader("Your virtual assistant to help you solve conflicts")
else:
    st.subheader("Tvoj virtualni pomočnik pri reševanju konfliktov")

if st.button("Exit Chat"):
    st.session_state.messages = []  # Clear the chat history
    st.session_state.start_chat = False  # Reset the chat state
    st.session_state.thread_id = None

if st.session_state.start_chat:
    if "openai_model" not in st.session_state:
        st.session_state.openai_model = "gpt-4-1106-preview"
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input(placeholder_text):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=prompt
        )

        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=assistant_id,
        )

        while run.status != 'completed':
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id
            )
        messages = client.beta.threads.messages.list(
            thread_id=st.session_state.thread_id
        )

        # Process and display assistant messages
        assistant_messages_for_run = [
            message for message in messages
            if message.run_id == run.id and message.role == "assistant"
        ]
        for message in assistant_messages_for_run:
            st.session_state.messages.append({"role": "assistant", "content": message.content[0].text.value})
            with st.chat_message("assistant"):
                st.markdown(message.content[0].text.value)

else:
    st.write("Select your language and click 'Start Chat' to begin.")
