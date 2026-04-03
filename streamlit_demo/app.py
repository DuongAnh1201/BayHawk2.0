"""
Wildfire Watch MVP — Streamlit Demo
Interactive demonstration of the BayHawk 2.0 AI-powered wildfire detection
and drone response system.
"""

import time
import json
import streamlit as st
import pandas as pd
import pydeck as pdk

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Wildfire Watch MVP",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Data ─────────────────────────────────────────────────────────────────────

CAMERAS = [
    {"id": "1", "name": "Sierra Peak North", "code": "cam-01", "lat": 34.32, "lon": -117.73},
    {"id": "2", "name": "Cajon Pass West",   "code": "cam-02", "lat": 34.31, "lon": -117.45},
    {"id": "3", "name": "Malibu Canyon",     "code": "cam-03", "lat": 34.05, "lon": -118.68},
    {"id": "4", "name": "Angeles Crest",     "code": "cam-04", "lat": 34.25, "lon": -118.15},
]

DRONE_STATIONS = [
    {"id": "ds-1", "name": "Cajon Ridge Hub",      "code": "DS-01", "lat": 34.315, "lon": -117.59, "drones": 4, "water": 12, "smoke": 8, "retardant": 0},
    {"id": "ds-2", "name": "Santa Monica Station", "code": "DS-02", "lat": 34.15,  "lon": -118.415, "drones": 3, "water": 10, "smoke": 6, "retardant": 4},
    {"id": "ds-3", "name": "San Gabriel Center",   "code": "DS-03", "lat": 34.23,  "lon": -118.00, "drones": 5, "water": 15, "smoke": 10, "retardant": 0},
]

SCENARIOS = {
    "all_clear": {
        "label": "🟢 All Clear",
        "criticality": "LOW",
        "score": 0.03,
        "camera_conf": 0.03,
        "thermal_conf": 0.02,
        "wind_speed": 4.2,
        "humidity": 62,
        "spread_risk": 0.146,
        "fusion_status": "DISMISSED",
        "fusion_score": 0.024,
        "scene": "Clear skies over mountainous terrain with healthy green vegetation. No visible smoke, haze, or thermal anomalies.",
        "observations": [
            "Vegetation appears healthy with normal color and moisture levels",
            "No visible smoke, haze, or particulate matter",
            "Wind conditions are calm with no dust or debris movement",
            "All nearby structures appear intact",
        ],
        "action_plan": ["Continue routine monitoring", "No action required"],
        "alert_msg": "ALL CLEAR — Routine scan complete. No fire activity detected.",
        "resources": [],
        "hotspots": [],
    },
    "smoke": {
        "label": "🟡 Simulate Smoke",
        "criticality": "MEDIUM",
        "score": 0.38,
        "camera_conf": 0.42,
        "thermal_conf": 0.18,
        "wind_speed": 8.3,
        "humidity": 35,
        "spread_risk": 0.41,
        "fusion_status": "DISMISSED",
        "fusion_score": 0.348,
        "scene": "Light haze visible on the eastern ridge, possibly smoke from a distant source or controlled burn.",
        "observations": [
            "Light haze or smoke visible along the eastern ridge line",
            "No active flames or glowing embers detected",
            "Satellite thermal scan shows no hotspot",
            "Wind carrying particulate from west at 8.3 m/s",
            "Humidity at 35% — moderate fire weather conditions",
        ],
        "action_plan": [
            "Increase camera monitoring frequency to 30-second intervals",
            "Dispatch ground scout to verify smoke source",
            "Alert nearest fire station for potential rapid deployment",
        ],
        "alert_msg": "SMOKE ADVISORY — Unconfirmed smoke detected. Ground verification in progress.",
        "resources": ["1× ground scout vehicle", "1× Type-3 engine on standby"],
        "hotspots": [],
    },
    "fire_high": {
        "label": "🟠 Simulate Fire (HIGH)",
        "criticality": "HIGH",
        "score": 0.82,
        "camera_conf": 0.87,
        "thermal_conf": 0.76,
        "wind_speed": 13.5,
        "humidity": 18,
        "spread_risk": 0.732,
        "fusion_status": "CONFIRMED",
        "fusion_score": 0.826,
        "scene": "Dense smoke column rising from a steep hillside with active flame front advancing northeast.",
        "observations": [
            "Active flame front moving northeast driven by Santa Ana winds",
            "Dense smoke obscuring visibility beyond 500 m",
            "Dry chaparral acting as primary fuel — high burn rate expected",
            "No visible fire breaks or natural barriers ahead",
            "Nearest structures approximately 1.2 km from perimeter",
        ],
        "action_plan": [
            "🛸 Deploy drone from DS-01 with Water Bomb",
            "Deploy two aerial tankers to northern flank",
            "Establish firebreak along Ridge Road",
            "Evacuate residents within 2 km radius",
            "Pre-position engine crews at Pinecrest subdivision",
        ],
        "alert_msg": "WILDFIRE ALERT — HIGH criticality fire detected. Strong winds driving rapid spread.",
        "resources": [
            "🛸 DS-01 drone — Water Bomb",
            "2× aerial tankers (CL-415)",
            "4× Type-1 engine crews",
            "1× bulldozer for firebreak",
        ],
        "hotspots": [{"lat": 34.32, "lon": -117.73, "frp": 76.0}],
    },
    "critical": {
        "label": "🔴 Critical Emergency",
        "criticality": "CRITICAL",
        "score": 0.96,
        "camera_conf": 0.97,
        "thermal_conf": 0.94,
        "wind_speed": 22.4,
        "humidity": 8,
        "spread_risk": 0.948,
        "fusion_status": "CONFIRMED",
        "fusion_score": 0.958,
        "scene": "Massive fire front spanning 2+ km with multiple spot fires. Extreme ember cast driven by 22 m/s Santa Ana winds. Structures directly threatened.",
        "observations": [
            "Multi-kilometer fire front with active crown fire behavior",
            "Extreme ember cast creating spot fires 500+ m ahead",
            "Three distinct thermal hotspots (142, 98, 67 MW)",
            "Santa Ana winds at 22.4 m/s with 8% humidity",
            "Residential structures within 400 m of leading edge",
            "Road access compromised on northern evacuation route",
        ],
        "action_plan": [
            "🛸 Deploy ALL drones from DS-01 & DS-03",
            "Issue IMMEDIATE mandatory evacuation within 5 km",
            "Deploy all available aerial assets",
            "Activate emergency operations center (EOC)",
            "Close Highway 138 and Route 18",
            "Request National Guard assistance",
        ],
        "alert_msg": "CRITICAL WILDFIRE EMERGENCY — Extreme fire behavior with imminent threat to life. MANDATORY EVACUATION.",
        "resources": [
            "🛸 ALL drones from DS-01 — Water & Smoke Bombs",
            "🛸 DS-03 drones — Water Bombs for eastern flank",
            "6× aerial tankers + 2× heavy helicopters",
            "12× Type-1 engine crews",
            "National Guard evacuation support",
        ],
        "hotspots": [
            {"lat": 34.32, "lon": -117.73, "frp": 142.0},
            {"lat": 34.33, "lon": -117.71, "frp": 98.0},
            {"lat": 34.31, "lon": -117.75, "frp": 67.0},
        ],
    },
}

DEESCALATION_PHASES = [
    {
        "phase": "Responding",
        "icon": "🚀",
        "description": "Drones deployed, ground crews en route",
        "criticality": "HIGH",
        "score": 0.68,
        "camera_conf": 0.72,
        "thermal_conf": 0.58,
        "fusion_score": 0.68,
        "scene": "Drone water bomb has impacted the primary hotspot. Steam plume visible. Ground crews establishing firebreak.",
        "hotspots": [{"lat": 34.32, "lon": -117.73, "frp": 52.0}],
    },
    {
        "phase": "Containment",
        "icon": "🔶",
        "description": "Fire perimeter established, active suppression",
        "criticality": "MEDIUM",
        "score": 0.45,
        "camera_conf": 0.45,
        "thermal_conf": 0.31,
        "fusion_score": 0.41,
        "scene": "Fire perimeter established. Firebreak holding on all flanks. FRP dropped 76%. Smoke turning white.",
        "hotspots": [{"lat": 34.32, "lon": -117.73, "frp": 18.0}],
    },
    {
        "phase": "Controlled",
        "icon": "🔵",
        "description": "Fire contained, mop-up operations underway",
        "criticality": "LOW",
        "score": 0.15,
        "camera_conf": 0.15,
        "thermal_conf": 0.08,
        "fusion_score": 0.12,
        "scene": "No active flames. Light residual smoke from cooling embers. Ground crews conducting mop-up.",
        "hotspots": [],
    },
    {
        "phase": "Extinguished",
        "icon": "✅",
        "description": "Fire fully extinguished, scene secured",
        "criticality": "LOW",
        "score": 0.02,
        "camera_conf": 0.02,
        "thermal_conf": 0.01,
        "fusion_score": 0.015,
        "scene": "Fire completely extinguished. Zero structures damaged, zero injuries. Successful drone-assisted response.",
        "hotspots": [],
    },
]

CRITICALITY_COLORS = {
    "LOW": "#10b981",
    "MEDIUM": "#f59e0b",
    "HIGH": "#f97316",
    "CRITICAL": "#ef4444",
}

# ── Theme ────────────────────────────────────────────────────────────────────

THEMES = {
    "Dark": {
        "bg": "#080808", "card": "#111111", "border": "#1e1e1e",
        "text": "#ffffff", "muted": "#6b7280", "brand": "#d97706",
    },
    "Light": {
        "bg": "#f5f5f5", "card": "#ffffff", "border": "#e5e7eb",
        "text": "#111827", "muted": "#6b7280", "brand": "#d97706",
    },
    "Verizon": {
        "bg": "#000000", "card": "#1c1c1c", "border": "#2e2e2e",
        "text": "#ffffff", "muted": "#6b7280", "brand": "#ee0000",
    },
}

# ── Session state init ───────────────────────────────────────────────────────

if "scenario" not in st.session_state:
    st.session_state.scenario = "all_clear"
if "camera" not in st.session_state:
    st.session_state.camera = "1"
if "theme" not in st.session_state:
    st.session_state.theme = "Dark"
if "deesc_phase" not in st.session_state:
    st.session_state.deesc_phase = -1
if "drone_dispatches" not in st.session_state:
    st.session_state.drone_dispatches = []

theme = THEMES[st.session_state.theme]

# ── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown(f"""
<style>
    .stApp {{
        background-color: {theme["bg"]};
    }}
    .block-container {{
        padding-top: 1rem;
    }}
    .metric-card {{
        background: {theme["card"]};
        border: 1px solid {theme["border"]};
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 8px;
    }}
    .metric-label {{
        color: {theme["muted"]};
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }}
    .metric-value {{
        color: {theme["text"]};
        font-size: 24px;
        font-weight: 700;
    }}
    .status-badge {{
        display: inline-block;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    .alert-banner {{
        background: linear-gradient(90deg, #ef4444, #dc2626);
        color: white;
        padding: 12px 20px;
        border-radius: 10px;
        font-weight: 600;
        font-size: 14px;
        text-align: center;
        margin-bottom: 16px;
        animation: pulse-banner 2s ease-in-out infinite;
    }}
    @keyframes pulse-banner {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.8; }}
    }}
    .observation-item {{
        color: {theme["text"]};
        padding: 6px 0;
        border-bottom: 1px solid {theme["border"]};
        font-size: 13px;
    }}
    .phase-item {{
        padding: 10px 14px;
        border-radius: 8px;
        margin-bottom: 6px;
        font-size: 13px;
    }}
    .phase-active {{
        background: {theme["brand"]}22;
        border: 1px solid {theme["brand"]}44;
    }}
    .phase-done {{
        background: #10b98122;
        border: 1px solid #10b98144;
    }}
    .phase-pending {{
        background: {theme["card"]};
        border: 1px solid {theme["border"]};
        opacity: 0.4;
    }}
    h1, h2, h3, h4, h5, h6, p, span, div, label {{
        color: {theme["text"]} !important;
    }}
    .stSelectbox label, .stRadio label {{
        color: {theme["muted"]} !important;
    }}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.image("logo.png", width=60)
    st.markdown(f"### Wildfire Watch <span style='color:{theme[\"brand\"]}'>MVP</span>", unsafe_allow_html=True)
    st.caption("🟢 System Operational")

    st.divider()

    st.session_state.theme = st.selectbox(
        "Theme", list(THEMES.keys()),
        index=list(THEMES.keys()).index(st.session_state.theme),
    )

    st.divider()

    st.markdown("**Camera Nodes**")
    cam_names = [f"{c['name']} ({c['code']})" for c in CAMERAS]
    cam_idx = next(i for i, c in enumerate(CAMERAS) if c["id"] == st.session_state.camera)
    selected = st.radio("Select camera", cam_names, index=cam_idx, label_visibility="collapsed")
    st.session_state.camera = CAMERAS[cam_names.index(selected)]["id"]

    st.divider()

    st.markdown("**Demo Scenarios**")
    for key, val in SCENARIOS.items():
        if st.button(val["label"], key=f"btn_{key}", use_container_width=True):
            st.session_state.scenario = key
            st.session_state.deesc_phase = -1
            st.session_state.drone_dispatches = []

    st.divider()

    st.markdown("**Drone Stations**")
    for ds in DRONE_STATIONS:
        st.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-label'>{ds['code']}</div>"
            f"<div style='color:{theme[\"text\"]};font-weight:600;font-size:14px'>{ds['name']}</div>"
            f"<div style='color:{theme[\"muted\"]};font-size:12px'>"
            f"{ds['drones']} drones · W:{ds['water']} S:{ds['smoke']}"
            f"{'  R:' + str(ds['retardant']) if ds['retardant'] > 0 else ''}"
            f"</div></div>",
            unsafe_allow_html=True,
        )

    st.divider()
    st.caption("Battalion Chief: Khoi Duong")

# ── Main content ─────────────────────────────────────────────────────────────

scenario = SCENARIOS[st.session_state.scenario]
cam = next(c for c in CAMERAS if c["id"] == st.session_state.camera)
crit_color = CRITICALITY_COLORS.get(scenario["criticality"], "#6b7280")

# Alert banner for HIGH / CRITICAL
if scenario["criticality"] in ("HIGH", "CRITICAL"):
    st.markdown(
        f"<div class='alert-banner'>⚠️ {scenario['alert_msg']}</div>",
        unsafe_allow_html=True,
    )

# ── Tab navigation ───────────────────────────────────────────────────────────

tab_main, tab_drone, tab_report, tab_deesc = st.tabs([
    "📡 Main Event Camera",
    "🛸 Drone Command System",
    "📋 Incident Report",
    "🔽 De-escalation Simulation",
])

# ── TAB: Main Event ─────────────────────────────────────────────────────────

with tab_main:
    col_feed, col_map = st.columns([3, 2])

    with col_feed:
        st.markdown(f"#### Live Ingestion Engine — {cam['name']}")

        if st.session_state.scenario in ("fire_high", "critical") and st.session_state.deesc_phase < 2:
            video_url = (
                "https://assets.mixkit.co/videos/5280/5280-720.mp4"
                if st.session_state.scenario == "critical"
                else "https://assets.mixkit.co/videos/11028/11028-720.mp4"
            )
            st.video(video_url)
        else:
            alertca_url = f"https://cameras.alertcalifornia.org/?pos={cam['lat']:.4f}_{cam['lon']:.4f}_12"
            st.markdown(
                f'<iframe src="{alertca_url}" width="100%" height="400" '
                f'style="border:none;border-radius:10px"></iframe>',
                unsafe_allow_html=True,
            )

        # HUD metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("YOLO Confidence", f"{scenario['camera_conf'] * 100:.0f}%")
        m2.metric("Thermal Confidence", f"{scenario['thermal_conf'] * 100:.0f}%")
        m3.metric("Fusion", scenario["fusion_status"], delta=f"{scenario['fusion_score']:.2f}")
        m4.metric("Criticality", scenario["criticality"])

    with col_map:
        st.markdown("#### Spatial Monitoring")

        map_data = []
        for c in CAMERAS:
            map_data.append({
                "lat": c["lat"], "lon": c["lon"], "name": c["name"],
                "type": "camera",
                "color": [37, 99, 235, 180] if c["id"] != st.session_state.camera else [217, 119, 6, 220],
                "radius": 600 if c["id"] != st.session_state.camera else 900,
            })
        for ds in DRONE_STATIONS:
            map_data.append({
                "lat": ds["lat"], "lon": ds["lon"], "name": ds["name"],
                "type": "drone_station",
                "color": [5, 150, 105, 200],
                "radius": 700,
            })
        for h in scenario["hotspots"]:
            map_data.append({
                "lat": h["lat"], "lon": h["lon"], "name": f"Hotspot FRP:{h['frp']}MW",
                "type": "hotspot",
                "color": [239, 68, 68, 180],
                "radius": 1200,
            })

        df_map = pd.DataFrame(map_data)

        st.pydeck_chart(pdk.Deck(
            initial_view_state=pdk.ViewState(
                latitude=34.22, longitude=-118.0, zoom=8.5, pitch=30,
            ),
            layers=[
                pdk.Layer(
                    "ScatterplotLayer",
                    data=df_map,
                    get_position=["lon", "lat"],
                    get_color="color",
                    get_radius="radius",
                    pickable=True,
                ),
            ],
            tooltip={"text": "{name} ({type})"},
            map_style="mapbox://styles/mapbox/dark-v11",
        ), height=450)

    # Visual Reasoning
    st.markdown("---")
    st.markdown("#### Visual Reasoning (AI Analysis)")

    col_scene, col_obs = st.columns([3, 2])
    with col_scene:
        st.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-label'>Scene Description</div>"
            f"<p style='font-size:14px;line-height:1.6;margin-top:8px'>{scenario['scene']}</p>"
            f"</div>",
            unsafe_allow_html=True,
        )

        st.markdown(f"<div class='metric-card'><div class='metric-label'>Classification</div>"
                     f"<div style='margin-top:8px'>"
                     f"<span class='status-badge' style='background:{crit_color}22;color:{crit_color}'>{scenario['criticality']}</span>"
                     f"<span style='margin-left:12px;font-size:20px;font-weight:700;color:{theme[\"text\"]}'>{scenario['score'] * 100:.0f}%</span>"
                     f"</div></div>", unsafe_allow_html=True)

    with col_obs:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Key Observations</div>", unsafe_allow_html=True)
        for obs in scenario["observations"]:
            st.markdown(f"<div class='observation-item'>• {obs}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Action plan & Weather
    col_action, col_weather = st.columns([3, 2])
    with col_action:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Suggested Action Plan</div>", unsafe_allow_html=True)
        for i, step in enumerate(scenario["action_plan"], 1):
            st.markdown(f"<div class='observation-item'>{i}. {step}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col_weather:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Weather Intelligence</div>", unsafe_allow_html=True)
        w1, w2 = st.columns(2)
        w1.metric("Wind Speed", f"{scenario['wind_speed']} m/s")
        w2.metric("Humidity", f"{scenario['humidity']}%")
        w3, w4 = st.columns(2)
        w3.metric("Spread Risk", f"{scenario['spread_risk'] * 100:.0f}%")
        w4.metric("Fire Weather", "YES" if scenario["humidity"] < 25 else "NO")
        st.markdown("</div>", unsafe_allow_html=True)

# ── TAB: Drone Command System ───────────────────────────────────────────────

with tab_drone:
    st.markdown("#### 🛸 Drone Command System")

    # Fleet summary
    total_drones = sum(ds["drones"] for ds in DRONE_STATIONS)
    total_water = sum(ds["water"] for ds in DRONE_STATIONS)
    total_smoke = sum(ds["smoke"] for ds in DRONE_STATIONS)
    total_retardant = sum(ds["retardant"] for ds in DRONE_STATIONS)

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Stations", len(DRONE_STATIONS))
    k2.metric("Total Drones", total_drones)
    k3.metric("Water Bombs", total_water)
    k4.metric("Smoke Bombs", total_smoke)
    k5.metric("Retardant", total_retardant)

    st.markdown("---")

    # Station detail cards
    col_stations, col_map_drone = st.columns([3, 2])

    with col_stations:
        st.markdown("##### Station Inventory")
        for ds in DRONE_STATIONS:
            drone_pct = 100
            with st.container():
                st.markdown(
                    f"<div class='metric-card'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:center'>"
                    f"<div>"
                    f"<div style='font-weight:700;font-size:15px;color:{theme[\"text\"]}'>{ds['name']}</div>"
                    f"<div style='color:{theme[\"muted\"]};font-size:12px'>{ds['code']} · {ds['lat']:.3f}°N, {abs(ds['lon']):.3f}°W</div>"
                    f"</div>"
                    f"<span class='status-badge' style='background:#10b98122;color:#10b981'>OPERATIONAL</span>"
                    f"</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Drones", f"{ds['drones']}/{ds['drones']}")
                c2.metric("Water Bomb", ds["water"])
                c3.metric("Smoke Bomb", ds["smoke"])
                c4.metric("Retardant", ds["retardant"])
                st.progress(drone_pct / 100, text=f"Fleet: {drone_pct}% ready")

    with col_map_drone:
        st.markdown("##### Station Map")
        drone_map = []
        for ds in DRONE_STATIONS:
            drone_map.append({
                "lat": ds["lat"], "lon": ds["lon"], "name": ds["name"],
                "type": "Drone Station",
                "color": [5, 150, 105, 220],
                "radius": 1000,
            })
        for c in CAMERAS:
            drone_map.append({
                "lat": c["lat"], "lon": c["lon"], "name": c["name"],
                "type": "Camera",
                "color": [37, 99, 235, 120],
                "radius": 500,
            })

        st.pydeck_chart(pdk.Deck(
            initial_view_state=pdk.ViewState(
                latitude=34.22, longitude=-118.0, zoom=8.5, pitch=20,
            ),
            layers=[
                pdk.Layer(
                    "ScatterplotLayer",
                    data=pd.DataFrame(drone_map),
                    get_position=["lon", "lat"],
                    get_color="color",
                    get_radius="radius",
                    pickable=True,
                ),
            ],
            tooltip={"text": "{name}\n{type}"},
            map_style="mapbox://styles/mapbox/dark-v11",
        ), height=450)

    # Deploy section
    st.markdown("---")
    st.markdown("##### Deploy Drone")

    d1, d2, d3 = st.columns(3)
    with d1:
        deploy_station = st.selectbox("Station", [ds["name"] for ds in DRONE_STATIONS])
    with d2:
        deploy_payload = st.selectbox("Payload", ["Water Bomb", "Smoke Bomb", "Retardant"])
    with d3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Deploy Drone", use_container_width=True, type="primary"):
            st.session_state.drone_dispatches.append({
                "station": deploy_station,
                "payload": deploy_payload,
                "time": time.strftime("%H:%M:%S"),
            })
            st.success(f"Drone deployed from {deploy_station} with {deploy_payload}!")

    if st.session_state.drone_dispatches:
        st.markdown("##### Mission Log")
        df_dispatches = pd.DataFrame(st.session_state.drone_dispatches)
        st.dataframe(df_dispatches, use_container_width=True, hide_index=True)

# ── TAB: Incident Report ────────────────────────────────────────────────────

with tab_report:
    st.markdown("#### 📋 Incident Report")

    col_r1, col_r2 = st.columns([3, 2])

    with col_r1:
        st.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-label'>Incident Summary</div>"
            f"<p style='margin-top:8px'>"
            f"<strong>Event ID:</strong> demo-{st.session_state.scenario}<br>"
            f"<strong>Camera:</strong> {cam['name']} ({cam['code']})<br>"
            f"<strong>Location:</strong> {cam['lat']:.4f}°N, {abs(cam['lon']):.4f}°W<br>"
            f"<strong>Criticality:</strong> <span style='color:{crit_color};font-weight:700'>{scenario['criticality']}</span> ({scenario['score'] * 100:.0f}%)<br>"
            f"<strong>Fusion:</strong> {scenario['fusion_status']} (Score: {scenario['fusion_score']:.3f})<br>"
            f"<strong>Wind:</strong> {scenario['wind_speed']} m/s · <strong>Humidity:</strong> {scenario['humidity']}% · <strong>Spread Risk:</strong> {scenario['spread_risk'] * 100:.0f}%"
            f"</p></div>",
            unsafe_allow_html=True,
        )

        st.markdown(f"<div class='metric-card'><div class='metric-label'>Scene Description</div>"
                     f"<p style='margin-top:8px'>{scenario['scene']}</p></div>", unsafe_allow_html=True)

        if scenario["resources"]:
            st.markdown(f"<div class='metric-card'><div class='metric-label'>Recommended Resources</div>", unsafe_allow_html=True)
            for r in scenario["resources"]:
                st.markdown(f"<div class='observation-item'>{r}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with col_r2:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Analyst Verdict</div>", unsafe_allow_html=True)
        verdict = st.radio(
            "Verdict",
            ["True Positive", "False Positive", "True Negative", "False Negative"],
            label_visibility="collapsed",
        )
        analyst = st.text_input("Analyst Name", value="Khoi Duong")
        notes = st.text_area("Notes", placeholder="Add analyst notes here...")
        st.markdown("</div>", unsafe_allow_html=True)

        col_a1, col_a2 = st.columns(2)
        with col_a1:
            if st.button("📋 Copy Report", use_container_width=True):
                report_text = json.dumps({
                    "event_id": f"demo-{st.session_state.scenario}",
                    "camera": cam["name"],
                    "criticality": scenario["criticality"],
                    "score": scenario["score"],
                    "verdict": verdict,
                    "analyst": analyst,
                    "notes": notes,
                }, indent=2)
                st.code(report_text, language="json")
        with col_a2:
            if st.button("📤 Export JSON", use_container_width=True):
                report = {
                    "event_id": f"demo-{st.session_state.scenario}",
                    "camera": cam["name"],
                    "criticality": scenario["criticality"],
                    "score": scenario["score"],
                    "fusion": scenario["fusion_status"],
                    "weather": {"wind": scenario["wind_speed"], "humidity": scenario["humidity"]},
                    "verdict": verdict,
                    "analyst": analyst,
                    "notes": notes,
                    "scene": scenario["scene"],
                    "observations": scenario["observations"],
                }
                st.download_button(
                    "⬇️ Download JSON",
                    json.dumps(report, indent=2),
                    file_name=f"incident_{st.session_state.scenario}.json",
                    mime="application/json",
                    use_container_width=True,
                )

# ── TAB: De-escalation ──────────────────────────────────────────────────────

with tab_deesc:
    st.markdown("#### 🔽 De-escalation Simulation")

    if st.session_state.scenario not in ("fire_high", "critical"):
        st.info("Load a **Simulate Fire** or **Critical Emergency** scenario first to run de-escalation.")
    else:
        st.markdown(f"Active scenario: **{scenario['label']}**")

        if st.button("▶ Start De-escalation Simulation", type="primary", use_container_width=True):
            st.session_state.deesc_phase = 0

        if st.session_state.deesc_phase >= 0:
            col_timeline, col_live = st.columns([2, 3])

            with col_timeline:
                st.markdown("##### Phase Timeline")
                for i, phase in enumerate(DEESCALATION_PHASES):
                    if i < st.session_state.deesc_phase:
                        css_class = "phase-done"
                        status_icon = "✅"
                    elif i == st.session_state.deesc_phase:
                        css_class = "phase-active"
                        status_icon = "🔄"
                    else:
                        css_class = "phase-pending"
                        status_icon = "⏳"

                    st.markdown(
                        f"<div class='phase-item {css_class}'>"
                        f"{status_icon} <strong>{phase['phase']}</strong><br>"
                        f"<span style='font-size:12px;color:{theme[\"muted\"]}'>{phase['description']}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                if st.session_state.deesc_phase < len(DEESCALATION_PHASES) - 1:
                    if st.button("⏭ Advance to Next Phase", use_container_width=True):
                        st.session_state.deesc_phase += 1
                        st.rerun()
                else:
                    st.success("🎉 Fire successfully extinguished! Mission accomplished.")

            with col_live:
                current_phase = DEESCALATION_PHASES[st.session_state.deesc_phase]
                phase_color = CRITICALITY_COLORS.get(current_phase["criticality"], "#6b7280")

                st.markdown(f"##### Current Phase: {current_phase['icon']} {current_phase['phase']}")

                pm1, pm2, pm3, pm4 = st.columns(4)
                pm1.metric("Criticality", current_phase["criticality"])
                pm2.metric("Score", f"{current_phase['score'] * 100:.0f}%")
                pm3.metric("Camera", f"{current_phase['camera_conf'] * 100:.0f}%")
                pm4.metric("Thermal", f"{current_phase['thermal_conf'] * 100:.0f}%")

                st.markdown(
                    f"<div class='metric-card'>"
                    f"<div class='metric-label'>Scene Update</div>"
                    f"<p style='margin-top:8px'>{current_phase['scene']}</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

                # De-escalation map
                deesc_map_data = []
                for c in CAMERAS:
                    deesc_map_data.append({
                        "lat": c["lat"], "lon": c["lon"], "name": c["name"],
                        "color": [37, 99, 235, 120], "radius": 500,
                    })
                for ds in DRONE_STATIONS:
                    deesc_map_data.append({
                        "lat": ds["lat"], "lon": ds["lon"], "name": ds["name"],
                        "color": [5, 150, 105, 200], "radius": 700,
                    })
                for h in current_phase["hotspots"]:
                    deesc_map_data.append({
                        "lat": h["lat"], "lon": h["lon"],
                        "name": f"Hotspot FRP:{h['frp']}MW",
                        "color": [239, 68, 68, 180], "radius": h["frp"] * 10,
                    })

                st.pydeck_chart(pdk.Deck(
                    initial_view_state=pdk.ViewState(
                        latitude=34.22, longitude=-118.0, zoom=8.5,
                    ),
                    layers=[
                        pdk.Layer(
                            "ScatterplotLayer",
                            data=pd.DataFrame(deesc_map_data),
                            get_position=["lon", "lat"],
                            get_color="color",
                            get_radius="radius",
                            pickable=True,
                        ),
                    ],
                    tooltip={"text": "{name}"},
                    map_style="mapbox://styles/mapbox/dark-v11",
                ), height=350)

# ── Footer ───────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown(
    f"<div style='text-align:center;color:{theme[\"muted\"]};font-size:12px;padding:8px'>"
    f"Wildfire Watch MVP — BayHawk 2.0 · AI-Powered Wildfire Detection & Drone Response"
    f"</div>",
    unsafe_allow_html=True,
)
