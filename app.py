import streamlit as st
import requests

# Configurazione per il tuo Pixel 10 Pro
st.set_page_config(page_title="Orto ITRENT123", layout="centered")

st.title("🌿 Dashboard Orto Trento")
st.subheader("Stazione: Wunderground ITRENT123")

# --- LOGICA DI CALCOLO ---
def calcola_consigli(temp, pioggia, vento, umidita):
    consigli = []
    # Logica Irrigazione (Terreno Argilloso)
    if pioggia > 5:
        irrigazione = "🔴 STOP (Terreno Saturo)"
        consigli.append("L'argilla trattiene l'acqua: non irrigare per 24-48h per evitare asfissia radicale.")
    else:
        irrigazione = "🟢 ATTIVA (Poco a poco)"
        consigli.append("Irrigazione a goccia consigliata per pomodori e meloni.")

    # Logica Trattamenti (Pompa Elettrica - Zeolite/Neem)
    if vento < 10 and umidita < 75:
        trattamento = "🟢 IDEALE"
    else:
        trattamento = "🔴 EVITARE (Vento/Umidità)"
        
    return irrigazione, trattamento, consigli

# --- SIMULAZIONE DATI (In attesa della tua API Key) ---
# Qui poi collegheremo i dati reali della tua stazione
temp, pioggia, vento, umidita = 19.5, 7.2, 4.0, 82.0

irrig, tratt, suggerimenti = calcola_consigli(temp, pioggia, vento, umidita)

# --- INTERFACCIA MOBILE ---
col1, col2 = st.columns(2)
with col1:
    st.metric("Pioggia Oggi", f"{pioggia} mm")
    st.write(f"**Irrigazione:** {irrig}")

with col2:
    st.metric("Vento", f"{vento} km/h")
    st.write(f"**Trattamenti:** {tratt}")

st.divider()
st.info(f"💡 **Consiglio Tecnico:** {suggerimenti[0]}")

# Alert Elateridi
if temp > 12 and pioggia > 5:
    st.warning("⚠️ **Allerta Elateridi:** Terreno umido e caldo, i 'ferretti' potrebbero risalire. Monitora le radici dei meloni.")
