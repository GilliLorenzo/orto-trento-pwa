import streamlit as st
import requests
from datetime import datetime, timedelta

# Configurazione interfaccia ottimizzata per Google Pixel 10 Pro
st.set_page_config(page_title="Orto Digitale ITRENT123", layout="centered")

# --- RECUPERO SEGRETI E CONFIGURAZIONE ---
try:
    API_KEY = st.secrets["wunderground_key"]
except:
    st.error("Errore: API Key non trovata nei Secrets di Streamlit!")
    st.stop()

STATION_ID = "ITRENT123"

# --- FUNZIONI DI RECUPERO DATI ---

def get_current_data():
    """Recupera i dati meteo in tempo reale"""
    url = f"https://api.weather.com/v2/pws/observations/current?stationId={STATION_ID}&format=json&units=m&apiKey={API_KEY}"
    try:
        r = requests.get(url)
        return r.json()['observations'][0]
    except:
        return None

def get_historical_data():
    """Recupera il riepilogo delle ultime 24 ore per il bilancio idrico"""
    # Usiamo l'endpoint per le osservazioni giornaliere
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    url = f"https://api.weather.com/v2/pws/history/daily?stationId={STATION_ID}&format=json&units=m&date={yesterday}&apiKey={API_KEY}"
    try:
        r = requests.get(url)
        # Prendiamo il riepilogo massimo di pioggia caduta ieri
        return r.json()['observations'][0]['metric']['precipTotal']
    except:
        return 0.0

# --- LOGICA AGRONOMICA AVANZATA ---

def elabora_strategia(current, pioggia_ieri):
    temp = current['metric']['temp']
    pioggia_oggi = current['metric']['precipTotal']
    vento = current['metric']['windSpeed']
    umidita = current['humidity']
    
    # Calcolo Bilancio Idrico Semplificato per terreno Argilloso
    # L'argilla trattiene molto, quindi pesiamo molto la pioggia di ieri
    bilancio_48h = (pioggia_ieri * 0.8) + pioggia_oggi
    
    # 1. Decisione Irrigazione (Pomodori, Meloni, Fragole, Lamponi)
    if bilancio_48h > 6.0:
        irrig_status = "🔴 STOP TOTALE"
        irrig_msg = f"Terreno saturo ({bilancio_48h:.1f}mm accumulati). Rischio asfissia radicale nell'argilla."
    elif bilancio_48h > 2.0:
        irrig_status = "🟡 ATTENDI"
        irrig_msg = "Umidità residua sufficiente. Non bagnare i pomodori oggi."
    else:
        irrig_status = "🟢 ATTIVA"
        irrig_msg = "Il terreno sta asciugando. Procedere con irrigazione a goccia."

    # 2. Decisione Trattamenti (Zeolite / Olio di Neem)
    # Requisiti: Vento debole (< 10km/h) e foglie non bagnate (umidità < 75%)
    if vento < 10 and umidita < 75 and pioggia_oggi == 0:
        tratt_status = "🟢 IDEALE"
        tratt_msg = "Condizioni perfette per pompa elettrica. Il prodotto aderirà bene."
    else:
        tratt_status = "🔴 EVITARE"
        tratt_msg = "Vento forte o troppa umidità: rischio deriva o lavaggio del prodotto."

    return irrig_status, irrig_msg, tratt_status, tratt_msg

# --- INTERFACCIA UTENTE (UI) ---

st.title("🌿 Orto Digitale Trento")
st.markdown(f"**Monitoraggio Stazione {STATION_ID}**")

current = get_current_data()
pioggia_ieri = get_historical_data()

if current:
    # Indicatori principali (Metriche)
    col1, col2, col3 = st.columns(3)
    col1.metric("Temperatura", f"{current['metric']['temp']}°C")
    col2.metric("Pioggia Oggi", f"{current['metric']['precipTotal']} mm")
    col3.metric("Vento", f"{current['metric']['windSpeed']} km/h")

    irrig_s, irrig_m, tratt_s, tratt_m = elabora_strategia(current, pioggia_ieri)

    st.divider()

    # Sezione Irrigazione
    st.subheader(f"Irrigazione: {irrig_s}")
    st.info(f"{irrig_m} (Accumulo 48h: {float(pioggia_ieri) + float(current['metric']['precipTotal']):.1f} mm)")

    # Sezione Trattamenti
    st.subheader(f"Trattamenti: {tratt_s}")
    if "🟢" in tratt_s:
        st.success(tratt_m)
    else:
        st.warning(tratt_m)

    st.divider()

    # Allerta Parassiti e Patologie
    st.subheader("⚠️ Alert Protezione Piante")
    
    # Alert Elateridi (Ferretti)
    if current['metric']['temp'] > 12 and (pioggia_ieri + current['metric']['precipTotal']) > 5:
        st.error("🚨 **Allerta Elateridi:** Terreno umido e caldo. Risalita ferretti probabile su meloni e pomodori!")
    
    # Alert Peronospora
    if current['humidity'] > 80 and current['metric']['temp'] > 16:
        st.warning("🍄 **Rischio Funghi:** Alta umidità. Controlla le foglie di cetrioli e lamponi.")

else:
    st.error("Impossibile recuperare i dati live. Verifica la connessione della stazione.")

st.caption(f"Ultimo aggiornamento: {datetime.now().strftime('%H:%M:%S')} - Dati storici inclusi per gestione terreno argilloso.")
