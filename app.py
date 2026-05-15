import streamlit as st
import requests
from datetime import datetime, timedelta

# Configurazione ottimizzata per mobile
st.set_page_config(page_title="Orto Digitale ITRENT123", layout="centered")

# --- RECUPERO SEGRETI ---
try:
    API_KEY = st.secrets["wunderground_key"]
except:
    st.error("Errore: API Key non trovata nei Secrets!")
    st.stop()

STATION_ID = "ITRENT123"

# --- FUNZIONI DATI ---

def get_current_data():
    url = f"https://api.weather.com/v2/pws/observations/current?stationId={STATION_ID}&format=json&units=m&apiKey={API_KEY}"
    try:
        r = requests.get(url)
        return r.json()['observations'][0]
    except:
        return None

def get_historical_data():
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    url = f"https://api.weather.com/v2/pws/history/daily?stationId={STATION_ID}&format=json&units=m&date={yesterday}&apiKey={API_KEY}"
    try:
        r = requests.get(url)
        data = r.json()['observations'][0]
        # Restituiamo media temp per confronto e pioggia totale di ieri
        return data['metric']['tempAvg'], data['metric']['precipTotal']
    except:
        return 0.0, 0.0

# --- LOGICA E UI ---

st.title("🌿 Orto Digitale ITRENT123")

current = get_current_data()
temp_ieri_media, pioggia_ieri = get_historical_data()

if current:
    curr_m = current['metric']
    
    # --- SEZIONE DATI STAZIONE (Layout 2 colonne per Pixel) ---
    st.subheader("📊 Dati Stazione")
    
    diff_temp = curr_m['temp'] - temp_ieri_media

    # Riga 1
    col1, col2 = st.columns(2)
    col1.metric("Temp", f"{curr_m['temp']}°C", f"{diff_temp:+.1f} vs ieri")
    col2.metric("Pioggia 1h", f"{curr_m.get('precipRate', 0)} mm")

    # Riga 2
    col3, col4 = st.columns(2)
    col3.metric("Vento", f"{curr_m['windSpeed']} km/h")
    col4.metric("Umidità", f"{current.get('humidity', '--')}%")

    st.markdown("---")

    # Riga 3 (Riepilogo)
    col5, col6 = st.columns(2)
    t_max = curr_m.get('tempHigh', curr_m.get('highterm', '--'))
    t_min = curr_m.get('tempLow', curr_m.get('lowterm', '--'))
    col5.metric("Temp Max", f"{t_max}°C")
    col6.metric("Temp Min", f"{t_min}°C")

    # Riga 4
    col7, col8 = st.columns(2)
    v_max = curr_m.get('windGust', '--')
    col7.metric("Tot Accumulo", f"{curr_m.get('precipTotal', 0)} mm")
    col8.metric("Raffica Max", f"{v_max} km/h")

    st.divider()

    # --- LOGICA AGRONOMICA (Somma Reale) ---
    bilancio_48h = pioggia_ieri + curr_m['precipTotal']
    
    st.subheader("🤖 Consigli Operativi")
    
    # Semaforo Irrigazione
    if bilancio_48h > 6.0:
        st.error(f"🔴 **IRRIGAZIONE: STOP TOTALE**\n\nAccumulo 48h: {bilancio_48h:.1f} mm. Terreno argilloso saturo.")
    elif bilancio_48h > 2.0:
        st.warning(f"🟡 **IRRIGAZIONE: ATTENDI**\n\nAccumulo 48h: {bilancio_48h:.1f} mm. Umidità residua sufficiente.")
    else:
        st.success("🟢 **IRRIGAZIONE: OK**\n\nProcedere con irrigazione a goccia se necessario.")

    # Semaforo Trattamenti
    if curr_m['windSpeed'] < 10 and current['humidity'] < 75:
        st.success("🟢 **TRATTAMENTI: IDEALE**\n\nOttima finestra per Zeolite o Olio di Neem.")
    else:
        st.warning("🔴 **TRATTAMENTI: EVITARE**\n\nVento o umidità fuori soglia.")

    # Alert Parassiti
    if curr_m['temp'] > 12 and bilancio_48h > 5:
        st.sidebar.error("🚨 **ALERT ELATERIDI**\nCondizioni ideali per risalita ferretti!")

else:
    st.error("Connessione alla stazione fallita. Controlla API Key o stato PWS.")

st.caption(f"Aggiornato: {datetime.now().strftime('%H:%M:%S')} | Trento")
