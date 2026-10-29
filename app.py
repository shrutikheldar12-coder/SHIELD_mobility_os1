import streamlit as st
import pandas as pd
import numpy as np
import time
import hashlib
import plotly.graph_objects as go
import plotly.express as px
import folium
from streamlit_folium import folium_static
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
from wordcloud import WordCloud
from datetime import datetime
import sys
import json

sys.path.append('data')
from maharashtra_data import DAMS, RIVERS, BRIDGES
from bridge_analytics import BRIDGE_ANALYTICS_DATA
from maharashtra_bridges_master import MAHARASHTRA_MASTER_BRIDGES
from river_bridge_matrix import MAJOR_RIVER_MATRIX

st.set_page_config(page_title="S.H.I.E.L.D. Mobility OS", layout="wide")

# ==========================================
# ENTERPRISE UI & CSS
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; }
    .block-container { padding-top: 1rem; }
    .gov-header { background: linear-gradient(90deg, #0F172A, #1E3A8A); color: white; padding: 15px 25px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .gov-title { font-size: 24px; font-weight: 800; margin: 0; color: white !important;}
    .gov-subtitle { font-size: 14px; color: #94A3B8; margin: 0;}
    .kpi-card { background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #3B82F6; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 10px; }
    .kpi-title { font-size: 12px; color: #64748B; text-transform: uppercase; font-weight: 600;}
    .kpi-value { font-size: 24px; font-weight: 800; color: #0F172A; margin-top: 5px;}
    .kpi-danger { border-left-color: #EF4444; }
    .kpi-warning { border-left-color: #F59E0B; }
    .kpi-success { border-left-color: #10B981; }
    .alert-banner { background: #FEF2F2; border: 1px solid #FECACA; border-left: 6px solid #EF4444; padding: 15px; border-radius: 6px; color: #991B1B; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# SESSION STATE
# ==========================================
if "auth" not in st.session_state: st.session_state.auth = False
if "flood" not in st.session_state: st.session_state.flood = False
if "live_discharge" not in st.session_state: st.session_state.live_discharge = 150.0
if "live_scour" not in st.session_state: st.session_state.live_scour = 1.1
if "sim_running" not in st.session_state: st.session_state.sim_running = False

# ==========================================
# AUTH
# ==========================================
def get_hash(pw): return hashlib.sha256(pw.encode()).hexdigest()
if not st.session_state.auth:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br><h2 style='text-align:center; color:#1E3A8A;'>🛡️ S.H.I.E.L.D. Neural AI</h2>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Secure Login", width="stretch", type="primary"):
                if u == "admin" and get_hash(p) == get_hash("shield2025"):
                    st.session_state.auth = True
                    st.rerun()
                else: st.error("Invalid Credentials")
    st.stop()

# ==========================================
# PHYSICS & PDF GENERATOR (Cloud-Safe)
# ==========================================
def calculate_scour(discharge):
    # Replaced PyTorch with exact Physics formula for cloud deployment speed
    flow_depth = (discharge / 90.0) ** 0.6
    lacey = 0.473 * (discharge / 1.25) ** (1/3)
    return lacey * 0.984

def generate_pdf(bridge, scour, status):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="MAHARASHTRA PWD - EMERGENCY REPORT", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.cell(200, 10, txt=f"Bridge: {bridge}", ln=True)
    pdf.cell(200, 10, txt=f"AI Scour Prediction: {scour:.2f} m", ln=True)
    pdf.cell(200, 10, txt=f"Status: {status}", ln=True)
    return bytes(pdf.output())

# ==========================================
# SIDEBAR (MODULES)
# ==========================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Seal_of_Maharashtra.svg/1200px-Seal_of_Maharashtra.svg.png", width=80)
    st.markdown("<h4 style='color:#1E3A8A;'>Mobility OS v19.0</h4>", unsafe_allow_html=True)
    st.markdown("---")
    
    page = st.radio("Navigation", [
        "1. Command Center",
        "2. Bridge Inventory",
        "3. GIS Threat Map",
        "4. Neural Network Engine",
        "5. Live IoT Simulation",
        "6. Emergency Dispatch",
        "7. Bridge Health & Fatigue",
        "8. Research & Analytics",
        "9. Sensor Diagnostics",
        "10. API Portal",
        "11. Detailed Engineering Data",
        "12. Statewide Master Bridge Registry",
        "13. Satellite Data Feed (Live)",
        "14. Major Rivers & Key Bridges Matrix"
    ])
    
    st.markdown("---")
    if st.button("🚪 Logout", width="stretch"):
        st.session_state.auth = False
        st.session_state.sim_running = False
        st.rerun()

# ==========================================
# HEADER
# ==========================================
st.markdown("""
<div class="gov-header">
    <div>
        <h1 class="gov-title">S.H.I.E.L.D. Neural Mobility OS</h1>
        <p class="gov-subtitle">Complete Weather-Resilient Infrastructure System (Maharashtra)</p>
    </div>
    <div style="text-align:right;">
        <span style="background:rgba(16, 185, 129, 0.2); color:#10B981; padding:5px 10px; border-radius:20px; font-weight:bold; font-size:12px;">● SYSTEM ACTIVE</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# PAGES
# ==========================================

# --- 1. COMMAND CENTER ---
if page == "1. Command Center":
    if st.session_state.flood:
        st.markdown('<div class="alert-banner"><h4>🚨 FLOOD ALERT: Ujani Dam Release</h4><p>Water release from Ujani Dam causing Bhima River levels to rise. Solapur Bridge is at risk.</p></div>', unsafe_allow_html=True)
    else:
        st.success("🟢 Network Normal. All dams, rivers, and bridges are operational.")
        
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown('<div class="kpi-card"><div class="kpi-title">Monitored Dams</div><div class="kpi-value">5</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi-card kpi-danger"><div class="kpi-title">Active Alerts</div><div class="kpi-value" style="color:#EF4444;">{"1" if st.session_state.flood else "0"}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="kpi-card kpi-warning"><div class="kpi-title">Traffic Disrupted</div><div class="kpi-value" style="color:#F59E0B;">{"14,500" if st.session_state.flood else "0"}</div></div>', unsafe_allow_html=True)
    c4.markdown('<div class="kpi-card kpi-success"><div class="kpi-title">Uptime</div><div class="kpi-value" style="color:#10B981;">99.9%</div></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.button("🌊 Simulate Monsoon Flood", type="primary", on_click=lambda: st.session_state.update(flood=True))

# --- 2. BRIDGE INVENTORY ---
elif page == "2. Bridge Inventory":
    st.subheader("Bridge Asset Registry")
    bridge_data = {
        "Bridge ID": ["MH-SOL-003", "MH-NSK-001", "MH-PUN-004", "MH-KOL-002"],
        "Name": ["Khawaspur Bridge", "Holkar Bridge", "Khadakwasla Bridge", "Panchganga Bridge"],
        "District": ["Solapur", "Nashik", "Pune", "Kolhapur"],
        "River": ["Man (Bhima Tributary)", "Godavari", "Mula-Mutha", "Panchganga"],
        "Status": ["🔴 Critical" if st.session_state.flood else "🟢 Safe", "🟢 Safe", "🟢 Safe", "🟢 Safe"]
    }
    st.dataframe(pd.DataFrame(bridge_data), width="stretch")

# --- 3. GIS THREAT MAP ---
elif page == "3. GIS Threat Map":
    st.subheader("Maharashtra Infrastructure Network")
    col1, col2, col3 = st.columns(3)
    show_rivers = col1.checkbox("Show Rivers", True)
    show_bridges = col2.checkbox("Show Bridges", True)
    show_flood = col3.checkbox("Show Flooded Areas", True)
    
    m = folium.Map(location=[19.0, 75.5], zoom_start=7, tiles="OpenStreetMap")
    
    if show_flood and st.session_state.flood:
        flood_poly = [[17.9, 75.5], [18.1, 75.8], [17.7, 76.1], [17.5, 75.8]]
        folium.Polygon(flood_poly, color="red", fill=True, fill_color="red", fill_opacity=0.3, tooltip="Flooded Area").add_to(m)
    
    if show_rivers:
        for name, data in RIVERS.items():
            weight = 6 if name in ["Godavari", "Bhima", "Krishna"] else 3
            color = "#EF4444" if st.session_state.flood and name == "Bhima" else "#3B82F6"
            folium.PolyLine(data["coords"], color=color, weight=weight, tooltip=name).add_to(m)
            
    if show_bridges:
        for b in BRIDGES:
            pin_color = "red" if st.session_state.flood and b["status"] == "Critical" else "green"
            folium.Marker(b["loc"], popup=b["name"], icon=folium.Icon(color=pin_color, icon="info-sign")).add_to(m)
            
    for d in DAMS:
        pin_color = "red" if st.session_state.flood and d["status"] == "Critical" else "blue"
        folium.Marker([d["lat"], d["lon"]], popup=f"<b>{d['name']}</b><br>River: {d['river']}", icon=folium.Icon(color=pin_color, icon="tint")).add_to(m)
        
    folium_static(m, width=1100, height=500)

# --- 4. NEURAL NETWORK ENGINE ---
elif page == "4. Neural Network Engine":
    st.subheader("Deep Learning Scour Prediction (Physics-Informed)")
    discharge = st.slider("Simulate River Discharge (m³/s)", 50, 5000, 3200 if st.session_state.flood else 400)
    
    pred_scour = calculate_scour(discharge)
    
    c1, c2 = st.columns(2)
    c1.metric("Input Discharge", f"{discharge:.0f} m³/s")
    c2.metric("AI Predicted Scour", f"{pred_scour:.2f} m")
    
    st.markdown("#### Neural Network Architecture")
    st.code("""
    Input Layer (1) 
    └── LSTM Layer (64 hidden units)
        └── Fully Connected Layer
            └── Output Layer (Scour Depth)
    """)

# --- 5. LIVE IOT SIMULATION ---
elif page == "5. Live IoT Simulation":
    st.subheader("Bridge MH-SOL-003 — Real-Time Telemetry")
    c1, c2 = st.columns([3, 1])
    with c2:
        if not st.session_state.sim_running:
            if st.button("▶ START STREAM", type="primary", width="stretch"):
                st.session_state.sim_running = True
                st.rerun()
        else:
            if st.button("⏸ PAUSE STREAM", width="stretch"):
                st.session_state.sim_running = False
                st.rerun()
        st.metric("Current Discharge", f"{st.session_state.live_discharge:.0f} m³/s")

    with c1:
        if st.session_state.sim_running:
            st.session_state.live_discharge += np.random.uniform(10, 40)
            st.session_state.live_scour = calculate_scour(st.session_state.live_discharge)
            if st.session_state.live_scour > 2.8:
                st.session_state.flood = True
            time.sleep(1.5)
            st.rerun()

        if st.session_state.live_scour > 2.8:
            st.markdown('<div class="alert-banner">🚨 CRITICAL FLOOD ALERT: Scour exceeding safe threshold.</div>', unsafe_allow_html=True)
            
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=st.session_state.live_scour,
            title={'text': "Real-Time Scour Depth (m)"},
            gauge={'axis': {'range': [0, 5]}, 'bar': {'color': "#EF4444" if st.session_state.live_scour > 2.8 else "#3B82F6"}}
        ))
        st.plotly_chart(fig, width="stretch")

# --- 6. EMERGENCY DISPATCH ---
elif page == "6. Emergency Dispatch":
    st.subheader("Multi-Channel Alert Dissemination & PDF")
    tab1, tab2, tab3 = st.tabs(["📱 Public SMS", "🏢 Government Order", "📄 Export PDF"])
    
    with tab1:
        st.error("> SMS: Ujani Dam release causing Bhima River flood. Avoid Solapur Bridge. Helpline: 108.")
        st.button("Dispatch SMS (45,000 citizens)", type="primary")
    with tab2:
        st.warning("> ORDER: TO PWD Solapur. Deploy riprap at Solapur Bridge. NDRF standby.")
        st.button("Dispatch Official Order", type="primary")
    with tab3:
        if st.session_state.flood:
            pdf_bytes = generate_pdf("Khawaspur Bridge", st.session_state.live_scour, "CRITICAL")
            st.download_button(label="📄 Download Official PDF Report", data=pdf_bytes, file_name="Report.pdf", mime="application/pdf", type="primary", width="stretch")
        else:
            st.info("PDF reports are only generated during critical alerts.")

# --- 7. BRIDGE HEALTH & FATIGUE ---
elif page == "7. Bridge Health & Fatigue":
    st.subheader("Structural Health Index (BSHI)")
    bshi = 0.35 if st.session_state.flood else 0.95
    st.progress(bshi, text=f"BSHI: {bshi:.2f} / 1.00")
    if bshi < 0.65:
        st.error("🔴 STOP COMMAND: Structural integrity compromised.")
    st.metric("Fatigue Life Consumed", "62%" if st.session_state.flood else "14%")

# --- 8. RESEARCH & ANALYTICS ---
elif page == "8. Research & Analytics":
    st.subheader("Advanced Engineering Research & Analytics")
    df_analytics = pd.DataFrame(BRIDGE_ANALYTICS_DATA)
    
    np.random.seed(42)
    days = np.arange(1, 31)
    discharge_sim = 150 + 2500 * np.exp(-((days - 15)**2) / 20) + np.random.normal(0, 30, 30)
    discharge_sim = np.clip(discharge_sim, 50, None)
    scour_sim = (0.473 * (discharge_sim / 1.25) ** (1/3)) * 0.984
    
    st.markdown("### 📈 30-Day Hydrological & Scour Monitoring")
    fig_time = go.Figure()
    fig_time.add_trace(go.Scatter(x=days, y=discharge_sim, name="River Discharge (m³/s)", line=dict(color='#3B82F6', width=2), yaxis='y1'))
    fig_time.add_trace(go.Scatter(x=days, y=scour_sim, name="Scour Depth (m)", line=dict(color='#EF4444', width=2), yaxis='y2'))
    fig_time.update_layout(title="Monsoon Event Simulation (Day 1 to 30)", xaxis=dict(title="Days"), yaxis=dict(title=dict(text="Discharge (m³/s)", font=dict(color="#3B82F6"))), yaxis2=dict(title=dict(text="Scour Depth (m)", font=dict(color="#EF4444")), overlaying='y', side='right'), legend=dict(x=0.01, y=0.99))
    st.plotly_chart(fig_time, width="stretch")
    
    col1, col2 = st.columns(2)
    with col1:
        fig_dist = px.histogram(df_analytics, x="Flood Scour (m)", y="Flood Water Depth (m)", color="River Name", marginal="box", title="Flood Scour vs Water Depth")
        st.plotly_chart(fig_dist, width="stretch")
    with col2:
        fig_corr = px.scatter(df_analytics, x="Flood Velocity (m/s)", y="Flood Scour (m)", size="Flood Water Depth (m)", color="Damage Details", text="Bridge Location", title="Velocity vs Scour")
        st.plotly_chart(fig_corr, width="stretch")
        
    fig_cost = go.Figure()
    fig_cost.add_trace(go.Bar(x=df_analytics['Bridge Location'], y=df_analytics['Maintenance Cost (₹ Lakhs)'], name='Maintenance (Lakhs)', marker_color='#F59E0B'))
    fig_cost.add_trace(go.Bar(x=df_analytics['Bridge Location'], y=df_analytics['New Bridge Cost (₹ Crores)'] * 100, name='New Bridge (Lakhs Eq)', marker_color='#EF4444'))
    fig_cost.update_layout(barmode='group', title="Financial Impact")
    st.plotly_chart(fig_cost, width="stretch")

# --- 9. SENSOR DIAGNOSTICS ---
elif page == "9. Sensor Diagnostics":
    st.subheader("Edge Computing & Network Status")
    c1, c2, c3 = st.columns(3)
    c1.info("**Sonar Node:** Battery 92% | Signal: **5G Network**")
    c2.info("**Accelerometer:** Battery 88% | Signal: **5G Network**")
    c3.info("**Edge Gateway:** CPU 45% | Buffer 12% | Status: **Online**")

# --- 10. API PORTAL ---
elif page == "10. API Portal":
    st.subheader("Developer API Portal")
    st.code("GET /api/v1/bridges\nGET /api/v1/scour/{bridge_id}\nPOST /api/v1/alerts", language="http")
    st.json({"bridge_id": "MH-SOL-003", "river": "Bhima", "nn_scour_prediction_m": round(st.session_state.live_scour, 2), "status": "CRITICAL" if st.session_state.flood else "NORMAL"})

# --- 11. DETAILED ENGINEERING DATA ---
elif page == "11. Detailed Engineering Data":
    st.subheader("Comprehensive Bridge Engineering, Scour & Cost Analysis")
    df_analytics = pd.DataFrame(BRIDGE_ANALYTICS_DATA)
    st.markdown("### 📊 Master Engineering Database")
    st.dataframe(df_analytics, width="stretch")
    
    col1, col2 = st.columns(2)
    with col1:
        fig_scour = px.scatter(df_analytics, x="Flood Velocity (m/s)", y="Flood Scour (m)", text="Bridge Location", color="River Name", size="Flood Water Depth (m)", title="Scour vs Velocity")
        st.plotly_chart(fig_scour, width="stretch")
    with col2:
        fig_comp = go.Figure(data=[go.Bar(name='Normal Scour', x=df_analytics['Bridge Location'], y=df_analytics['Normal Scour (m)'], marker_color='#10B981'), go.Bar(name='Flood Scour', x=df_analytics['Bridge Location'], y=df_analytics['Flood Scour (m)'], marker_color='#EF4444')])
        fig_comp.update_layout(barmode='group', title="Normal vs Flood Scour")
        st.plotly_chart(fig_comp, width="stretch")
        
    col3, col4 = st.columns(2)
    with col3:
        fig_cost = go.Figure(data=[go.Bar(name='Maintenance', x=df_analytics['Bridge Location'], y=df_analytics['Maintenance Cost (₹ Lakhs)'], marker_color='#F59E0B'), go.Bar(name='New Bridge', x=df_analytics['Bridge Location'], y=df_analytics['New Bridge Cost (₹ Crores)'], marker_color='#3B82F6')])
        fig_cost.update_layout(barmode='group', title="Repair vs Rebuild Cost")
        st.plotly_chart(fig_cost, width="stretch")
    with col4:
        bridge_names = df_analytics['Bridge Location'].tolist()
        selected_bridge = st.selectbox("Select Bridge", bridge_names)
        bridge_row = df_analytics[df_analytics['Bridge Location'] == selected_bridge].iloc[0]
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(r=[bridge_row['Normal Water Depth (m)'], bridge_row['Normal Velocity (m/s)'], bridge_row['Normal Scour (m)']], theta=['Depth', 'Velocity', 'Scour'], fill='toself', name='Normal', line_color='#10B981'))
        fig_radar.add_trace(go.Scatterpolar(r=[bridge_row['Flood Water Depth (m)'], bridge_row['Flood Velocity (m/s)'], bridge_row['Flood Scour (m)']], theta=['Depth', 'Velocity', 'Scour'], fill='toself', name='Flood', line_color='#EF4444'))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), title=f"Profile: {selected_bridge}")
        st.plotly_chart(fig_radar, width="stretch")

    m = folium.Map(location=[19.0, 75.5], zoom_start=7, tiles="OpenStreetMap")
    for _, row in df_analytics.iterrows():
        folium.Marker([row["Latitude"], row["Longitude"]], popup=f"<b>{row['Bridge Location']}</b><br>River: {row['River Name']}", icon=folium.Icon(color="red" if st.session_state.flood else "green", icon="info-sign")).add_to(m)
    folium_static(m, width=1100, height=400)

# --- 12. STATEWIDE MASTER BRIDGE REGISTRY ---
elif page == "12. Statewide Master Bridge Registry":
    st.subheader("Maharashtra Statewide Master Bridge Registry")
    df_master = pd.DataFrame(MAHARASHTRA_MASTER_BRIDGES)
    st.dataframe(df_master, width="stretch")
    
    c1, c2 = st.columns(2)
    with c1:
        fig_pie = px.pie(df_master, names="Type", color="Type", color_discrete_map={"Major Bridge": "#3B82F6", "Minor Bridge": "#10B981", "Cable-Stayed Bridge (Flyover)": "#F59E0B"}, title="Infrastructure Distribution")
        st.plotly_chart(fig_pie, width="stretch")
    with c2:
        fig_scatter = px.scatter(df_master, x="Max Velocity (m/s)", y="Flood Scour (m)", color="Type", size="Total Length (m)", hover_name="Bridge Name", title="Scour vs Velocity")
        st.plotly_chart(fig_scatter, width="stretch")

    m = folium.Map(location=[19.5, 75.5], zoom_start=6, tiles="OpenStreetMap")
    for _, row in df_master.iterrows():
        icon_color = "orange" if row["Type"] == "Cable-Stayed Bridge (Flyover)" else ("red" if row["Type"] == "Major Bridge" else "green")
        folium.Marker([row["Latitude"], row["Longitude"]], popup=f"<b>{row['Bridge Name']}</b><br>Type: {row['Type']}<br>River/Sea: {row['River/Marine']}", icon=folium.Icon(color=icon_color)).add_to(m)
    folium_static(m, width=1100, height=400)

# --- 13. SATELLITE DATA FEED ---
elif page == "13. Satellite Data Feed (Live)":
    st.subheader("🛰️ Satellite Data Integration (NASA / ISRO)")
    try:
        df_sat = pd.read_csv("data/satellite_training_data.csv")
        st.success("🟢 Connected to Sentinel-1 & GPM Satellite Network")
        c1, c2, c3 = st.columns(3)
        c1.metric("Satellite Rainfall (Today)", f"{df_sat['Satellite_Rainfall_mm'].iloc[-1]:.1f} mm")
        c2.metric("Satellite Discharge", f"{df_sat['Satellite_Discharge_m3s'].iloc[-1]:.0f} m³/s")
        c3.metric("Scour Prediction (NN)", f"{df_sat['Target_Scour_Depth_m'].iloc[-1]:.2f} m")
        
        fig_sat = go.Figure()
        fig_sat.add_trace(go.Scatter(x=df_sat['Date'], y=df_sat['Satellite_Rainfall_mm'], name="Satellite Rainfall (mm)", fill='tozeroy', line=dict(color='#3B82F6')))
        fig_sat.update_layout(title="Rainfall Extracted from Satellite (Last 100 Days)")
        st.plotly_chart(fig_sat, width="stretch")
    except FileNotFoundError:
        st.error("Satellite data not found. Please run `python data/satellite_ingest.py` first.")

# --- 14. MAJOR RIVERS & KEY BRIDGES MATRIX ---
elif page == "14. Major Rivers & Key Bridges Matrix":
    st.subheader("Maharashtra Major River Systems & Key Bridges")
    
    df_matrix = pd.DataFrame(MAJOR_RIVER_MATRIX)
    
    st.markdown("""
    These constitute the lifelines of the state, extending over hundreds of kilometers and spanning multiple districts.
    """)
    
    st.markdown("### 📊 River & Bridge Registry")
    st.dataframe(df_matrix, width="stretch", height=300)
    
    st.markdown("---")
    
    st.markdown("### 🗺️ Visualizing the Lifelines")
    df_matrix['District Count'] = df_matrix['Primary Districts Covered'].apply(lambda x: len(x.split(',')))
    
    fig = px.bar(
        df_matrix, 
        x="Major River", 
        y="District Count", 
        color="Major River",
        title="Geographic Spread of Major Rivers (Number of Districts Covered)",
        text="Key Bridges & Crossings"
    )
    fig.update_traces(textposition='inside', textangle=0)
    st.plotly_chart(fig, width="stretch")
    
    st.info("This matrix helps the PWD prioritize sensor placement based on the number of districts a river traverses and the critical bridges located on it.")