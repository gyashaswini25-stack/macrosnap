import streamlit as st
from google import genai
from google.genai import types
from twilio.rest import Client
from prompts import SYSTEM_PROMPT, WELCOME_MESSAGE_TEMPLATE, SUMMARY_REQUEST_PROMPT

MODEL_NAME = "gemini-3.5-flash"
st.set_page_config(page_title="MacroSnap", page_icon="🥗")

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
TWILIO_ACCOUNT_SID = st.secrets["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = st.secrets["TWILIO_AUTH_TOKEN"]
TWILIO_WHATSAPP_FROM = st.secrets.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

@st.cache_resource
def gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)

@st.cache_resource
def twilio_client():
    return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def create_chat():
    return gemini_client().chats.create(
        model=MODEL_NAME,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
    )

def ask_gemini(parts):
    try:
        return st.session_state.chat.send_message(parts).text
    except Exception as e:
        return f"Gemini error: {e}"

def send_whatsapp(to_number, body):
    try:
        msg = twilio_client().messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            to=f"whatsapp:{to_number}",
            body=body
        )
        return True, msg.sid
    except Exception as e:
        return False, str(e)

for k, v in {"onboarded":False, "name":"", "whatsapp":"", "chat":None, "messages":[]}.items():
    st.session_state.setdefault(k, v)

if not st.session_state.onboarded:
    st.title("🥗 MacroSnap")
    st.caption("Snap it. Understand it. Send the summary to WhatsApp.")
    with st.form("onboarding"):
        name = st.text_input("Your name")
        whatsapp = st.text_input("WhatsApp number", placeholder="+91XXXXXXXXXX")
        submitted = st.form_submit_button("Let's go 🚀")
    if submitted:
        if not name.strip() or not whatsapp.strip():
            st.warning("Enter both your name and WhatsApp number.")
        elif not whatsapp.strip().startswith("+"):
            st.warning("Include country code, for example +91...")
        else:
            st.session_state.name = name.strip()
            st.session_state.whatsapp = whatsapp.strip()
            st.session_state.chat = create_chat()
            st.session_state.onboarded = True
            st.rerun()
    st.stop()

st.title("🥗 MacroSnap")
st.caption(f"User: {st.session_state.name} · WhatsApp: {st.session_state.whatsapp}")

if st.button("📲 Send summary"):
    if not st.session_state.messages:
        st.warning("Discuss a meal first.")
    else:
        with st.spinner("Preparing summary..."):
            summary = ask_gemini([SUMMARY_REQUEST_PROMPT])
        ok, info = send_whatsapp(st.session_state.whatsapp, summary)
        if ok:
            st.success("Summary sent to WhatsApp! 📲")
        else:
            st.error("WhatsApp send failed. With the Sandbox, first join it and send a message to open the customer-service window.\n\n" + info)

if not st.session_state.messages:
    st.session_state.messages.append({
        "role":"assistant",
        "content":WELCOME_MESSAGE_TEMPLATE.format(name=st.session_state.name)
    })

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        if m.get("image"):
            st.image(m["image"], width=320)
        else:
            st.markdown(m["content"])

user_input = st.chat_input(
    "Ask about a meal or attach a meal photo",
    accept_file=True,
    file_type=["jpg","jpeg","png"]
)

if user_input:
    photo = user_input.files[0] if user_input.files else None
    text = user_input.text.strip()
    parts = []
    if photo:
        data = photo.getvalue()
        st.session_state.messages.append({"role":"user","image":data})
        parts.append(types.Part.from_bytes(data=data, mime_type=photo.type or "image/jpeg"))
    if text:
        st.session_state.messages.append({"role":"user","content":text})
        parts.append(text)
    elif photo:
        parts.append("Identify this meal and estimate calories, protein, carbohydrates, and fat.")
    if parts:
        with st.spinner("Analyzing your meal..."):
            answer = ask_gemini(parts)
        st.session_state.messages.append({"role":"assistant","content":answer})
        st.rerun()
