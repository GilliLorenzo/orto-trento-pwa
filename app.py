import streamlit as st
import requests
from datetime import datetime, timedelta

# Configurazione ottimizzata per mobile (Pixel 10 Pro)
st.set_page_config(page_title="Orto Digitale ITRENT123", layout="centered")

# --- RECUPERO SEGRETI ---
try:
    API_KEY = st.secrets["wunderground_key"]
except:
    st.error("Errore: API Key non trouvata nei Secrets!")
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

def get_historical_and_hourly_data():
    """Recupera i dati di ieri (orari per il delta e totali per il bilancio) e il riepilogo di oggi"""
    today_str = datetime.now().strftime('%Y%m%d')
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    ora_attuale = datetime.now().hour

    # 1. Recuperiamo il riepilogo giornaliero di oggi (per Max/Min/Accumulo correnti)
    url_today = f"https://api.weather.com/v2/pws/history/daily?stationId={STATION_ID}&format=json&units=m&date={today_str}&apiKey={API_KEY}"
    
    # 2. Recuperiamo il dettaglio ORARIO di ieri per trovare la stessa ora
    url_yesterday_hourly = f"https://api.weather.com/v2/pws/history/hourly?stationId={STATION_ID}&format=json&units=m&date={yesterday_str}&apiKey={API_KEY}"
    
    # 3. Recuperiamo il riepilogo di ieri (per il totale pioggia delle 48h)
    url_yesterday_daily = f"https://api.weather.com/v2/pws/history/daily?stationId={STATION_ID}&format=json&units=m&date={yesterday_str}&apiKey={API_KEY}"

    today_metrics = None
    temp_ieri_stessa_ora = None
    pioggia_ieri = 0.0

    try:
        r_today = requests.get(url_today)
        today_metrics = r_today.json()['observations'][0]['metric']
    except: pass

    try:
        r_yst_daily = requests.get(url_yesterday_daily)
        pioggia_ieri = r_yst_daily.json()['observations'][0]['metric']['precipTotal']
    except: pass

    try:
        r_yst_hourly = requests.get(url_yesterday_hourly)
        observations = r_yst_hourly.json()['observations']
        
        # Cerchiamo l'osservazione di ieri che si avvicina di più all'ora attuale
        # Wunderground di solito restituisce i dati ogni 5-10 minuti, cerchiamo il primo match dell'ora corrente
        for obs in observations:
            obs_time = datetime.strptime(obs['obsTimeLocal'], '%Y-%m-%d %H:%M:%S')
            if obs_time.hour == ora_attuale:
                temp_ieri_stessa_ora = obs['metric']['temp']
                break
        
        # Se non troviamo l'ora esatta, usiamo l'ultima osservazione disponibile come fallback
        if temp_ieri_stessa_ora is None and observations:
            temp_ieri_stessa_ora = observations[-1]['metric']['temp']
    except:
        pass

    return today_metrics, temp_ieri_stessa_ora, pioggia_ieri

# --- LOGICA E UI ---

st.title("🌿 Orto Digitale ITRENT123")

current = get_current_data()
today_metrics, temp_ieri_stessa_ora, pioggia_ieri = get_historical_and_hourly_data()

if current and today_metrics:
    curr_m = current['metric']
    
    # --- SEZIONE DATI STAZIONE ---
    st.subheader("📊 Dati Stazione")
    
    # Calcolo differenza rispetto alla STESSA ORA di ieri
    if temp_ieri_stessa_ora is None:
        # Se fallisce il recupero orario, non mostriamo il delta per non dare dati errati
        delta_testo = "N/D"
        diff_temp = 0.0
    else:
        diff_temp = curr_m['temp'] - temp_ieri_stessa_ora
        delta_testo = f"{diff_temp:+.1f}°C vs ieri stessa ora"

    # Riga 1
    col1, col2 = st.columns(2)
    # Passiamo il testo personalizzato nel campo delta di st.metric
    col1.metric("Temp", f"{curr_m['temp']}°C", delta_testo if temp_ieri_stessa_ora is None else f"{diff_temp:+.1f}°C ieri stessa ora")
    col2.metric("Pioggia 1h", f"{curr_m.get('precipRate', 0)} mm")

    # Riga 2
    col3, col4 = st.columns(2)
    col3.metric("Vento", f"{curr_m['windSpeed']} km/h")
    col4.metric("Umidità", f"{current.get('humidity', '--')}%")

    st.markdown("---")

    # Riga 3 (Riepilogo REALE)
    col5, col6 = st.columns(2)
    col5.metric("Temp Max", f"{today_metrics.get('tempHigh', '--')}°C")
    col6.metric("Temp Min", f"{today_metrics.get('tempLow', '--')}°C")

    # Riga 4
    col7, col8 = st.columns(2)
    col7.metric("Tot Accumulo", f"{today_metrics.get('precipTotal', 0)} mm")
    col8.metric("Raffica Max", f"{today_metrics.get('windGust', '--')} km/h")

    st.divider()

    # --- LOGICA AGRONOMICA (Somma Reale Pura) ---
    bilancio_48h = pioggia_ieri + today_metrics['precipTotal']
    
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
    st.error("Connessione alla stazione fallita. Verifica API Key o stato PWS.")

st.caption(f"Aggiornato: {datetime.now().strftime('%H:%M:%S')} | Confronto orario basato su storico ITRENT123")
