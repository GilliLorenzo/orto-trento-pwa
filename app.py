import streamlit as st
import requests
import math
from datetime import datetime, timedelta
import zoneinfo  # Libreria standard per gestire i fusi orari

# Configurazione ottimizzata per mobile (Pixel 10 Pro)
st.set_page_config(page_title="Orto Digitale ITRENT123", layout="centered")

# Definizione del fuso orario corretto (Europe/Rome gestisce anche l'ora legale in automatico)
FUSO_ITALIA = zoneinfo.ZoneInfo("Europe/Rome")

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

def get_historical_daily_data():
    """Recupera i riassunti giornalieri usando l'ora italiana"""
    ora_locale = datetime.now(FUSO_ITALIA)
    today_str = ora_locale.strftime('%Y%m%d')
    yesterday_str = (ora_locale - timedelta(days=1)).strftime('%Y%m%d')

    url_today = f"https://api.weather.com/v2/pws/history/daily?stationId={STATION_ID}&format=json&units=m&date={today_str}&apiKey={API_KEY}"
    url_yesterday = f"https://api.weather.com/v2/pws/history/daily?stationId={STATION_ID}&format=json&units=m&date={yesterday_str}&apiKey={API_KEY}"

    today_metrics = None
    yesterday_metrics = None

    try:
        r_today = requests.get(url_today)
        today_metrics = r_today.json()['observations'][0]['metric']
    except: pass

    try:
        r_yesterday = requests.get(url_yesterday)
        yesterday_metrics = r_yesterday.json()['observations'][0]['metric']
    except: pass

    return today_metrics, yesterday_metrics

def stima_temperatura_oraria(temp_max, temp_min, ora_target):
    """Calcola la sinusoide termica basandosi sull'ora locale"""
    temp_media = (temp_max + temp_min) / 2
    ampiezza = (temp_max - temp_min) / 2
    angolo = 2 * math.pi * (ora_target - 9) / 24
    temp_stimata = temp_media + ampiezza * math.sin(angolo)
    return round(temp_stimata, 1)

# --- LOGICA E UI ---

st.title("🌿 Orto Digitale ITRENT123")

current = get_current_data()
today_metrics, yesterday_metrics = get_historical_daily_data()

# Recuperiamo l'ora esatta italiana per l'interfaccia e per il calcolo
ora_locale_adesso = datetime.now(FUSO_ITALIA)

if current and today_metrics:
    curr_m = current['metric']
    
    # --- SEZIONE DATI STAZIONE ---
    st.subheader("📊 Dati Stazione")
    
    if yesterday_metrics:
        ora_attuale_ita = ora_locale_adesso.hour
        t_max_ieri = yesterday_metrics.get('tempHigh')
        t_min_ieri = yesterday_metrics.get('tempLow')
        
        if t_max_ieri is not None and t_min_ieri is not None:
            temp_ieri_stessa_ora = stima_temperatura_oraria(t_max_ieri, t_min_ieri, ora_attuale_ita)
            diff_temp = curr_m['temp'] - temp_ieri_stessa_ora
            delta_testo = f"{diff_temp:+.1f}°C ieri stessa ora"
        else:
            delta_testo = "--"
    else:
        delta_testo = "--"

    # Riga 1
    col1, col2 = st.columns(2)
    col1.metric("Temp", f"{curr_m['temp']}°C", delta_testo)
    col2.metric("Pioggia 1h", f"{curr_m.get('precipRate', 0)} mm")

    # Riga 2
    col3, col4 = st.columns(2)
    col3.metric("Vento", f"{curr_m['windSpeed']} km/h")
    col4.metric("Umidità", f"{current.get('humidity', '--')}%")

    st.markdown("---")

    # Riga 3 (Riepilogo REALE di Oggi)
    col5, col6 = st.columns(2)
    col5.metric("Temp Max", f"{today_metrics.get('tempHigh', '--')}°C")
    col6.metric("Temp Min", f"{today_metrics.get('tempLow', '--')}°C")

    # Riga 4
    col7, col8 = st.columns(2)
    col7.metric("Tot Accumulo", f"{today_metrics.get('precipTotal', 0)} mm")
    col8.metric("Raffica Max", f"{today_metrics.get('windGust', '--')} km/h")

    st.divider()

    # --- LOGICA AGRONOMICA (Somma Reale Pura) ---
    pioggia_ieri = yesterday_metrics.get('precipTotal', 0.0) if yesterday_metrics else 0.0
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

# Mostra l'orario di aggiornamento allineato all'ora italiana
st.caption(f"Aggiornato alle {ora_locale_adesso.strftime('%H:%M:%S')} (Ora locale Trento)")
