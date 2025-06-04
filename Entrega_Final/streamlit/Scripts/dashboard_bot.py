"""
Dashboard IoT + ChatBot (DeepSeek)
---------------------------------
  • Muestra datos que llegan desde Flask (/ultimos) en tiempo real.
  • ChatBot usa la API de DeepSeek; se le pasa el JSON actual como contexto
    para que pueda contestar preguntas naturales sobre las monedas, etc.
  • Recarga automática cada 5 s (funciona en Streamlit 1.18 → 1.33).
"""

import streamlit as st, requests, os, json, time, datetime as dt
from gtts import gTTS

# =============== CONFIGURACIÓN =================
API_KEY = 'sk-53751d5c6f344a5dbc0571de9f51313e'
API_URL = 'https://api.deepseek.com/v1/chat/completions'
DATOS_URL = 'http://localhost:5000/ultimos'   # Flask en el mismo PC
REFRESH_MS = 5000                             # 5 s

# =============== FUNCIONES BÁSICAS =============
def get_datos():
    try:
        return requests.get(DATOS_URL, timeout=2).json()
    except Exception:
        return None

def deepseek_chat(prompt, datos_json):
    """
    Enviamos el JSON como 'system' para que el modelo tenga contexto
    y el prompt del usuario como 'user'.
    """
    mensajes = [
        {"role": "system",
         "content": (
            "Eres un asistente que responde sobre un sistema de conteo de monedas.\n"
            f"Aquí tienes los datos en vivo en formato JSON:\n{json.dumps(datos_json, indent=2)}\n"
            "Usa esa información para contestar con precisión. "
            "Si el usuario pregunta algo fuera de contexto, respóndelo igualmente, pero "
            "cuando pregunten sobre monedas o el carrito, usa los números del JSON."
         )},
        {"role": "user", "content": prompt}
    ]
    headers = {"Authorization": f"Bearer {API_KEY}",
               "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": mensajes}
    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=25)
        r.raise_for_status()
        return r.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"⚠ Error llamando a DeepSeek: {e}"

def hablar(txt):
    tts = gTTS(text=txt, lang='es')
    tts.save("tts.mp3")
    st.audio("tts.mp3")
    os.remove("tts.mp3")

# =============== UI STREAMLIT ==================
st.set_page_config(page_title="Dashboard IoT", page_icon="🤖", layout="wide")
st.title("📊 Dashboard monedas & Carrito 🤖")

# Estado de sesión
ss = st.session_state
ss.setdefault("chat_history", [])        # lista de mensajes
ss.setdefault("ultimo_carrito", "")      # para avisos TTS

# ------------- PANEL DE DATOS ------------------
placeholder = st.empty()     # se rellenará en cada ciclo

def dibujar_panel(datos):
    """Muestra métricas bonitas"""
    ir = datos["ir"]
    total = datos.get("monedas_totales", sum(ir.values()))
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total monedas", total)
    col2.metric("Monedas $100",  ir.get("100", 0))
    col3.metric("Monedas $200",  ir.get("200", 0))
    col4.metric("Monedas $1000", ir.get("1000", 0))

    st.write("### Detalle completo")
    st.json(datos, expanded=False)

# ------------- BUCLE DE REFRESCO --------------
#   Nota: usar st.experimental_rerun() al final
datos_actuales = get_datos()
if datos_actuales:
    with placeholder.container():
        dibujar_panel(datos_actuales)

    # Aviso por voz si carrito salió
    if datos_actuales["carrito"] and datos_actuales["carrito"] != ss.ultimo_carrito:
        hablar(f"El carrito salió por la denominación {datos_actuales['carrito']} pesos.")
        ss.ultimo_carrito = datos_actuales["carrito"]

# ------------- HISTORIAL CHAT -----------------
for m in ss.chat_history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ------------- ENTRADA DEL USUARIO ------------
if prompt := st.chat_input("Pregúntame sobre el sistema…"):
    # Mostrar mensaje del usuario
    with st.chat_message("user"):
        st.markdown(prompt)
    ss.chat_history.append({"role": "user", "content": prompt})

    # Obtener respuesta del modelo con contexto
    datos_contexto = get_datos() or {}
    respuesta = deepseek_chat(prompt, datos_contexto)

    # Mostrar y hablar
    with st.chat_message("assistant"):
        st.markdown(respuesta)
        hablar(respuesta)

    ss.chat_history.append({"role": "assistant", "content": respuesta})

# ------------- AUTO-REFRESH -------------------
#   En <=1.32 usamos experimental_rerun, en >=1.33 podemos usar st.rerun
time.sleep(REFRESH_MS / 1000)
if hasattr(st, "rerun"):
    st.rerun()
else:
    st.experimental_rerun()