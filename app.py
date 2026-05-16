import streamlit as st
import requests
import math
from datetime import datetime, timedelta
import zoneinfo

st.set_page_config(page_title="Orto Digitale ITRENT123", layout="centered")

FUSO_ITALIA = zoneinfo.ZoneInfo("Europe/Rome")

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
    temp_media = (temp_max + temp_min) / 2
    ampiezza = (temp_max - temp_min) / 2
    angolo = 2 * math.pi * (ora_target - 9) / 24
    temp_stimata = temp_media + ampiezza * math.sin(angolo)
    return round(temp_stimata, 1)

def calcola_umidita_virtuale(temp_attuale, temp_min_oggi):
    """
    In mancanza del sensore, stima l'umidità relativa.
    Assume che all'ora della temperatura minima l'umidità fosse vicina al 95%.
    """
    try:
        # Approssimazione basata sulla depressione del punto di rugiada
        dew_point = temp_min_oggi - 0.5  
        # Formula di Magnus-Tetens semplificata per l'umidità relativa
        es = 6.11 * math.exp((17.27 * temp_attuale) / (237.3 + temp_attuale))
        e = 6.11 * math.exp((17.27 * dew_point) / (237.3 + dew_point))
        rh = (e / es) * 100
        # Limitiamo i valori tra il 40% e il 98% per sicurezza agronomica
        return max(40, min(98, round(rh)))
    except:
        return 70 # Fallback standard se il calcolo fallisce

# --- LOGICA E UI ---

st.title("🌿 Orto Digitale ITRENT123")

current = get_current_data()
today_metrics, yesterday_metrics = get_historical_daily_data()
ora_locale_adesso = datetime.now(FUSO_ITALIA)

if current and today_metrics:
    curr_m = current['metric']
    
    # --- CORREZIONE SOFTWARE SENSORE GUASTO ---
    umidita_stazione = current.get('humidity', 10)
    
    if umidita_stazione <= 12: # Se il sensore è bloccato al 10% o giù di lì
        t_min_oggi = today_metrics.get('tempLow', curr_m['temp'] - 5)
        umidita_reale = calcola_umidita_virtuale(curr_m['temp'], t_min_oggi)
        nota_umidita = "⚠️ Sensore guasto: valore stimato via software"
    else:
        umidita_reale = umidita_stazione
        nota_umidita = "Stazione LIVE"
    
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
        else: delta_testo = "--"
    else: delta_testo = "--"

    # Riga 1
    col1, col2 = st.columns(2)
    col1.metric("Temp", f"{curr_m['temp']}°C", delta_testo)
    col2.metric("Pioggia 1h", f"{curr_m.get('precipRate', 0)} mm")

    # Riga 2
    col3, col4 = st.columns(2)
    col3.metric("Vento", f"{curr_m['windSpeed']} km/h")
    # Mostriamo l'umidità calcolata e aggiungiamo una nota informativa sotto
    col4.metric("Umidità", f"{umidita_reale}%", help=nota_umidita)

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

    # Semaforo Trattamenti (Ora basato sull'umidità stimata corretta!)
    if curr_m['windSpeed'] < 10 and umidita_reale < 75:
        st.success("🟢 **TRATTAMENTI: IDEALE**\n\nOttima finestra per Zeolite o Olio di Neem.")
    else:
        st.warning("🔴 **TRATTAMENTI: EVITARE**\n\nVento forte o umidità troppo alta (rischio scarsa adesione).")

    # Alert Parassiti
    if curr_m['temp'] > 12 and bilancio_48h > 5:
        st.sidebar.error("🚨 **ALERT ELATERIDI**\nCondizioni ideali per risalita ferretti!")

else:
    st.error("Connessione alla stazione fallita. Verifica API Key o stato PWS.")

st.caption(f"Aggiornato alle {ora_locale_adesso.strftime('%H:%M:%S')} (Ora locale Trento) | Correzione igrometro attiva.")
