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
            .stButton>button {{ 
                width: 100%; 
                margin-top: -10px;
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
if 'confirmar_eliminar' not in st.session_state: st.session_state.confirmar_eliminar = False

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

def actualizar_calculos_automaticos():
    # Esta función se asegura de calcular los días en cualquier momento si las fechas existen
    d = st.session_state.fila_datos
    d[55] = calcular_dias(d[6], d[10])
    d[56] = calcular_dias(d[20], d[21]) if d[18] == "Aplica" else ""
    d[57] = calcular_dias(d[27], d[28]) if d[25] == "Aplica" else ""
    d[58] = calcular_dias(d[34], d[35]) if d[32] == "Aplica" else ""

def guardar_en_excel():
    if st.session_state.fila_actual:
        actualizar_calculos_automaticos() # Calcula antes de guardar siempre
        rango = f"A{st.session_state.fila_actual}:BH{st.session_state.fila_actual}"
        hoja_datos.update(values=[st.session_state.fila_datos], range_name=rango)

def navegar(destino):
    guardar_en_excel()
    st.session_state.pantalla = destino

def reset_app():
    st.session_state.pantalla = 'inicio'
    st.session_state.area_seleccionada = None
    st.session_state.fila_actual = None
    st.session_state.fila_datos = [""] * 60
    st.session_state.confirmar_eliminar = False
    st.rerun()

# ==========================================
# 3. PANTALLAS DE NAVEGACIÓN
# ==========================================

# --- PANTALLA 1: INICIO ---
if st.session_state.pantalla == 'inicio':
    col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
    with col_logo2:
        try: st.image("logo_superior.png", use_container_width=True)
        except: pass
            
    st.markdown("<h2 style='text-align: center; color: white;'>Seleccione su área</h2>", unsafe_allow_html=True)
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
        if st.button("Buscar Eventos"):
            st.session_state.modo = "editar"
            st.session_state.pantalla = 'buscador_eventos'
            st.rerun()
    
    st.write("---")
    if st.button("🏠 Volver al inicio"): reset_app()

# --- BUSCADOR DE EVENTOS ---
elif st.session_state.pantalla == 'buscador_eventos':
    st.markdown("<h3 style='text-align: center; color: white;'>Seleccionar evento</h3>", unsafe_allow_html=True)
    
    lista_resp = ["Responsable 1", "Responsable 2", "Responsable 3", "Responsable 4", "Responsable 5"] if st.session_state.area_seleccionada == "Culturas y Patrimonio" else ["Responsable 6", "Responsable 7", "Responsable 8"]
    resp_busqueda = st.selectbox("Seleccione el responsable", lista_resp)
    
    try:
        todos_los_datos = hoja_datos.get_all_values()
        eventos_encontrados_dict = {}
        
        for i in range(1, len(todos_los_datos)):
            fila = todos_los_datos[i]
            if len(fila) > 4:
                if fila[1] == st.session_state.area_seleccionada and fila[3] == resp_busqueda:
                    n_registro = fila[0]
                    nombre_ev = fila[4]
                    fecha_ev = fila[10] if len(fila) > 10 else "Sin Fecha"
                    estado = "Finalizado" if len(fila) >= 60 and fila[59] == "Finalizado" else "En proceso"
                    
                    unique_key = f"{nombre_ev} (Fecha: {fecha_ev} - N° {n_registro} - {estado})"
                    eventos_encontrados_dict[unique_key] = (i + 1, fila)
        
        opciones_eventos = list(eventos_encontrados_dict.keys())
        opciones_eventos.reverse()
        
        if opciones_eventos:
            evento_seleccionado = st.selectbox("Seleccione el evento", opciones_eventos)
            col1, col2 = st.columns(2)
            with col2:
                if st.button("Abrir Evento"):
                    fila_real, datos_fila = eventos_encontrados_dict[evento_seleccionado]
                    st.session_state.fila_actual = fila_real
                    mientras_datos = datos_fila + [""] * (60 - len(datos_fila))
                    st.session_state.fila_datos = mientras_datos[:60]
                    st.session_state.pantalla = 'seccion_2'
                    st.rerun()
            with col1:
                if st.button("Regresar"):
                    st.session_state.pantalla = 'opciones_evento'
                    st.rerun()
        else:
            st.warning("Aún no ha creado eventos.")
            if st.button("Regresar"): st.session_state.pantalla = 'opciones_evento'; st.rerun()
                
    except Exception as e:
        st.error("Hubo un problema al buscar los datos en el Excel.")
        if st.button("Regresar"): st.session_state.pantalla = 'opciones_evento'; st.rerun()

    st.write("---")
    if st.button("🏠 Volver al inicio"): reset_app()

# ==========================================
# 4. FORMULARIOS (SECCIONES 2 A 6)
# ==========================================

# --- SECCIÓN 2: INFORMACIÓN DEL EVENTO ---
elif st.session_state.pantalla == 'seccion_2':
    st.markdown("<h3 style='text-align: center; color: white;'>Información del Evento</h3>", unsafe_allow_html=True)
    
    lista_resp = ["Responsable 1", "Responsable 2", "Responsable 3", "Responsable 4", "Responsable 5"] if st.session_state.area_seleccionada == "Culturas y Patrimonio" else ["Responsable 6", "Responsable 7", "Responsable 8"]
    d = st.session_state.fila_datos
    
    resp_index = lista_resp.index(d[3]) if d[3] in lista_resp else 0
    responsable = st.selectbox("Responsable de área", lista_resp, index=resp_index)
    
    nombre_evento = st.text_input("Nombre del evento", value=d[4])
    tipo_evento = st.selectbox("Tipo de evento", ["Propio", "Apoyo"], index=0 if d[5] != "Apoyo" else 1)
    
    # Manejo de fechas para que no den error si están vacías al editar
    try: def_i_org = datetime.strptime(d[6], "%d/%m/%Y").date() if d[6] else date.today()
    except: def_i_org = date.today()
    try: def_f_ev = datetime.strptime(d[10], "%d/%m/%Y").date() if d[10] else date.today()
    except: def_f_ev = date.today()
    
    c1, c2 = st.columns(2)
    with c1:
        inicio_org = st.date_input("Inicio organización del evento", value=def_i_org)
        fecha_evento = st.date_input("Fecha del evento", value=def_f_ev)
    with c2:
        nombre_org = st.text_input("Nombre del organizador", value=d[7])
        hora_evento = st.time_input("Hora del evento")
        
    celular_org = st.text_input("Celular del organizador", max_chars=10, value=d[8])
    lugar_evento = st.text_input("Lugar del evento", value=d[9])
    
    st.write("---")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1: btn_regresar = st.button("⬅️ Regresar y Guardar")
    with col_btn2: btn_guardar = st.button("Guardar y Continuar ➡️")
        
    if btn_guardar or btn_regresar:
        if nombre_evento.strip() == "" or nombre_org.strip() == "" or celular_org.strip() == "" or lugar_evento.strip() == "":
            st.error("❌ Alto ahí: Debes llenar todos los campos de esta sección.")
        elif not celular_org.isdigit() or len(celular_org) != 10:
            st.error("❌ El celular del organizador debe tener exactamente 10 dígitos numéricos.")
        else:
            meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            mes_texto = meses[fecha_evento.month - 1]
            
            st.session_state.fila_datos[1:12] = [st.session_state.area_seleccionada, mes_texto, responsable, nombre_evento, tipo_evento, inicio_org.strftime("%d/%m/%Y"), nombre_org, celular_org, lugar_evento, fecha_evento.strftime("%d/%m/%Y"), hora_evento.strftime("%H:%M")]
            
            # Etiqueta "En proceso" automática
            if st.session_state.modo == "nuevo" and not st.session_state.fila_actual:
                num_filas = len(hoja_datos.col_values(1))
                st.session_state.fila_datos[0] = str(num_filas)
                st.session_state.fila_datos[59] = "En proceso"
                hoja_datos.append_row(st.session_state.fila_datos)
                st.session_state.fila_actual = num_filas + 1
            elif not d[59] or d[59] == "":
                st.session_state.fila_datos[59] = "En proceso"
            
            if btn_guardar: navegar('seccion_3')
            if btn_regresar: navegar('opciones_evento')
            st.rerun()
            
    st.write("---")
    if st.button("🏠 Volver al inicio"): reset_app()

# --- SECCIÓN 3: EXTERNAS (CARGA DE DATOS ARREGLADA) ---
elif st.session_state.pantalla == 'seccion_3':
    st.markdown("<h3 style='text-align: center; color: white;'>Coordinación con Entidades Externas</h3>", unsafe_allow_html=True)
    d = st.session_state.fila_datos
    
    aplica = st.radio("¿Aplica?", ["No aplica", "Aplica"], index=1 if d[12] != "" else 0)
    entidades_str = ""; solicitudes_str = ""; f_sol_str = ""; f_resp_str = ""
    
    if aplica == "Aplica":
        # Desempaquetamos los datos guardados si existen
        ent_exist = d[12].split('\n') if d[12] else []
        sol_exist = d[13].split('\n') if d[13] else []
        fs_exist = d[14].split('\n') if d[14] else []
        fr_exist = d[15].split('\n') if d[15] else []
        
        num_entidades_default = len(ent_exist) if len(ent_exist) > 0 else 1
        num_entidades = st.selectbox("¿Cuántas entidades externas?", list(range(1, 9)), index=num_entidades_default-1)
        
        lista_nombres = []; lista_solicitudes = []; lista_f_sol = []; lista_f_resp = []
        
        for i in range(num_entidades):
            st.markdown(f"**Entidad {i+1}**")
            
            # Rescatamos los valores previos limpiando el "1. " del inicio
            val_nom = ent_exist[i].split('. ', 1)[1] if i < len(ent_exist) and '. ' in ent_exist[i] else ""
            val_sol = sol_exist[i].split('. ', 1)[1] if i < len(sol_exist) and '. ' in sol_exist[i] else ""
            
            val_fs_str = fs_exist[i].split('. ', 1)[1] if i < len(fs_exist) and '. ' in fs_exist[i] else ""
            try: val_fs = datetime.strptime(val_fs_str, "%d/%m/%Y").date()
            except: val_fs = date.today()
                
            val_fr_str = fr_exist[i].split('. ', 1)[1] if i < len(fr_exist) and '. ' in fr_exist[i] else ""
            try: val_fr = datetime.strptime(val_fr_str, "%d/%m/%Y").date()
            except: val_fr = date.today()

            nom = st.text_input(f"Nombre de la entidad {i+1}", value=val_nom, key=f"ent_{i}")
            sol = st.text_area(f"Solicitud {i+1}", value=val_sol, key=f"sol_{i}")
            c1, c2 = st.columns(2)
            with c1: fs = st.date_input(f"Fecha de solicitud {i+1}", value=val_fs, key=f"fs_{i}")
            with c2: fr = st.date_input(f"Fecha de respuesta {i+1}", value=val_fr, key=f"fr_{i}")
            
            if nom != "": 
                lista_nombres.append(f"{i+1}. {nom}")
                lista_solicitudes.append(f"{i+1}. {sol}")
                lista_f_sol.append(f"{i+1}. {fs.strftime('%d/%m/%Y')}")
                lista_f_resp.append(f"{i+1}. {fr.strftime('%d/%m/%Y')}")
                
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
            st.session_state.fila_datos[12:16] = [entidades_str, solicitudes_str, f_sol_str, f_resp_str]
        else:
            st.session_state.fila_datos[12:16] = ["", "", "", ""]
            
        if btn_guardar: navegar('seccion_4')
        if btn_regresar: navegar('seccion_2')
        st.rerun()
        
    st.write("---")
    if st.button("🏠 Volver al inicio"): reset_app()

# --- SECCIÓN 4: INTERNAS (CON TEXT_AREA GIGANTES) ---
elif st.session_state.pantalla == 'seccion_4':
    st.markdown("<h3 style='text-align: center; color: white;'>Coordinación con Áreas Internas</h3>", unsafe_allow_html=True)
    d = st.session_state.fila_datos
    
    st.markdown("**1. Dirección Culturas, Patrimonio y Recreación**")
    ap_culturas = st.radio("¿Aplica?", ["No aplica", "Aplica"], key="r_cult", index=1 if d[16]=="Aplica" else 0)
    # Cambio a text_area gigante
    rec_culturas = st.text_area("Recursos entregados", value=d[17]) if ap_culturas == "Aplica" else ""
    
    st.write("---")
    def dibujar_direccion(nombre, idx_base):
        st.markdown(f"**{nombre}**")
        aplica = st.radio("¿Aplica?", ["No aplica", "Aplica"], key=f"ap_{idx_base}", index=1 if d[idx_base]=="Aplica" else 0)
        if aplica == "Aplica":
            # Cambios a text_area gigante
            sol = st.text_area("Solicitud realizada", value=d[idx_base+1], key=f"s_{idx_base}")
            
            try: val_fs = datetime.strptime(d[idx_base+2], "%d/%m/%Y").date() if d[idx_base+2] else date.today()
            except: val_fs = date.today()
            try: val_fr = datetime.strptime(d[idx_base+3], "%d/%m/%Y").date() if d[idx_base+3] else date.today()
            except: val_fr = date.today()
                
            c1, c2 = st.columns(2)
            with c1: f_sol = st.date_input("Fecha solicitud", value=val_fs, key=f"fs_{idx_base}")
            with c2: f_res = st.date_input("Fecha respuesta", value=val_fr, key=f"fr_{idx_base}")
            
            rec = st.text_area("Recursos Entregados", value=d[idx_base+4], key=f"r_{idx_base}")
            
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
        st.session_state.fila_datos[16:39] = [ap_culturas, rec_culturas] + res_com + res_th + res_adm
        
        if btn_guardar: navegar('seccion_5')
        if btn_regresar: navegar('seccion_3')
        st.rerun()
        
    st.write("---")
    if st.button("🏠 Volver al inicio"): reset_app()

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

    res_cam = dibujar_logistica("Camionetas", 15) 
    st.write("---")
    res_bus = dibujar_logistica("Busetas", 15) 
    st.write("---")
    res_aux = dibujar_logistica("Auxiliares", 50) 
    st.write("---")
    
    insumos = st.text_area("Detalle de los insumos solicitados", value=d[51])
    ubicacion = st.text_area("Ubicación (detallada)", value=d[52])

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1: btn_regresar = st.button("⬅️ Regresar y Guardar")
    with col_btn2: btn_guardar = st.button("Guardar y Continuar ➡️")
    
    if btn_guardar or btn_regresar:
        hay_error_celular = False
        for c in celulares_ingresados:
            if not c.isdigit() or len(c) != 10:
                hay_error_celular = True
                break
                
        if hay_error_celular:
            st.error("❌ Todo número de celular ingresado en esta sección debe tener exactamente 10 dígitos numéricos.")
        else:
            st.session_state.fila_datos[39:54] = [resp_asiste, cel_asiste, hora_salida.strftime("%H:%M"), concentracion] + res_cam + res_bus + res_aux + [insumos, ubicacion]
            
            if btn_guardar: navegar('seccion_6')
            if btn_regresar: navegar('seccion_4')
            st.rerun()
            
    st.write("---")
    if st.button("🏠 Volver al inicio"): reset_app()

# --- SECCIÓN 6: EVALUACIÓN Y FIN CON ELIMINAR ---
elif st.session_state.pantalla == 'seccion_6':
    st.markdown("<h3 style='text-align: center; color: white;'>Evaluación del Evento</h3>", unsafe_allow_html=True)
    d = st.session_state.fila_datos
    
    nivel_ejec = st.radio("Nivel de ejecución del evento", ["1 (Muy Deficiente)", "2 (Deficiente)", "3 (Regular)", "4 (Bueno)", "5 (Perfecto)"])
    obs = st.text_area("Observaciones", value=d[54])
    
    st.write("---")
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1: btn_regresar = st.button("⬅️ Regresar y Guardar")
    with col_btn2: btn_terminar = st.button("TERMINADO ✔️")
    with col_btn3: btn_eliminar = st.button("🗑️ Eliminar Evento")
    
    # --- LÓGICA DE ELIMINAR CON CONFIRMACIÓN ---
    if btn_eliminar:
        st.session_state.confirmar_eliminar = True
        
    if st.session_state.confirmar_eliminar:
        st.warning("⚠️ ¿Estás completamente seguro de que deseas eliminar este evento? Esta acción no se puede deshacer.")
        col_conf1, col_conf2 = st.columns(2)
        with col_conf1:
            if st.button("✔️ Sí, eliminar permanentemente"):
                if st.session_state.fila_actual:
                    try:
                        hoja_datos.delete_rows(st.session_state.fila_actual)
                        total_filas = len(hoja_datos.col_values(1))
                        if total_filas > 1:
                            nuevos_nums = [[str(i)] for i in range(1, total_filas)]
                            hoja_datos.update(values=nuevos_nums, range_name=f"A2:A{total_filas}")
                        st.success("🗑️ Evento borrado permanentemente y numeración actualizada.")
                        reset_app()
                    except Exception as e:
                        st.error(f"Error al intentar borrar: {e}")
        with col_conf2:
            if st.button("❌ Cancelar"):
                st.session_state.confirmar_eliminar = False
                st.rerun()

    # --- LÓGICA DE TERMINAR Y REGRESAR ---
    if not st.session_state.confirmar_eliminar and (btn_terminar or btn_regresar):
        st.session_state.fila_datos[53] = nivel_ejec[0]
        st.session_state.fila_datos[54] = obs
        
        if btn_terminar:
            # Pone la etiqueta de "Finalizado" que reemplaza la de "En proceso"
            st.session_state.fila_datos[59] = "Finalizado"
            guardar_en_excel()
            st.success("🎉 ¡Evento Finalizado y Guardado Exitosamente!")
            reset_app()
        
        if btn_regresar:
            navegar('seccion_5')
            st.rerun()

    st.write("---")
    if st.button("🏠 Volver al inicio"): reset_app()
