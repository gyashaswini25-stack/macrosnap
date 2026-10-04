# MacroSnap
Gemini Vision + Streamlit + Twilio WhatsApp nutrition demo.

## Run
```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
streamlit run app.py
```

Create `.streamlit/secrets.toml` from the example and add your real Gemini/Twilio credentials.

For Twilio Sandbox testing, join the Sandbox from the WhatsApp number you will use and send a message to the Sandbox to open the customer-service window before testing the Send summary button. Outside that window, WhatsApp business-initiated messages require an approved template and suitable sender setup.

Never commit `.streamlit/secrets.toml`.
