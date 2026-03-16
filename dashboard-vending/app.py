import streamlit as st
import pandas as pd
from datetime import datetime
import io
import plotly.express as px

st.set_page_config(page_title="Migración QR 3.0", layout="wide")

# --- ESTILO CSS ---
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

# --- SIDEBAR ---
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

        # --- LIMPIEZA DE NÚMEROS ---
        for col in ['Operaciones BT', 'Operaciones QR3.0']:
            if df[col].dtype == 'object':
                df[col] = df[col].str.replace(',', '', regex=False).fillna(0).astype(float)
            else:
                df[col] = df[col].fillna(0).astype(float)
        
        df = df[df['Pais'].isin(['Argentina', 'Chile', 'Uruguay'])]
        
        # --- PROCESAMIENTO ---
        total_bt = int(df['Operaciones BT'].sum())
        total_qr = int(df['Operaciones QR3.0'].sum())
        total_ums = df['SerialUM'].nunique()
        ums_con_qr = df[df['Operaciones QR3.0'] > 0]['SerialUM'].nunique()
        porcentaje_migrado = (ums_con_qr / total_ums) * 100 if total_ums > 0 else 0

        # --- MÉTRICAS ---
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Ops BT Acumuladas", f"{total_bt:,}")
        col2.metric("Ops QR 3.0 Acumuladas", f"{total_qr:,}")
        col3.metric("Cant. UM Totales", f"{total_ums:,}")
        col4.metric("UMs con QR3.0", f"{ums_con_qr:,}")
        col5.metric("% Migración UMs", f"{porcentaje_migrado:.1f}%")

        # --- BOTÓN DESCARGAR (UBICACIÓN ARRIBA) ---
        resumen = df.groupby(['Pais', 'Reseller']).agg(
            Cant_UM=('SerialUM', 'nunique'),
            Suma_BT=('Operaciones BT', 'sum'),
            Suma_QR3=('Operaciones QR3.0', 'sum'),
            UM_con_QR3=('Operaciones QR3.0', lambda x: (x > 0).sum())
        ).reset_index()
        resumen['% QR3'] = (resumen['UM_con_QR3'] / resumen['Cant_UM'] * 100).round(1)
        resumen['UM_Pendientes'] = resumen['Cant_UM'] - resumen['UM_con_QR3']
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            resumen.to_excel(writer, index=False, sheet_name='Resumen')
        
        st.download_button(
            label="📥 Descargar Informe en Excel",
            data=output.getvalue(),
            file_name=f"Informe_Migracion_QR_{fecha_carga.strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # --- TABLA PRINCIPAL ---
        st.subheader(f"Estado de Clientes al {fecha_carga.strftime('%d/%m/%Y')}")
        st.dataframe(resumen.sort_values(by='% QR3', ascending=False), use_container_width=True)

        st.divider()

        # --- RANKINGS ---
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🔝 Top 10: Más UM")
            st.table(resumen.sort_values(by='Cant_UM', ascending=False).head(10)[['Reseller', 'Cant_UM', '% QR3']])
        with c2:
            st.subheader("⚠️ Top 10: Críticos")
            st.table(resumen.sort_values(by='UM_Pendientes', ascending=False).head(10)[['Reseller', 'Cant_UM', 'UM_Pendientes', '% QR3']])

        # --- SECCIÓN DE GRÁFICOS ---
        st.divider()
        st.header("📊 Análisis Visual")
        
        g1, g2 = st.columns(2)
        
        with g1:
            # 1. Gráfico de Dona: Distribución de UMs por País
            fig_dona = px.pie(resumen, values='Cant_UM', names='Pais', hole=0.5, 
                             title="Distribución Total de UMs por País")
            st.plotly_chart(fig_dona, use_container_width=True)
            

        with g2:
            # 2. Gráfico de Barras Apiladas: Migrado vs Pendiente
            resumen_pais = resumen.groupby('Pais').agg({'UM_con_QR3': 'sum', 'UM_Pendientes': 'sum'}).reset_index()
            fig_barras = px.bar(resumen_pais, x='Pais', y=['UM_con_QR3', 'UM_Pendientes'], 
                               title="Estado de Migración por País (Equipos)",
                               labels={'value': 'Cantidad de UMs', 'variable': 'Estado'},
                               color_discrete_map={'UM_con_QR3': '#00CC96', 'UM_Pendientes': '#EF553B'})
            st.plotly_chart(fig_barras, use_container_width=True)
            

        # 3. Matriz de Riesgo (Scatter Plot)
        st.subheader("🎯 Matriz de Riesgo: Volumen vs Avance")
        fig_scatter = px.scatter(resumen, x='Cant_UM', y='% QR3', size='UM_Pendientes', 
                                 color='Pais', hover_name='Reseller',
                                 title="Clientes: Tamaño vs % de Migración (Círculos más grandes = más pendientes)")
        st.plotly_chart(fig_scatter, use_container_width=True)
        
            
    except Exception as e:
        st.error(f"Error técnico: {e}")
else:
    st.info("👈 Cargá un archivo para ver los gráficos.")
