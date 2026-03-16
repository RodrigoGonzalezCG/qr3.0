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
    
    # Simular que los datos de hoy son los que cargamos
    # Para la comparativa, como el archivo es acumulativo al 100%, 
    # calcularemos la diferencia contra el objetivo o una carga previa.
    
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
    
    # Cálculo de salud de la migración por reseller
    resumen['% QR3'] = (resumen['UM_con_QR3'] / resumen['Cant_UM'] * 100).round(1)
    
    # Mostrar tabla con formato
    st.dataframe(resumen.sort_values(by='% QR3', ascending=False), use_container_width=True)

    # --- RECOMENDACIÓN ---
    st.divider()

else:
    st.info("👈 Por favor, seleccioná la fecha y subí tu archivo en el panel de la izquierda.")
