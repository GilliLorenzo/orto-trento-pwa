import streamlit as st
import requests

st.set_page_config(page_title="Orto ITRENT123", layout="centered")

# Recupero sicuro dell'API Key dai Secrets
try:
    API_KEY = st.secrets["wunderground_key"]
except:
    API_KEY = None
    st.error("API Key non trovata nei Secrets!")

STATION_ID = "ITRENT123"

def get_real_data():
    if not API_KEY:
        return None
    url = f"https://api.weather.com/v2/pws/observations/current?stationId={STATION_ID}&format=json&units=m&apiKey={API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        obs = data['observations'][0]
        return {
            "temp": obs['metric']['temp'],
            "rain_today": obs['metric']['precipTotal'],
            "wind": obs['metric']['windSpeed'],
            "humidity": obs['humidity']
        }
    except:
        return None

# Esecuzione
meteo = get_real_data()

if meteo:
    st.title("🌿 Dashboard Orto Trento")
    st.subheader(f"Stazione: {STATION_ID} (LIVE)")

    col1, col2 = st.columns(2)
    col1.metric("Pioggia Oggi", f"{meteo['rain_today']} mm")
    col2.metric("Vento", f"{meteo['wind']} km/h")

    st.divider()

    # Logica specifica per il tuo terreno argilloso
    if meteo['rain_today'] > 5:
        st.error("🔴 STOP IRRIGAZIONE (Terreno Saturo)")
        st.info("L'argilla trattiene l'acqua. Per le tue 30 piante di pomodoro, attendi che il terreno asciughi in superficie.")
    else:
        st.success("🟢 IRRIGAZIONE OK")

    # Logica trattamenti (Zeolite/Neem) con pompa elettrica
    if meteo['wind'] < 10 and meteo['humidity'] < 75:
        st.success("🟢 TRATTAMENTI: MOMENTO IDEALE")
    else:
        st.warning("🔴 TRATTAMENTI: EVITARE")

    # Allerta Parassiti (Elateridi)
    if meteo['temp'] > 12 and meteo['rain_today'] > 5:
        st.warning("⚠️ ALLERTA ELATERIDI: Risalita ferretti probabile su meloni e cetrioli.")
else:
    st.warning("⚠️ In attesa di dati validi dalla stazione ITRENT123...")
