import streamlit as st
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Orto Digitale ITRENT123", layout="centered")

try:
    API_KEY = st.secrets["wunderground_key"]
except:
    st.error("Errore: API Key non trovata!")
    st.stop()

STATION_ID = "ITRENT123"

# --- FUNZIONI DI RECUPERO DATI ---

def get_current_data():
    url = f"https://api.weather.com/v2/pws/observations/current?stationId={STATION_ID}&format=json&units=m&apiKey={API_KEY}"
    try:
        r = requests.get(url)
        return r.json()['observations'][0]
    except: return None

def get_comparison_data():
    """Recupera i dati di ieri per il confronto orario e i mm totali"""
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    url_history = f"https://api.weather.com/v2/pws/history/daily?stationId={STATION_ID}&format=json&units=m&date={yesterday_str}&apiKey={API_KEY}"
    try:
        r = requests.get(url_history)
        data = r.json()['observations'][0]
        # Cerchiamo la temp alla stessa ora di ieri (approssimata)
        # Nota: Le API Daily a volte danno solo riepiloghi. Per precisione assoluta servirebbe l'endpoint 'hourly'.
        return data['metric']['tempAvg'], data['metric']['precipTotal']
    except: return 0.0, 0.0

# --- INTERFACCIA UTENTE ---

st.title("🌿 Orto Digitale ITRENT123")

current = get_current_data()
temp_ieri_media, pioggia_ieri = get_comparison_data()

if current:
    curr_m = current['metric']
    

# --- SEZIONE DATI STAZIONE ODIERNI (Versione Robusta) ---
    st.subheader("📊 Dati Stazione")
    
    # Calcolo differenza temperatura rispetto a ieri
    diff_temp = curr_m['temp'] - temp_ieri_media

    # Prima riga: Istantanei
    r1_col1, r1_col2, r1_col3, r1_col4 = st.columns(4)
    r1_col1.metric("Temp", f"{curr_m['temp']}°C", f"{diff_temp:+.1f} vs ieri")
    # Usiamo .get() per evitare errori se il campo manca
    r1_col2.metric("Pioggia 1h", f"{curr_m.get('precipRate', 0)} mm")
    r1_col3.metric("Vento", f"{curr_m['windSpeed']} km/h")
    r1_col4.metric("Umidità", f"{current.get('humidity', '--')}%")

    # Seconda riga: Riepilogo Giornaliero
    # Wunderground spesso fornisce questi dati come 'heatIndex', 'windchill' o in pacchetti riassuntivi
    # Per sicurezza, se non li trova, mettiamo N/D (Non Disponibile)
    r2_col1, r2_col2, r2_col3, r2_col4 = st.columns(4)
    
    # Proviamo a recuperare i valori, altrimenti mettiamo "--"
    t_max = curr_m.get('tempHigh', curr_m.get('highterm', '--'))
    t_min = curr_m.get('tempLow', curr_m.get('lowterm', '--'))
    v_max = curr_m.get('windGust', '--')
    
    r2_col1.metric("Temp Max", f"{t_max}°C")
    r2_col2.metric("Temp Min", f"{t_min}°C")
    r2_col3.metric("Tot Accumulo", f"{curr_m.get('precipTotal', 0)} mm")
    r2_col4.metric("Raffica Max", f"{v_max} km/h")


    st.divider()
    
    # --- LOGICA AGRONOMICA (Somma Reale Pura) ---
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
    st.error("Connessione alla stazione ITRENT123 fallita.")

st.caption(f"Aggiornato alle {datetime.now().strftime('%H:%M:%S')} | Trento")
