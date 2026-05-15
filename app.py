import streamlit as st
import requests
from datetime import datetime, timedelta

# Configurazione per Google Pixel 10 Pro
st.set_page_config(page_title="Orto ITRENT123", layout="centered")

# --- SEGRETI ---
try:
    API_KEY = st.secrets["wunderground_key"]
except:
    st.error("API Key non trovata!")
    st.stop()

STATION_ID = "ITRENT123"

# --- RECUPERO DATI INTEGRATO ---

def get_full_weather_data():
    """Recupera Live, Oggi (Max/Min) e Ieri (Bilancio)"""
    now = datetime.now()
    today_str = now.strftime('%Y%m%d')
    yesterday_str = (now - timedelta(days=1)).strftime('%Y%m%d')
    
    # 1. Dati Real-time
    url_curr = f"https://api.weather.com/v2/pws/observations/current?stationId={STATION_ID}&format=json&units=m&apiKey={API_KEY}"
    # 2. Riepilogo Oggi (Max/Min)
    url_today = f"https://api.weather.com/v2/pws/history/daily?stationId={STATION_ID}&format=json&units=m&date={today_str}&apiKey={API_KEY}"
    # 3. Riepilogo Ieri (Bilancio)
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
    
    # Correzione Umidità: alcune stazioni inviano valori scalati o errati
    umidita_reale = current.get('humidity')
    if umidita_reale is None or umidita_reale < 5:
        # Fallback sull'umidità media giornaliera se il dato live è corrotto
        umidita_reale = today.get('humidityAvg', '--')

    st.title("🌿 Orto Digitale ITRENT123")
    
    # --- SEZIONE 1: DATI STAZIONE ODIERNI ---
    st.subheader("📊 Dati Stazione")
    
    # Differenza temperatura rispetto alla media di ieri
    diff_temp = curr_m['temp'] - yesterday['tempAvg']

    # Prima riga: Istantanei
    r1_col1, r1_col2, r1_col3, r1_col4 = st.columns(4)
    r1_col1.metric("Temp", f"{curr_m['temp']}°C", f"{diff_temp:+.1f} vs ieri")
    r1_col2.metric("Pioggia 1h", f"{curr_m.get('precipRate', 0)} mm")
    r1_col3.metric("Vento", f"{curr_m['windSpeed']} km/h")
    r1_col4.metric("Umidità", f"{umidita_reale}%")

    # Seconda riga: Riepilogo Giornaliero
    r2_col1, r2_col2, r2_col3, r2_col4 = st.columns(4)
    r2_col1.metric("Temp Max", f"{today.get('tempHigh', '--')}°C")
    r2_col2.metric("Temp Min", f"{today.get('tempLow', '--')}°C")
    r2_col3.metric("Tot Accumulo", f"{today.get('precipTotal', 0)} mm")
    r2_col4.metric("Raffica Max", f"{today.get('windGust', '--')} km/h")

    st.divider()

    # --- SEZIONE 2: LOGICA AGRONOMICA (Somma Reale 48h) ---
    bilancio_48h = yesterday['precipTotal'] + today['precipTotal']
    
    st.subheader("🤖 Consigli Operativi")
    
    # Semaforo Irrigazione
    if bilancio_48h > 6.0:
        st.error(f"🔴 **IRRIGAZIONE: STOP TOTALE** \nAccumulo 48h: {bilancio_48h:.1f} mm. Terreno saturo.")
    elif bilancio_48h > 2.0:
        st.warning(f"🟡 **IRRIGAZIONE: ATTENDI** \nAccumulo 48h: {bilancio_48h:.1f} mm. Argilla ancora umida.")
    else:
        st.success("🟢 **IRRIGAZIONE: OK** \nProcedere con irrigazione a goccia.")

    # Semaforo Trattamenti
    if curr_m['windSpeed'] < 10 and float(umidita_reale) < 75:
        st.success("🟢 **TRATTAMENTI: IDEALE** \nOttimo per Zeolite o Neem.")
    else:
        st.warning("🔴 **TRATTAMENTI: EVITARE** \nVento forte o umidità eccessiva (foglie bagnate).")

    # --- SEZIONE 3: ALERT PROTEZIONE ---
    if curr_m['temp'] > 12 and bilancio_48h > 5:
        st.sidebar.error("🚨 **ALERT ELATERIDI** \nAttenzione ai meloni: i ferretti risalgono con l'umidità!")
    
    if float(umidita_reale) > 85 and curr_m['temp'] > 16:
        st.sidebar.warning("🍄 **ALERT FUNGHI** \nUmidità alle stelle: rischio peronospora.")

else:
    st.error("Errore nel recupero dati stazione. Controlla il collegamento.")

st.caption(f"Aggiornato alle {datetime.now().strftime('%H:%M:%S')} | Trento")
