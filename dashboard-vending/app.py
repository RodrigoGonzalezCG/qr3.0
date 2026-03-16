import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Migración QR 3.0", layout="wide")

# --- ESTILO CSS PARA LAS TARJETAS ---
st.markdown("""
    <style>
    [data-testid="stMetric"] {
        background-color: #31333F;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #464855;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("Monitor de Migración: BT a QR 3.0")

# --- ENTRADA DE DATOS (CONFIGURACIÓN) ---
with st.sidebar:
    st.header("Configuración")
    st.link_button("🚀 Obtener datos (Metabase)", 
                   "https://data.srvcontrol.com.ar:8000/public/question/95d0dd10-944c-4923-8990-1cf82c4103b7")
    st.divider()
    fecha_carga = st.date_input("¿A qué fecha corresponde este reporte?", datetime.now())
    archivo = st.file_uploader("Subí el reporte acumulado (XLS o CSV)", type=['xlsx', 'csv'])

if archivo:
    try:
        if archivo.name.endswith('.xlsx'):
            df = pd.read_excel(archivo)
        else:
            df = pd.read_csv(archivo, sep=None, engine='python', encoding='utf-8')
        
        df.columns = df.columns.str.strip() 

        # --- LIMPIEZA DE NÚMEROS (Quitar comas de los miles) ---
        for col in ['Operaciones BT', 'Operaciones QR3.0']:
            if df[col].dtype == 'object':
                df[col] = df[col].str.replace(',', '', regex=False).fillna(0).astype(float)
            else:
                df[col] = df[col].fillna(0).astype(float)
        
        # --- FILTRO DE PAÍS ---
        df = df[df['Pais'].isin(['Argentina', 'Chile', 'Uruguay'])]
        
        # --- PROCESAMIENTO ---
        total_bt = int(df['Operaciones BT'].sum())
        total_qr = int(df['Operaciones QR3.0'].sum())
        total_ums = df['SerialUM'].nunique()
        ums_con_qr = df[df['Operaciones QR3.0'] > 0]['SerialUM'].nunique()
        porcentaje_migrado = (ums_con_qr / total_ums) * 100 if total_ums > 0 else 0

        # --- MÉTRICAS PRINCIPALES ---
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Ops BT Acumuladas", f"{total_bt:,}")
        col2.metric("Ops QR 3.0 Acumuladas", f"{total_qr:,}")
        col3.metric("Cant. UM Totales", f"{total_ums:,}")
        col4.metric("UMs con QR3.0", f"{ums_con_qr:,}")
        col5.metric("% Migración UMs", f"{porcentaje_migrado:.1f}%")

        # --- ANÁLISIS POR RESELLER ---
        st.subheader(f"Estado de Clientes al {fecha_carga.strftime('%d/%m/%Y')}")
        
        resumen = df.groupby(['Pais', 'Reseller']).agg(
            Cant_UM=('SerialUM', 'nunique'),
            Suma_BT=('Operaciones BT', 'sum'),
            Suma_QR3=('Operaciones QR3.0', 'sum'),
            UM_con_QR3=('Operaciones QR3.0', lambda x: (x > 0).sum())
        ).reset_index()
        
        resumen['% QR3'] = (resumen['UM_con_QR3'] / resumen['Cant_UM'] * 100).round(1)
        resumen['UM_Pendientes'] = resumen['Cant_UM'] - resumen['UM_con_QR3']
        
        st.dataframe(resumen.sort_values(by='% QR3', ascending=False), use_container_width=True)

        st.divider()

        # --- SECCIÓN DE RANKINGS ---
        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("🔝 Top 10: Clientes con más UM")
            top_10_volumen = resumen.sort_values(by='Cant_UM', ascending=False).head(10)
            st.table(top_10_volumen[['Reseller', 'Cant_UM', '% QR3']])

        with col_right:
            st.subheader("⚠️ Top 10: Clientes Críticos")
            criticos_reales = resumen.sort_values(by='UM_Pendientes', ascending=False).head(10)
            st.table(criticos_reales[['Reseller', 'Cant_UM', 'UM_Pendientes', '% QR3']])
            
    except Exception as e:
        st.error(f"Error técnico: {e}")
else:
    st.info("👈 Hacé clic en 'Obtener datos', descarga el archivo y subilo acá.")
