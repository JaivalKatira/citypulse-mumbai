import os
import sqlite3
from datetime import datetime
from urllib.parse import quote

import folium
import pandas as pd
import streamlit as st
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation

from osm_utils import (MUMBAI_CENTER, find_police_stations, geocode_locality,
                       haversine_km, search_place)

# ─────────────────────────────────────────────
# PATHS (relative to this file so it works on Streamlit Cloud)
# ─────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE, "mumbai_women_safety.csv")
COORDS_PATH = os.path.join(BASE, "locality_coords.csv")   # pre-computed OSM lookups (optional)
DB_PATH = os.path.join(BASE, "safety_data.db")
GEOCODE_CHUNK = 30   # localities looked up per run when coords file is missing

st.set_page_config(
    page_title="Mumbai Women Safety Risk Map",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
defaults = {
    "dark_mode": True,
    "user_lat": None,
    "user_lon": None,
    "user_label": "",
    "emergency_active": False,
    "last_geo": None,
    "place_results": [],
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

DARK = st.session_state.dark_mode
if DARK:
    BG, SIDEBAR, SIDE_BRD, SIDE_CLR = "#0e1117", "linear-gradient(180deg, #141a24 0%, #1a2232 100%)", "#2a3550", "#c9d1e0"
    CARD_BG, CARD_BRD, TXT, SUBTXT, HDRTXT = "linear-gradient(135deg, #1a2232 0%, #1e293b 100%)", "#2a3550", "#e0e0e0", "#7a8899", "#4fc3f7"
    MAP_TILE, TOGGLE_LABEL = "dark", "☀️ Light Mode"
else:
    BG, SIDEBAR, SIDE_BRD, SIDE_CLR = "#f0f2f6", "linear-gradient(180deg, #ffffff 0%, #e8edf5 100%)", "#c8d0e0", "#1a2232"
    CARD_BG, CARD_BRD, TXT, SUBTXT, HDRTXT = "linear-gradient(135deg, #ffffff 0%, #f0f4fa 100%)", "#c8d0e0", "#1a2232", "#5a6880", "#1565c0"
    MAP_TILE, TOGGLE_LABEL = "light", "🌙 Dark Mode"

st.markdown(f"""
<style>
html, body, [data-testid="stAppViewContainer"] {{ background-color: {BG} !important; color: {TXT} !important; }}
[data-testid="stSidebar"] {{ background: {SIDEBAR} !important; border-right: 1px solid {SIDE_BRD} !important; }}
[data-testid="stSidebar"] * {{ color: {SIDE_CLR} !important; }}
.main-title {{ text-align:center; font-size:2.1rem; font-weight:800;
  background: linear-gradient(90deg,#ff4d4d 0%,#ff9900 40%,#00e676 100%);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:.2rem; letter-spacing:-.5px; }}
.sub-title {{ text-align:center; color:{SUBTXT}; font-size:.9rem; margin-bottom:1.5rem; }}
.metric-row {{ display:flex; gap:12px; margin-bottom:16px; flex-wrap:wrap; }}
.metric-card {{ flex:1; min-width:120px; background:{CARD_BG}; border:1px solid {CARD_BRD}; border-radius:12px; padding:16px 20px; text-align:center; }}
.metric-card .val {{ font-size:1.9rem; font-weight:800; }}
.metric-card .lbl {{ font-size:.75rem; color:{SUBTXT}; margin-top:4px; }}
.red {{ color:#ff4d4d; }} .amber {{ color:#ff9900; }} .green {{ color:#00e676; }} .blue {{ color:#4fc3f7; }}
.section-hdr {{ font-size:.78rem; text-transform:uppercase; letter-spacing:1.5px; color:{HDRTXT}; margin:18px 0 8px 0; font-weight:700; }}
.emergency-panel {{ background:linear-gradient(135deg,#3d0000 0%,#660000 100%); border:2px solid #ff4444; border-radius:14px; padding:18px 22px; margin:12px 0; animation:pulse-border 1.5s infinite; }}
@keyframes pulse-border {{
  0% {{ border-color:#ff4444; box-shadow:0 0 0 0 rgba(255,68,68,.5); }}
  50% {{ border-color:#ff9999; box-shadow:0 0 0 8px rgba(255,68,68,0); }}
  100% {{ border-color:#ff4444; box-shadow:0 0 0 0 rgba(255,68,68,0); }} }}
.emergency-title {{ color:#ff4444; font-size:1.1rem; font-weight:800; margin-bottom:10px; }}
.station-card {{ background:rgba(255,255,255,.07); border:1px solid rgba(255,255,255,.15); border-radius:10px; padding:12px 16px; margin:8px 0; }}
.station-name {{ font-weight:700; color:#fff; font-size:.95rem; }}
.station-dist {{ color:#ffaa00; font-size:.82rem; margin:2px 0; }}
.nav-link {{ display:inline-block; background:#1a73e8; color:#fff !important; padding:5px 14px; border-radius:20px; font-size:.78rem; text-decoration:none; margin:6px 6px 0 0; }}
.nav-link:hover {{ background:#1558b0; }}
.loc-badge {{ display:inline-block; padding:4px 12px; border-radius:20px; font-size:.78rem; font-weight:600; margin-bottom:8px; }}
.loc-active {{ background:rgba(0,230,118,.15); color:#00e676 !important; border:1px solid #00e676; }}
.loc-inactive {{ background:rgba(122,136,153,.15); border:1px solid {SUBTXT}; }}
#MainMenu, footer {{ visibility:hidden; }}
.block-container {{ padding-top:1.5rem !important; }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SQLITE BACKEND
# (note: on Streamlit Cloud the DB file is shared by all visitors and is
#  recreated from the CSV whenever the app restarts)
# ─────────────────────────────────────────────
INSERT_SQL = """
    INSERT INTO localities
    (locality, city, population, area_sq_km, population_density, uhi_index,
     police_chowkis, internet_pct, total_crimes, crimes_women, police_density,
     safety_index, risk_index, lat, lon, geo_status, updated_at)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
"""


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS localities (
                id INTEGER PRIMARY KEY,
                locality TEXT, city TEXT, population INTEGER, area_sq_km REAL,
                population_density REAL, uhi_index REAL, police_chowkis INTEGER,
                internet_pct REAL, total_crimes INTEGER, crimes_women INTEGER,
                police_density REAL, safety_index REAL, risk_index REAL,
                lat REAL, lon REAL, geo_status TEXT, updated_at TEXT
            )""")


def _row_tuple(row, lat, lon, status, now):
    return (
        str(row["locality"]), str(row.get("city", "Mumbai")), int(row["population"]),
        float(row["area sq km"]), float(row["populationdensity"]),
        float(row["urban heat island index"]), int(row["police chowkis"]),
        float(row["internet penetration percent"]), int(row["total crimes"]),
        int(row["crimes against women"]), float(row["police_density"]),
        float(row["women safety index"]), float(row["risk index"]),
        lat, lon, status, now,
    )


def load_csv_to_db(csv_path=CSV_PATH):
    df = pd.read_csv(csv_path)
    coords = pd.read_csv(COORDS_PATH) if os.path.exists(COORDS_PATH) else pd.DataFrame()
    lookup = {}
    if not coords.empty:
        for r in coords.itertuples():
            lookup[int(r.row_id)] = (str(r.locality), r.lat, r.lon, r.status)
    now = datetime.now().isoformat()
    rows = []
    for i, (_, row) in enumerate(df.iterrows(), start=1):
        hit = lookup.get(i)
        if hit and hit[0] == str(row["locality"]) and hit[3] in ("ok", "notfound"):
            lat = float(hit[1]) if hit[3] == "ok" else None
            lon = float(hit[2]) if hit[3] == "ok" else None
            rows.append(_row_tuple(row, lat, lon, hit[3], now))
        else:
            rows.append(_row_tuple(row, None, None, None, now))   # None = still to geocode
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM localities")
        conn.executemany(INSERT_SQL, rows)


def insert_from_df(df_new):
    now = datetime.now().isoformat()
    rows = [_row_tuple(r, None, None, None, now) for _, r in df_new.iterrows()]
    with sqlite3.connect(DB_PATH) as conn:
        conn.executemany(INSERT_SQL, rows)


def fetch_all():
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql("SELECT * FROM localities ORDER BY risk_index DESC", conn)


def report_incident(locality, severity="general"):
    bump = 2.0 if severity == "severe" else 1.0
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""UPDATE localities SET risk_index = risk_index + ?,
                        crimes_women = crimes_women + 1, total_crimes = total_crimes + 1,
                        updated_at = ? WHERE locality = ?""",
                     (bump, datetime.now().isoformat(), locality))
        return pd.read_sql("SELECT * FROM localities WHERE locality = ?", conn, params=(locality,))


def geocode_pending_chunk(n=GEOCODE_CHUNK):
    """Look up the next `n` un-located rows on OpenStreetMap. Returns (looked_up, errors)."""
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT id, locality, lat, lon, geo_status FROM localities ORDER BY id").fetchall()
        anchor, done, errors = None, 0, 0
        for rid, name, lat, lon, status in rows:
            if status == "ok":
                anchor = (lat, lon)
                continue
            if status is not None or done >= n:
                continue
            st_, la, lo = geocode_locality(name, anchor)
            done += 1
            if st_ == "error":
                errors += 1
                continue
            conn.execute("UPDATE localities SET lat=?, lon=?, geo_status=? WHERE id=?",
                         (la, lo, st_, rid))
            if st_ == "ok":
                anchor = (la, lo)
        conn.commit()
    return done, errors


# ─────────────────────────────────────────────
# POLICE STATIONS (OpenStreetMap / Overpass)
# ─────────────────────────────────────────────
FALLBACK_STATIONS = pd.DataFrame({
    "name": ["Cuffe Parade Police Station", "Yellow Gate Police Station", "Nirmal Nagar Police Station",
             "Santacruz Police Station", "Malvani Police Station", "Andheri Police Station",
             "Bandra Police Station", "Borivali Police Station", "Kurla Police Station",
             "Chembur Police Station"],
    "lat": [18.9155, 18.9475, 19.0596, 19.0786, 19.1915, 19.1136, 19.0544, 19.2290, 19.0728, 19.0622],
    "lon": [72.8213, 72.8400, 72.8519, 72.8394, 72.8202, 72.8697, 72.8402, 72.8567, 72.8826, 72.9005],
    "phone": [""] * 10,
})


@st.cache_data(ttl=600, show_spinner=False)
def _osm_police(lat_r: float, lon_r: float):
    df = find_police_stations(lat_r, lon_r, 5000)
    if df is None or len(df) < 3:
        wider = find_police_stations(lat_r, lon_r, 12000)
        df = wider if wider is not None else df
    return df


def nearest_stations(user_lat, user_lon, n=3):
    """Returns (DataFrame of n nearest stations, source label)."""
    df = _osm_police(round(user_lat, 3), round(user_lon, 3))
    source = "OpenStreetMap"
    if df is None or df.empty:
        df, source = FALLBACK_STATIONS.copy(), "built-in list (OSM unreachable)"
    df = df.copy()
    df["distance_km"] = [haversine_km(user_lat, user_lon, a, b) for a, b in zip(df["lat"], df["lon"])]
    df["gmaps_link"] = [f"https://www.google.com/maps/dir/?api=1&origin={user_lat},{user_lon}"
                        f"&destination={a},{b}&travelmode=driving" for a, b in zip(df["lat"], df["lon"])]
    df["osm_link"] = [f"https://www.openstreetmap.org/directions?engine=fossgis_osrm_car"
                      f"&route={user_lat}%2C{user_lon}%3B{a}%2C{b}" for a, b in zip(df["lat"], df["lon"])]
    return df.nsmallest(n, "distance_km").reset_index(drop=True), source


# ─────────────────────────────────────────────
# RISK + MAP
# ─────────────────────────────────────────────
def classify(risk):
    return "high" if risk >= 15 else "medium" if risk >= 7 else "low"


def build_map(df, show_high, show_med, show_low, selected_locality=None,
              user_lat=None, user_lon=None, emergency_stations=None):
    lat0, lon0, zoom = MUMBAI_CENTER[0], MUMBAI_CENTER[1], 11
    if emergency_stations is not None and user_lat:
        lat0, lon0, zoom = user_lat, user_lon, 14
    elif selected_locality and selected_locality != "— All —":
        row = df[df["locality"] == selected_locality]
        if not row.empty:
            lat0, lon0, zoom = float(row.iloc[0]["lat"]), float(row.iloc[0]["lon"]), 15
    elif user_lat:
        lat0, lon0, zoom = user_lat, user_lon, 13

    m = folium.Map(location=[lat0, lon0], zoom_start=zoom, tiles=None, prefer_canvas=True)

    # Store your CARTO key in Streamlit Cloud → App settings → Secrets:
    # CARTO_API_KEY = "your_key_here"
    # Local development: use .streamlit/secrets.toml or CARTO_API_KEY env var.
    try:
        carto_api_key = st.secrets.get("CARTO_API_KEY", "")
    except (FileNotFoundError, KeyError):
        carto_api_key = ""
    carto_api_key = str(carto_api_key or os.getenv("CARTO_API_KEY", "")).strip()

    if carto_api_key:
        # CARTO requires ?key= on each raster tile URL (dark and light).
        style = "dark_all" if MAP_TILE == "dark" else "light_all"
        tile_url = (
            f"https://basemaps.cartocdn.com/rastertiles/{style}/"
            "{z}/{x}/{y}.png?key=" + quote(carto_api_key, safe="")
        )
        folium.TileLayer(
            tiles=tile_url,
            attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="https://carto.com/attribution/">CARTO</a>',
            name="CARTO Dark" if MAP_TILE == "dark" else "CARTO Light",
            max_zoom=19,
            control=False,
        ).add_to(m)
    else:
        # Without a key, avoid CARTO's "API KEY REQUIRED" watermark.
        folium.TileLayer("OpenStreetMap", name="OpenStreetMap", control=False).add_to(m)

    mapped = df.dropna(subset=["lat", "lon"])
    if not mapped.empty:
        r_min, r_max = mapped["risk_index"].min(), mapped["risk_index"].max()
        norm = lambda v: float((v - r_min) / (r_max - r_min + 1e-9))
        pts = {"high": [], "medium": [], "low": []}
        for _, r in mapped.iterrows():
            pts[classify(r["risk_index"])].append([r["lat"], r["lon"], norm(r["risk_index"])])
        cfg = dict(min_opacity=0.35, max_zoom=16, radius=28, blur=22)
        if show_high and pts["high"]:
            HeatMap(pts["high"], gradient={0.0: "#3d0000", 0.4: "#cc0000", 0.7: "#ff4444", 1.0: "#ff0000"},
                    name="🔴 High Risk", **cfg).add_to(m)
        if show_med and pts["medium"]:
            HeatMap(pts["medium"], gradient={0.0: "#2a1a00", 0.4: "#cc7700", 0.7: "#ffaa00", 1.0: "#ffcc00"},
                    name="🟡 Medium Risk", **cfg).add_to(m)
        if show_low and pts["low"]:
            HeatMap(pts["low"], gradient={0.0: "#001a00", 0.4: "#006600", 0.7: "#00cc44", 1.0: "#00ff66"},
                    name="🟢 Safe Zones", **cfg).add_to(m)

    if user_lat:
        folium.CircleMarker([user_lat, user_lon], radius=10, color="#00bfff", fill=True,
                            fill_color="#00bfff", fill_opacity=0.9,
                            popup="📍 Your Location", tooltip="You are here").add_to(m)
        folium.CircleMarker([user_lat, user_lon], radius=22, color="#00bfff", fill=False,
                            weight=2, opacity=0.5).add_to(m)

    if emergency_stations is not None:
        line_cols = ["#ff4444", "#ff8800", "#ffcc00"]
        for idx, s in emergency_stations.iterrows():
            folium.Marker(
                [s["lat"], s["lon"]],
                icon=folium.Icon(color=["red", "orange", "beige"][idx % 3], icon="shield", prefix="fa"),
                popup=folium.Popup(f"<b>🚔 {s['name']}</b><br>Distance: {s['distance_km']:.2f} km<br>"
                                   f"<a href='{s['gmaps_link']}' target='_blank'>Navigate →</a>", max_width=250),
                tooltip=f"#{idx+1} {s['name']} ({s['distance_km']:.2f} km)",
            ).add_to(m)
            if user_lat:
                folium.PolyLine([[user_lat, user_lon], [s["lat"], s["lon"]]],
                                color=line_cols[idx % 3], weight=2, dash_array="6 4", opacity=.8).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m


# ─────────────────────────────────────────────
# INIT DATA
# ─────────────────────────────────────────────
init_db()
with sqlite3.connect(DB_PATH) as _c:
    _count = _c.execute("SELECT COUNT(*) FROM localities").fetchone()[0]
if _count == 0:
    load_csv_to_db()

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
t_col, b_col = st.columns([5, 1])
with t_col:
    st.markdown('<div class="main-title">🛡️ Mumbai Women Safety Risk Map</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Locality-wise safety risk · Places & police stations from OpenStreetMap</div>',
                unsafe_allow_html=True)
with b_col:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button(TOGGLE_LABEL, width="stretch"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Controls")
    st.markdown('<div class="section-hdr">📍 My Location</div>', unsafe_allow_html=True)

    if st.session_state.user_lat is not None:
        lbl = st.session_state.user_label or f"{st.session_state.user_lat:.4f}, {st.session_state.user_lon:.4f}"
        st.markdown(f'<span class="loc-badge loc-active">✅ {lbl[:60]}</span>', unsafe_allow_html=True)
        if st.button("🗑️ Clear Location", width="stretch"):
            st.session_state.user_lat = st.session_state.user_lon = None
            st.session_state.user_label = ""
            st.session_state.emergency_active = False
            st.rerun()
    else:
        st.markdown('<span class="loc-badge loc-inactive">⚫ No location set</span>', unsafe_allow_html=True)

    # 1) Browser GPS
    st.caption("Option 1 – use your device GPS")
    geo = streamlit_geolocation()
    if geo and geo.get("latitude") is not None and geo.get("longitude") is not None:
        cur = (round(geo["latitude"], 6), round(geo["longitude"], 6))
        if cur != st.session_state.last_geo:          # apply each new GPS fix once
            st.session_state.last_geo = cur
            st.session_state.user_lat, st.session_state.user_lon = cur
            st.session_state.user_label = "My GPS location"
            st.rerun()

    # 2) OpenStreetMap place search
    st.caption("Option 2 – search a place / address (OpenStreetMap)")
    with st.form("place_form", clear_on_submit=False):
        q = st.text_input("Place", placeholder="e.g. Andheri station, Bandra Bandstand",
                          label_visibility="collapsed")
        submitted = st.form_submit_button("🔎 Search", width="stretch")
    if submitted and q.strip():
        with st.spinner("Searching OpenStreetMap…"):
            res = search_place(q.strip())
        if res is None:
            st.warning("OpenStreetMap search is unreachable right now. Try again in a moment.")
            st.session_state.place_results = []
        elif not res:
            st.info("No match inside Mumbai. Try a more specific name.")
            st.session_state.place_results = []
        else:
            st.session_state.place_results = res
    if st.session_state.place_results:
        opts = st.session_state.place_results
        idx = st.selectbox("Matches", range(len(opts)),
                           format_func=lambda i: opts[i]["name"][:70], label_visibility="collapsed")
        if st.button("📌 Use this place", width="stretch"):
            st.session_state.user_lat = opts[idx]["lat"]
            st.session_state.user_lon = opts[idx]["lon"]
            st.session_state.user_label = opts[idx]["name"].split(",")[0]
            st.session_state.emergency_active = False
            st.session_state.place_results = []
            st.rerun()

    st.markdown('<div class="section-hdr">🚨 Emergency</div>', unsafe_allow_html=True)
    emg_label = ("🚨 EMERGENCY – Find Police NOW" if not st.session_state.emergency_active
                 else "✅ Emergency Active – Click to Reset")
    if st.button(emg_label, width="stretch", type="primary"):
        if st.session_state.user_lat is not None:
            st.session_state.emergency_active = not st.session_state.emergency_active
            st.rerun()
        else:
            st.warning("⚠️ Please set your location first!")

    st.markdown("---")
    st.markdown('<div class="section-hdr">Risk Threshold</div>', unsafe_allow_html=True)
    risk_range = st.slider("Risk Index Range", 0.0, 30.0, (0.0, 30.0), 0.5, label_visibility="collapsed")
    st.markdown('<div class="section-hdr">Population Density</div>', unsafe_allow_html=True)
    density_range = st.slider("Pop. Density (per sq km)", 0, 85000, (0, 85000), 500, label_visibility="collapsed")

    st.markdown('<div class="section-hdr">Layer Visibility</div>', unsafe_allow_html=True)
    show_high = st.checkbox("🔴 High Risk Zones", True)
    show_med = st.checkbox("🟡 Medium Risk Zones", True)
    show_low = st.checkbox("🟢 Safe Zones", True)

    st.markdown('<div class="section-hdr">Zoom to Locality</div>', unsafe_allow_html=True)
    df_all = fetch_all()
    loc_names = sorted(df_all["locality"].unique().tolist())
    selected_loc = st.selectbox("Select locality", ["— All —"] + loc_names, label_visibility="collapsed")

    st.markdown("---")
    st.markdown('<div class="section-hdr">📣 Report Incident</div>', unsafe_allow_html=True)
    report_locality = st.selectbox("Locality", loc_names, key="report_loc", label_visibility="collapsed")
    severity = st.radio("Severity", ["General", "Severe"], horizontal=True, label_visibility="collapsed")
    if st.button("📤 Submit Report", width="stretch"):
        upd = report_incident(report_locality, severity.lower())
        if not upd.empty:
            st.toast(f"Report saved for {report_locality}. New risk index: {upd.iloc[0]['risk_index']:.1f}", icon="✅")
        st.rerun()

    st.markdown("---")
    st.markdown('<div class="section-hdr">Upload New Data (CSV)</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")
    if uploaded and st.session_state.get("last_upload") != uploaded.file_id:
        try:
            new_df = pd.read_csv(uploaded)
            insert_from_df(new_df)
            st.session_state.last_upload = uploaded.file_id
            st.toast(f"{len(new_df)} rows added – locating them on OpenStreetMap…", icon="✅")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

    if st.button("🔄 Reload from original CSV", width="stretch"):
        load_csv_to_db()
        st.toast("Database reloaded", icon="✅")
        st.rerun()

    n_orig = len(pd.read_csv(CSV_PATH, usecols=["locality"]))
    cache_df = df_all[(df_all["id"] <= n_orig) & df_all["geo_status"].notna()]
    if len(cache_df) == n_orig and not os.path.exists(COORDS_PATH):
        out = cache_df.sort_values("id")[["id", "locality", "lat", "lon", "geo_status"]]
        out.columns = ["row_id", "locality", "lat", "lon", "status"]
        st.markdown("---")
        st.caption("All localities located. Download this file and commit it to GitHub as "
                   "`locality_coords.csv` so the app starts instantly next time.")
        st.download_button("⬇️ locality_coords.csv", out.to_csv(index=False),
                           "locality_coords.csv", "text/csv", width="stretch")

# ─────────────────────────────────────────────
# FILTER
# ─────────────────────────────────────────────
df_all = fetch_all()
df_filtered = df_all[
    df_all["risk_index"].between(*risk_range) &
    df_all["population_density"].between(*density_range)
]

# ─────────────────────────────────────────────
# EMERGENCY / NEAREST STATIONS
# ─────────────────────────────────────────────
user_lat, user_lon = st.session_state.user_lat, st.session_state.user_lon
stations, station_src = None, ""
if user_lat is not None:
    with st.spinner("Finding police stations on OpenStreetMap…"):
        stations, station_src = nearest_stations(user_lat, user_lon, n=3)

emergency_df = stations if st.session_state.emergency_active else None

if emergency_df is not None:
    medals = ["🥇", "🥈", "🥉"]
    cards = ""
    for i, r in emergency_df.iterrows():
        phone = f" · 📞 {r['phone']}" if r["phone"] else ""
        cards += (f'<div class="station-card"><div class="station-name">{medals[i]} {r["name"]}</div>'
                  f'<div class="station-dist">📏 {r["distance_km"]:.2f} km away{phone}</div>'
                  f'<a class="nav-link" href="{r["gmaps_link"]}" target="_blank">🗺️ Google Maps</a>'
                  f'<a class="nav-link" href="{r["osm_link"]}" target="_blank">🧭 OpenStreetMap</a></div>')
    st.markdown(f'<div class="emergency-panel"><div class="emergency-title">'
                f'🚨 EMERGENCY MODE — Nearest Police Stations</div>{cards}</div>', unsafe_allow_html=True)
    st.caption(f"Station data: {station_src}")
    st.error("📞 **Police: 100** | Women Helpline: **1091** | Emergency: **112**")

# ─────────────────────────────────────────────
# METRICS
# ─────────────────────────────────────────────
n_high = int((df_filtered["risk_index"] >= 15).sum())
n_med = int(((df_filtered["risk_index"] >= 7) & (df_filtered["risk_index"] < 15)).sum())
n_low = int((df_filtered["risk_index"] < 7).sum())
avg_risk = df_filtered["risk_index"].mean() if not df_filtered.empty else 0

st.markdown(f"""
<div class="metric-row">
  <div class="metric-card"><div class="val blue">{len(df_filtered)}</div><div class="lbl">Localities Shown</div></div>
  <div class="metric-card"><div class="val red">{n_high}</div><div class="lbl">High Risk Zones</div></div>
  <div class="metric-card"><div class="val amber">{n_med}</div><div class="lbl">Medium Risk Zones</div></div>
  <div class="metric-card"><div class="val green">{n_low}</div><div class="lbl">Safe Zones</div></div>
  <div class="metric-card"><div class="val amber">{avg_risk:.1f}</div><div class="lbl">Avg Risk Index</div></div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# MAP | TABLE
# ─────────────────────────────────────────────
col_map, col_data = st.columns([2.6, 1], gap="medium")
with col_map:
    if df_filtered.empty:
        st.warning("No localities match the current filters.")
    else:
        m = build_map(df_filtered, show_high, show_med, show_low, selected_loc,
                      user_lat, user_lon, emergency_df)
        st_folium(m, width=None, height=580, returned_objects=[], use_container_width=True)
        unmapped = int(df_filtered["lat"].isna().sum())
        if unmapped:
            st.caption(f"ℹ️ {unmapped} localities are not on the map (not found on OpenStreetMap or still being located).")

with col_data:
    if stations is not None and not st.session_state.emergency_active:
        st.markdown('<div class="section-hdr">🚔 Nearest Police Stations</div>', unsafe_allow_html=True)
        for _, r in stations.iterrows():
            st.markdown(f"**{r['name']}**  \n📏 {r['distance_km']:.2f} km · [Navigate]({r['gmaps_link']})")
        st.caption(f"Source: {station_src}")
        st.markdown("---")

    st.markdown('<div class="section-hdr">Top 25 Riskiest Localities</div>', unsafe_allow_html=True)
    top25 = df_filtered.nlargest(25, "risk_index")[
        ["locality", "risk_index", "crimes_women", "police_density", "total_crimes"]
    ].rename(columns={"locality": "Locality", "risk_index": "Risk", "crimes_women": "Crimes(W)",
                      "police_density": "Police/km²", "total_crimes": "Total Crimes"}).reset_index(drop=True)

    def color_risk(v):
        return ("color:#ff4444;font-weight:700" if v >= 15 else
                "color:#ffaa00;font-weight:600" if v >= 7 else "color:#00e676")

    styler = top25.style
    styler = (styler.map if hasattr(styler, "map") else styler.applymap)(color_risk, subset=["Risk"])
    st.dataframe(styler.format({"Risk": "{:.1f}", "Police/km²": "{:.2f}"}), width="stretch", height=480)

# ─────────────────────────────────────────────
# ANALYTICS
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-hdr">📊 Analytics</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("**Risk Distribution**")
    st.bar_chart(pd.DataFrame({"Zone": ["🔴 High (≥15)", "🟡 Medium (7-15)", "🟢 Safe (<7)"],
                               "Count": [n_high, n_med, n_low]}).set_index("Zone"), color="#4fc3f7")
with c2:
    st.markdown("**Top 10 by Crimes Against Women**")
    st.bar_chart(df_filtered.nlargest(10, "crimes_women").set_index("locality")[["crimes_women"]], color="#ff4444")
with c3:
    st.markdown("**Top 10 Police Density**")
    st.bar_chart(df_filtered.nlargest(10, "police_density").set_index("locality")[["police_density"]], color="#00e676")

with st.expander("📋 Full Data Table", expanded=False):
    cols = ["locality", "risk_index", "crimes_women", "total_crimes", "police_density",
            "population_density", "uhi_index", "internet_pct", "population", "lat", "lon"]
    st.dataframe(df_filtered[cols].rename(columns={
        "locality": "Locality", "risk_index": "Risk Index", "crimes_women": "Crimes (Women)",
        "total_crimes": "Total Crimes", "police_density": "Police Density",
        "population_density": "Pop. Density", "uhi_index": "UHI Index",
        "internet_pct": "Internet %", "population": "Population", "lat": "Lat", "lon": "Lon",
    }).sort_values("Risk Index", ascending=False).reset_index(drop=True), width="stretch", height=400)
    st.download_button("⬇️ Download filtered data as CSV", df_filtered.to_csv(index=False),
                       "filtered_data.csv", "text/csv")

st.markdown(f"""
<div style="text-align:center;color:{SUBTXT};font-size:.75rem;margin-top:24px;padding-bottom:12px">
  Mumbai Women Safety Risk Map · Map data © <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors
  · Built with Streamlit + Folium
</div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# BACKGROUND GEOCODING (only runs if locality_coords.csv is missing / incomplete)
# ─────────────────────────────────────────────
pending = int(df_all["geo_status"].isna().sum())
if pending:
    total = len(df_all)
    st.info(f"📡 Locating localities on OpenStreetMap… {total - pending}/{total} done. "
            f"The map fills in automatically (≈1 per second).")
    looked, errs = geocode_pending_chunk()
    if looked and errs >= max(1, looked // 2):
        st.warning("OpenStreetMap (Nominatim) isn't responding. Pausing – refresh the page to retry.")
    else:
        st.rerun()
