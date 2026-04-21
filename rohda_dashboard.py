import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
import shutil
from datetime import datetime
from pathlib import Path

# --- Page Configuration ---
st.set_page_config(
    page_title="ROHDA Raalte — Player Load Dashboard",
    page_icon="⚽",
    layout="wide",
)

# --- Rohda Brand Colors ---
ROHDA_RED = "#C8102E"
ROHDA_YELLOW = "#FFD100"
ROHDA_DARK = "#1a1a1a"
ROHDA_LIGHT_BG = "#fafafa"
ROHDA_RED_LIGHT = "#fce4ec"
ROHDA_YELLOW_LIGHT = "#fffde7"
ROHDA_GREEN = "#2e7d32"
ROHDA_ORANGE = "#f57f17"

# --- Custom Styling ---
st.markdown(f"""
<style>
    /* Main background */
    .stApp {{
        background-color: {ROHDA_LIGHT_BG};
    }}

    /* Header bar */
    .rohda-header {{
        background: linear-gradient(135deg, {ROHDA_RED} 0%, #8B0000 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 1.5rem;
        box-shadow: 0 4px 15px rgba(200, 16, 46, 0.3);
    }}
    .rohda-header img {{
        height: 80px;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
    }}
    .rohda-header-text {{
        color: white;
    }}
    .rohda-header-text h1 {{
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
        color: white;
        letter-spacing: 0.5px;
    }}
    .rohda-header-text p {{
        margin: 0.2rem 0 0 0;
        font-size: 1rem;
        color: {ROHDA_YELLOW};
        font-weight: 500;
    }}

    /* Metric cards */
    [data-testid="stMetric"] {{
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }}
    [data-testid="stMetric"] label {{
        color: #555 !important;
        font-size: 0.85rem !important;
    }}
    [data-testid="stMetric"] [data-testid="stMetricValue"] {{
        color: {ROHDA_DARK} !important;
        font-weight: 700 !important;
    }}

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0;
        background-color: white;
        border-radius: 10px;
        padding: 4px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {ROHDA_RED} !important;
        color: white !important;
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: white;
        border-right: 3px solid {ROHDA_RED};
    }}
    [data-testid="stSidebar"] .stMarkdown h2 {{
        color: {ROHDA_RED};
    }}

    /* Status cards */
    .status-danger {{
        background: linear-gradient(135deg, #ffebee, #ffcdd2);
        border-left: 4px solid {ROHDA_RED};
        padding: 0.8rem 1rem;
        border-radius: 0 8px 8px 0;
        margin-bottom: 0.5rem;
    }}
    .status-watch {{
        background: linear-gradient(135deg, #fff8e1, #ffecb3);
        border-left: 4px solid {ROHDA_YELLOW};
        padding: 0.8rem 1rem;
        border-radius: 0 8px 8px 0;
        margin-bottom: 0.5rem;
    }}
    .status-safe {{
        background: linear-gradient(135deg, #e8f5e9, #c8e6c9);
        border-left: 4px solid {ROHDA_GREEN};
        padding: 0.8rem 1rem;
        border-radius: 0 8px 8px 0;
        margin-bottom: 0.5rem;
    }}

    /* Section headers */
    .section-header {{
        color: {ROHDA_RED};
        font-weight: 700;
        font-size: 1.3rem;
        border-bottom: 3px solid {ROHDA_YELLOW};
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }}

    /* Divider */
    hr {{
        border: none;
        border-top: 2px solid {ROHDA_YELLOW};
        margin: 1.5rem 0;
    }}

    /* Upload area */
    [data-testid="stFileUploader"] {{
        background-color: white;
        border: 2px dashed {ROHDA_RED};
        border-radius: 12px;
        padding: 1rem;
    }}

    /* Dataframe styling */
    .stDataFrame {{
        border-radius: 10px;
        overflow: hidden;
    }}

    /* Footer */
    .rohda-footer {{
        text-align: center;
        color: #999;
        font-size: 0.8rem;
        margin-top: 3rem;
        padding: 1rem;
        border-top: 1px solid #eee;
    }}
</style>
""", unsafe_allow_html=True)

# --- Header with Logo ---
LOGO_URL = "https://www.rohdaraalte.nl/wp-content/uploads/rohda/cropped-logo-512.png"
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
    if ratio < 0.8:
        return "🔴"
    elif ratio <= 1.3:
        return "🟢"
    elif ratio <= 1.5:
        return "🟠"
    else:
        return "🔴"

def get_ac_status(ratio):
    if ratio < 0.8:
        return "Under-trained"
    elif ratio <= 1.3:
        return "Safe"
    elif ratio <= 1.5:
        return "Watch"
    else:
        return "Danger"

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

# --- Metrics we track ---
METRICS = {
    "Totale afstand": "Total Distance",
    "Hoge intensiteit afstand": "High Intensity Distance",
    "Afstand per minuut": "Distance Per Minute",
    "DSL": "Dynamic Stress Load",
}

# --- Helper: Convert StatSports CSV to master format ---
def convert_statsports_csv(csv_file):
    """Convert a raw StatSports export CSV to the master file format."""
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

# --- File Paths ---
# The dashboard stores data in the same folder as the script
APP_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
MASTER_FILE = APP_DIR / "rohda_master_data.xlsx"
BACKUP_DIR = APP_DIR / "backups"

# Create backup folder if it doesn't exist
BACKUP_DIR.mkdir(exist_ok=True)

def save_master(df):
    """Save the master dataframe to Excel."""
    df.to_excel(MASTER_FILE, index=False)

def create_backup():
    """Create a timestamped backup of the master file."""
    if MASTER_FILE.exists():
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        backup_path = BACKUP_DIR / f"rohda_master_backup_{timestamp}.xlsx"
        shutil.copy2(MASTER_FILE, backup_path)
        return backup_path
    return None

# --- Data Loading Section ---
st.markdown("---")

# Check if master file exists
master_exists = MASTER_FILE.exists()

if master_exists:
    # Master file found — show status and option to add new activity
    st.markdown(f"#### ✅ Master file loaded automatically")
    st.caption(f"📁 `{MASTER_FILE}`")
    
    col_add, col_manage = st.columns([2, 1])
    
    with col_add:
        new_activity_file = st.file_uploader(
            "➕ Add new StatSports CSV export",
            type=["csv"],
            help="Raw CSV export from StatSports. Will be automatically converted, backed up, and merged.",
            key="activity_upload"
        )
    
    with col_manage:
        st.markdown("")
        st.markdown("")
        if st.button("🔄 Replace master file"):
            st.session_state["show_replace_upload"] = True
        
        # Count backups
        n_backups = len(list(BACKUP_DIR.glob("*.xlsx")))
        st.caption(f"📦 {n_backups} backup(s) in `/backups`")
    
    # Show replace upload if requested
    if st.session_state.get("show_replace_upload", False):
        replace_file = st.file_uploader(
            "Upload a new master Excel file to replace the current one",
            type=["xlsx"],
            key="replace_upload"
        )
        if replace_file is not None:
            create_backup()
            new_master = pd.read_excel(replace_file)
            new_master["Session Date"] = pd.to_datetime(new_master["Session Date"])
            save_master(new_master)
            st.success("✅ Master file replaced! Backup of the old file was created.")
            st.session_state["show_replace_upload"] = False
            st.rerun()
    
    # Load master data
    df = pd.read_excel(MASTER_FILE)
    df["Session Date"] = pd.to_datetime(df["Session Date"])
    
    # Merge new activity if uploaded
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
                st.warning(f"⚠️ **{new_session_name}** ({new_session_date}) already exists in the master file. Skipping merge.")
            else:
                # Create backup before merging
                backup_path = create_backup()
                
                # Merge and save
                df = pd.concat([df, new_data], ignore_index=True)
                save_master(df)
                
                st.success(f"✅ **{new_session_name}** ({new_session_date}) merged and saved! "
                          f"Type: {new_session_type} | Players: {n_players} | Season: {detected_season}")
                if backup_path:
                    st.caption(f"📦 Backup created: `{backup_path.name}`")
        except Exception as e:
            st.error(f"❌ Error converting StatSports file: {str(e)}")

else:
    # No master file found — first time setup
    st.markdown("#### 📂 First-time setup: Upload your master Excel file")
    st.markdown("This file will be saved locally so you don't have to upload it again.")
    
    initial_upload = st.file_uploader(
        "Upload your season Excel file",
        type=["xlsx"],
        help="The main file with all historical session data.",
        key="initial_upload"
    )
    
    if initial_upload is not None:
        df_initial = pd.read_excel(initial_upload)
        df_initial["Session Date"] = pd.to_datetime(df_initial["Session Date"])
        save_master(df_initial)
        st.success(f"✅ Master file saved! Found {len(df_initial)} records, "
                  f"{df_initial['Player Name'].nunique()} players. "
                  f"The dashboard will now load this automatically.")
        st.rerun()

# --- Continue with dashboard only if master data is loaded ---
if master_exists:
    df = df.sort_values(["Player Name", "Session Date"])

    # Create a unique session identifier using date + name
    df["Session ID"] = df["Session Date"].dt.strftime("%Y-%m-%d") + " | " + df["Session Name"]

    # For gameday sessions, only use "Total" rows (not First Half / Second Half)
    df_analysis = df[
        (df["Session Type"] == "Practice") |
        ((df["Session Type"] == "Gameday") & (df["Drill Title"] == "Total"))
    ].copy()

    # --- Sidebar Filters ---
    st.sidebar.image(LOGO_URL, width=120)
    st.sidebar.markdown(f'<h2 style="color: {ROHDA_RED}; margin-top: 0.5rem;">Filters</h2>', unsafe_allow_html=True)

    seasons = sorted(df_analysis["Seizoen"].unique())
    selected_season = st.sidebar.selectbox("Season", seasons, index=len(seasons)-1)
    df_filtered = df_analysis[df_analysis["Seizoen"] == selected_season]

    # Get sessions sorted by date
    sessions_by_date = (
        df_filtered
        .sort_values("Session Date")
        .drop_duplicates(subset="Session ID", keep="first")
        [["Session Date", "Session Name", "Session ID", "Session Type"]]
    )
    all_session_ids = sessions_by_date["Session ID"].tolist()

    latest_session_id = all_session_ids[-1] if len(all_session_ids) > 0 else None

    # Session selector in sidebar — default to latest, but allow picking any session
    # Create readable labels: "Session Name (dd-mm-yyyy)"
    session_labels = {}
    for sid in reversed(all_session_ids):  # Reversed so latest is first
        date_part, name_part = sid.split(" | ")
        date_readable = pd.to_datetime(date_part).strftime("%d-%m-%Y")
        session_labels[sid] = f"{name_part}  ({date_readable})"

    st.sidebar.markdown("---")
    st.sidebar.markdown(f'**📍 Select activity:**')
    selected_session_id = st.sidebar.selectbox(
        "Activity",
        list(session_labels.keys()),
        index=0,  # First item = latest (because we reversed)
        format_func=lambda x: session_labels[x],
        label_visibility="collapsed"
    )

    selected_session_name = selected_session_id.split(" | ")[1]
    selected_session_date_str = selected_session_id.split(" | ")[0]

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**📊 Sessions this season:** {len(all_session_ids)}")
    st.sidebar.markdown(f"**👥 Players:** {df_filtered['Player Name'].nunique()}")

    # =====================================================
    # TAB 1: LATEST ACTIVITY OVERVIEW
    # =====================================================
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Activity Overview", "⚖️ A/C Ratios", "🚦 Squad Status", "🏆 Leaderboard"])

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

            # Summary metrics for the squad
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                avg_td = summary_data["Totale afstand"].mean()
                st.metric("Avg Total Distance", f"{avg_td:,.0f} m")
            with col2:
                avg_hid = summary_data["Hoge intensiteit afstand"].mean()
                st.metric("Avg High Intensity Dist.", f"{avg_hid:,.0f} m")
            with col3:
                avg_dpm = summary_data["Afstand per minuut"].mean()
                st.metric("Avg Distance/Min", f"{avg_dpm:.0f} m/min")
            with col4:
                avg_dsl = summary_data["DSL"].mean()
                st.metric("Avg DSL", f"{avg_dsl:.0f}")

            st.markdown("---")

            # Bar chart per player for each metric
            st.markdown(f'<div class="section-header">Player Breakdown</div>', unsafe_allow_html=True)
            selected_metric = st.selectbox(
                "Select metric to visualize",
                list(METRICS.keys()),
                format_func=lambda x: METRICS[x]
            )

            chart_data = summary_data[["Player Name", selected_metric]].sort_values(selected_metric, ascending=True)

            fig = px.bar(
                chart_data,
                x=selected_metric,
                y="Player Name",
                orientation="h",
                title=f"{METRICS[selected_metric]} — {selected_session_name}",
                color=selected_metric,
                color_continuous_scale=[ROHDA_YELLOW, ROHDA_RED],
            )
            fig.update_layout(
                height=max(400, len(chart_data) * 30),
                showlegend=False,
                yaxis_title="",
                xaxis_title=METRICS[selected_metric],
                font=dict(family="Arial, sans-serif"),
                plot_bgcolor="white",
                paper_bgcolor="white",
                title_font_color=ROHDA_RED,
                title_font_size=16,
            )
            fig.update_xaxes(gridcolor="#f0f0f0")
            fig.update_yaxes(gridcolor="#f0f0f0")
            st.plotly_chart(fig, use_container_width=True)

            # Raw data table
            with st.expander("📋 View raw data for this session"):
                display_cols = ["Player Name", "Totale afstand", "Hoge intensiteit afstand", "Afstand per minuut", "DSL"]
                st.dataframe(
                    summary_data[display_cols].sort_values("Player Name").reset_index(drop=True),
                    use_container_width=True
                )

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

        # --- Toggle filters ---
        toggle_col1, toggle_col2 = st.columns(2)
        with toggle_col1:
            show_overload_only = st.toggle("🔴 Show only overload risk (ratio > 1.3)", value=False)
        with toggle_col2:
            latest_activity_only = st.toggle("📍 Latest activity players only", value=False)

        st.markdown("")

        # Determine which players to include
        if latest_activity_only:
            latest_players = df_filtered[df_filtered["Session ID"] == selected_session_id]["Player Name"].unique()
            players = sorted(latest_players)
        else:
            players = sorted(df_filtered["Player Name"].unique())

        ac_results = []

        for player in players:
            player_data = df_filtered[df_filtered["Player Name"] == player].sort_values("Session Date")
            if len(player_data) < 2:
                continue

            ratios = calculate_ac_ratios(player_data, list(METRICS.keys()))
            row = {"Player": player}
            has_overload = False
            for metric_key, metric_label in METRICS.items():
                ratio = ratios.get(metric_key)
                if ratio is not None:
                    row[f"{metric_label}"] = ratio
                    row[f"{metric_label}_status"] = get_ac_status(ratio)
                    row[f"{metric_label}_icon"] = get_ac_color(ratio)
                    if ratio > 1.3:
                        has_overload = True
                else:
                    row[f"{metric_label}"] = None
                    row[f"{metric_label}_status"] = "N/A"
                    row[f"{metric_label}_icon"] = "⚪"
            row["_has_overload"] = has_overload

            # Apply overload filter
            if show_overload_only and not has_overload:
                continue

            ac_results.append(row)

        if ac_results:
            ac_df = pd.DataFrame(ac_results)

            # Sort: danger/watch players first, then safe
            def risk_sort_key(row):
                statuses = []
                for metric_label in METRICS.values():
                    s = row.get(f"{metric_label}_status", "N/A")
                    if s == "Danger":
                        return 0
                    elif s == "Watch":
                        statuses.append(1)
                if 1 in statuses:
                    return 1
                return 2

            ac_results_sorted = sorted(ac_results, key=risk_sort_key)

            display_data = []
            for row in ac_results_sorted:
                display_row = {"Player": row["Player"]}
                for metric_label in METRICS.values():
                    ratio = row.get(metric_label)
                    icon = row.get(f"{metric_label}_icon", "")
                    if ratio is not None:
                        display_row[metric_label] = f"{icon} {ratio:.2f}"
                    else:
                        display_row[metric_label] = "⚪ N/A"
                display_data.append(display_row)

            display_df = pd.DataFrame(display_data)

            # Show count summary
            n_danger = sum(1 for r in ac_results_sorted if r.get("_has_overload", False))
            n_total = len(ac_results_sorted)
            if show_overload_only:
                st.markdown(f"Showing **{n_total} player(s)** with overload risk (ratio > 1.3)")
            else:
                st.markdown(f"Showing **{n_total} players** — **{n_danger}** with overload risk")

            st.dataframe(display_df, use_container_width=True, hide_index=True)

            # Detailed view per player
            st.markdown("---")
            st.markdown(f'<div class="section-header">Detailed Player View</div>', unsafe_allow_html=True)

            detail_col1, detail_col2 = st.columns([2, 1])
            with detail_col1:
                player_list_for_detail = [r["Player"] for r in ac_results_sorted]
                selected_player = st.selectbox("Select a player", player_list_for_detail)
            with detail_col2:
                session_type_filter = st.selectbox("Session type", ["All", "Gameday", "Practice"])

            player_data = df_filtered[df_filtered["Player Name"] == selected_player].sort_values("Session Date")

            # Apply session type filter
            if session_type_filter != "All":
                player_data_display = player_data[player_data["Session Type"] == session_type_filter]
            else:
                player_data_display = player_data

            if len(player_data) >= 2:
                player_ratios = calculate_ac_ratios(player_data, list(METRICS.keys()))

                cols = st.columns(4)
                for i, (metric_key, metric_label) in enumerate(METRICS.items()):
                    ratio = player_ratios.get(metric_key)
                    if ratio is not None:
                        status = get_ac_status(ratio)
                        icon = get_ac_color(ratio)
                        cols[i].metric(
                            metric_label,
                            f"{icon} {ratio:.2f}",
                            delta=f"{status}",
                            delta_color="off"
                        )
                    else:
                        cols[i].metric(metric_label, "N/A")

                st.markdown(f"##### Last 6 sessions ({session_type_filter})")
                last_sessions = player_data_display.tail(6)
                if len(last_sessions) > 0:
                    session_display = last_sessions[["Session Date", "Session Name", "Session Type"] + list(METRICS.keys())].copy()
                    session_display["Session Date"] = session_display["Session Date"].dt.strftime("%d-%m-%Y")
                    session_display = session_display.rename(columns=METRICS)
                    st.dataframe(session_display.reset_index(drop=True), use_container_width=True, hide_index=True)
                else:
                    st.info(f"No {session_type_filter.lower()} sessions found for this player.")
            else:
                st.info("Not enough data for this player to calculate A/C ratios (need at least 2 sessions).")
        else:
            if show_overload_only:
                st.success("No players with overload risk — everyone is in the safe zone!")
            else:
                st.info("Not enough data to calculate A/C ratios.")

    # =====================================================
    # TAB 3: SQUAD STATUS OVERVIEW
    # =====================================================
    with tab3:
        st.markdown(f'<div class="section-header">🚦 Squad Status Overview</div>', unsafe_allow_html=True)
        st.markdown("Player cards showing current A/C ratio status across all 4 metrics.")

        st.markdown("---")

        if ac_results:
            # Categorize players into 4 groups
            overload_players = []
            underload_players = []
            watch_players = []
            safe_players = []

            for row in ac_results:
                player = row["Player"]
                has_overload = False
                has_underload = False
                has_watch = False
                
                player_metrics = {}
                for metric_label in METRICS.values():
                    ratio = row.get(metric_label)
                    status = row.get(f"{metric_label}_status", "N/A")
                    icon = row.get(f"{metric_label}_icon", "⚪")
                    player_metrics[metric_label] = {"ratio": ratio, "status": status, "icon": icon}
                    
                    if status == "Danger":
                        has_overload = True
                    elif status == "Under-trained":
                        has_underload = True
                    elif status == "Watch":
                        has_watch = True
                
                player_info = {"player": player, "metrics": player_metrics}
                
                if has_overload:
                    overload_players.append(player_info)
                elif has_underload:
                    underload_players.append(player_info)
                elif has_watch:
                    watch_players.append(player_info)
                else:
                    safe_players.append(player_info)

            # Summary counts
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🔴 Overload", len(overload_players))
            with col2:
                st.metric("🔵 Underload", len(underload_players))
            with col3:
                st.metric("🟠 Watch", len(watch_players))
            with col4:
                st.metric("🟢 Safe", len(safe_players))

            st.markdown("---")

            # --- FIFA-style player cards using single HTML blocks ---
            def render_player_card(player_info, card_color, border_color, badge_text, badge_bg):
                """Generate HTML for a compact FIFA-style player card."""
                name = player_info["player"]
                m = player_info["metrics"]
                
                # Build metric lines as a simple table
                metric_lines = ""
                for label, data in m.items():
                    ratio = data["ratio"]
                    icon = data["icon"]
                    short_label = label.replace("Total Distance", "TD").replace("High Intensity Distance", "HID").replace("Distance Per Minute", "DPM").replace("Dynamic Stress Load", "DSL")
                    if ratio is not None:
                        metric_lines += f"<tr><td style='color:#aaa;font-size:0.75rem;padding:2px 4px;'>{short_label}</td><td style='text-align:right;font-weight:700;font-size:0.85rem;padding:2px 4px;'>{icon} {ratio:.2f}</td></tr>"
                    else:
                        metric_lines += f"<tr><td style='color:#aaa;font-size:0.75rem;padding:2px 4px;'>{short_label}</td><td style='text-align:right;font-size:0.85rem;padding:2px 4px;'>⚪ N/A</td></tr>"
                
                return (
                    f"<div style='background:linear-gradient(145deg,{card_color},#1a1a2e);border:2px solid {border_color};"
                    f"border-radius:12px;padding:0.8rem;color:white;box-shadow:0 4px 12px rgba(0,0,0,0.3);margin-bottom:0.5rem;'>"
                    f"<table style='width:100%;border:none;border-collapse:collapse;'>"
                    f"<tr><td style='font-size:0.95rem;font-weight:700;padding-bottom:6px;'>{name}</td>"
                    f"<td style='text-align:right;'><span style='background:{badge_bg};color:white;font-size:0.6rem;"
                    f"font-weight:700;padding:2px 6px;border-radius:3px;letter-spacing:0.5px;'>{badge_text}</span></td></tr>"
                    f"{metric_lines}"
                    f"</table></div>"
                )

            def render_card_grid(players, card_color, border_color, badge_text, badge_bg, cols_per_row=4):
                """Render a grid of player cards."""
                if not players:
                    return
                # Build all cards as one HTML block
                cards_html = "<div style='display:grid;grid-template-columns:" + " ".join(["1fr"] * min(cols_per_row, len(players))) + ";gap:0.5rem;'>"
                for p in players:
                    cards_html += render_player_card(p, card_color, border_color, badge_text, badge_bg)
                cards_html += "</div>"
                st.markdown(cards_html, unsafe_allow_html=True)

            # Render all categories
            if overload_players:
                st.markdown("### 🔴 Overload Risk")
                render_card_grid(overload_players, "#4a0e0e", ROHDA_RED, "OVERLOAD", "#c62828", 4)
            else:
                st.success("No players with overload risk!")

            st.markdown("")

            if underload_players:
                st.markdown("### 🔵 Underload Risk")
                render_card_grid(underload_players, "#0e1a4a", "#1565c0", "UNDERLOAD", "#1565c0", 4)

            st.markdown("")

            if watch_players:
                st.markdown("### 🟠 Watch")
                render_card_grid(watch_players, "#3e2f0e", ROHDA_YELLOW, "WATCH", "#f57f17", 4)

            st.markdown("")

            if safe_players:
                st.markdown("### 🟢 Safe")
                render_card_grid(safe_players, "#0e2e0e", ROHDA_GREEN, "SAFE", "#2e7d32", 5)
        else:
            st.info("Upload data with at least 2 sessions per player to see the squad status.")

    # =====================================================
    # TAB 4: LEADERBOARD
    # =====================================================
    with tab4:
        st.markdown(f'<div class="section-header">🏆 Leaderboard — Season {selected_season}</div>', unsafe_allow_html=True)

        st.markdown("---")

        # --- Helper: render a leaderboard as a styled HTML table ---
        def render_leaderboard(title, data, metric_label, unit="", emoji="🏆"):
            """Render a top-5 leaderboard as styled HTML. One entry per player."""
            rows = ""
            for i, (_, row) in enumerate(data.head(5).iterrows()):
                name = row["Player Name"]
                value = row[metric_label]
                bg = "rgba(255,209,0,0.1)" if i == 0 else "transparent"
                bold = "font-weight:700;" if i == 0 else ""
                rows += (
                    f"<tr style='background:{bg};'>"
                    f"<td style='padding:6px 8px;font-size:0.9rem;width:30px;color:{ROHDA_YELLOW};font-weight:700;'>{i+1}.</td>"
                    f"<td style='padding:6px 8px;{bold}'>{name}</td>"
                    f"<td style='padding:6px 8px;text-align:right;{bold}font-size:1rem;'>{value:,.0f} {unit}</td>"
                    f"</tr>"
                )
            
            return (
                f"<div style='background:linear-gradient(145deg,#1a1a2e,#2a2a4e);border-radius:12px;"
                f"padding:1rem;color:white;box-shadow:0 4px 12px rgba(0,0,0,0.3);margin-bottom:0.5rem;'>"
                f"<div style='font-size:1rem;font-weight:700;margin-bottom:0.6rem;color:{ROHDA_YELLOW};'>"
                f"{emoji} {title}</div>"
                f"<table style='width:100%;border-collapse:collapse;'>{rows}</table>"
                f"</div>"
            )

        # =========================
        # ACCUMULATED TOTALS
        # =========================
        st.markdown("### 📊 Accumulated Season Totals")
        st.markdown("Total values accumulated across all sessions this season.")
        st.markdown("")

        # Calculate accumulated totals per player
        acc = df_filtered.groupby("Player Name").agg({
            "Totale afstand": "sum",
            "Hoge intensiteit afstand": "sum",
            "DSL": "sum",
        }).reset_index()

        # Also count sessions per player
        acc["Sessions"] = df_filtered.groupby("Player Name")["Session ID"].nunique().values

        # Calculate average DPM (can't sum distance per minute, so average it)
        acc_dpm = df_filtered.groupby("Player Name")["Afstand per minuut"].mean().reset_index()

        acc_col1, acc_col2 = st.columns(2)
        
        with acc_col1:
            top_td = acc.sort_values("Totale afstand", ascending=False)
            st.markdown(render_leaderboard(
                "Most Total Distance", top_td, "Totale afstand", "m", "🏃"
            ), unsafe_allow_html=True)

        with acc_col2:
            top_hid = acc.sort_values("Hoge intensiteit afstand", ascending=False)
            st.markdown(render_leaderboard(
                "Most High Intensity Distance", top_hid, "Hoge intensiteit afstand", "m", "⚡"
            ), unsafe_allow_html=True)

        acc_col3, acc_col4 = st.columns(2)

        with acc_col3:
            top_dsl = acc.sort_values("DSL", ascending=False)
            st.markdown(render_leaderboard(
                "Most Dynamic Stress Load", top_dsl, "DSL", "", "💪"
            ), unsafe_allow_html=True)

        with acc_col4:
            top_sessions = acc.sort_values("Sessions", ascending=False)
            st.markdown(render_leaderboard(
                "Most Sessions Played", top_sessions, "Sessions", "", "📅"
            ), unsafe_allow_html=True)

        st.markdown("---")

        # =========================
        # PEAK PERFORMERS
        # =========================
        st.markdown("### ⚡ Peak Performers")
        st.markdown("Highest single-session values achieved this season.")
        st.markdown("")

        # For each metric, find the top 5 single-session values (one per player — their best)
        peak_data = df_filtered[["Player Name", "Session Name", "Session Date", "Session Type",
                                  "Totale afstand", "Hoge intensiteit afstand", 
                                  "Afstand per minuut", "DSL"]].copy()

        def get_peak_per_player(data, metric_col):
            """Get each player's single best session for a metric."""
            idx = data.groupby("Player Name")[metric_col].idxmax()
            return data.loc[idx].sort_values(metric_col, ascending=False)

        def render_peak_leaderboard(title, data, metric_col, unit="", emoji="⚡"):
            """Render a peak performance leaderboard. One entry per player (their best session)."""
            top5 = data.head(5)
            rows = ""
            for i, (_, row) in enumerate(top5.iterrows()):
                name = row["Player Name"]
                value = row[metric_col]
                session = row["Session Name"]
                date = row["Session Date"].strftime("%d-%m-%Y")
                bg = "rgba(255,209,0,0.1)" if i == 0 else "transparent"
                bold = "font-weight:700;" if i == 0 else ""
                rows += (
                    f"<tr style='background:{bg};'>"
                    f"<td style='padding:5px 8px;font-size:0.9rem;width:30px;color:{ROHDA_YELLOW};font-weight:700;'>{i+1}.</td>"
                    f"<td style='padding:5px 8px;{bold}'>{name}</td>"
                    f"<td style='padding:5px 8px;text-align:right;{bold}font-size:1rem;'>{value:,.0f} {unit}</td>"
                    f"<td style='padding:5px 8px;text-align:right;color:#aaa;font-size:0.75rem;'>{session}<br>{date}</td>"
                    f"</tr>"
                )
            
            return (
                f"<div style='background:linear-gradient(145deg,#1a1a2e,#2a2a4e);border-radius:12px;"
                f"padding:1rem;color:white;box-shadow:0 4px 12px rgba(0,0,0,0.3);margin-bottom:0.5rem;'>"
                f"<div style='font-size:1rem;font-weight:700;margin-bottom:0.6rem;color:{ROHDA_YELLOW};'>"
                f"{emoji} {title}</div>"
                f"<table style='width:100%;border-collapse:collapse;'>{rows}</table>"
                f"</div>"
            )

        peak_col1, peak_col2 = st.columns(2)

        with peak_col1:
            peak_td = get_peak_per_player(peak_data, "Totale afstand")
            st.markdown(render_peak_leaderboard(
                "Highest Total Distance (single session)", peak_td, "Totale afstand", "m", "🏃"
            ), unsafe_allow_html=True)

        with peak_col2:
            peak_hid = get_peak_per_player(peak_data, "Hoge intensiteit afstand")
            st.markdown(render_peak_leaderboard(
                "Highest High Intensity Distance (single session)", peak_hid, "Hoge intensiteit afstand", "m", "⚡"
            ), unsafe_allow_html=True)

        peak_col3, peak_col4 = st.columns(2)

        with peak_col3:
            peak_dpm = get_peak_per_player(peak_data, "Afstand per minuut")
            st.markdown(render_peak_leaderboard(
                "Highest Distance Per Minute (single session)", peak_dpm, "Afstand per minuut", "m/min", "🔥"
            ), unsafe_allow_html=True)

        with peak_col4:
            peak_dsl = get_peak_per_player(peak_data, "DSL")
            st.markdown(render_peak_leaderboard(
                "Highest DSL (single session)", peak_dsl, "DSL", "", "💪"
            ), unsafe_allow_html=True)

    # --- Footer ---
    st.markdown(f"""
    <div class="rohda-footer">
        ROHDA Raalte — Player Load Dashboard v1.3 &nbsp; | &nbsp; © Jordi Koggel, Human Movement Scientist &nbsp; | &nbsp; Season {selected_season}
    </div>
    """, unsafe_allow_html=True)

else:
    if not master_exists:
        # --- First time setup info ---
        st.markdown("")

        st.markdown("---")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            ### 📊 Latest Activity
            See how the latest session looked across all 4 metrics for the whole squad.
            """)
        with col2:
            st.markdown(f"""
            ### ⚖️ A/C Ratios
            Compare each player's latest activity to their average of the previous 5 activities.
            """)
        with col3:
            st.markdown(f"""
            ### 🚦 Squad Status
            Quick red/orange/green overview of which players need attention.
            """)

        st.markdown("---")
        st.markdown("### How it works:")
        st.markdown("""
        1. **First time:** Upload your master Excel file — it gets saved locally
        2. **Every next time:** The dashboard loads your data automatically — no upload needed
        3. **Add new sessions:** Just upload the raw StatSports CSV — it gets merged automatically
        4. **Backups:** A backup is created before every merge, stored in the `/backups` folder
        """)

    # Footer
    st.markdown("""
    <div class="rohda-footer">
        ROHDA Raalte — Player Load Dashboard v1.3 &nbsp; | &nbsp; © Jordi Koggel, Human Movement Scientist
    </div>
    """, unsafe_allow_html=True)
