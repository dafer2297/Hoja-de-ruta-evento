import streamlit as st
import base64
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
from fpdf import FPDF

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
            /* Diseño para contenedores premium */
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
if 'fila_datos' not in st.session_state: st.session_state.fila_datos = [""] * 60

def calcular_dias(fecha_inicio, fecha_fin):
    if not fecha_inicio or not fecha_fin or fecha_inicio == "" or fecha_fin == "": return ""
    try:
        d1 = datetime.strptime(fecha_inicio, "%d/%m/%Y").date()
        d2 = datetime.strptime(fecha_fin, "%d/%m/%Y").date()
        return str((d2 - d1).days)
    except: return ""

def actualizar_calculos_automaticos():
    d = st.session_state.fila_datos
    d[55] = calcular_dias(d[6], d[10])
    d[56] = calcular_dias(d[20], d[21]) if d[18] == "Aplica" else ""
    d[57] = calcular_dias(d[27], d[28]) if d[25] == "Aplica" else ""
    d[58] = calcular_dias(d[34], d[35]) if d[32] == "Aplica" else ""

def guardar_en_excel():
    if st.session_state.fila_actual:
        actualizar_calculos_automaticos()
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
# 3. GENERADORES DE PDF (CORREGIDOS)
# ==========================================
def txt(texto):
    # ESCUDO ANTI-ERRORES: Si está vacío, devuelve un guion.
    if not texto or str(texto).strip() == "": return "-"
    # Respeta los saltos de línea (\n) para los recuadros grandes
    return str(texto).replace('“', '"').replace('”', '"').encode('latin-1', 'replace').decode('latin-1')

def generar_pdf_hoja_ruta(d):
    pdf = FPDF()
    pdf.add_page()
    try: pdf.image("logo_superior.png", 10, 8, 40)
    except: pass
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 20, "", ln=True) 
    pdf.cell(0, 10, txt(d[4].upper()), ln=True, align='C')
    pdf.ln(5)
    
    def fila_pdf(label, valor):
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(40, 7, txt(label), 0, 0)
        pdf.set_font("Arial", '', 11)
        pdf.multi_cell(0, 7, txt(valor))
        
    fila_pdf("Lugar:", d[9])
    fila_pdf("Día:", d[10])
    fila_pdf("Hora:", d[11])
    fila_pdf("Concentración:", d[42])
    fila_pdf("Responsable:", f"{d[39]} - Cel: {d[40]}")
    
    if d[43] == "Aplica": fila_pdf("Camionetas:", d[45].replace("\n", ", "))
    if d[46] == "Aplica": fila_pdf("Busetas:", d[48].replace("\n", ", "))
    if d[49] == "Aplica": fila_pdf("Auxiliares:", d[51].replace("\n", ", "))
    
    pdf.ln(3)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 7, txt("Descripción y Requerimientos:"), ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(0, 6, txt(d[52]))
    pdf.ln(3)
    
    if (d[16] == "Aplica" and d[17]) or (d[18] == "Aplica" and d[22]) or (d[32] == "Aplica" and d[36]):
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, txt("RECURSOS INSTITUCIONALES ASIGNADOS"), ln=True, border='B')
        pdf.ln(2)
        if d[16] == "Aplica" and d[17]:
            pdf.set_font("Arial", 'B', 10); pdf.cell(0, 6, txt("Recursos Culturas y Recreación:"), ln=True)
            pdf.set_font("Arial", '', 10); pdf.multi_cell(0, 5, txt(d[17])); pdf.ln(1)
        if d[18] == "Aplica" and d[22]:
            pdf.set_font("Arial", 'B', 10); pdf.cell(0, 6, txt("Recursos Comunicación:"), ln=True)
            pdf.set_font("Arial", '', 10); pdf.multi_cell(0, 5, txt(d[22])); pdf.ln(1)
        if d[32] == "Aplica" and d[36]:
            pdf.set_font("Arial", 'B', 10); pdf.cell(0, 6, txt("Recursos Administración:"), ln=True)
            pdf.set_font("Arial", '', 10); pdf.multi_cell(0, 5, txt(d[36])); pdf.ln(1)

    pdf.ln(8)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, txt(f"ORGANIZADOR DEL EVENTO: {d[7]} ({d[8]})"), ln=True, align='C')
    
    salida = pdf.output(dest='S')
    return salida.encode('latin-1') if isinstance(salida, str) else bytes(salida)

def generar_pdf_expediente(d):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 15)
    pdf.cell(0, 10, txt("EXPEDIENTE COMPLETO DEL EVENTO"), ln=True, align='C')
    pdf.ln(5)
    
    def tit(texto):
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, txt(texto), ln=True, border='B')
        pdf.ln(2)
        
    def lin(label, valor):
        pdf.set_font("Arial", 'B', 10); pdf.cell(50, 6, txt(label), 0, 0)
        pdf.set_font("Arial", '', 10); pdf.multi_cell(0, 6, txt(valor))

    tit("1. Datos Generales")
    lin("Área Institucional:", d[1])
    lin("Nombre del Evento:", d[4])
    lin("Tipo de Evento:", d[5])
    lin("Responsable Planificación:", d[3])
    lin("Lugar:", d[9])
    lin("Fecha y Hora:", f"{d[10]} | {d[11]}")
    lin("Inicio Planificación:", d[6])
    lin("Organizador Externo:", f"{d[7]} (Cel: {d[8]})")
    
    pdf.ln(5)
    tit("2. Entidades Externas")
    lin("Aplica Externas:", d[12] if d[12]!="" else "No")
    
    pdf.ln(5)
    tit("3. Áreas Internas")
    lin("Culturas / Recreación:", f"Aplica: {d[16]} | Recursos: {d[17]}")
    lin("Comunicación:", f"Aplica: {d[18]} | Cumplimiento: {d[23]}")
    lin("Talento Humano:", f"Aplica: {d[25]} | Cumplimiento: {d[30]}")
    lin("Administración:", f"Aplica: {d[32]} | Cumplimiento: {d[37]}")
    
    pdf.ln(5)
    tit("4. Logística y Transporte")
    lin("Resp. en territorio:", f"{d[39]} (Cel: {d[40]})")
    lin("Vehículos / Personal:", f"Camionetas: {d[43]} | Busetas: {d[46]} | Auxiliares: {d[49]}")
    lin("Descripción/Insumos:", d[52])
    
    pdf.ln(5)
    tit("5. Evaluación Final")
    lin("Estado del Evento:", d[59])
    lin("Nivel de Ejecución:", d[53])
    lin("Observaciones Finales:", d[54])
    
    salida = pdf.output(dest='S')
    return salida.encode('latin-1') if isinstance(salida, str) else bytes(salida)

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
                    estado = "Finalizado" if len(fila) >= 60 and fila[59] == "Finalizado" else "En proceso"
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
                    st.session_state.fila_datos = (datos_fila + [""] * 60)[:60]
                    st.session_state.pantalla = 'seccion_2'
                    st.rerun()
            with col1:
                if st.button("Regresar"): st.session_state.pantalla = 'opciones_evento'; st.rerun()
        else:
            st.warning("Aún no ha creado eventos.")
            if st.button("Regresar"): st.session_state.pantalla = 'opciones_evento'; st.rerun()
    except:
        st.error("Error al buscar.")
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
            hora_inicio = st.time_input("Hora de inicio", value=def_h_ev)
            con_fin = st.checkbox("¿Añadir hora de cierre?", value=con_fin_def)
            if con_fin: hora_fin = st.time_input("Hora de cierre", value=def_h_fin)
    
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
                st.session_state.fila_datos[59] = "En proceso"
                hoja_datos.append_row(st.session_state.fila_datos)
                st.session_state.fila_actual = num_filas + 1
            elif not d[59]: st.session_state.fila_datos[59] = "En proceso"
            
            if btn_guardar: navegar('seccion_3')
            if btn_regresar: navegar('opciones_evento')
            st.rerun()
    st.write("---")
    if st.button("🏠 Volver al inicio"): reset_app()

# --- SECCIÓN 3 --- 
elif st.session_state.pantalla == 'seccion_3':
    st.markdown("<h3 style='text-align: center; color: white;'>Coordinación con Entidades Externas</h3>", unsafe_allow_html=True)
    d = st.session_state.fila_datos
    
    aplica_def = 1 if str(d[12]).strip() != "" else 0
    aplica = st.radio("¿Aplica coordinación externa?", ["No aplica", "Aplica"], index=aplica_def)
    
    ent_str = ""; sol_str = ""; fs_str = ""; fr_str = ""
    
    if aplica == "Aplica":
        e_ex = [x for x in str(d[12]).split('\n') if x.strip()]
        s_ex = [x for x in str(d[13]).split('\n') if x.strip()]
        fs_ex = [x for x in str(d[14]).split('\n') if x.strip()]
        fr_ex = [x for x in str(d[15]).split('\n') if x.strip()]
        
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
        st.session_state.fila_datos[12:16] = [ent_str, sol_str, fs_str, fr_str] if aplica=="Aplica" else ["","","",""]
        navegar('seccion_2'); st.rerun()
    if col2.button("Guardar y Continuar ➡️"):
        st.session_state.fila_datos[12:16] = [ent_str, sol_str, fs_str, fr_str] if aplica=="Aplica" else ["","","",""]
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
        rec_cult = st.text_area("Recursos entregados (Detalle)", value=d[17], height=150) if ap_cult == "Aplica" else ""
    
    def dib_dir(idx_base):
        ap = st.radio("¿Aplica?", ["No aplica", "Aplica"], key=f"ap_{idx_base}", index=1 if d[idx_base]=="Aplica" else 0)
        if ap == "Aplica":
            sol = st.text_area("Solicitud realizada (Detalle)", value=d[idx_base+1], key=f"s_{idx_base}", height=100)
            try: vfs = datetime.strptime(d[idx_base+2], "%d/%m/%Y").date() if d[idx_base+2] else date.today()
            except: vfs = date.today()
            try: vfr = datetime.strptime(d[idx_base+3], "%d/%m/%Y").date() if d[idx_base+3] else date.today()
            except: vfr = date.today()
            c1, c2 = st.columns(2)
            with c1: fs = st.date_input("Fecha solicitud", value=vfs, key=f"fs_{idx_base}")
            with c2: fr = st.date_input("Fecha respuesta", value=vfr, key=f"fr_{idx_base}")
            rec = st.text_area("Recursos Entregados (Detalle)", value=d[idx_base+4], key=f"r_{idx_base}", height=100)
            cp = st.radio("¿Se entregó todo lo solicitado?", ["Sí", "No"], key=f"c_{idx_base}", index=1 if d[idx_base+5]=="No" else 0)
            nv = st.selectbox("Nivel de cumplimiento", ["1 (20%)", "2 (40%)", "3 (60%)", "4 (80%)"], key=f"n_{idx_base}")[0] if cp=="No" else "5"
            return ["Aplica", sol, fs.strftime("%d/%m/%Y"), fr.strftime("%d/%m/%Y"), rec, cp, nv]
        return ["No aplica", "", "", "", "", "", ""]

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
        with c1: resp_asiste = st.text_input("Nombre del responsable que asiste", value=d[39])
        with c2: cel_asiste = st.text_input("Celular", max_chars=10, value=d[40])
        c3, c4 = st.columns(2)
        with c3:
            try: hs_def = datetime.strptime(d[41], "%H:%M").time() if d[41] else datetime.now().time()
            except: hs_def = datetime.now().time()
            hora_salida = st.time_input("Hora de salida hacia el evento", value=hs_def)
        with c4: concentracion = st.text_input("Lugar de concentración", value=d[42])
    
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
            return ["No aplica", "", ""]

    r_cam = dib_log("Camionetas", 15, 43)
    r_bus = dib_log("Busetas", 15, 46)
    r_aux = dib_log("Auxiliares", 50, 49)
    
    with st.container():
        st.markdown("#### 📋 Detalles Operativos")
        insumos = st.text_area("Descripción y requerimientos del evento (Resumen e insumos)", value=d[52], height=150)
        ubicacion = st.text_input("Ubicación exacta / Link de Maps", value=d[53])

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
            val_idx = int(str(d[53]).strip()[0]) - 1
            if val_idx < 0 or val_idx > 4: val_idx = 4
        except:
            val_idx = 4
            
        nivel_ejec = st.radio("Nivel de ejecución del evento", ["1 (Muy Deficiente)", "2 (Deficiente)", "3 (Regular)", "4 (Bueno)", "5 (Perfecto)"], index=val_idx)
        obs = st.text_area("Observaciones Finales", value=d[54])
    
    st.markdown("#### 📥 Descargar Documentos Generados")
    col_pdf1, col_pdf2 = st.columns(2)
    with col_pdf1:
        pdf_ruta = generar_pdf_hoja_ruta(d)
        st.download_button(label="📄 Descargar Hoja de Ruta Operativa", data=pdf_ruta, file_name=f"Hoja_Ruta_{d[4]}.pdf", mime="application/pdf")
    with col_pdf2:
        pdf_exp = generar_pdf_expediente(d)
        st.download_button(label="📑 Descargar Expediente Completo", data=pdf_exp, file_name=f"Expediente_{d[4]}.pdf", mime="application/pdf")

    st.write("---")
    c1, c2, c3 = st.columns(3)
    with c1: btn_regresar = st.button("⬅️ Regresar y Guardar")
    with c2: btn_terminar = st.button("TERMINADO ✔️")
    with c3: btn_eliminar = st.button("🗑️ Eliminar Evento")
    
    if btn_eliminar: st.session_state.confirmar_eliminar = True
        
    if st.session_state.confirmar_eliminar:
        st.warning("⚠️ ¿Estás completamente seguro de que deseas eliminar este evento? Esta acción no se puede deshacer.")
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
        st.session_state.fila_datos[53] = nivel_ejec[0]
        st.session_state.fila_datos[54] = obs
        if btn_terminar:
            st.session_state.fila_datos[59] = "Finalizado"
            guardar_en_excel(); st.success("🎉 ¡Evento Finalizado!"); reset_app()
        if btn_regresar: navegar('seccion_5'); st.rerun()

    st.write("---")
    if st.button("🏠 Volver al inicio"): reset_app()
