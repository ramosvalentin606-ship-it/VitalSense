import streamlit as st
import io
import time
import random
import base64
from PIL import Image
import requests
import speech_recognition as sr
from streamlit_mic_recorder import mic_recorder

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="VitalSense | Tu Salud",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CONFIGURACIÓN DE LA API DE GEMINI ---
api_configurada = False
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    api_configurada = True
except Exception as e:
    st.sidebar.error("⚠️ Falta configurar GEMINI_API_KEY en secrets.toml.")

# --- FUNCIONES DE INTELIGENCIA ARTIFICIAL ---
def transcribir_audio(audio_bytes):
    r = sr.Recognizer()
    audio_file = io.BytesIO(audio_bytes)
    try:
        with sr.AudioFile(audio_file) as source:
            audio_data = r.record(source)
            texto = r.recognize_google(audio_data, language="es-CO") 
            return texto
    except sr.UnknownValueError:
        return "No pude entender el audio con claridad."
    except Exception as e:
        return None

def obtener_orientacion_medica(sintomas_texto, imagen_b64=None):
    """Envía los síntomas (y la imagen si existe) a la IA dinámicamente."""
    prompt_completo = f"""
    Eres el Doctor Andrés, el motor de IA de VitalSense. Eres un asistente médico virtual pre-diagnóstico.
    Analiza los síntomas descritos por el usuario (y la imagen proporcionada, si la hay) y responde con este formato en Markdown:
    
    ### 🔍 Posibles Afecciones
    (Menciona 2 o 3 afecciones posibles, aclarando que es una evaluación preliminar).
    
    ### 💡 Recomendaciones de Cuidado en Casa
    (Da 3 a 4 consejos prácticos).
    
    ### 🚨 Nivel de Alerta y Recomendación de Visita
    (Nivel Bajo, Medio o Alto. Di claramente si debe acudir a un centro médico).
    
    IMPORTANTE: Si hay una imagen, descríbela brevemente en tu análisis. Nunca des un diagnóstico definitivo. Usa un tono empático y profesional.
    
    SÍNTOMAS DEL PACIENTE:
    "{sintomas_texto}"
    """
    
    # Autodescubrimiento del modelo
    url_listar = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    nombre_modelo = "models/gemini-1.5-flash" # Por defecto (ideal para visión y texto)
    
    try:
        res_modelos = requests.get(url_listar).json()
        if 'models' in res_modelos:
            for m in res_modelos['models']:
                if 'generateContent' in m.get('supportedGenerationMethods', []) and 'gemini' in m.get('name', '').lower():
                    nombre_modelo = m['name']
                    break
    except:
        pass 
        
    url_generar = f"https://generativelanguage.googleapis.com/v1beta/{nombre_modelo}:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    # Estructuramos el mensaje para que acepte Texto + Imagen
    parts = [{"text": prompt_completo}]
    if imagen_b64:
        parts.append({
            "inlineData": {
                "mimeType": "image/jpeg",
                "data": imagen_b64
            }
        })
        
    data = {"contents": [{"parts": parts}]}
    
    try:
        respuesta = requests.post(url_generar, headers=headers, json=data)
        respuesta_json = respuesta.json()
        if 'error' in respuesta_json:
            return f"Error del servicio de IA: {respuesta_json['error']['message']}"
        return respuesta_json['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return "No se pudo conectar con el servidor de Inteligencia Artificial."

# --- ESTILOS PERSONALIZADOS (CSS MEJORADO) ---
st.markdown("""
    <style>
    .main-title { font-size: 42px; font-weight: 800; color: #1E3A8A; text-align: center; margin-bottom: 5px; }
    .sub-title { font-size: 18px; color: #64748B; text-align: center; margin-bottom: 30px; }
    .dr-andres-card { background-color: #F0F9FF; padding: 20px; border-radius: 15px; border-left: 6px solid #0EA5E9; margin-bottom: 25px; display: flex; align-items: center; gap: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
    .dr-andres-icon { font-size: 50px; }
    .sensor-card { background-color: #F0FDF4; padding: 20px; border-radius: 12px; border: 1px solid #BBF7D0; text-align: center; }
    .alert-card { background-color: #FEF2F2; padding: 20px; border-radius: 12px; border: 1px solid #FECACA; text-align: center; color: #991B1B; font-weight: bold;}
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px 8px 0px 0px; padding: 10px 20px; background-color: #F8FAFC; }
    .stTabs [aria-selected="true"] { background-color: #DBEAFE; font-weight: bold; color: #1D4ED8; }
    </style>
""", unsafe_allow_html=True)

# --- MENÚ LATERAL ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2854/2854904.png", width=80)
    st.title("VitalSense")
    st.markdown("---")
    st.subheader("📋 Datos del Paciente")
    nombre = st.text_input("Nombre Completo", placeholder="Ej. Juan Pérez")
    edad = st.number_input("Edad", min_value=0, max_value=120, value=25)
    st.markdown("---")
    st.info("Sistema de monitoreo y pre-diagnóstico multimodal.")

# --- CUERPO PRINCIPAL ---
st.markdown('<p class="main-title">🩺 VitalSense</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Plataforma Inteligente de Orientación Médica</p>', unsafe_allow_html=True)

# Tarjeta de Bienvenida del Doctor Andrés
st.markdown("""
<div class="dr-andres-card">
    <div class="dr-andres-icon">👨‍⚕️</div>
    <div>
        <h4 style="margin:0; color:#0369A1;">¡Hola! Soy el Doctor Andrés</h4>
        <p style="margin:5px 0 0 0; color:#334155;">
        Soy tu asistente virtual en VitalSense. Puedes escribirme, enviarme un audio o usar la cámara para mostrarme cualquier afección visible (como manchas o irritaciones). Estoy aquí para orientarte.
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

tab_sintomas, tab_sensores, tab_reporte = st.tabs([
    "🗣️ Consulta Multimodal", 
    "📊 Monitoreo Wokwi/ESP32", 
    "📋 Tu Reporte Médico"
])

# ==========================================
# TAB 1: INTERACCIÓN MULTIMODAL CON CÁMARA
# ==========================================
with tab_sintomas:
    st.write("### ¿Cómo te podemos ayudar hoy?")
    
    col1, col2 = st.columns(2)
    imagen_b64 = None
    audio = None
    
    with col1:
        with st.expander("✍️ Describir por Texto", expanded=True):
            sintomas_texto = st.text_area("Detalla tus molestias aquí:", height=130, placeholder="Ej. Tengo dolor de cabeza desde ayer...")
            
        with st.expander("🎙️ Grabar Nota de Voz"):
            st.info("Presiona el botón para hablar. Asegúrate de estar en un lugar sin mucho ruido.")
            audio = mic_recorder(start_prompt="🔴 Iniciar Grabación", stop_prompt="⏹️ Detener Grabación", key='recorder')
            if audio:
                st.audio(audio['bytes'])
                
    with col2:
        with st.expander("📷 Escáner Visual (Análisis por Imagen)", expanded=True):
            st.write("Si tienes un síntoma visible en la piel, tómale una foto.")
            img_file = st.camera_input("Capturar síntoma")
            if img_file:
                bytes_data = img_file.getvalue()
                # Convertimos la imagen a base64 para enviarla a Gemini
                imagen_b64 = base64.b64encode(bytes_data).decode('utf-8')
                st.success("✅ Imagen lista para ser procesada por la IA.")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Botón de análisis mejorado
    if st.button("🧠 Analizar Síntomas con el Doctor Andrés", type="primary", use_container_width=True):
        if not api_configurada:
            st.error("La API Key de Gemini no está configurada.")
        elif not (sintomas_texto or audio or imagen_b64):
            st.warning("Por favor, ingresa texto, un audio o una fotografía para poder analizar tu caso.")
        else:
            with st.spinner("El Doctor Andrés está procesando tu información..."):
                sintomas_finales = sintomas_texto if sintomas_texto else ""
                
                # Procesar audio si existe
                if audio is not None:
                    texto_transcrito = transcribir_audio(audio['bytes'])
                    if texto_transcrito and "No pude entender" not in texto_transcrito:
                        sintomas_finales += f" [Audio transcrito: {texto_transcrito}]"
                        st.toast("🎙️ Audio procesado correctamente")
                
                # Si solo mandó foto sin texto, agregamos un contexto por defecto
                if imagen_b64 and not sintomas_finales.strip():
                    sintomas_finales = "El paciente adjuntó una imagen de su síntoma físico para evaluación visual."
                    
                # Llamada a la IA con Texto e Imagen
                analisis_ia = obtener_orientacion_medica(sintomas_finales, imagen_b64)
                
                # Guardado en sesión
                st.session_state['resultado_ia'] = analisis_ia
                st.session_state['analizado'] = True
                st.session_state['sintomas_detectados'] = sintomas_finales
                
                st.success("✨ Análisis completado. Revisa la pestaña 'Tu Reporte Médico'.")

# ==========================================
# TAB 2: MONITOREO DE SENSORES
# ==========================================
with tab_sensores:
    st.write("### Simulación en Tiempo Real (Hardware)")
    st.info("Aquí se integrarán los datos provenientes del ESP32 simulado en Wokwi.")
    
    placeholder = st.empty()
    if st.toggle("Activar transmisión de sensores"):
        for i in range(5):
            ritmo_cardiaco = random.randint(65, 115)
            temperatura = round(random.uniform(36.2, 38.9), 1)
            
            with placeholder.container():
                c1, c2 = st.columns(2)
                with c1:
                    st.metric(label="❤️ Ritmo Cardíaco", value=f"{ritmo_cardiaco} BPM", delta=random.randint(-2, 2))
                with c2:
                    st.metric(label="🌡️ Temperatura", value=f"{temperatura} °C", delta=round(random.uniform(-0.5, 0.5), 1))
                
                if temperatura >= 38.0 or ritmo_cardiaco > 100:
                    st.markdown('<div class="alert-card">⚠️ <b>ALERTA:</b> Signos vitales alterados (Fiebre/Taquicardia).</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="sensor-card">✅ Signos vitales estables.</div>', unsafe_allow_html=True)
            time.sleep(1)

# ==========================================
# TAB 3: REPORTE FINAL
# ==========================================
with tab_reporte:
    if st.session_state.get('analizado', False):
        st.write(f"### 📋 Reporte Clínico Preliminar")
        st.caption(f"**Paciente:** {nombre if nombre else 'No registrado'} | **Edad:** {edad} años")
        st.markdown("---")
        
        # Imprime la respuesta detallada de la IA
        st.markdown(st.session_state['resultado_ia'])
        
        st.markdown("---")
        reporte_texto = f"REPORTE VITALSENSE (DR. ANDRÉS)\nPaciente: {nombre}\nEdad: {edad}\n\n{st.session_state['resultado_ia']}"
        
        st.download_button(
            label="📥 Descargar Reporte PDF/TXT",
            data=reporte_texto,
            file_name="VitalSense_Reporte.txt",
            mime="text/plain",
            type="primary"
        )
    else:
        st.info("👈 Ve a la pestaña 'Consulta Multimodal' e ingresa tus datos para generar este reporte.")
