import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="ROHDA Raalte — Player Load Dashboard",
    page_icon="⚽",
    layout="wide",
)

# --- Google Sheet Configuration ---
SHEET_ID = "1fikJsJ8rFry3YHdfv-Zl3J7UVf3VtIIFhg_DbcMBOjo"
GPS_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=734190721"

# --- Rohda Brand Colors ---
ROHDA_RED = "#C8102E"
ROHDA_YELLOW = "#FFD100"
ROHDA_DARK = "#1a1a1a"
ROHDA_LIGHT_BG = "#fafafa"
ROHDA_GREEN = "#2e7d32"
ROHDA_ORANGE = "#f57f17"
LOGO_URL = "https://www.rohdaraalte.nl/wp-content/uploads/rohda/cropped-logo-512.png"

# --- Custom Styling ---
st.markdown(f"""
<style>
    .stApp {{ background-color: {ROHDA_LIGHT_BG}; }}
    .rohda-header {{
        background: linear-gradient(135deg, {ROHDA_RED} 0%, #8B0000 100%);
        padding: 1.5rem 2rem; border-radius: 12px; margin-bottom: 1.5rem;
        display: flex; align-items: center; gap: 1.5rem;
        box-shadow: 0 4px 15px rgba(200, 16, 46, 0.3);
    }}
    .rohda-header img {{ height: 80px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3)); }}
    .rohda-header-text {{ color: white; }}
    .rohda-header-text h1 {{ margin: 0; font-size: 1.8rem; font-weight: 700; color: white; }}
    .rohda-header-text p {{ margin: 0.2rem 0 0 0; font-size: 1rem; color: {ROHDA_YELLOW}; font-weight: 500; }}
    [data-testid="stMetric"] {{
        background-color: white; border: 1px solid #e0e0e0; border-radius: 10px;
        padding: 1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0; background-color: white; border-radius: 10px; padding: 4px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }}
    .stTabs [data-baseweb="tab"] {{ border-radius: 8px; padding: 0.6rem 1.5rem; font-weight: 600; }}
    .stTabs [aria-selected="true"] {{ background-color: {ROHDA_RED} !important; color: white !important; }}
    [data-testid="stSidebar"] {{ background-color: white; border-right: 3px solid {ROHDA_RED}; }}
    .section-header {{
        color: {ROHDA_RED}; font-weight: 700; font-size: 1.3rem;
        border-bottom: 3px solid {ROHDA_YELLOW}; padding-bottom: 0.5rem; margin-bottom: 1rem;
    }}
    hr {{ border: none; border-top: 2px solid {ROHDA_YELLOW}; margin: 1.5rem 0; }}
    [data-testid="stFileUploader"] {{
        background-color: white; border: 2px dashed {ROHDA_RED}; border-radius: 12px; padding: 1rem;
    }}
    .rohda-footer {{
        text-align: center; color: #999; font-size: 0.8rem; margin-top: 3rem;
        padding: 1rem; border-top: 1px solid #eee;
    }}
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown(f"""
<div class="rohda-header">
    <img src="{LOGO_URL}" alt="ROHDA Raalte">
    <div class="rohda-header-text">
        <h1>ROHDA Raalte — Player Load Dashboard</h1>
        <p>Performance Analysis & Injury Prevention</p>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Helper Functions ---
def get_ac_color(ratio):
    if ratio < 0.8: return "🔴"
    elif ratio <= 1.3: return "🟢"
    elif ratio <= 1.5: return "🟠"
    else: return "🔴"

def get_ac_status(ratio):
    if ratio < 0.8: return "Under-trained"
    elif ratio <= 1.3: return "Safe"
    elif ratio <= 1.5: return "Watch"
    else: return "Danger"

def calculate_ac_ratios(player_data, metrics):
    results = {}
    for metric in metrics:
        values = player_data[metric].values
        if len(values) < 2:
            results[metric] = None
            continue
        latest = values[-1]
        previous = values[-6:-1] if len(values) >= 6 else values[:-1]
        avg_previous = np.mean(previous)
        if avg_previous > 0:
            results[metric] = round(latest / avg_previous, 2)
        else:
            results[metric] = None
    return results

def convert_statsports_csv(csv_file):
    raw = pd.read_csv(csv_file)
    is_match = "Drill Title" in raw.columns
    if is_match:
        converted = raw.rename(columns={
            "Total Distance": "Totale afstand",
            "High Intensity Distance": "Hoge intensiteit afstand",
            "Distance per min": "Afstand per minuut",
        })
    else:
        converted = raw.copy()
        converted["Drill Title"] = None
    converted["Session Date"] = pd.to_datetime(converted["Session Date"], dayfirst=True)
    date_sample = converted["Session Date"].iloc[0]
    if date_sample.month >= 7:
        season = f"{date_sample.year}-{date_sample.year + 1}"
    else:
        season = f"{date_sample.year - 1}-{date_sample.year}"
    converted["Seizoen"] = season
    expected_cols = [
        "Player Name", "Squad Name", "Session Date", "Session Name",
        "Session Type", "Drill Title", "Totale afstand",
        "Hoge intensiteit afstand", "Afstand per minuut", "DSL", "Seizoen"
    ]
    converted = converted[expected_cols]
    return converted, season

METRICS = {
    "Totale afstand": "Total Distance",
    "Hoge intensiteit afstand": "High Intensity Distance",
    "Afstand per minuut": "Distance Per Minute",
    "DSL": "Dynamic Stress Load",
}

# --- Data Loading ---
st.markdown("---")

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_gps_data():
    """Load GPS data from Google Sheets."""
    try:
        df = pd.read_csv(GPS_CSV_URL)
        df["Session Date"] = pd.to_datetime(df["Session Date"])
        return df, None
    except Exception as e:
        return None, str(e)

# Load data from Google Sheets
with st.spinner("Loading data from Google Sheets..."):
    df, load_error = load_gps_data()

if load_error:
    st.error(f"Could not load data from Google Sheets: {load_error}")
    st.info("You can still upload an Excel file manually below.")
    uploaded_file = st.file_uploader("📂 Upload Excel file", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        df["Session Date"] = pd.to_datetime(df["Session Date"])
    else:
        st.stop()

# Optional: merge a new StatSports CSV
new_activity_file = st.file_uploader(
    "➕ Add new StatSports CSV export (optional — merges with existing data for this session only)",
    type=["csv"],
    key="activity_upload"
)

if new_activity_file is not None:
    try:
        new_data, detected_season = convert_statsports_csv(new_activity_file)
        new_session_name = new_data["Session Name"].iloc[0]
        new_session_date = new_data["Session Date"].iloc[0].strftime("%d-%m-%Y")
        new_session_type = new_data["Session Type"].iloc[0]
        n_players = new_data["Player Name"].nunique()
        existing_check = df[
            (df["Session Name"] == new_session_name) &
            (df["Session Date"] == new_data["Session Date"].iloc[0])
        ]
        if len(existing_check) > 0:
            st.warning(f"⚠️ **{new_session_name}** ({new_session_date}) already exists. Skipping merge.")
        else:
            df = pd.concat([df, new_data], ignore_index=True)
            st.success(f"✅ **{new_session_name}** ({new_session_date}) merged for this session! "
                      f"Type: {new_session_type} | Players: {n_players} | Season: {detected_season}")
            st.caption("💡 To permanently add this data, paste it into the Google Sheet.")
    except Exception as e:
        st.error(f"❌ Error converting StatSports file: {str(e)}")

# --- Process Data ---
df = df.sort_values(["Player Name", "Session Date"])
df["Session ID"] = df["Session Date"].dt.strftime("%Y-%m-%d") + " | " + df["Session Name"]

df_analysis = df[
    (df["Session Type"] == "Practice") |
    ((df["Session Type"] == "Gameday") & (df["Drill Title"] == "Total"))
].copy()

# --- Sidebar ---
st.sidebar.image(LOGO_URL, width=120)
st.sidebar.markdown(f'<h2 style="color: {ROHDA_RED}; margin-top: 0.5rem;">Filters</h2>', unsafe_allow_html=True)

seasons = sorted(df_analysis["Seizoen"].unique())
selected_season = st.sidebar.selectbox("Season", seasons, index=len(seasons)-1)
df_filtered = df_analysis[df_analysis["Seizoen"] == selected_season]

sessions_by_date = (
    df_filtered.sort_values("Session Date")
    .drop_duplicates(subset="Session ID", keep="first")
    [["Session Date", "Session Name", "Session ID", "Session Type"]]
)
all_session_ids = sessions_by_date["Session ID"].tolist()
latest_session_id = all_session_ids[-1] if len(all_session_ids) > 0 else None

session_labels = {}
for sid in reversed(all_session_ids):
    date_part, name_part = sid.split(" | ")
    date_readable = pd.to_datetime(date_part).strftime("%d-%m-%Y")
    session_labels[sid] = f"{name_part}  ({date_readable})"

st.sidebar.markdown("---")
st.sidebar.markdown(f'**📍 Select activity:**')
selected_session_id = st.sidebar.selectbox(
    "Activity", list(session_labels.keys()), index=0,
    format_func=lambda x: session_labels[x], label_visibility="collapsed"
)
selected_session_name = selected_session_id.split(" | ")[1]
selected_session_date_str = selected_session_id.split(" | ")[0]

st.sidebar.markdown("---")
st.sidebar.markdown(f"**📊 Sessions this season:** {len(all_session_ids)}")
st.sidebar.markdown(f"**👥 Players:** {df_filtered['Player Name'].nunique()}")

# =====================================================
# TABS
# =====================================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Activity Overview", "⚖️ A/C Ratios", "🚦 Squad Status", "🏆 Leaderboard"])

# =====================================================
# TAB 1: ACTIVITY OVERVIEW
# =====================================================
with tab1:
    st.markdown(f'<div class="section-header">Activity: {selected_session_name}</div>', unsafe_allow_html=True)
    selected_data = df_filtered[df_filtered["Session ID"] == selected_session_id]

    if selected_data.empty:
        st.warning("No data found for the selected session.")
    else:
        selected_date_display = selected_data["Session Date"].iloc[0].strftime("%A %d %B %Y")
        selected_type = selected_data["Session Type"].iloc[0]
        type_emoji = "🏟️" if selected_type == "Gameday" else "🏋️"
        st.markdown(f"**📅 Date:** {selected_date_display} &nbsp; | &nbsp; **{type_emoji} Type:** {selected_type}")

        summary_data = selected_data
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Avg Total Distance", f"{summary_data['Totale afstand'].mean():,.0f} m")
        with col2: st.metric("Avg High Intensity Dist.", f"{summary_data['Hoge intensiteit afstand'].mean():,.0f} m")
        with col3: st.metric("Avg Distance/Min", f"{summary_data['Afstand per minuut'].mean():.0f} m/min")
        with col4: st.metric("Avg DSL", f"{summary_data['DSL'].mean():.0f}")

        st.markdown("---")
        st.markdown(f'<div class="section-header">Player Breakdown</div>', unsafe_allow_html=True)
        selected_metric = st.selectbox("Select metric", list(METRICS.keys()), format_func=lambda x: METRICS[x])
        chart_data = summary_data[["Player Name", selected_metric]].sort_values(selected_metric, ascending=True)

        fig = px.bar(chart_data, x=selected_metric, y="Player Name", orientation="h",
                     title=f"{METRICS[selected_metric]} — {selected_session_name}",
                     color=selected_metric, color_continuous_scale=[ROHDA_YELLOW, ROHDA_RED])
        fig.update_layout(height=max(400, len(chart_data) * 30), showlegend=False, yaxis_title="",
                         xaxis_title=METRICS[selected_metric], plot_bgcolor="white", paper_bgcolor="white",
                         title_font_color=ROHDA_RED, title_font_size=16)
        fig.update_xaxes(gridcolor="#f0f0f0")
        fig.update_yaxes(gridcolor="#f0f0f0")
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("📋 View raw data"):
            display_cols = ["Player Name", "Totale afstand", "Hoge intensiteit afstand", "Afstand per minuut", "DSL"]
            st.dataframe(summary_data[display_cols].sort_values("Player Name").reset_index(drop=True), use_container_width=True)

# =====================================================
# TAB 2: A/C RATIOS
# =====================================================
with tab2:
    st.markdown(f'<div class="section-header">A/C Ratios — Latest vs. Average of Last 5</div>', unsafe_allow_html=True)
    st.markdown("Compares each player's latest activity to their average of the previous 5 activities.")

    col_legend1, col_legend2, col_legend3 = st.columns(3)
    col_legend1.markdown("🟢 **Safe** (0.8 – 1.3)")
    col_legend2.markdown("🟠 **Watch** (1.3 – 1.5)")
    col_legend3.markdown("🔴 **Danger** (>1.5)")
    st.markdown("---")

    toggle_col1, toggle_col2 = st.columns(2)
    with toggle_col1:
        show_overload_only = st.toggle("🔴 Show only overload risk (ratio > 1.3)", value=False)
    with toggle_col2:
        latest_activity_only = st.toggle("📍 Selected activity players only", value=False)

    if latest_activity_only:
        players = sorted(df_filtered[df_filtered["Session ID"] == selected_session_id]["Player Name"].unique())
    else:
        players = sorted(df_filtered["Player Name"].unique())

    ac_results = []
    for player in players:
        player_data = df_filtered[df_filtered["Player Name"] == player].sort_values("Session Date")
        if len(player_data) < 2: continue
        ratios = calculate_ac_ratios(player_data, list(METRICS.keys()))
        row = {"Player": player, "_has_overload": False}
        for metric_key, metric_label in METRICS.items():
            ratio = ratios.get(metric_key)
            if ratio is not None:
                row[metric_label] = ratio
                row[f"{metric_label}_status"] = get_ac_status(ratio)
                row[f"{metric_label}_icon"] = get_ac_color(ratio)
                if ratio > 1.3: row["_has_overload"] = True
            else:
                row[metric_label] = None
                row[f"{metric_label}_status"] = "N/A"
                row[f"{metric_label}_icon"] = "⚪"
        if show_overload_only and not row["_has_overload"]: continue
        ac_results.append(row)

    if ac_results:
        def risk_sort_key(row):
            for ml in METRICS.values():
                if row.get(f"{ml}_status") == "Danger": return 0
            for ml in METRICS.values():
                if row.get(f"{ml}_status") == "Watch": return 1
            return 2

        ac_results_sorted = sorted(ac_results, key=risk_sort_key)
        display_data = []
        for row in ac_results_sorted:
            dr = {"Player": row["Player"]}
            for ml in METRICS.values():
                ratio = row.get(ml)
                icon = row.get(f"{ml}_icon", "")
                dr[ml] = f"{icon} {ratio:.2f}" if ratio is not None else "⚪ N/A"
            display_data.append(dr)

        n_danger = sum(1 for r in ac_results_sorted if r.get("_has_overload"))
        n_total = len(ac_results_sorted)
        if show_overload_only:
            st.markdown(f"Showing **{n_total} player(s)** with overload risk")
        else:
            st.markdown(f"Showing **{n_total} players** — **{n_danger}** with overload risk")

        st.dataframe(pd.DataFrame(display_data), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown(f'<div class="section-header">Detailed Player View</div>', unsafe_allow_html=True)
        detail_col1, detail_col2 = st.columns([2, 1])
        with detail_col1:
            player_list = [r["Player"] for r in ac_results_sorted]
            selected_player = st.selectbox("Select a player", player_list)
        with detail_col2:
            session_type_filter = st.selectbox("Session type", ["All", "Gameday", "Practice"])

        player_data = df_filtered[df_filtered["Player Name"] == selected_player].sort_values("Session Date")
        if session_type_filter != "All":
            player_data_display = player_data[player_data["Session Type"] == session_type_filter]
        else:
            player_data_display = player_data

        if len(player_data) >= 2:
            player_ratios = calculate_ac_ratios(player_data, list(METRICS.keys()))
            cols = st.columns(4)
            for i, (mk, ml) in enumerate(METRICS.items()):
                ratio = player_ratios.get(mk)
                if ratio is not None:
                    cols[i].metric(ml, f"{get_ac_color(ratio)} {ratio:.2f}", delta=get_ac_status(ratio), delta_color="off")
                else:
                    cols[i].metric(ml, "N/A")

            st.markdown(f"##### Last 6 sessions ({session_type_filter})")
            last_sessions = player_data_display.tail(6)
            if len(last_sessions) > 0:
                sd = last_sessions[["Session Date", "Session Name", "Session Type"] + list(METRICS.keys())].copy()
                sd["Session Date"] = sd["Session Date"].dt.strftime("%d-%m-%Y")
                sd = sd.rename(columns=METRICS)
                st.dataframe(sd.reset_index(drop=True), use_container_width=True, hide_index=True)
            else:
                st.info(f"No {session_type_filter.lower()} sessions found.")
    else:
        if show_overload_only:
            st.success("No players with overload risk — everyone is in the safe zone!")
        else:
            st.info("Not enough data to calculate A/C ratios.")

# =====================================================
# TAB 3: SQUAD STATUS
# =====================================================
with tab3:
    st.markdown(f'<div class="section-header">🚦 Squad Status Overview</div>', unsafe_allow_html=True)
    st.markdown("Player cards showing current A/C ratio status across all 4 metrics.")
    st.markdown("---")

    if ac_results:
        overload_players, underload_players, watch_players, safe_players = [], [], [], []

        for row in ac_results:
            has_overload = has_underload = has_watch = False
            player_metrics = {}
            for ml in METRICS.values():
                ratio = row.get(ml)
                status = row.get(f"{ml}_status", "N/A")
                icon = row.get(f"{ml}_icon", "⚪")
                player_metrics[ml] = {"ratio": ratio, "status": status, "icon": icon}
                if status == "Danger": has_overload = True
                elif status == "Under-trained": has_underload = True
                elif status == "Watch": has_watch = True

            pi = {"player": row["Player"], "metrics": player_metrics}
            if has_overload: overload_players.append(pi)
            elif has_underload: underload_players.append(pi)
            elif has_watch: watch_players.append(pi)
            else: safe_players.append(pi)

        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("🔴 Overload", len(overload_players))
        with col2: st.metric("🔵 Underload", len(underload_players))
        with col3: st.metric("🟠 Watch", len(watch_players))
        with col4: st.metric("🟢 Safe", len(safe_players))
        st.markdown("---")

        def render_player_card(pi, card_color, border_color, badge_text, badge_bg):
            name = pi["player"]
            m = pi["metrics"]
            metric_lines = ""
            for label, data in m.items():
                ratio = data["ratio"]
                icon = data["icon"]
                short = label.replace("Total Distance","TD").replace("High Intensity Distance","HID").replace("Distance Per Minute","DPM").replace("Dynamic Stress Load","DSL")
                val = f"{icon} {ratio:.2f}" if ratio is not None else "⚪ N/A"
                metric_lines += f"<tr><td style='color:#aaa;font-size:0.75rem;padding:2px 4px;'>{short}</td><td style='text-align:right;font-weight:700;font-size:0.85rem;padding:2px 4px;'>{val}</td></tr>"
            return (
                f"<div style='background:linear-gradient(145deg,{card_color},#1a1a2e);border:2px solid {border_color};"
                f"border-radius:12px;padding:0.8rem;color:white;box-shadow:0 4px 12px rgba(0,0,0,0.3);margin-bottom:0.5rem;'>"
                f"<table style='width:100%;border:none;border-collapse:collapse;'>"
                f"<tr><td style='font-size:0.95rem;font-weight:700;padding-bottom:6px;'>{name}</td>"
                f"<td style='text-align:right;'><span style='background:{badge_bg};color:white;font-size:0.6rem;"
                f"font-weight:700;padding:2px 6px;border-radius:3px;'>{badge_text}</span></td></tr>"
                f"{metric_lines}</table></div>"
            )

        def render_card_grid(players, cc, bc, bt, bg, cols=4):
            if not players: return
            html = "<div style='display:grid;grid-template-columns:" + " ".join(["1fr"]*min(cols,len(players))) + ";gap:0.5rem;'>"
            for p in players:
                html += render_player_card(p, cc, bc, bt, bg)
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)

        if overload_players:
            st.markdown("### 🔴 Overload Risk")
            render_card_grid(overload_players, "#4a0e0e", ROHDA_RED, "OVERLOAD", "#c62828")
        else:
            st.success("No players with overload risk!")
        st.markdown("")
        if underload_players:
            st.markdown("### 🔵 Underload Risk")
            render_card_grid(underload_players, "#0e1a4a", "#1565c0", "UNDERLOAD", "#1565c0")
        st.markdown("")
        if watch_players:
            st.markdown("### 🟠 Watch")
            render_card_grid(watch_players, "#3e2f0e", ROHDA_YELLOW, "WATCH", "#f57f17")
        st.markdown("")
        if safe_players:
            st.markdown("### 🟢 Safe")
            render_card_grid(safe_players, "#0e2e0e", ROHDA_GREEN, "SAFE", "#2e7d32", 5)
    else:
        st.info("Not enough data for squad status.")

# =====================================================
# TAB 4: LEADERBOARD
# =====================================================
with tab4:
    st.markdown(f'<div class="section-header">🏆 Leaderboard — Season {selected_season}</div>', unsafe_allow_html=True)
    st.markdown("---")

    def render_leaderboard(title, data, metric_label, unit="", emoji="🏆"):
        rows = ""
        for i, (_, row) in enumerate(data.head(5).iterrows()):
            bg = "rgba(255,209,0,0.1)" if i == 0 else "transparent"
            bold = "font-weight:700;" if i == 0 else ""
            rows += (
                f"<tr style='background:{bg};'>"
                f"<td style='padding:6px 8px;font-size:0.9rem;width:30px;color:{ROHDA_YELLOW};font-weight:700;'>{i+1}.</td>"
                f"<td style='padding:6px 8px;{bold}'>{row['Player Name']}</td>"
                f"<td style='padding:6px 8px;text-align:right;{bold}font-size:1rem;'>{row[metric_label]:,.0f} {unit}</td></tr>"
            )
        return (
            f"<div style='background:linear-gradient(145deg,#1a1a2e,#2a2a4e);border-radius:12px;"
            f"padding:1rem;color:white;box-shadow:0 4px 12px rgba(0,0,0,0.3);margin-bottom:0.5rem;'>"
            f"<div style='font-size:1rem;font-weight:700;margin-bottom:0.6rem;color:{ROHDA_YELLOW};'>{emoji} {title}</div>"
            f"<table style='width:100%;border-collapse:collapse;'>{rows}</table></div>"
        )

    st.markdown("### 📊 Accumulated Season Totals")
    acc = df_filtered.groupby("Player Name").agg({"Totale afstand":"sum","Hoge intensiteit afstand":"sum","DSL":"sum"}).reset_index()
    acc["Sessions"] = df_filtered.groupby("Player Name")["Session ID"].nunique().values

    c1, c2 = st.columns(2)
    with c1: st.markdown(render_leaderboard("Most Total Distance", acc.sort_values("Totale afstand",ascending=False), "Totale afstand", "m", "🏃"), unsafe_allow_html=True)
    with c2: st.markdown(render_leaderboard("Most High Intensity Distance", acc.sort_values("Hoge intensiteit afstand",ascending=False), "Hoge intensiteit afstand", "m", "⚡"), unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    with c3: st.markdown(render_leaderboard("Most Dynamic Stress Load", acc.sort_values("DSL",ascending=False), "DSL", "", "💪"), unsafe_allow_html=True)
    with c4: st.markdown(render_leaderboard("Most Sessions Played", acc.sort_values("Sessions",ascending=False), "Sessions", "", "📅"), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### ⚡ Peak Performers")
    peak_data = df_filtered[["Player Name","Session Name","Session Date","Session Type","Totale afstand","Hoge intensiteit afstand","Afstand per minuut","DSL"]].copy()

    def get_peak_per_player(data, col):
        idx = data.groupby("Player Name")[col].idxmax()
        return data.loc[idx].sort_values(col, ascending=False)

    def render_peak_leaderboard(title, data, col, unit="", emoji="⚡"):
        rows = ""
        for i, (_, row) in enumerate(data.head(5).iterrows()):
            bg = "rgba(255,209,0,0.1)" if i == 0 else "transparent"
            bold = "font-weight:700;" if i == 0 else ""
            date = row["Session Date"].strftime("%d-%m-%Y")
            rows += (
                f"<tr style='background:{bg};'>"
                f"<td style='padding:5px 8px;font-size:0.9rem;width:30px;color:{ROHDA_YELLOW};font-weight:700;'>{i+1}.</td>"
                f"<td style='padding:5px 8px;{bold}'>{row['Player Name']}</td>"
                f"<td style='padding:5px 8px;text-align:right;{bold}font-size:1rem;'>{row[col]:,.0f} {unit}</td>"
                f"<td style='padding:5px 8px;text-align:right;color:#aaa;font-size:0.75rem;'>{row['Session Name']}<br>{date}</td></tr>"
            )
        return (
            f"<div style='background:linear-gradient(145deg,#1a1a2e,#2a2a4e);border-radius:12px;"
            f"padding:1rem;color:white;box-shadow:0 4px 12px rgba(0,0,0,0.3);margin-bottom:0.5rem;'>"
            f"<div style='font-size:1rem;font-weight:700;margin-bottom:0.6rem;color:{ROHDA_YELLOW};'>{emoji} {title}</div>"
            f"<table style='width:100%;border-collapse:collapse;'>{rows}</table></div>"
        )

    p1, p2 = st.columns(2)
    with p1: st.markdown(render_peak_leaderboard("Highest Total Distance", get_peak_per_player(peak_data,"Totale afstand"), "Totale afstand", "m", "🏃"), unsafe_allow_html=True)
    with p2: st.markdown(render_peak_leaderboard("Highest High Intensity Distance", get_peak_per_player(peak_data,"Hoge intensiteit afstand"), "Hoge intensiteit afstand", "m", "⚡"), unsafe_allow_html=True)
    p3, p4 = st.columns(2)
    with p3: st.markdown(render_peak_leaderboard("Highest Distance Per Minute", get_peak_per_player(peak_data,"Afstand per minuut"), "Afstand per minuut", "m/min", "🔥"), unsafe_allow_html=True)
    with p4: st.markdown(render_peak_leaderboard("Highest DSL", get_peak_per_player(peak_data,"DSL"), "DSL", "", "💪"), unsafe_allow_html=True)

# --- Footer ---
st.markdown(f"""
<div class="rohda-footer">
    ROHDA Raalte — Player Load Dashboard v2.0 &nbsp; | &nbsp; © Jordi Koggel, Human Movement Scientist &nbsp; | &nbsp; Season {selected_season}
</div>
""", unsafe_allow_html=True)
