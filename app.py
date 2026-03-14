import streamlit as st
import base64
import json
import gspread
import io
from google.oauth2.service_account import Credentials
from datetime import datetime, date
from docxtpl import DocxTemplate

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
            .stButton>button {{ width: 100%; margin-top: -10px; }}
            div[data-testid="stExpander"] {{ background-color: rgba(255,255,255,0.05); border-radius: 10px; }}
            </style>
            """,
            unsafe_allow_html=True
        )
    except: pass

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
if 'fila_datos' not in st.session_state: st.session_state.fila_datos = [""] * 65

def calcular_dias(fecha_inicio, fecha_fin):
    if not fecha_inicio or not fecha_fin or fecha_inicio == "-" or fecha_fin == "-": return "-"
    try:
        d1 = datetime.strptime(fecha_inicio, "%d/%m/%Y").date()
        d2 = datetime.strptime(fecha_fin, "%d/%m/%Y").date()
        return str((d2 - d1).days)
    except: return "-"

def actualizar_calculos_automaticos():
    d = st.session_state.fila_datos
    d[56] = calcular_dias(d[6], d[10])
    d[57] = calcular_dias(d[20], d[21]) if d[18] == "Aplica" else "-"
    d[58] = calcular_dias(d[27], d[28]) if d[25] == "Aplica" else "-"
    d[59] = calcular_dias(d[34], d[35]) if d[32] == "Aplica" else "-"

def guardar_en_excel():
    if st.session_state.fila_actual:
        actualizar_calculos_automaticos()
        rango = f"A{st.session_state.fila_actual}:BM{st.session_state.fila_actual}"
        hoja_datos.update(values=[st.session_state.fila_datos], range_name=rango)

def navegar(destino):
    guardar_en_excel()
    st.session_state.pantalla = destino

def reset_app():
    st.session_state.pantalla = 'inicio'
    st.session_state.area_seleccionada = None
    st.session_state.fila_actual = None
    st.session_state.fila_datos = [""] * 65
    st.session_state.confirmar_eliminar = False
    st.rerun()

# ==========================================
# 3. GENERADORES DE PLANTILLAS WORD (DOCXTPL)
# ==========================================
def txt(texto):
    return str(texto) if texto and str(texto).strip() != "" else "-"

def armar_lista_vehiculos(aplica, contactos_str):
    if aplica != "Aplica": return []
    lineas = [x for x in contactos_str.split('\n') if x.strip()]
    return [{"num": str(i+1), "contacto": lineas[i]} for i in range(len(lineas))]

def generar_word_expediente(d):
    doc = DocxTemplate("Expediente del evento plantilla.docx")
    
    context = {
        "evento": txt(d[4]), "estado": txt(d[60]), "inicio_plan": txt(d[6]),
        "area": txt(d[1]), "responsable_area": txt(d[3]), "tipo": txt(d[5]),
        "lugar": txt(d[9]), "dia": txt(d[10]), "hora": txt(d[11]),
        "organizador": f"{d[7]} ({d[8]})",
        
        "aplica_externas": True if txt(d[12]) != "-" else False,
        "ent_nombre": txt(d[12]).replace('\n', ' | '),
        "ent_solicitud": txt(d[13]).replace('\n', ' | '),
        "ent_f_sol": txt(d[14]).replace('\n', ' | '),
        "ent_f_resp": txt(d[15]).replace('\n', ' | '),
        
        "aplica_culturas": True if d[16] == "Aplica" else False,
        "rec_culturas": txt(d[17]),
        
        "aplica_comunicacion": True if d[18] == "Aplica" else False,
        "sol_com": txt(d[19]), "fs_com": txt(d[20]), "fr_com": txt(d[21]), 
        "rec_com": txt(d[22]), "niv_com": txt(d[24]),
        
        "aplica_th": True if d[25] == "Aplica" else False,
        "sol_th": txt(d[26]), "fs_th": txt(d[27]), "fr_th": txt(d[28]), 
        "rec_th": txt(d[29]), "niv_th": txt(d[31]),
        
        "aplica_admin": True if d[32] == "Aplica" else False,
        "sol_adm": txt(d[33]), "fs_adm": txt(d[34]), "fr_adm": txt(d[35]), 
        "rec_adm": txt(d[36]), "niv_adm": txt(d[38]),
        
        "responsable": f"{d[39]} ({d[40]})",
        "ubicacion_detalle": txt(d[53]),
        "hora_concentracion": txt(d[41]), "lugar_concentracion": txt(d[42]),
        
        "aplica_cam": True if d[43] == "Aplica" else False,
        "camionetas": armar_lista_vehiculos(d[43], d[45]),
        
        "aplica_bus": True if d[46] == "Aplica" else False,
        "busetas": armar_lista_vehiculos(d[46], d[48]),
        
        "aplica_aux": True if d[49] == "Aplica" else False,
        "auxiliares": armar_lista_vehiculos(d[49], d[51]),
        
        "descripcion": txt(d[52]),
        "nivel_texto": txt(d[54]),
        "observaciones": txt(d[55]),
        
        "dias_ejecucion": txt(d[56]), "dias_com": txt(d[57]),
        "dias_th": txt(d[58]), "dias_admin": txt(d[59])
    }
    
    doc.render(context)
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def generar_word_hoja_ruta(d):
    doc = DocxTemplate("HOJA DE RUTA EVENTO plantilla.docx")
    
    recursos = []
    if d[16] == "Aplica" and d[17]: recursos.append(f"CULTURAS:\n{d[17]}")
    if d[18] == "Aplica" and d[22]: recursos.append(f"COMUNICACIÓN:\n{d[22]}")
    if d[32] == "Aplica" and d[36]: recursos.append(f"ADMINISTRACIÓN:\n{d[36]}")
    recursos_str = "\n\n".join(recursos) if recursos else "-"

    context = {
        "evento": txt(d[4]), "lugar": txt(d[9]), "dia": txt(d[10]), "hora": txt(d[11]),
        "lugar_concentracion": txt(d[42]), "hora_concentracion": txt(d[41]),
        "responsable": f"{d[39]} ({d[40]})", "organizador": f"{d[7]} ({d[8]})",
        
        "aplica_cam": txt(d[43]),
        "num_cam": txt(d[44]) if d[43]=="Aplica" else "-",
        "cont_cam": txt(d[45]).replace('\n', ' | ') if d[43]=="Aplica" else "-",
        
        "aplica_bus": txt(d[46]),
        "num_bus": txt(d[47]) if d[46]=="Aplica" else "-",
        "cont_bus": txt(d[48]).replace('\n', ' | ') if d[46]=="Aplica" else "-",
        
        "aplica_aux": txt(d[49]),
        "num_aux": txt(d[50]) if d[49]=="Aplica" else "-",
        "cont_aux": txt(d[51]).replace('\n', ' | ') if d[49]=="Aplica" else "-",
        
        "recursos_totales": recursos_str,
        "ubicacion_detalle": txt(d[53]),
        "descripcion": txt(d[52])
    }
    
    doc.render(context)
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# ==========================================
# 4. PANTALLAS DE INICIO Y BUSCADOR
# ==========================================
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

elif st.session_state.pantalla == 'opciones_evento':
    st.markdown(f"<h3 style='text-align: center; color: white;'>Área: {st.session_state.area_seleccionada}</h3>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Nuevo Evento"):
            st.session_state.modo = "nuevo"
            st.session_state.fila_datos = [""] * 65
            st.session_state.pantalla = 'seccion_2'
            st.rerun()
    with col2:
        if st.button("Buscar Eventos"):
            st.session_state.modo = "editar"
            st.session_state.pantalla = 'buscador_eventos'
            st.rerun()
    st.write("---")
    if st.button("🏠 Volver al inicio"): reset_app()

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
                    estado = "Finalizado" if len(fila) >= 61 and fila[60] == "Finalizado" else "En proceso"
                    fecha_ev = fila[10] if len(fila) > 10 else "Sin Fecha"
                    unique_key = f"{fila[4]} (Fecha: {fecha_ev} - N° {fila[0]} - {estado})"
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
                    st.session_state.fila_datos = (datos_fila + [""] * 65)[:65]
                    st.session_state.pantalla = 'seccion_2'
                    st.rerun()
            with col1:
                if st.button("Regresar"): st.session_state.pantalla = 'opciones_evento'; st.rerun()
        else:
            st.warning("Aún no ha creado eventos.")
            if st.button("Regresar"): st.session_state.pantalla = 'opciones_evento'; st.rerun()
    except Exception as e: # ¡ESTO ARREGLA EL ERROR DEL DOBLE CLIC!
        st.error("Error al buscar. Vuelve a intentarlo.")
        if st.button("Regresar"): st.session_state.pantalla = 'opciones_evento'; st.rerun()
    st.write("---")
    if st.button("🏠 Volver al inicio"): reset_app()

# ==========================================
# 5. FORMULARIOS (SECCIONES 2 A 6) 
# ==========================================

# --- SECCIÓN 2 ---
elif st.session_state.pantalla == 'seccion_2':
    st.markdown("<h3 style='text-align: center; color: white;'>Información del Evento</h3>", unsafe_allow_html=True)
    d = st.session_state.fila_datos
    lista_resp = ["Responsable 1", "Responsable 2", "Responsable 3", "Responsable 4", "Responsable 5"] if st.session_state.area_seleccionada == "Culturas y Patrimonio" else ["Responsable 6", "Responsable 7", "Responsable 8"]
    
    with st.container():
        st.markdown("#### 📝 1. Datos Generales")
        nombre_evento = st.text_input("Nombre del evento", value=d[4])
        c1, c2 = st.columns(2)
        with c1: tipo_evento = st.selectbox("Tipo de evento", ["Propio", "Apoyo"], index=0 if d[5] != "Apoyo" else 1)
        with c2: lugar_evento = st.text_input("Lugar del evento", value=d[9])
    
    st.write("---")
    with st.container():
        st.markdown("#### 📅 2. Fechas y Horarios")
        try: def_i_org = datetime.strptime(d[6], "%d/%m/%Y").date() if d[6] else date.today()
        except: def_i_org = date.today()
        try: def_f_ev = datetime.strptime(d[10], "%d/%m/%Y").date() if d[10] else date.today()
        except: def_f_ev = date.today()
        
        con_fin_def = False
        try:
            if "-" in d[11]:
                def_h_ev = datetime.strptime(d[11].split("-")[0].strip(), "%I:%M %p").time()
                def_h_fin = datetime.strptime(d[11].split("-")[1].strip(), "%I:%M %p").time()
                con_fin_def = True
            else:
                def_h_ev = datetime.strptime(d[11], "%I:%M %p").time()
                def_h_fin = datetime.now().time()
        except:
            def_h_ev = datetime.now().time()
            def_h_fin = datetime.now().time()

        c3, c4 = st.columns(2)
        with c3:
            fecha_evento = st.date_input("Fecha del evento", value=def_f_ev)
            inicio_org = st.date_input("Fecha de inicio de planificación", value=def_i_org)
        with c4:
            hora_inicio = st.time_input("Hora de inicio del evento", value=def_h_ev) # CAMBIADO
            con_fin = st.checkbox("¿Añadir hora de cierre?", value=con_fin_def)
            if con_fin: hora_fin = st.time_input("Hora de cierre del evento", value=def_h_fin) # CAMBIADO
    
    st.write("---")
    with st.container():
        st.markdown("#### 👥 3. Involucrados")
        resp_index = lista_resp.index(d[3]) if d[3] in lista_resp else 0
        responsable = st.selectbox("Responsable de área (Interno)", lista_resp, index=resp_index)
        c5, c6 = st.columns(2)
        with c5: nombre_org = st.text_input("Nombre del organizador externo", value=d[7])
        with c6: celular_org = st.text_input("Celular del organizador", max_chars=10, value=d[8])
    
    st.write("---")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1: btn_regresar = st.button("⬅️ Regresar y Guardar")
    with col_btn2: btn_guardar = st.button("Guardar y Continuar ➡️")
        
    if btn_guardar or btn_regresar:
        if nombre_evento.strip() == "" or nombre_org.strip() == "" or celular_org.strip() == "" or lugar_evento.strip() == "":
            st.error("❌ Debes llenar todos los campos (Nombre, Lugar y Datos del Organizador).")
        elif not celular_org.isdigit() or len(celular_org) != 10:
            st.error("❌ El celular debe tener 10 dígitos numéricos.")
        else:
            meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            hora_str = hora_inicio.strftime("%I:%M %p")
            if con_fin: hora_str += f" - {hora_fin.strftime('%I:%M %p')}"
            
            st.session_state.fila_datos[1:12] = [st.session_state.area_seleccionada, meses[fecha_evento.month-1], responsable, nombre_evento, tipo_evento, inicio_org.strftime("%d/%m/%Y"), nombre_org, celular_org, lugar_evento, fecha_evento.strftime("%d/%m/%Y"), hora_str]
            
            if st.session_state.modo == "nuevo" and not st.session_state.fila_actual:
                num_filas = len(hoja_datos.col_values(1))
                st.session_state.fila_datos[0] = str(num_filas)
                st.session_state.fila_datos[60] = "En proceso"
                hoja_datos.append_row(st.session_state.fila_datos)
                st.session_state.fila_actual = num_filas + 1
            elif not d[60]: st.session_state.fila_datos[60] = "En proceso"
            
            if btn_guardar: navegar('seccion_3')
            if btn_regresar: navegar('opciones_evento')
            st.rerun()
    st.write("---")
    if st.button("🏠 Volver al inicio"): reset_app()

# --- SECCIÓN 3 --- 
elif st.session_state.pantalla == 'seccion_3':
    st.markdown("<h3 style='text-align: center; color: white;'>Coordinación con Entidades Externas</h3>", unsafe_allow_html=True)
    d = st.session_state.fila_datos
    
    aplica_def = 1 if str(d[12]).strip() != "" and str(d[12]).strip() != "-" else 0
    aplica = st.radio("¿Aplica coordinación externa?", ["No aplica", "Aplica"], index=aplica_def)
    
    ent_str = ""; sol_str = ""; fs_str = ""; fr_str = ""
    
    if aplica == "Aplica":
        e_ex = [x for x in str(d[12]).split('\n') if x.strip() and x.strip() != "-"]
        s_ex = [x for x in str(d[13]).split('\n') if x.strip() and x.strip() != "-"]
        fs_ex = [x for x in str(d[14]).split('\n') if x.strip() and x.strip() != "-"]
        fr_ex = [x for x in str(d[15]).split('\n') if x.strip() and x.strip() != "-"]
        
        num_ent_def = len(e_ex) if len(e_ex) > 0 else 1
        if num_ent_def > 8: num_ent_def = 8
        
        num_ent = st.selectbox("¿Cuántas entidades?", list(range(1, 9)), index=num_ent_def-1)
        l_nom=[]; l_sol=[]; l_fs=[]; l_fr=[]
        
        for i in range(num_ent):
            with st.expander(f"🏢 Entidad Externa {i+1}", expanded=True):
                vn = e_ex[i] if i < len(e_ex) else ""
                if ". " in vn: vn = vn.split('. ', 1)[1]
                
                vs = s_ex[i] if i < len(s_ex) else ""
                if ". " in vs: vs = vs.split('. ', 1)[1]
                
                vfs_str = fs_ex[i] if i < len(fs_ex) else ""
                if ". " in vfs_str: vfs_str = vfs_str.split('. ', 1)[1]
                try: vfs = datetime.strptime(vfs_str, "%d/%m/%Y").date()
                except: vfs = date.today()
                
                vfr_str = fr_ex[i] if i < len(fr_ex) else ""
                if ". " in vfr_str: vfr_str = vfr_str.split('. ', 1)[1]
                try: vfr = datetime.strptime(vfr_str, "%d/%m/%Y").date()
                except: vfr = date.today()

                nom = st.text_input("Nombre de la entidad", value=vn, key=f"e_{i}")
                sol = st.text_area("Solicitud realizada", value=vs, key=f"s_{i}")
                c1, c2 = st.columns(2)
                with c1: fs = st.date_input("Fecha solicitud", value=vfs, key=f"fs_{i}")
                with c2: fr = st.date_input("Fecha respuesta", value=vfr, key=f"fr_{i}")
                
                if nom.strip(): 
                    l_nom.append(f"{i+1}. {nom}"); l_sol.append(f"{i+1}. {sol}")
                    l_fs.append(f"{i+1}. {fs.strftime('%d/%m/%Y')}"); l_fr.append(f"{i+1}. {fr.strftime('%d/%m/%Y')}")
                    
        ent_str="\n".join(l_nom); sol_str="\n".join(l_sol); fs_str="\n".join(l_fs); fr_str="\n".join(l_fr)
        
    st.write("---")
    col1, col2 = st.columns(2)
    if col1.button("⬅️ Regresar y Guardar"):
        st.session_state.fila_datos[12:16] = [ent_str, sol_str, fs_str, fr_str] if aplica=="Aplica" else ["-","-","-","-"]
        navegar('seccion_2'); st.rerun()
    if col2.button("Guardar y Continuar ➡️"):
        st.session_state.fila_datos[12:16] = [ent_str, sol_str, fs_str, fr_str] if aplica=="Aplica" else ["-","-","-","-"]
        navegar('seccion_4'); st.rerun()
    st.write("---")
    if st.button("🏠 Volver al inicio"): reset_app()

# --- SECCIÓN 4 ---
elif st.session_state.pantalla == 'seccion_4':
    st.markdown("<h3 style='text-align: center; color: white;'>Coordinación con Áreas Internas</h3>", unsafe_allow_html=True)
    d = st.session_state.fila_datos
    
    tab1, tab2, tab3, tab4 = st.tabs(["🎨 Culturas y Rec.", "📢 Comunicación", "👥 Talento Humano", "🏢 Administración"])
    
    with tab1:
        st.markdown("#### Dirección de Culturas, Patrimonio y Recreación")
        ap_cult = st.radio("¿Aplica?", ["No aplica", "Aplica"], key="r_cult", index=1 if d[16]=="Aplica" else 0)
        rec_cult = st.text_area("Recursos entregados (Detalle)", value=d[17] if d[17]!="-" else "", height=150) if ap_cult == "Aplica" else "-"
    
    def dib_dir(idx_base):
        ap = st.radio("¿Aplica?", ["No aplica", "Aplica"], key=f"ap_{idx_base}", index=1 if d[idx_base]=="Aplica" else 0)
        if ap == "Aplica":
            sol = st.text_area("Solicitud realizada (Detalle)", value=d[idx_base+1] if d[idx_base+1]!="-" else "", key=f"s_{idx_base}", height=100)
            try: vfs = datetime.strptime(d[idx_base+2], "%d/%m/%Y").date() if d[idx_base+2] and d[idx_base+2]!="-" else date.today()
            except: vfs = date.today()
            try: vfr = datetime.strptime(d[idx_base+3], "%d/%m/%Y").date() if d[idx_base+3] and d[idx_base+3]!="-" else date.today()
            except: vfr = date.today()
            c1, c2 = st.columns(2)
            with c1: fs = st.date_input("Fecha solicitud", value=vfs, key=f"fs_{idx_base}")
            with c2: fr = st.date_input("Fecha respuesta", value=vfr, key=f"fr_{idx_base}")
            rec = st.text_area("Recursos Entregados (Detalle)", value=d[idx_base+4] if d[idx_base+4]!="-" else "", key=f"r_{idx_base}", height=100)
            
            cp = st.radio("¿Se entregó todo lo solicitado?", ["Sí", "No"], key=f"c_{idx_base}", index=1 if d[idx_base+5]=="No" else 0)
            
            # CÁLCULO DE NIVEL DE CUMPLIMIENTO (1-9 o 10)
            try: idx_nv = int(d[idx_base+6]) - 1 if str(d[idx_base+6]).isdigit() else 0
            except: idx_nv = 0
            if idx_nv > 8: idx_nv = 8 # Protección por si guardó "10" antes
            
            opciones_nv = ["1 (10%)", "2 (20%)", "3 (30%)", "4 (40%)", "5 (50%)", "6 (60%)", "7 (70%)", "8 (80%)", "9 (90%)"]
            nv_val = st.selectbox("Nivel de cumplimiento", opciones_nv, key=f"n_{idx_base}", index=idx_nv)
            nv = nv_val.split(" ")[0] if cp=="No" else "10"
            
            return ["Aplica", sol, fs.strftime("%d/%m/%Y"), fr.strftime("%d/%m/%Y"), rec, cp, nv]
        return ["No aplica", "-", "-", "-", "-", "-", "-"]

    with tab2: st.markdown("#### Dirección de Comunicación"); r_com = dib_dir(18)
    with tab3: st.markdown("#### Dirección de Talento Humano"); r_th = dib_dir(25)
    with tab4: st.markdown("#### Dirección de Administración"); r_adm = dib_dir(32)

    st.write("---")
    col1, col2 = st.columns(2)
    if col1.button("⬅️ Regresar y Guardar"):
        st.session_state.fila_datos[16:39] = [ap_cult, rec_cult] + r_com + r_th + r_adm
        navegar('seccion_3'); st.rerun()
    if col2.button("Guardar y Continuar ➡️"):
        st.session_state.fila_datos[16:39] = [ap_cult, rec_cult] + r_com + r_th + r_adm
        navegar('seccion_5'); st.rerun()
    st.write("---")
    if st.button("🏠 Volver al inicio"): reset_app()

# --- SECCIÓN 5 ---
elif st.session_state.pantalla == 'seccion_5':
    st.markdown("<h3 style='text-align: center; color: white;'>Logística y Transporte</h3>", unsafe_allow_html=True)
    d = st.session_state.fila_datos
    
    with st.container():
        st.markdown("#### 👤 Responsable en territorio")
        c1, c2 = st.columns(2)
        with c1: resp_asiste = st.text_input("Nombre del responsable que asiste", value=d[39] if d[39]!="-" else "")
        with c2: cel_asiste = st.text_input("Celular", max_chars=10, value=d[40] if d[40]!="-" else "")
        c3, c4 = st.columns(2)
        with c3:
            try: hs_def = datetime.strptime(d[41], "%H:%M").time() if d[41] and d[41]!="-" else datetime.now().time()
            except: hs_def = datetime.now().time()
            hora_salida = st.time_input("Hora de concentración", value=hs_def) # CAMBIADO
        with c4: concentracion = st.text_input("Lugar de concentración", value=d[42] if d[42]!="-" else "")
    
    celulares = [cel_asiste] if cel_asiste else []
    
    def dib_log(n, mx, idx):
        with st.expander(f"🚐 Requerimiento de {n}", expanded=(d[idx]=="Aplica")):
            ap = st.radio(f"¿Aplica {n}?", ["No aplica", "Aplica"], key=f"ap_{idx}", index=1 if d[idx]=="Aplica" else 0)
            if ap == "Aplica":
                v_n = int(d[idx+1]) if str(d[idx+1]).isdigit() else 1
                num = st.selectbox(f"N° de {n}", list(range(1, mx+1)), key=f"n_{idx}", index=v_n-1)
                cont = []
                for i in range(num):
                    cx1, cx2 = st.columns(2)
                    with cx1: nom = st.text_input(f"Chofer/Personal {i+1}", key=f"nm_{idx}_{i}")
                    with cx2: cel = st.text_input(f"Celular {i+1}", max_chars=10, key=f"cl_{idx}_{i}")
                    if cel: celulares.append(cel)
                    if nom or cel: cont.append(f"{nom} ({cel})")
                return ["Aplica", str(num), "\n".join(cont)]
            return ["No aplica", "-", "-"]

    r_cam = dib_log("Camionetas", 15, 43)
    r_bus = dib_log("Busetas", 15, 46)
    r_aux = dib_log("Auxiliares", 50, 49)
    
    with st.container():
        st.markdown("#### 📋 Detalles Operativos")
        insumos = st.text_area("Descripción y requerimientos del evento", value=d[52] if d[52]!="-" else "", height=150) # CAMBIADO
        ubicacion = st.text_area("Ubicación exacta / Link de Maps", value=d[53] if d[53]!="-" else "", height=100) # CAMBIADO

    st.write("---")
    col1, col2 = st.columns(2)
    if col1.button("⬅️ Regresar y Guardar"):
        if any(not c.isdigit() or len(c)!=10 for c in celulares): st.error("❌ Los celulares deben tener 10 números.")
        else:
            st.session_state.fila_datos[39:54] = [resp_asiste, cel_asiste, hora_salida.strftime("%H:%M"), concentracion] + r_cam + r_bus + r_aux + [insumos, ubicacion]
            navegar('seccion_4'); st.rerun()
    if col2.button("Guardar y Continuar ➡️"):
        if any(not c.isdigit() or len(c)!=10 for c in celulares): st.error("❌ Los celulares deben tener 10 números.")
        else:
            st.session_state.fila_datos[39:54] = [resp_asiste, cel_asiste, hora_salida.strftime("%H:%M"), concentracion] + r_cam + r_bus + r_aux + [insumos, ubicacion]
            navegar('seccion_6'); st.rerun()
    st.write("---")
    if st.button("🏠 Volver al inicio"): reset_app()

# --- SECCIÓN 6 --- 
elif st.session_state.pantalla == 'seccion_6':
    st.markdown("<h3 style='text-align: center; color: white;'>Cierre y Evaluación del Evento</h3>", unsafe_allow_html=True)
    d = st.session_state.fila_datos
    
    with st.container():
        try:
            val_idx = int(str(d[54]).strip()[0]) - 1
            if val_idx < 0 or val_idx > 4: val_idx = 4
        except:
            val_idx = 4
            
        nivel_ejec = st.radio("Nivel de ejecución del evento", ["1 (Muy Deficiente)", "2 (Deficiente)", "3 (Regular)", "4 (Bueno)", "5 (Perfecto)"], index=val_idx)
        obs = st.text_area("Observaciones Finales", value=d[55] if d[55]!="-" else "")
    
    # RECUERDA: Ahora descargamos .DOCX (Word)
    st.markdown("#### 📥 Descargar Documentos en Word")
    col_pdf1, col_pdf2 = st.columns(2)
    
    try:
        with col_pdf1:
            word_ruta = generar_word_hoja_ruta(d)
            st.download_button(label="📝 Descargar Hoja de Ruta", data=word_ruta, file_name=f"Hoja_Ruta_{d[4]}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        with col_pdf2:
            word_exp = generar_word_expediente(d)
            st.download_button(label="📑 Descargar Expediente", data=word_exp, file_name=f"Expediente_{d[4]}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    except Exception as e:
        st.error(f"Sube las dos plantillas de Word a GitHub para habilitar las descargas. Detalles: {e}")

    st.write("---")
    c1, c2, c3 = st.columns(3)
    with c1: btn_regresar = st.button("⬅️ Regresar y Guardar")
    with c2: btn_terminar = st.button("TERMINADO ✔️")
    with c3: btn_eliminar = st.button("🗑️ Eliminar Evento")
    
    if btn_eliminar: st.session_state.confirmar_eliminar = True
        
    if st.session_state.confirmar_eliminar:
        st.warning("⚠️ ¿Estás completamente seguro de que deseas eliminar este evento?")
        cx1, cx2 = st.columns(2)
        with cx1:
            if st.button("✔️ Sí, eliminar permanentemente"):
                if st.session_state.fila_actual:
                    try:
                        hoja_datos.delete_rows(st.session_state.fila_actual)
                        tot = len(hoja_datos.col_values(1))
                        if tot > 1: hoja_datos.update(values=[[str(i)] for i in range(1, tot)], range_name=f"A2:A{tot}")
                        st.success("🗑️ Evento borrado."); reset_app()
                    except: st.error("Error al borrar.")
        with cx2:
            if st.button("❌ Cancelar"): st.session_state.confirmar_eliminar = False; st.rerun()

    if not st.session_state.confirmar_eliminar and (btn_terminar or btn_regresar):
        st.session_state.fila_datos[54] = nivel_ejec
        st.session_state.fila_datos[55] = obs
        if btn_terminar:
            st.session_state.fila_datos[60] = "Finalizado"
            guardar_en_excel(); st.success("🎉 ¡Evento Finalizado!"); reset_app()
        if btn_regresar: navegar('seccion_5'); st.rerun()

    st.write("---")
    if st.button("🏠 Volver al inicio"): reset_app()
