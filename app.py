import streamlit as st
import base64
import json
import gspread
from google.oauth2.service_account import Credentials

# 1. Configuración de la página
st.set_page_config(page_title="Hoja de Ruta - Eventos", layout="centered")

# --- NUEVO: CONEXIÓN A GOOGLE SHEETS ---
# Usamos cache para que el "mensajero" no se conecte desde cero cada vez que damos un clic
@st.cache_resource
def conectar_excel():
    try:
        # A. Sacar la llave de la bóveda secreta de Streamlit
        llave_secreta = st.secrets["json_key"]
        credenciales_dict = json.loads(llave_secreta)
        
        # B. Darle permisos al robot para leer y escribir
        permisos = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # C. Crear la credencial oficial
        credenciales = Credentials.from_service_account_info(credenciales_dict, scopes=permisos)
        
        # D. Conectar el mensajero (gspread)
        cliente = gspread.authorize(credenciales)
        
        # E. Abrir el archivo de Drive (El nombre debe ser EXACTAMENTE el que tiene en Drive)
        # Asegúrate de haberle dado permiso de "Editor" al correo del robot en este archivo
        archivo = cliente.open("Hoja de ruta dirección de Culturas, Patrimonio y Recreación")
        hoja = archivo.sheet1 # Selecciona la primera pestaña del Excel
        
        return hoja
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

# Inicializar la tubería de datos
hoja_datos = conectar_excel()

# Pequeña prueba visual (luego la borraremos)
if hoja_datos is not None:
    st.toast("¡Conexión exitosa con el Excel!", icon="✅")


# --- DE AQUÍ EN ADELANTE VA EL RESTO DE TU CÓDIGO ---
# (La función agregar_fondo, el control de navegación, y las pantallas que ya tenías)

# 2. Función para cargar el fondo de pantalla de forma fija
def agregar_fondo(imagen_archivo):
    with open(imagen_archivo, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url(data:image/{"png"};base64,{encoded_string});
            background-size: cover;
            background-position: center;
            background-attachment: fixed; /* Esto hace que el fondo se quede quieto al hacer scroll */
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Aplicar el fondo con el nombre exacto que me diste
try:
    agregar_fondo("fondo_app.png")
except FileNotFoundError:
    pass

# 3. Control de Navegación (Memoria de la app)
if 'pantalla' not in st.session_state:
    st.session_state.pantalla = 'inicio'
if 'area_seleccionada' not in st.session_state:
    st.session_state.area_seleccionada = None

# --- PANTALLA 1: INICIO ---
if st.session_state.pantalla == 'inicio':
    
    # Logo superior centrado
    col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
    with col_logo2:
        try:
            st.image("logo_superior.png", use_container_width=True)
        except:
            st.write("*(Falta cargar logo_superioir.png)*")
            
    st.write("---") 
    st.markdown("<h2 style='text-align: center; color: white;'>Seleccione su Área</h2>", unsafe_allow_html=True)
    st.write("") 
    
    # Dos columnas para los íconos de los departamentos
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            st.image("icono_cultura.png", use_container_width=True)
        except:
            st.write("*(Falta icono_cultura.png)*")
        if st.button("Culturas y Patrimonio", use_container_width=True):
            st.session_state.area_seleccionada = "Culturas y Patrimonio"
            st.session_state.pantalla = 'opciones_evento' # Nos manda a la pantalla 2
            st.rerun()

    with col2:
        try:
            st.image("icono_recreacion.png", use_container_width=True)
        except:
            st.write("*(Falta icono_recreacion.png)*")
        if st.button("Recreación", use_container_width=True):
            st.session_state.area_seleccionada = "Recreación"
            st.session_state.pantalla = 'opciones_evento' # Nos manda a la pantalla 2
            st.rerun()

# --- PANTALLA 2: NUEVO O EXISTENTE ---
elif st.session_state.pantalla == 'opciones_evento':
    # Título que recuerda el área elegida
    st.markdown(f"<h3 style='text-align: center; color: white;'>Área: {st.session_state.area_seleccionada}</h3>", unsafe_allow_html=True)
    st.write("")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Nuevo Evento", use_container_width=True):
            # Aquí irá la lógica para ir a la Sección 2
            st.success("Yendo a crear un Nuevo Evento...") 
            
    with col2:
        if st.button("Evento ya hecho", use_container_width=True):
            # Aquí irá la lógica para buscar en el Excel
            st.info("Yendo a buscar eventos existentes...")
            
    st.write("---")
    # Botón para regresar si se equivocaron de área
    if st.button("Volver al inicio"):
        st.session_state.pantalla = 'inicio'
        st.rerun()
