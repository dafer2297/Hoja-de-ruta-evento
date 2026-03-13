import streamlit as st
import base64

# 1. Configuración de la página
st.set_page_config(page_title="Hoja de Ruta - Eventos", layout="centered")

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
            st.image("logo_superioir.png", use_container_width=True)
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
