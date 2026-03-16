import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Migración QR 3.0", layout="wide")

st.title("Monitor de Migración: BT a QR 3.0")

# --- ENTRADA DE DATOS ---
with st.sidebar:
    st.header("Configuración")
    fecha_carga = st.date_input("¿A qué fecha corresponde este reporte?", datetime.now())
    archivo = st.file_uploader("Subí el reporte acumulado (XLS o CSV)", type=['xlsx', 'csv'])

if archivo:
    # Leer datos
    df = pd.read_excel(archivo) if archivo.name.endswith('.xlsx') else pd.read_csv(archivo)
    df.columns = df.columns.str.strip() # Limpiar nombres de columnas
    
    # --- FILTRO DE PAÍS ---
    df = df[df['Pais'].isin(['Argentina', 'Chile', 'Uruguay'])]
    
    # --- PROCESAMIENTO ---
    total_bt = df['Operaciones BT'].sum()
    total_qr = df['Operaciones QR3.0'].sum()
    total_ums = df['SerialUM'].nunique()
    ums_con_qr = df[df['Operaciones QR3.0'] > 0]['SerialUM'].nunique()
    
    # Porcentaje de migración
    porcentaje_migrado = (ums_con_qr / total_ums) * 100 if total_ums > 0 else 0

    # --- MÉTRICAS PRINCIPALES ---
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Ops BT Acumuladas", f"{total_bt:,}")
    col2.metric("Ops QR 3.0 Acumuladas", f"{total_qr:,}")
    col3.metric("UMs con QR3.0", f"{ums_con_qr:,}")
    col4.metric("% Migración UMs", f"{porcentaje_migrado:.1f}%")

    # --- ANÁLISIS POR RESELLER ---
    st.subheader(f"Estado de Clientes al {fecha_carga.strftime('%d/%m/%Y')}")
    
    resumen = df.groupby(['Pais', 'Reseller']).agg(
        Cant_UM=('SerialUM', 'nunique'),
        Suma_BT=('Operaciones BT', 'sum'),
        Suma_QR3=('Operaciones QR3.0', 'sum'),
        UM_con_QR3=('Operaciones QR3.0', lambda x: (x > 0).sum())
    ).reset_index()
    
    resumen['% QR3'] = (resumen['UM_con_QR3'] / resumen['Cant_UM'] * 100).round(1)
    
    st.dataframe(resumen.sort_values(by='% QR3', ascending=False), use_container_width=True)

    st.divider()

    # --- NUEVAS TABLAS: TOP 10 ---
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("🔝 Top 10: Clientes con más UM")
        # Tomamos los 10 con más UM, pero los ordenamos por % QR3 de mayor a menor
        top_10_volumen = resumen.nlargest(10, 'Cant_UM').sort_values(by='% QR3', ascending=False)
        st.table(top_10_volumen[['Reseller', 'Cant_UM', '% QR3']])

    with col_right:
        st.subheader("✅ Top 10: Tarea Cumplida (100% QR)")
        # Filtramos 100%, y ordenamos por Suma_QR3 de mayor a menor
        tarea_cumplida = resumen[resumen['% QR3'] == 100].sort_values(by='Suma_QR3', ascending=False).head(10)
        if not tarea_cumplida.empty:
            st.table(tarea_cumplida[['Reseller', 'Cant_UM', 'Suma_QR3']])
        else:
            st.write("Aún no hay clientes con el 100% de la tarea realizada.")

else:
    st.info("👈 Por favor, seleccioná la fecha y subí tu archivo en el panel de la izquierda.")
