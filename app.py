import streamlit as st
import base64
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date

# ==========================================
# 1. CONFIGURACIÓN Y CONEXIÓN
# ==========================================
st.set_page_config(page_title="Hoja de Ruta - Eventos", layout="wide")

def agregar_fondo(imagen_archivo):
    try:
        with open(imagen_archivo, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url(data:image/png;base64,{encoded_string});
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
            }}
            .stButton>button {{ width: 100%; }}
            
            /* EFECTO DE LEVITACIÓN PARA LAS IMÁGENES */
            [data-testid="stImage"] img {{
                transition: transform 0.3s ease-in-out;
            }}
            [data-testid="stImage"] img:hover {{
                transform: translateY(-15px);
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    except:
        pass

agregar_fondo("fondo_app.png")

@st.cache_resource
def conectar_excel():
    try:
        llave_secreta = st.secrets["json_key"]
        credenciales_dict = json.loads(llave_secreta)
        permisos = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        credenciales = Credentials.from_service_account_info(credenciales_dict, scopes=permisos)
        cliente = gspread.authorize(credenciales)
        archivo = cliente.open("Hoja de ruta dirección de Culturas, Patrimonio y Recreación")
        return archivo.sheet1
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

hoja_datos = conectar_excel()

# ==========================================
# 2. FUNCIONES AUXILIARES Y MEMORIA
# ==========================================
if 'pantalla' not in st.session_state: st.session_state.pantalla = 'inicio'
if 'area_seleccionada' not in st.session_state: st.session_state.area_seleccionada = None
if 'fila_actual' not in st.session_state: st.session_state.fila_actual = None
if 'modo' not in st.session_state: st.session_state.modo = "nuevo"

if 'fila_datos' not in st.session_state:
    st.session_state.fila_datos = [""] * 60

def calcular_dias(fecha_inicio, fecha_fin):
    if not fecha_inicio or not fecha_fin or fecha_inicio == "" or fecha_fin == "": return ""
    try:
        d1 = datetime.strptime(fecha_inicio, "%d/%m/%Y").date()
        d2 = datetime.strptime(fecha_fin, "%d/%m/%Y").date()
        return str((d2 - d1).days)
    except:
        return ""

def guardar_en_excel():
    if st.session_state.fila_actual:
        rango = f"A{st.session_state.fila_actual}:BH{st.session_state.fila_actual}"
        hoja_datos.update(values=[st.session_state.fila_datos], range_name=rango)

def navegar(destino):
    guardar_en_excel()
    st.session_state.pantalla = destino

# ==========================================
# 3. PANTALLAS DE NAVEGACIÓN
# ==========================================

# --- PANTALLA 1: INICIO ---
if st.session_state.pantalla == 'inicio':
    col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
    with col_logo2:
        try: st.image("logo_superior.png", use_container_width=True)
        except: pass
            
    st.markdown("<h2 style='text-align: center; color: white;'>Seleccione su Área</h2>", unsafe_allow_html=True)
    st.write("---") 
    col1, col2 = st.columns(2)
    with col1:
        try: st.image("icono_cultura.png", use_container_width=True)
        except: pass
        if st.button("Culturas y Patrimonio"):
            st.session_state.area_seleccionada = "Culturas y Patrimonio"
            st.session_state.pantalla = 'opciones_evento'
            st.rerun()
    with col2:
        try: st.image("icono_recreacion.png", use_container_width=True)
        except: pass
        if st.button("Recreación"):
            st.session_state.area_seleccionada = "Recreación"
            st.session_state.pantalla = 'opciones_evento'
            st.rerun()

# --- PANTALLA 2: NUEVO O EN PROCESO ---
elif st.session_state.pantalla == 'opciones_evento':
    st.markdown(f"<h3 style='text-align: center; color: white;'>Área: {st.session_state.area_seleccionada}</h3>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Nuevo Evento"):
            st.session_state.modo = "nuevo"
            st.session_state.fila_datos = [""] * 60
            st.session_state.pantalla = 'seccion_2'
            st.rerun()
    with col2:
        if st.button("Evento en Proceso"):
            st.session_state.modo = "editar"
            st.session_state.pantalla = 'buscador_eventos'
            st.rerun()
    st.write("---")
    if st.button("Volver al Inicio"):
        st.session_state.pantalla = 'inicio'
        st.rerun()

# --- BUSCADOR DE EVENTOS EN PROCESO ---
elif st.session_state.pantalla == 'buscador_eventos':
    st.markdown("<h3 style='text-align: center; color: white;'>Seleccionar Evento en Proceso</h3>", unsafe_allow_html=True)
    
    lista_resp = ["Responsable 1", "Responsable 2", "Responsable 3", "Responsable 4", "Responsable 5"] if st.session_state.area_seleccionada == "Culturas y Patrimonio" else ["Responsable 6", "Responsable 7", "Responsable 8"]
    resp_busqueda = st.selectbox("Seleccione el Responsable", lista_resp)
    
    todos_los_datos = hoja_datos.get_all_values()
    eventos_encontrados = []
    for i in range(1, len(todos_los_datos)):
        fila = todos_los_datos[i]
        if len(fila) > 3 and fila[1] == st.session_state.area_seleccionada and fila[3] == resp_busqueda:
            if len(fila) < 60 or fila[59] != "Finalizado":
                eventos_encontrados.append((i + 1, fila))
    
    eventos_encontrados.reverse()
    
    if eventos_encontrados:
        opciones_mostrar = {f"{ev[1][4]} (Fecha: {ev[1][10]})": ev for ev in eventos_encontrados}
        evento_seleccionado = st.selectbox("Seleccione el Evento", list(opciones_mostrar.keys()))
        
        col1, col2 = st.columns(2)
        with col2:
            if st.button("Abrir Evento"):
                fila_real, datos_fila = opciones_mostrar[evento_seleccionado]
                st.session_state.fila_actual = fila_real
                mientras_datos = datos_fila + [""] * (60 - len(datos_fila))
                st.session_state.fila_datos = mientras_datos[:60]
                st.session_state.pantalla = 'seccion_2'
                st.rerun()
    else:
        st.info("No se encontraron eventos en proceso para este responsable.")
        
    with col1:
        if st.button("Regresar"):
            st.session_state.pantalla = 'opciones_evento'
            st.rerun()

# ==========================================
# 4. FORMULARIOS (SECCIONES 2 A 6)
# ==========================================

# --- SECCIÓN 2: INFORMACIÓN DEL EVENTO ---
elif st.session_state.pantalla == 'seccion_2':
    st.markdown("<h3 style='text-align: center; color: white;'>Información del Evento</h3>", unsafe_allow_html=True)
    
    lista_resp = ["Responsable 1", "Responsable 2", "Responsable 3", "Responsable 4", "Responsable 5"] if st.session_state.area_seleccionada == "Culturas y Patrimonio" else ["Responsable 6", "Responsable 7", "Responsable 8"]
    d = st.session_state.fila_datos
    
    resp_index = lista_resp.index(d[3]) if d[3] in lista_resp else 0
    responsable = st.selectbox("Responsable de Área", lista_resp, index=resp_index)
    
    nombre_evento = st.text_input("Nombre del evento", value=d[4])
    tipo_evento = st.selectbox("Tipo de evento", ["Propio", "Apoyo"], index=0 if d[5] != "Apoyo" else 1)
    
    c1, c2 = st.columns(2)
    with c1:
        inicio_org = st.date_input("Inicio organización del evento")
        fecha_evento = st.date_input("Fecha del evento")
    with c2:
        nombre_org = st.text_input("Nombre del organizador", value=d[7])
        hora_evento = st.time_input("Hora del evento")
        
    celular_org = st.text_input("Celular del organizador", max_chars=10, value=d[8])
    lugar_evento = st.text_input("Lugar del evento", value=d[9])
    
    st.write("---")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        btn_regresar = st.button("⬅️ Regresar y Guardar")
    with col_btn2:
        btn_guardar = st.button("Guardar y Continuar ➡️")
        
    if btn_guardar or btn_regresar:
        # Validación ESTRICTA de 10 dígitos
        if celular_org != "" and (not celular_org.isdigit() or len(celular_org) != 10):
            st.error("❌ El celular del organizador debe tener exactamente 10 dígitos numéricos.")
        elif nombre_evento == "":
            st.error("❌ El nombre del evento es obligatorio.")
        else:
            meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            mes_texto = meses[fecha_evento.month - 1]
            fecha_org_str = inicio_org.strftime("%d/%m/%Y")
            fecha_ev_str = fecha_evento.strftime("%d/%m/%Y")
            hora_str = hora_evento.strftime("%H:%M")
            
            st.session_state.fila_datos[1] = st.session_state.area_seleccionada
            st.session_state.fila_datos[2] = mes_texto
            st.session_state.fila_datos[3] = responsable
            st.session_state.fila_datos[4] = nombre_evento
            st.session_state.fila_datos[5] = tipo_evento
            st.session_state.fila_datos[6] = fecha_org_str
            st.session_state.fila_datos[7] = nombre_org
            st.session_state.fila_datos[8] = celular_org
            st.session_state.fila_datos[9] = lugar_evento
            st.session_state.fila_datos[10] = fecha_ev_str
            st.session_state.fila_datos[11] = hora_str
            
            if st.session_state.modo == "nuevo" and not st.session_state.fila_actual:
                num_filas = len(hoja_datos.col_values(1))
                st.session_state.fila_datos[0] = str(num_filas)
                hoja_datos.append_row(st.session_state.fila_datos)
                st.session_state.fila_actual = num_filas + 1
            
            if btn_guardar: navegar('seccion_3')
            if btn_regresar: navegar('opciones_evento')
            st.rerun()

# --- SECCIÓN 3: EXTERNAS (MÚLTIPLES ENTIDADES) ---
elif st.session_state.pantalla == 'seccion_3':
    st.markdown("<h3 style='text-align: center; color: white;'>Coordinación con Entidades Externas</h3>", unsafe_allow_html=True)
    d = st.session_state.fila_datos
    
    aplica = st.radio("¿Aplica?", ["No aplica", "Aplica"], index=1 if d[12] != "" else 0)
    
    entidades_str = ""; solicitudes_str = ""; f_sol_str = ""; f_resp_str = ""
    
    if aplica == "Aplica":
        # Selector de número de entidades (Máximo 8)
        num_entidades = st.selectbox("¿Cuántas entidades externas?", list(range(1, 9)))
        
        lista_nombres = []; lista_solicitudes = []; lista_f_sol = []; lista_f_resp = []
        
        for i in range(num_entidades):
            st.markdown(f"**Entidad {i+1}**")
            nom = st.text_input(f"Nombre de la entidad {i+1}", key=f"ent_{i}")
            sol = st.text_area(f"Solicitud {i+1}", key=f"sol_{i}")
            c1, c2 = st.columns(2)
            with c1: fs = st.date_input(f"Fecha de solicitud {i+1}", key=f"fs_{i}")
            with c2: fr = st.date_input(f"Fecha de respuesta {i+1}", key=f"fr_{i}")
            
            if nom != "": # Solo lo agrupa si escribieron el nombre
                lista_nombres.append(f"{i+1}. {nom}")
                lista_solicitudes.append(f"{i+1}. {sol}")
                lista_f_sol.append(f"{i+1}. {fs.strftime('%d/%m/%Y')}")
                lista_f_resp.append(f"{i+1}. {fr.strftime('%d/%m/%Y')}")
                
        # Une las listas con saltos de línea para que quede perfecto en la celda de Excel
        entidades_str = "\n".join(lista_nombres)
        solicitudes_str = "\n".join(lista_solicitudes)
        f_sol_str = "\n".join(lista_f_sol)
        f_resp_str = "\n".join(lista_f_resp)
        
    st.write("---")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1: btn_regresar = st.button("⬅️ Regresar y Guardar")
    with col_btn2: btn_guardar = st.button("Guardar y Continuar ➡️")
    
    if btn_guardar or btn_regresar:
        if aplica == "Aplica":
            st.session_state.fila_datos[12] = entidades_str
            st.session_state.fila_datos[13] = solicitudes_str
            st.session_state.fila_datos[14] = f_sol_str
            st.session_state.fila_datos[15] = f_resp_str
        else:
            st.session_state.fila_datos[12:16] = ["", "", "", ""]
            
        if btn_guardar: navegar('seccion_4')
        if btn_regresar: navegar('seccion_2')
        st.rerun()

# --- SECCIÓN 4: INTERNAS ---
elif st.session_state.pantalla == 'seccion_4':
    st.markdown("<h3 style='text-align: center; color: white;'>Coordinación con Áreas Internas</h3>", unsafe_allow_html=True)
    d = st.session_state.fila_datos
    
    st.markdown("**1. Dirección Culturas, Patrimonio y Recreación**")
    ap_culturas = st.radio("¿Aplica?", ["No aplica", "Aplica"], key="r_cult", index=1 if d[16]=="Aplica" else 0)
    rec_culturas = st.text_input("Recursos entregados", value=d[17]) if ap_culturas == "Aplica" else ""
    
    st.write("---")
    def dibujar_direccion(nombre, idx_base):
        st.markdown(f"**{nombre}**")
        aplica = st.radio("¿Aplica?", ["No aplica", "Aplica"], key=f"ap_{idx_base}", index=1 if d[idx_base]=="Aplica" else 0)
        if aplica == "Aplica":
            sol = st.text_input("Solicitud realizada", value=d[idx_base+1], key=f"s_{idx_base}")
            c1, c2 = st.columns(2)
            with c1: f_sol = st.date_input("Fecha solicitud", key=f"fs_{idx_base}")
            with c2: f_res = st.date_input("Fecha respuesta", key=f"fr_{idx_base}")
            rec = st.text_input("Recursos Entregados", value=d[idx_base+4], key=f"r_{idx_base}")
            
            cumplio = st.radio("¿Se entregó todo lo solicitado?", ["Sí", "No"], key=f"c_{idx_base}", index=1 if d[idx_base+5]=="No" else 0)
            nivel = "5"
            if cumplio == "No":
                nivel = st.selectbox("Nivel de cumplimiento", ["1 (20%)", "2 (40%)", "3 (60%)", "4 (80%)"], key=f"n_{idx_base}")
                nivel = nivel[0]
            else:
                st.info("Nivel automático: 5 (100%)")
            return ["Aplica", sol, f_sol.strftime("%d/%m/%Y"), f_res.strftime("%d/%m/%Y"), rec, cumplio, nivel]
        return ["No aplica", "", "", "", "", "", ""]

    res_com = dibujar_direccion("2. Dirección Comunicación", 18)
    st.write("---")
    res_th = dibujar_direccion("3. Dirección de Talento Humano", 25)
    st.write("---")
    res_adm = dibujar_direccion("4. Dirección de Administración", 32)

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1: btn_regresar = st.button("⬅️ Regresar y Guardar")
    with col_btn2: btn_guardar = st.button("Guardar y Continuar ➡️")
    
    if btn_guardar or btn_regresar:
        st.session_state.fila_datos[16] = ap_culturas
        st.session_state.fila_datos[17] = rec_culturas
        st.session_state.fila_datos[18:25] = res_com
        st.session_state.fila_datos[25:32] = res_th
        st.session_state.fila_datos[32:39] = res_adm
        
        if btn_guardar: navegar('seccion_5')
        if btn_regresar: navegar('seccion_3')
        st.rerun()

# --- SECCIÓN 5: LOGÍSTICA ---
elif st.session_state.pantalla == 'seccion_5':
    st.markdown("<h3 style='text-align: center; color: white;'>Logística y Transporte</h3>", unsafe_allow_html=True)
    d = st.session_state.fila_datos
    
    resp_asiste = st.text_input("Responsable que asiste al evento", value=d[39])
    cel_asiste = st.text_input("Celular del responsable", max_chars=10, value=d[40])
    c_hora, c_conc = st.columns(2)
    with c_hora: hora_salida = st.time_input("Hora de salida")
    with c_conc: concentracion = st.text_input("Concentración", value=d[42])
    
    st.write("---")
    
    # Recolector de todos los celulares para validarlos al final
    celulares_ingresados = []
    if cel_asiste != "": celulares_ingresados.append(cel_asiste)
    
    def dibujar_logistica(nombre, max_num):
        aplica = st.radio(f"¿Aplica {nombre}?", ["No aplica", "Aplica"], key=f"ap_{nombre}")
        if aplica == "Aplica":
            num = st.selectbox(f"N° {nombre}", list(range(1, max_num+1)), key=f"n_{nombre}")
            contactos = []
            for i in range(num):
                c1, c2 = st.columns(2)
                with c1: nom = st.text_input(f"Nombre {i+1}", key=f"nom_{nombre}_{i}")
                with c2: cel = st.text_input(f"Celular {i+1}", max_chars=10, key=f"cel_{nombre}_{i}")
                
                if cel != "": celulares_ingresados.append(cel)
                if nom or cel: contactos.append(f"{nom} ({cel})")
            return ["Aplica", str(num), "\n".join(contactos)]
        return ["No aplica", "", ""]

    res_cam = dibujar_logistica("Camionetas", 15) # Máximo 15
    st.write("---")
    res_bus = dibujar_logistica("Busetas", 15) # Máximo 15
    st.write("---")
    res_aux = dibujar_logistica("Auxiliares", 50) # Máximo 50
    st.write("---")
    
    insumos = st.text_area("Detalle de los insumos solicitados", value=d[51])
    ubicacion = st.text_area("Ubicación (detallada)", value=d[52])

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1: btn_regresar = st.button("⬅️ Regresar y Guardar")
    with col_btn2: btn_guardar = st.button("Guardar y Continuar ➡️")
    
    if btn_guardar or btn_regresar:
        # Validación de que TODOS los celulares tengan exactamente 10 dígitos numéricos
        hay_error_celular = False
        for c in celulares_ingresados:
            if not c.isdigit() or len(c) != 10:
                hay_error_celular = True
                break
                
        if hay_error_celular:
            st.error("❌ Todo número de celular ingresado en esta sección debe tener exactamente 10 dígitos numéricos.")
        else:
            st.session_state.fila_datos[39] = resp_asiste
            st.session_state.fila_datos[40] = cel_asiste
            st.session_state.fila_datos[41] = hora_salida.strftime("%H:%M")
            st.session_state.fila_datos[42] = concentracion
            st.session_state.fila_datos[43:46] = res_cam
            st.session_state.fila_datos[46:49] = res_bus
            st.session_state.fila_datos[49:52] = res_aux
            st.session_state.fila_datos[52] = insumos
            st.session_state.fila_datos[53] = ubicacion
            
            if btn_guardar: navegar('seccion_6')
            if btn_regresar: navegar('seccion_4')
            st.rerun()

# --- SECCIÓN 6: EVALUACIÓN Y FIN ---
elif st.session_state.pantalla == 'seccion_6':
    st.markdown("<h3 style='text-align: center; color: white;'>Evaluación del Evento</h3>", unsafe_allow_html=True)
    d = st.session_state.fila_datos
    
    nivel_ejec = st.radio("Nivel de ejecución del evento", ["1 (Muy Deficiente)", "2 (Deficiente)", "3 (Regular)", "4 (Bueno)", "5 (Perfecto)"])
    obs = st.text_area("Observaciones", value=d[54])
    
    st.write("---")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1: btn_regresar = st.button("⬅️ Regresar y Guardar")
    with col_btn2: btn_terminar = st.button("TERMINADO ✔️")
    
    if btn_terminar or btn_regresar:
        st.session_state.fila_datos[53] = nivel_ejec[0]
        st.session_state.fila_datos[54] = obs
        
        if btn_terminar:
            d = st.session_state.fila_datos
            d[55] = calcular_dias(d[6], d[10])
            d[56] = calcular_dias(d[20], d[21]) if d[18] == "Aplica" else ""
            d[57] = calcular_dias(d[27], d[28]) if d[25] == "Aplica" else ""
            d[58] = calcular_dias(d[34], d[35]) if d[32] == "Aplica" else ""
            d[59] = "Finalizado"
            
            guardar_en_excel()
            st.success("🎉 ¡Evento Finalizado y Guardado Exitosamente!")
            st.session_state.pantalla = 'inicio'
        
        if btn_regresar:
            navegar('seccion_5')
            
        st.rerun()
