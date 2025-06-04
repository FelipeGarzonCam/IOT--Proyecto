import streamlit as st
import requests
import os
import json
import time
import tempfile
from gtts import gTTS
from audio_recorder_streamlit import audio_recorder
import speech_recognition as sr

# ── CONFIG ────────────────────────────────────────
API_KEY   = 'sk-53751d5c6f344a5dbc0571de9f51313e'
API_URL   = 'https://api.deepseek.com/v1/chat/completions'
DATOS_URL = 'http://localhost:5000/ultimos'

# ── FUNCIONES ─────────────────────────────────────
def get_datos():
    try:
        return requests.get(DATOS_URL, timeout=2).json()
    except:
        return None

def deepseek_chat(prompt, datos):
    system_msg = (
        "Eres un asistente que responde preguntas sobre un sistema de conteo de monedas.\n"
        f"Aquí están los datos en vivo:\n{json.dumps(datos, indent=2)}"
    )
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": prompt}
        ]
    }
    headers = {"Authorization":f"Bearer {API_KEY}",
               "Content-Type":"application/json"}
    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=20)
        r.raise_for_status()
        return r.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"⚠ Error DeepSeek: {e}"

def generar_y_reproducir_audio(texto):
    """Genera y reproduce audio TTS"""
    try:
        tts = gTTS(text=texto, lang='es')
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            tts.save(f.name)
            st.audio(f.name, autoplay=True)
            # Programar limpieza del archivo
            return f.name
    except Exception as e:
        st.error(f"Error generando audio: {e}")
        return None

# ── UI STREAMLIT ──────────────────────────────────
st.set_page_config(page_title="Dashboard IoT", page_icon="🤖", layout="wide")
st.title("📊 Dashboard Monedas & Carrito 🤖")

# Estados de sesión
if 'chat' not in st.session_state:
    st.session_state.chat = []
if 'ultimo_carrito' not in st.session_state:
    st.session_state.ultimo_carrito = ""
if 'refresh_enabled' not in st.session_state:
    st.session_state.refresh_enabled = True
if 'archivos_audio' not in st.session_state:
    st.session_state.archivos_audio = []

# Botón para controlar auto-refresh
col1, col2 = st.columns([3, 1])
with col2:
    if st.button("🔄 Refresh Manual"):
        st.rerun()
    
    refresh_auto = st.checkbox("Auto-refresh", value=st.session_state.refresh_enabled)
    st.session_state.refresh_enabled = refresh_auto

# Panel de datos
datos = get_datos()
if datos:
    cols = st.columns(4)
    cols[0].metric("Total monedas", datos.get("monedas_totales", 0))
    ir = datos.get("ir", {})
    cols[1].metric("Monedas $100",  ir.get("100", 0))
    cols[2].metric("Monedas $200",  ir.get("200", 0))
    cols[3].metric("Monedas $1000", ir.get("1000", 0))

    with st.expander("📋 Ver JSON completo"):
        st.json(datos)

    # Notificación de carrito
    carrito_actual = datos.get("carrito", "")
    if carrito_actual and carrito_actual != st.session_state.ultimo_carrito:
        st.success(f"🛒 Carrito procesado: ${carrito_actual}")
        
        # Generar audio para carrito
        archivo_audio = generar_y_reproducir_audio(f"Carrito salió por {carrito_actual} pesos")
        if archivo_audio:
            st.session_state.archivos_audio.append(archivo_audio)
        
        st.session_state.ultimo_carrito = carrito_actual
        # Deshabilitar auto-refresh temporalmente para evitar bucle
        st.session_state.refresh_enabled = False
        
        # Mostrar mensaje de control
        st.info("🔊 Reproduciendo audio... Auto-refresh pausado temporalmente")
        
        # Re-habilitar refresh después de 5 segundos
        if st.button("✅ Audio terminado - Reanudar auto-refresh"):
            st.session_state.refresh_enabled = True
            st.rerun()

# Chat
st.subheader("💬 Chat con IA")

# Mostrar historial
for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input de chat
if prompt := st.chat_input("Escribe tu pregunta..."):
    # Deshabilitar auto-refresh durante chat
    st.session_state.refresh_enabled = False
    
    # Agregar mensaje usuario
    st.session_state.chat.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generar respuesta
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            respuesta = deepseek_chat(prompt, datos or {})
        
        st.markdown(respuesta)
        
        # Generar audio
        archivo_audio = generar_y_reproducir_audio(respuesta)
        if archivo_audio:
            st.session_state.archivos_audio.append(archivo_audio)
    
    # Agregar respuesta al historial
    st.session_state.chat.append({"role": "assistant", "content": respuesta})
    
    # Mostrar controles de audio
    st.info("🔊 Reproduciendo respuesta... Use los controles abajo cuando termine")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Audio terminado"):
            st.session_state.refresh_enabled = True
            st.success("Auto-refresh reactivado")
            st.rerun()
    with col2:
        if st.button("🔇 Silenciar y continuar"):
            st.session_state.refresh_enabled = True
            st.rerun()

# Voz
st.subheader("🎤 Pregunta por voz")

audio_bytes = audio_recorder(
    text="Presiona para grabar",
    recording_color="#e74c3c",
    neutral_color="#34495e"
)

if audio_bytes:
    # Deshabilitar auto-refresh durante procesamiento de voz
    st.session_state.refresh_enabled = False
    
    st.audio(audio_bytes, format="audio/wav")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        f.write(audio_bytes)
        audio_path = f.name

    recognizer = sr.Recognizer()
    try:
        with st.spinner("Transcribiendo..."):
            with sr.AudioFile(audio_path) as source:
                audio_data = recognizer.record(source)
                texto = recognizer.recognize_google(audio_data, language="es-ES")
        
        st.success(f"📝 Transcripción: {texto}")
        
        # Agregar al chat
        st.session_state.chat.append({"role": "user", "content": texto})
        
        # Generar respuesta
        with st.spinner("Generando respuesta..."):
            respuesta = deepseek_chat(texto, datos or {})
        
        st.session_state.chat.append({"role": "assistant", "content": respuesta})
        
        st.markdown(f"🤖 **Respuesta:** {respuesta}")
        
        # Generar audio de respuesta
        archivo_audio = generar_y_reproducir_audio(respuesta)
        if archivo_audio:
            st.session_state.archivos_audio.append(archivo_audio)
        
        # Controles de audio
        st.info("🔊 Reproduciendo respuesta...")
        if st.button("✅ Continuar", key="voz_continuar"):
            st.session_state.refresh_enabled = True
            st.rerun()
            
    except sr.UnknownValueError:
        st.error("❌ No se pudo entender el audio")
        st.session_state.refresh_enabled = True
    except Exception as e:
        st.error(f"❌ Error: {e}")
        st.session_state.refresh_enabled = True
    
    try:
        os.remove(audio_path)
    except:
        pass

# Limpiar archivos de audio antiguos
if st.session_state.archivos_audio:
    archivos_a_eliminar = []
    for archivo in st.session_state.archivos_audio:
        try:
            if os.path.exists(archivo):
                # Intentar eliminar archivos que tengan más de 30 segundos
                if time.time() - os.path.getctime(archivo) > 30:
                    os.remove(archivo)
                    archivos_a_eliminar.append(archivo)
        except:
            archivos_a_eliminar.append(archivo)
    
    # Remover de la lista
    for archivo in archivos_a_eliminar:
        if archivo in st.session_state.archivos_audio:
            st.session_state.archivos_audio.remove(archivo)

# Auto-refresh controlado
if st.session_state.refresh_enabled:
    time.sleep(3)
    st.rerun()
else:
    # Mostrar estado cuando está pausado
    st.sidebar.info("⏸️ Auto-refresh pausado para reproducir audio")
    time.sleep(0.5)