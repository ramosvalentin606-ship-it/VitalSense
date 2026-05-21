import streamlit as st
import io
import time
import random
from PIL import Image
import requests
import speech_recognition as sr
from streamlit_mic_recorder import mic_recorder

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="VitalSense",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CONFIGURACIÓN DE LA API DE GEMINI ---
api_configurada = False
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    api_configurada = True
except FileNotFoundError:
    st.sidebar.error("⚠️ Falta el archivo secrets.toml.")
except KeyError:
    st.sidebar.error("⚠️ Falta configurar GEMINI_API_KEY en secrets.toml.")
except Exception as e:
    st.sidebar.error(f"⚠️ Error al configurar la clave: {e}")

# --- FUNCIONES DE INTELIGENCIA ARTIFICIAL ---
def transcribir_audio(audio_bytes):
    """Convierte el audio del usuario a texto."""
    r = sr.Recognizer()
    audio_file = io.BytesIO(audio_bytes)
    try:
        with sr.AudioFile(audio_file) as source:
            audio_data = r.record(source)
            texto = r.recognize_google(audio_data, language="es-CO") 
            return texto
    except sr.UnknownValueError:
        return "Lo siento, no pude entender el audio."
    except Exception as e:
        return None

def obtener_orientacion_medica(sintomas_texto):
    """Envía los síntomas a la IA descubriendo el modelo válido dinámicamente."""
    prompt_completo = f"""
    Eres el motor de IA de VitalSense, un asistente de orientación médica pre-diagnóstica.
    Analiza los síntomas descritos por el usuario y responde estrictamente con este formato en Markdown:
    
    ### 🔍 Posibles Afecciones
    (Menciona 2 o 3 afecciones posibles, aclarando que es una evaluación preliminar).
    
    ### 💡 Recomendaciones de Cuidado en Casa
    (Da 3 a 4 consejos prácticos y seguros para aliviar los síntomas).
    
    ### 🚨 Nivel de Alerta y Recomendación de Visita
    (Indica si el nivel es Bajo, Medio o Alto. Di claramente si debe acudir a un médico o urgencias).
    
    IMPORTANTE: Nunca des un diagnóstico definitivo ni recetes medicamentos. Usa un tono empático, profesional y tranquilizador.
    
    SÍNTOMAS DEL PACIENTE:
    "{sintomas_texto}"
    """
    
    # 1. AUTODESCUBRIMIENTO: Preguntarle a Google qué modelos están disponibles para tu Clave
    url_listar = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    nombre_modelo = None
    
    try:
        res_modelos = requests.get(url_listar).json()
        if 'models' in res_modelos:
            for m in res_modelos['models']:
                # Buscamos un modelo que permita generar texto y sea de la familia Gemini
                if 'generateContent' in m.get('supportedGenerationMethods', []) and 'gemini' in m.get('name', '').lower():
                    nombre_modelo = m['name'] # Ejemplo: retorna 'models/gemini-1.5-flash'
                    break
    except Exception as e:
        pass # Si falla, continuará e intentará usar el modelo por defecto
        
    # Si la búsqueda falló, usamos este por defecto como último recurso
    if not nombre_modelo:
        nombre_modelo = "models/gemini-1.5-flash"
        
    # 2. PETICIÓN REAL DE ANÁLISIS
    url_generar = f"https://generativelanguage.googleapis.com/v1beta/{nombre_modelo}:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt_completo}]}]
    }
    
    try:
        respuesta = requests.post(url_generar, headers=headers, json=data)
        respuesta_json = respuesta.json()
        
        # Si la API de Google devuelve un error, lo mostramos indicando el modelo exacto que falló
        if 'error' in respuesta_json:
            error_msg = respuesta_json['error']['message']
            st.error(f"Error de Google API usando el modelo '{nombre_modelo}': {error_msg}")
            return f"Ocurrió un error con el servicio de IA. Revisa los mensajes de error arriba."
            
        return respuesta_json['candidates'][0]['content']['parts'][0]['text']
        
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return "No se pudo conectar con el servidor de Inteligencia Artificial."

# --- ESTILOS PERSONALIZADOS (CSS) ---
st.markdown("""
    <style>
    .main-title { font-size: 38px; font-weight: bold; color: #007bff; text-align: center; margin-bottom: 20px; }
    .sensor-card { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #28a745; margin-bottom: 10px; }
    .alert-card { background-color: #fff3cd; padding: 15px; border-radius: 10px; border-left: 5px solid #ffc107; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- MENÚ LATERAL ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2854/2854904.png", width=100)
st.sidebar.title("VitalSense Panel")
st.sidebar.subheader("📋 Registro de Paciente")
nombre = st.sidebar.text_input("Nombre Completo")
edad = st.sidebar.number_input("Edad", min_value=0, max_value=120, value=25)

# --- CUERPO PRINCIPAL ---
st.markdown('<p class="main-title">🩺 VitalSense: Orientación Médica Multimodal</p>', unsafe_allow_html=True)
st.write("Identifica posibles afecciones de manera rápida y monitorea signos vitales en tiempo real.")

tab_sintomas, tab_sensores, tab_reporte = st.tabs([
    "🗣️ Consulta de Síntomas", 
    "📊 Monitoreo de Sensores", 
    "📋 Estado Final y Reporte"
])

# ==========================================
# TAB 1: INTERACCIÓN MULTIMODAL
# ==========================================
with tab_sintomas:
    st.header("Déjanos saber qué sientes")
    st.write("Puedes usar texto, tu voz o la cámara para describir tus síntomas.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("✍️ Entrada por Texto")
        sintomas_texto = st.text_area("Describe detalladamente tus molestias aquí:")
        
    with col2:
        st.subheader("🎙️ Entrada por Voz")
        st.write("Presiona para grabar tus síntomas:")
        audio = mic_recorder(start_prompt="🔴 Grabar Voz", stop_prompt="⏹️ Detener", key='recorder')
        if audio:
            st.audio(audio['bytes'])
            st.success("¡Audio recibido con éxito!")
            
    with col3:
        st.subheader("📷 Escaneo Inteligente")
        img_file = st.camera_input("Toma una foto (Opcional, en desarrollo)")
        if img_file:
            st.image(Image.open(img_file), caption="Imagen capturada", use_container_width=True)
            st.info("La integración de IA con imágenes estará disponible pronto.")

    st.write("---")
    
    if st.button("Analizar Síntomas", type="primary"):
        if not api_configurada:
            st.error("No se puede analizar porque la API Key de Gemini no está configurada o es incorrecta.")
        else:
            with st.spinner("La Inteligencia Artificial está analizando tus síntomas y verificando conexión..."):
                sintomas_finales = ""
                
                if audio is not None:
                    st.info("Procesando tu nota de voz...")
                    texto_transcrito = transcribir_audio(audio['bytes'])
                    if texto_transcrito and texto_transcrito != "Lo siento, no pude entender el audio.":
                        sintomas_finales = texto_transcrito
                        st.success(f"🎙️ Escuchamos: '{sintomas_finales}'")
                    else:
                        st.error("Hubo un problema transcribiendo el audio. Intenta usar el texto.")
                elif sintomas_texto.strip() != "":
                    sintomas_finales = sintomas_texto
                    
                if sintomas_finales:
                    analisis_ia = obtener_orientacion_medica(sintomas_finales)
                    st.session_state['resultado_ia'] = analisis_ia
                    st.session_state['analizado'] = True
                    st.session_state['sintomas_detectados'] = sintomas_finales
                    st.success("Análisis completado exitosamente. Ve a la pestaña 'Estado Final y Reporte'.")
                else:
                    st.warning("Por favor, describe tus síntomas escribiendo o grabando un audio antes de analizar.")

# ==========================================
# TAB 2: MONITOREO DE SENSORES
# ==========================================
with tab_sensores:
    st.header("📊 Simulación de Sensores Biomédicos")
    st.write("Simulación de conexión con ESP32 / WOKWI.")
    
    placeholder = st.empty()
    
    if st.checkbox("Activar monitoreo en vivo"):
        for i in range(5):
            ritmo_cardiaco = random.randint(65, 115)
            temperatura = round(random.uniform(36.2, 38.9), 1)
            
            with placeholder.container():
                c1, c2 = st.columns(2)
                with c1:
                    st.metric(label="❤️ Ritmo Cardíaco", value=f"{ritmo_cardiaco} BPM")
                with c2:
                    st.metric(label="🌡️ Temperatura Corporal", value=f"{temperatura} °C")
                
                if temperatura >= 38.0 or ritmo_cardiaco > 100:
                    st.markdown(f"""
                    <div class="alert-card">
                        ⚠️ <b>ALERTA AUTOMÁTICA:</b> Se detectaron anomalías (Fiebre o Taquicardia). 
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="sensor-card">
                        ✅ Signos vitales estables dentro del rango normal.
                    </div>
                    """, unsafe_allow_html=True)
                    
            time.sleep(1)

# ==========================================
# TAB 3: ESTADO FINAL Y REPORTE
# ==========================================
with tab_reporte:
    st.header("📋 Conclusión y Recomendaciones")
    
    if st.session_state.get('analizado', False):
        st.subheader(f"Reporte de Orientación para: {nombre if nombre else 'Paciente Anónimo'}")
        if edad > 0:
            st.info(f"Edad: {edad} años | Síntomas reportados: {st.session_state.get('sintomas_detectados', '')}")
        
        st.markdown(st.session_state['resultado_ia'])
        st.write("---")
        
        reporte_texto = f"REPORTE VITALSENSE\n"
        reporte_texto += f"------------------\n"
        reporte_texto += f"Paciente: {nombre if nombre else 'Anónimo'}\n"
        reporte_texto += f"Edad: {edad}\n"
        reporte_texto += f"Síntomas declarados: {st.session_state.get('sintomas_detectados', '')}\n\n"
        reporte_texto += f"ANALISIS IA:\n"
        reporte_texto += f"{st.session_state['resultado_ia']}\n"
        
        st.download_button(
            label="📥 Descargar Reporte Médico (TXT)",
            data=reporte_texto,
            file_name="reporte_vitalsense.txt",
            mime="text/plain",
            type="primary"
        )
    else:
        st.warning("Por favor, ve a la pestaña 'Consulta de Síntomas' y analiza tus datos primero.")
