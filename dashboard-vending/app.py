import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Migración QR 3.0", layout="wide")

# Título y cuenta regresiva al 31 de marzo
st.title("🚀 Control Global: Monitor Migración QR 3.0")
deadline = datetime(2026, 3, 31)
dias_restantes = (deadline - datetime.now()).days
st.warning(f"⏳ Faltan {dias_restantes} días para el apagón de la tecnología BT.")

# Subida de archivo
file = st.file_uploader("Subí tu archivo acumulativo (Excel o CSV)", type=['xlsx', 'csv'])

if file:
    # Cargar datos
    df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    
    # Obtener las dos últimas fechas para comparar
    fechas = sorted(df['Fecha'].unique(), reverse=True)
    hoy = fechas[0]
    ayer = fechas[1] if len(fechas) > 1 else hoy

    # Filtrar data
    df_hoy = df[df['Fecha'] == hoy]
    df_ayer = df[df['Fecha'] == ayer]

    # --- KPIs PRINCIPALES ---
    c1, c2, c3 = st.columns(3)
    
    # Ops BT (Queremos que baje)
    bt_hoy = df_hoy['Cantidad de operaciones BT'].sum()
    bt_ayer = df_ayer['Cantidad de operaciones BT'].sum()
    c1.metric("Ops BT Totales", f"{bt_hoy:,}", delta=int(bt_hoy - bt_ayer), delta_color="inverse")

    # Ops QR (Queremos que suba)
    qr_hoy = df_hoy['cantidad de operaciones QR3.0'].sum()
    qr_ayer = df_ayer['cantidad de operaciones QR3.0'].sum()
    c2.metric("Ops QR 3.0 Totales", f"{qr_hoy:,}", delta=int(qr_hoy - qr_ayer))

    # UMs Migradas (Cualquiera que tenga al menos 1 op QR)
    ums_qr = df_hoy[df_hoy['cantidad de operaciones QR3.0'] > 0]['Serial UM'].nunique()
    c3.metric("UMs con QR Activo", ums_qr)

    # --- TABLA DE RESELLERS ---
    st.subheader(f"Estado por Reseller al {hoy.strftime('%d/%m/%Y')}")
    
    resumen = df_hoy.groupby(['Pais', 'Reseller']).agg(
        Cant_UM=('Serial UM', 'nunique'),
        Total_BT=('Cantidad de operaciones BT', 'sum'),
        Total_QR=('cantidad de operaciones QR3.0', 'sum'),
        UMs_con_QR=('cantidad de operaciones QR3.0', lambda x: (x > 0).sum())
    ).reset_index()

    st.dataframe(resumen, use_container_width=True)