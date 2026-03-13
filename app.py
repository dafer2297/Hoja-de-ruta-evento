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
    st.markdown(f"<h3 style='text-align: center; color: white;'>Área: {st.session_state.area_seleccionada}</h3>", unsafe_allow_html=True)
    st.write("")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Nuevo Evento", use_container_width=True):
            st.session_state.pantalla = 'info_evento' # Vamos a la primera parte
            st.rerun()
            
    with col2:
        if st.button("Evento ya hecho", use_container_width=True):
            st.info("Buscador de eventos en construcción...")
            
    st.write("---")
    if st.button("Volver al inicio"):
        st.session_state.pantalla = 'inicio'
        st.rerun()

# =====================================================================
# PANTALLA: INFORMACIÓN DEL EVENTO (Ex Sección 2)
# =====================================================================
elif st.session_state.pantalla == 'info_evento':
    st.markdown("<h3 style='text-align: center; color: white;'>Información del Evento</h3>", unsafe_allow_html=True)
    
    if st.session_state.area_seleccionada == "Culturas y Patrimonio":
        lista_responsables = ["Responsable 1", "Responsable 2", "Responsable 3", "Responsable 4", "Responsable 5"]
    else:
        lista_responsables = ["Responsable 6", "Responsable 7", "Responsable 8"]

    with st.form("form_info_evento"):
        responsable = st.selectbox("Responsable de Área", lista_responsables)
        tipo_area = st.selectbox("Tipo de Área", ["Propio", "Apoyo"])
        nombre_evento = st.text_input("Nombre del Evento")
        lugar_evento = st.text_input("Lugar del Evento")
        
        col_fecha, col_hora = st.columns(2)
        with col_fecha:
            fecha_evento = st.date_input("Fecha del Evento")
        with col_hora:
            hora_evento = st.time_input("Hora del Evento")
            
        celular = st.text_input("Número de Celular del Responsable", max_chars=10)
        submit_btn = st.form_submit_button("Guardar y Continuar")

        if submit_btn:
            if celular != "" and not celular.isdigit():
                st.error("❌ El celular solo debe contener números.")
            elif nombre_evento == "" or lugar_evento == "":
                st.error("❌ Llena el nombre y lugar del evento.")
            else:
                meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                mes_texto = meses[fecha_evento.month - 1]
                fecha_str = fecha_evento.strftime("%d/%m/%Y")
                hora_str = hora_evento.strftime("%H:%M")
                
                try:
                    fila_nueva = [mes_texto, st.session_state.area_seleccionada, responsable, tipo_area, nombre_evento, lugar_evento, fecha_str, hora_str, celular]
                    hoja_datos.append_row(fila_nueva)
                    
                    # Guardamos en memoria en qué fila se guardó para actualizarla en las siguientes pantallas
                    st.session_state.fila_actual = len(hoja_datos.get_all_values()) 
                    
                    st.success("✅ Evento creado.")
                    st.session_state.pantalla = 'entidades_externas'
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

# =====================================================================
# PANTALLA: ENTIDADES EXTERNAS (Ex Sección 3)
# =====================================================================
elif st.session_state.pantalla == 'entidades_externas':
    st.markdown("<h3 style='text-align: center; color: white;'>Coordinación con Entidades Externas</h3>", unsafe_allow_html=True)
    
    with st.form("form_externas"):
        aplica_externa = st.radio("¿Aplica coordinación con entidades externas?", ["No aplica", "Aplica"])
        
        entidad = ""
        solicitud = ""
        if aplica_externa == "Aplica":
            entidad = st.text_input("Nombre de la Entidad Externa")
            solicitud = st.text_area("Detalle de la Solicitud")
            
        submit_btn = st.form_submit_button("Guardar y Continuar")
        
        if submit_btn:
            # Aquí mandaríamos a actualizar las columnas correspondientes en el Excel usando st.session_state.fila_actual
            # Ejemplo: hoja_datos.update(f"J{st.session_state.fila_actual}:L{st.session_state.fila_actual}", [[aplica_externa, entidad, solicitud]])
            st.session_state.pantalla = 'coordinacion_interna'
            st.rerun()

# =====================================================================
# PANTALLA: COORDINACIÓN INTERNA (Ex Sección 4)
# =====================================================================
elif st.session_state.pantalla == 'coordinacion_interna':
    st.markdown("<h3 style='text-align: center; color: white;'>Coordinación Interna</h3>", unsafe_allow_html=True)
    
    with st.form("form_interna"):
        # 1. Dirección Propia (Culturas/Recreación)
        st.markdown("**1. Dirección de Culturas, Patrimonio y Recreación**")
        aplica_nuestra = st.radio("¿Aplica?", ["No aplica", "Aplica"], key="dir_nuestra")
        recursos_nuestros = ""
        if aplica_nuestra == "Aplica":
            recursos_nuestros = st.text_input("Recursos entregados")
        
        st.write("---")
        # 2. Dirección de Comunicación
        st.markdown("**2. Dirección de Comunicación**")
        aplica_com = st.radio("¿Aplica?", ["No aplica", "Aplica"], key="dir_com")
        nivel_com = ""
        if aplica_com == "Aplica":
            cumplio_com = st.radio("¿Se entregó lo solicitado?", ["Sí", "No"], key="cump_com")
            if cumplio_com == "Sí":
                st.info("Nivel de cumplimiento: 5 (100%) automático")
                nivel_com = "5"
            else:
                nivel_com = st.selectbox("Nivel de cumplimiento", ["1 (20%)", "2 (40%)", "3 (60%)", "4 (80%)"], key="niv_com")
                nivel_com = nivel_com[0] # Extrae solo el número

        # (Aquí puedes replicar el bloque de Comunicación para las Direcciones 3 y 4)
        
        submit_btn = st.form_submit_button("Guardar y Continuar")
        if submit_btn:
            # Lógica de actualización en Excel
            st.session_state.pantalla = 'logistica'
            st.rerun()

# =====================================================================
# PANTALLA: LOGÍSTICA Y TRANSPORTE (Ex Sección 5)
# =====================================================================
elif st.session_state.pantalla == 'logistica':
    st.markdown("<h3 style='text-align: center; color: white;'>Logística y Transporte</h3>", unsafe_allow_html=True)
    
    with st.form("form_logistica"):
        # Camionetas / Busetas
        st.markdown("**Camionetas o Busetas**")
        aplica_transporte = st.radio("¿Aplica transporte?", ["No aplica", "Aplica"], key="aplica_trans")
        
        cadena_choferes = ""
        if aplica_transporte == "Aplica":
            num_vehiculos = st.selectbox("Número de Camionetas/Busetas", [1, 2, 3, 4, 5, 6, 7, 8])
            datos_choferes = []
            
            # Generador dinámico de campos
            for i in range(num_vehiculos):
                c1, c2 = st.columns(2)
                with c1:
                    nom = st.text_input(f"Nombre Chofer {i+1}", key=f"nom_c_{i}")
                with c2:
                    cel = st.text_input(f"Celular {i+1}", max_chars=10, key=f"cel_c_{i}")
                
                if nom != "" or cel != "":
                    datos_choferes.append(f"{nom} ({cel})")
            
            # Une todos los contactos con un salto de línea para el Excel
            cadena_choferes = "\n".join(datos_choferes) 

        st.write("---")
        
        # Auxiliares
        st.markdown("**Auxiliares**")
        aplica_aux = st.radio("¿Aplica auxiliares?", ["No aplica", "Aplica"], key="aplica_aux")
        
        cadena_auxiliares = ""
        if aplica_aux == "Aplica":
            num_auxiliares = st.selectbox("Número de Auxiliares", [1, 2, 3, 4, 5, 6, 7, 8])
            datos_aux = []
            
            for i in range(num_auxiliares):
                c1, c2 = st.columns(2)
                with c1:
                    nom = st.text_input(f"Nombre Auxiliar {i+1}", key=f"nom_a_{i}")
                with c2:
                    cel = st.text_input(f"Celular {i+1}", max_chars=10, key=f"cel_a_{i}")
                
                if nom != "" or cel != "":
                    datos_aux.append(f"{nom} ({cel})")
            
            cadena_auxiliares = "\n".join(datos_aux)

        submit_btn = st.form_submit_button("Guardar y Continuar")
        if submit_btn:
             # Lógica de actualización en Excel
            st.session_state.pantalla = 'evaluacion_final'
            st.rerun()

# =====================================================================
# PANTALLA: EVALUACIÓN FINAL (Ex Sección 6)
# =====================================================================
elif st.session_state.pantalla == 'evaluacion_final':
    st.markdown("<h3 style='text-align: center; color: white;'>Evaluación Final</h3>", unsafe_allow_html=True)
    
    with st.form("form_evaluacion"):
        st.write("Califique el nivel de ejecución general del evento:")
        nivel_ejecucion = st.radio("Nivel de Ejecución", ["1 (Muy Deficiente)", "2 (Deficiente)", "3 (Regular)", "4 (Bueno)", "5 (Perfecto)"])
        
        observaciones = st.text_area("Observaciones Finales (Opcional)")
        
        st.write("---")
        submit_btn = st.form_submit_button("TERMINADO ✔️")
        
        if submit_btn:
            numero_nivel = nivel_ejecucion[0]
            
            # --- Aquí mandamos el SÍ a la última columna de Excel ---
            # Ejemplo: hoja_datos.update(f"Z{st.session_state.fila_actual}", [["SÍ"]])
            
            st.success("¡Flujo completado! El evento ha sido cerrado y registrado exitosamente.")
            # Reiniciamos la app para el siguiente evento
            st.session_state.pantalla = 'inicio'
            st.rerun()
