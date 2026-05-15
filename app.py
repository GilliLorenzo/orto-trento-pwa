import streamlit as st
import requests
from datetime import datetime, timedelta

# Ottimizzazione per Google Pixel 10 Pro
st.set_page_config(page_title="Orto ITRENT123", layout="centered")

# --- SEGRETI ---
try:
    API_KEY = st.secrets["wunderground_key"]
except:
    st.error("API Key non trovata!")
    st.stop()

STATION_ID = "ITRENT123"

# --- RECUPERO DATI ---

def get_full_weather_data():
    now = datetime.now()
    today_str = now.strftime('%Y%m%d')
    yesterday_str = (now - timedelta(days=1)).strftime('%Y%m%d')
    
    url_curr = f"https://api.weather.com/v2/pws/observations/current?stationId={STATION_ID}&format=json&units=m&apiKey={API_KEY}"
    url_today = f"https://api.weather.com/v2/pws/history/daily?stationId={STATION_ID}&format=json&units=m&date={today_str}&apiKey={API_KEY}"
    url_yest = f"https://api.weather.com/v2/pws/history/daily?stationId={STATION_ID}&format=json&units=m&date={yesterday_str}&apiKey={API_KEY}"
    
    try:
        current = requests.get(url_curr).json()['observations'][0]
        today = requests.get(url_today).json()['observations'][0]['metric']
        yesterday = requests.get(url_yest).json()['observations'][0]['metric']
        return current, today, yesterday
    except:
        return None, None, None

# --- ESECUZIONE ---

current, today, yesterday = get_full_weather_data()

if current and today and yesterday:
    curr_m = current['metric']
    
    # --- CORREZIONE LOGICA UMIDITÀ ---
    # Se la stazione segna 10% ma piove, è un errore del sensore.
    umidita_raw = current.get('humidity', 0)
    pioggia_ora = curr_m.get('precipTotal', 0)
    
    if umidita_raw <= 10 and pioggia_ora > 0:
        umidita_fissata = 95 # Valore realistico durante pioggia
        umidita_nota = " (Dato Corretto: Sensore KO)"
    else:
        umidita_fissata = umidita_raw
        umidita_nota = ""

    st.title("🌿 Orto Digitale ITRENT123")
    
    # --- SEZIONE 1: DATI STAZIONE ---
    st.subheader("📊 Dati Stazione")
    
    # Delta Temperatura (con fallback su tempHigh se tempAvg manca)
    temp_ieri = yesterday.get('tempAvg', yesterday.get('tempHigh', curr_m['temp']))
    diff_temp = curr_m['temp'] - temp_ieri

    r1_col1, r1_col2, r1_col3, r1_col4 = st.columns(4)
    r1_col1.metric("Temp", f"{curr_m['temp']}°C", f"{diff_temp:+.1f} vs ieri")
    r1_col2.metric("Pioggia 1h", f"{curr_m.get('precipRate', 0)} mm")
    r1_col3.metric("Vento", f"{curr_m['windSpeed']} km/h")
    r1_col4.metric("Umidità", f"{umidita_fissata}%", umidita_nota)

    r2_col1, r2_col2, r2_col3, r2_col4 = st.columns(4)
    r2_col1.metric("Temp Max", f"{today.get('tempHigh', '--')}°C")
    r2_col2.metric("Temp Min", f"{today.get('tempLow', '--')}°C")
    r2_col3.metric("Tot Accumulo", f"{today.get('precipTotal', 0)} mm")
    r2_col4.metric("Raffica Max", f"{today.get('windGust', '--')} km/h")

    st.divider()

    # --- SEZIONE 2: BILANCIO E CONSIGLI ---
    # Somma reale 48h come richiesto
    bilancio_48h = yesterday.get('precipTotal', 0) + today.get('precipTotal', 0)
    
    st.subheader("🤖 Strategia Orto")
    
    # Semaforo Irrigazione
    if bilancio_48h > 6.0:
        st.error(f"🔴 **IRRIGAZIONE: STOP** \nAccumulo 48h: {bilancio_48h:.1f} mm. Terreno saturo.")
    elif bilancio_48h > 2.0:
        st.warning(f"🟡 **IRRIGAZIONE: ATTENDI** \nAccumulo 48h: {bilancio_48h:.1f} mm. Umidità nell'argilla.")
    else:
        st.success("🟢 **IRRIGAZIONE: OK** \nProcedere con impianto a goccia.")

    # Semaforo Trattamenti
    if curr_m['windSpeed'] < 10 and umidita_fissata < 75:
        st.success("🟢 **TRATTAMENTI: IDEALE** \nCondizioni ottime per Zeolite o Neem.")
    else:
        st.warning("🔴 **TRATTAMENTI: SOSPESI** \nFoglie bagnate o troppo vento.")

    # --- SEZIONE 3: ALERT LATERALE ---
    if curr_m['temp'] > 12 and bilancio_48h > 5:
        st.sidebar.error("🚨 **ELATERIDI** \nTerreno umido: rischio ferretti su meloni.")
    
    if umidita_fissata > 85 and curr_m['temp'] > 16:
        st.sidebar.warning("🍄 **PERONOSPORA** \nAlta umidità: rischio funghi su cetrioli.")

else:
    st.error("Errore comunicazione stazione ITRENT123.")

st.caption(f"Update: {datetime.now().strftime('%H:%M:%S')} | Logica Terreno Argilloso")
