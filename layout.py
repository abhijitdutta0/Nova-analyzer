# ─────────────────────────────────────────────────────────────────
# layout.py
#
# ✏️  ALL visual customization lives here — NOVA purple glass theme.
#     Edit this file freely to change look & feel.
#
# ⚠️  No AI logic, no data loading, no PDF generation here.
#     This file only renders what it is given.
# ─────────────────────────────────────────────────────────────────

import re
import streamlit as st


# ─────────────────────────────────────────────────────────────────
# NOVA LOGO — neural constellation orb matching the brand logo
# ─────────────────────────────────────────────────────────────────

def nova_logo_svg(size: int = 48) -> str:
    """Return the NOVA constellation logo as an inline SVG string."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" '
        f'width="{size}" height="{size}">'
        '<defs>'
          '<radialGradient id="obg" cx="50%" cy="50%" r="50%">'
            '<stop offset="0%" stop-color="#0d0a2e"/>'
            '<stop offset="100%" stop-color="#060412"/>'
          '</radialGradient>'
          '<radialGradient id="cglow" cx="50%" cy="50%" r="50%">'
            '<stop offset="0%" stop-color="rgba(130,80,230,0.5)"/>'
            '<stop offset="100%" stop-color="rgba(130,80,230,0)"/>'
          '</radialGradient>'
          '<filter id="bg" x="-80%" y="-80%" width="260%" height="260%">'
            '<feGaussianBlur stdDeviation="5" result="b"/>'
            '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>'
          '</filter>'
          '<filter id="sg" x="-100%" y="-100%" width="300%" height="300%">'
            '<feGaussianBlur stdDeviation="8" result="b"/>'
            '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>'
          '</filter>'
        '</defs>'
        '<circle cx="100" cy="100" r="95" fill="url(#obg)" stroke="rgba(120,80,220,0.4)" stroke-width="1.2"/>'
        '<circle cx="100" cy="118" r="44" fill="url(#cglow)" opacity="0.65"/>'
        '<circle cx="100" cy="100" r="62" fill="none" stroke="rgba(100,70,200,0.28)" stroke-width="0.8" stroke-dasharray="4 5"/>'
        '<g stroke="rgba(100,180,200,0.32)" stroke-width="0.85" fill="none">'
          '<line x1="100" y1="30"  x2="100" y2="118"/>'
          '<line x1="100" y1="30"  x2="150" y2="82"/>'
          '<line x1="100" y1="30"  x2="60"  y2="150"/>'
          '<line x1="150" y1="82"  x2="100" y2="118"/>'
          '<line x1="150" y1="82"  x2="60"  y2="150"/>'
          '<line x1="100" y1="118" x2="60"  y2="150"/>'
          '<line x1="100" y1="118" x2="110" y2="165"/>'
          '<line x1="60"  y1="150" x2="55"  y2="80"/>'
          '<line x1="150" y1="82"  x2="158" y2="110"/>'
        '</g>'
        '<circle cx="100" cy="30"  r="18" fill="rgba(160,140,255,0.12)" filter="url(#sg)"/>'
        '<circle cx="100" cy="30"  r="8"  fill="white" filter="url(#bg)"/>'
        '<circle cx="100" cy="30"  r="4"  fill="white"/>'
        '<circle cx="100" cy="118" r="22" fill="rgba(110,60,220,0.18)" filter="url(#sg)"/>'
        '<circle cx="100" cy="118" r="11" fill="rgba(190,170,255,0.88)" filter="url(#bg)"/>'
        '<circle cx="100" cy="118" r="5.5" fill="white"/>'
        '<circle cx="150" cy="82"  r="12" fill="rgba(0,220,200,0.12)" filter="url(#sg)"/>'
        '<circle cx="150" cy="82"  r="6"  fill="rgba(0,220,190,0.9)"  filter="url(#bg)"/>'
        '<circle cx="150" cy="82"  r="3"  fill="rgba(200,255,245,1)"/>'
        '<circle cx="60"  cy="150" r="12" fill="rgba(0,210,130,0.12)" filter="url(#sg)"/>'
        '<circle cx="60"  cy="150" r="6"  fill="rgba(0,210,120,0.88)" filter="url(#bg)"/>'
        '<circle cx="60"  cy="150" r="3"  fill="rgba(200,255,215,1)"/>'
        '<circle cx="55"  cy="80"  r="3"  fill="rgba(180,160,255,0.5)"/>'
        '<circle cx="158" cy="110" r="2.5" fill="rgba(0,200,180,0.55)"/>'
        '<circle cx="110" cy="165" r="3"  fill="rgba(0,200,180,0.45)"/>'
        '<circle cx="78"  cy="55"  r="2"  fill="rgba(200,180,255,0.38)"/>'
        '</svg>'
    )


# ─────────────────────────────────────────────────────────────────
# PAGE SETUP
# ─────────────────────────────────────────────────────────────────

def nova_page_setup():
    """Call once at the very top of app.py before anything else."""
    st.set_page_config(
        page_title="NOVA – Natural-language Optimized Visual Architect",
        page_icon="✦",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
        font-family: 'Inter', 'Segoe UI', sans-serif !important;
        background: linear-gradient(135deg, #0a0614 0%, #0e0a22 40%, #080618 100%) !important;
    }
    [data-testid="stApp"]::before {
        content: ''; position: fixed; top: -100px; left: 0;
        width: 400px; height: 400px; border-radius: 50%;
        background: radial-gradient(circle, rgba(80,40,180,0.14) 0%, transparent 70%);
        pointer-events: none; z-index: 0;
    }
    [data-testid="stApp"]::after {
        content: ''; position: fixed; bottom: -80px; right: 200px;
        width: 350px; height: 350px; border-radius: 50%;
        background: radial-gradient(circle, rgba(100,50,200,0.10) 0%, transparent 70%);
        pointer-events: none; z-index: 0;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: rgba(14,10,30,0.92) !important;
        backdrop-filter: blur(16px) !important;
        border-right: 1px solid rgba(100,60,200,0.22) !important;
    }
    [data-testid="stSidebarContent"] { padding: 12px 14px !important; }
    [data-testid="stSidebar"] .stSelectbox > div > div {
        background: rgba(20,14,45,0.75) !important;
        border: 1px solid rgba(100,60,200,0.28) !important;
        border-radius: 7px !important;
        color: rgba(190,175,240,0.95) !important;
        font-size: 12px !important;
    }
    [data-testid="stSidebar"] .stButton > button {
        background: rgba(30,20,60,0.65) !important;
        border: 1px solid rgba(100,60,200,0.28) !important;
        border-radius: 7px !important;
        color: rgba(200,185,255,0.92) !important;
        font-size: 11px !important;
        font-family: 'Inter', sans-serif !important;
        padding: 6px 12px !important;
        width: 100% !important;
        text-align: left !important;
        transition: all 0.18s ease !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(50,30,90,0.75) !important;
        border-color: rgba(130,80,230,0.48) !important;
        box-shadow: 0 0 12px rgba(130,80,230,0.18) !important;
    }

    /* ── File uploader ── */
    [data-testid="stFileUploader"] {
        border: 1.5px dashed rgba(100,60,200,0.4) !important;
        border-radius: 9px !important;
        background: rgba(20,14,45,0.42) !important;
        padding: 10px !important;
    }

    /* ── Section labels ── */
    .nova-label {
        color: rgba(140,110,220,0.85); font-size: 9px; font-weight: 700;
        letter-spacing: 0.14em; text-transform: uppercase;
        margin-bottom: 6px; display: block;
    }

    /* ── Stat cards ── */
    .stat-card {
        background: rgba(20,14,42,0.65); border: 1px solid rgba(100,60,200,0.22);
        border-radius: 9px; padding: 10px 12px;
        backdrop-filter: blur(8px); text-align: center;
    }
    .stat-value {
        color: rgba(220,210,255,0.97); font-size: 22px;
        font-weight: 800; line-height: 1.1;
    }
    .stat-key {
        color: rgba(130,100,220,0.75); font-size: 9px; font-weight: 700;
        letter-spacing: 0.12em; text-transform: uppercase;
    }

    /* ── Topbar ── */
    .nova-topbar {
        display: flex; align-items: center; justify-content: space-between;
        padding: 10px 20px; border-bottom: 1px solid rgba(80,50,160,0.22);
        background: rgba(8,5,20,0.55); backdrop-filter: blur(14px);
        margin: -1rem -1rem 1rem -1rem; position: sticky; top: 0; z-index: 100;
    }
    .nova-logo .n, .nova-logo .v {
        font-size: 26px; font-weight: 900; letter-spacing: -0.04em;
        background: linear-gradient(135deg, #fff 0%, rgba(220,200,255,0.95) 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .nova-logo .o, .nova-logo .a {
        font-size: 26px; font-weight: 900; letter-spacing: -0.04em;
        background: linear-gradient(135deg, rgba(180,140,255,0.97) 0%, rgba(120,70,230,0.92) 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .nova-pulse-dot {
        display: inline-block; width: 7px; height: 7px; border-radius: 50%;
        background: rgba(130,80,230,0.9); animation: nova-pulse 2s ease-in-out infinite;
        margin-right: 5px; vertical-align: middle;
    }
    @keyframes nova-pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

    /* ── Chat bubbles ── */
    .user-bubble {
        background: rgba(100,55,210,0.22); border: 1px solid rgba(120,70,220,0.32);
        border-radius: 13px; padding: 12px 16px; margin-bottom: 10px;
        display: flex; gap: 10px; align-items: flex-start;
        animation: fadeIn 0.3s ease forwards;
    }
    .ai-bubble {
        background: rgba(20,14,40,0.55); border: 1px solid rgba(80,50,160,0.22);
        border-radius: 13px; padding: 12px 16px; margin-bottom: 10px;
        display: flex; gap: 10px; align-items: flex-start;
        animation: fadeIn 0.3s ease forwards;
    }
    @keyframes fadeIn { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
    .user-icon {
        width:24px; height:24px; border-radius:7px;
        background:linear-gradient(135deg,#e04444,#c02020);
        display:flex; align-items:center; justify-content:center;
        flex-shrink:0; font-size:11px; color:white; font-weight:700;
    }
    .ai-icon {
        width:24px; height:24px; border-radius:7px;
        background:linear-gradient(135deg,#cc8822,#aa6600);
        display:flex; align-items:center; justify-content:center;
        flex-shrink:0; font-size:14px; color:white;
    }
    .bubble-text { color:rgba(190,175,240,0.92); font-size:13px; line-height:1.65; flex:1; }
    .bubble-text strong { color:rgba(215,200,255,1); font-weight:650; }
    .bullet { color:rgba(130,80,220,0.95); margin-right:6px; }

    /* ── File tag ── */
    .file-tag {
        background:rgba(20,14,40,0.75); border:1px solid rgba(100,60,200,0.22);
        border-radius:7px; padding:7px 10px; font-size:10px;
        color:rgba(160,145,210,0.88); display:flex; align-items:center;
        gap:6px; margin-bottom:12px;
    }

    /* ── Download buttons ── */
    [data-testid="stDownloadButton"] > button {
        background: rgba(30,20,60,0.65) !important;
        border: 1px solid rgba(100,60,200,0.28) !important;
        border-radius: 7px !important;
        color: rgba(200,185,255,0.92) !important;
        font-size: 11px !important;
        width: 100% !important;
    }
    [data-testid="stDownloadButton"] > button:hover {
        background: rgba(50,30,90,0.75) !important;
        border-color: rgba(130,80,230,0.48) !important;
    }

    /* ── Chat input ── */
    [data-testid="stChatInput"] {
        background: rgba(16,10,36,0.8) !important;
        border: 1px solid rgba(100,60,200,0.32) !important;
        border-radius: 11px !important;
        backdrop-filter: blur(10px) !important;
    }
    [data-testid="stChatInput"] textarea {
        color: rgba(200,185,255,0.93) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 13px !important;
    }
    [data-testid="stChatInput"] button {
        background: linear-gradient(135deg,rgba(110,60,210,0.92),rgba(70,30,160,0.92)) !important;
        border: 1px solid rgba(130,80,230,0.45) !important;
        border-radius: 8px !important;
    }

    /* ── Expander ── */
    [data-testid="stExpander"] {
        background: rgba(20,14,42,0.5) !important;
        border: 1px solid rgba(100,60,200,0.2) !important;
        border-radius: 7px !important;
    }

    /* ── Misc ── */
    footer { visibility: hidden; }
    hr { border-color: rgba(80,50,160,0.2) !important; }
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-thumb { background: rgba(100,60,200,0.32); border-radius: 99px; }
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# TOPBAR
# ─────────────────────────────────────────────────────────────────

def render_topbar():
    """Sticky NOVA logo bar with constellation icon, pulse dot and subtitle."""
    logo = nova_logo_svg(34)
    st.markdown(f"""
    <div class="nova-topbar">
      <div style="display:flex;align-items:center;gap:10px">
        {logo}
        <div class="nova-logo" style="display:inline-flex">
          <span class="n">N</span><span class="o">O</span><span class="v">V</span><span class="a">A</span>
        </div>
        <div style="display:flex;align-items:center;gap:6px">
          <span class="nova-pulse-dot"></span>
          <span style="color:rgba(130,100,200,0.72);font-size:9px;letter-spacing:0.09em;text-transform:uppercase">
            AI-POWERED · ANALYTICS · GEMINI 2.5 FLASH
          </span>
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:10px">
        <span style="color:rgba(100,80,180,0.62);font-size:9px">
          Natural-language Optimized Visual Architect
        </span>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# EMPTY STATE
# ─────────────────────────────────────────────────────────────────

def render_empty_state():
    """Shown in main area when no dataset is loaded yet."""
    logo = nova_logo_svg(120)
    st.markdown(f"""
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                padding:80px 20px;text-align:center">

      <!-- Constellation logo -->
      <div style="margin-bottom:20px;filter:drop-shadow(0 0 18px rgba(130,80,230,0.4))">
        {logo}
      </div>

      <!-- Greeting -->
      <div style="font-size:11px;font-weight:700;letter-spacing:0.18em;text-transform:uppercase;
                  color:rgba(130,80,230,0.85);margin-bottom:14px">
        Hello, I'm
      </div>
      <div style="display:inline-flex;margin-bottom:12px">
        <span style="font-size:42px;font-weight:900;letter-spacing:-0.04em;
                     background:linear-gradient(135deg,#fff 0%,rgba(220,200,255,0.95) 100%);
                     -webkit-background-clip:text;-webkit-text-fill-color:transparent">N</span>
        <span style="font-size:42px;font-weight:900;letter-spacing:-0.04em;
                     background:linear-gradient(135deg,rgba(180,140,255,0.97) 0%,rgba(120,70,230,0.92) 100%);
                     -webkit-background-clip:text;-webkit-text-fill-color:transparent">O</span>
        <span style="font-size:42px;font-weight:900;letter-spacing:-0.04em;
                     background:linear-gradient(135deg,#fff 0%,rgba(220,200,255,0.95) 100%);
                     -webkit-background-clip:text;-webkit-text-fill-color:transparent">V</span>
        <span style="font-size:42px;font-weight:900;letter-spacing:-0.04em;
                     background:linear-gradient(135deg,rgba(180,140,255,0.97) 0%,rgba(120,70,230,0.92) 100%);
                     -webkit-background-clip:text;-webkit-text-fill-color:transparent">A</span>
      </div>

      <!-- Tagline -->
      <div style="color:rgba(190,175,240,0.88);font-size:15px;font-weight:500;
                  line-height:1.6;max-width:440px;margin-bottom:10px">
        Your AI-powered data analyst. I turn natural language into insights,
        charts, and reports — instantly.
      </div>
      <div style="color:rgba(130,100,200,0.7);font-size:13px;margin-bottom:32px">
        How can I help you today?
      </div>

      <!-- Hint -->
      <div style="background:rgba(100,55,210,0.12);border:1px solid rgba(120,70,220,0.22);
                  border-radius:10px;padding:12px 24px;
                  color:rgba(160,145,210,0.75);font-size:11px;line-height:1.7">
        ⬅ Upload a <strong style="color:rgba(200,185,255,0.85)">CSV or Excel file</strong>
        from the sidebar to get started
      </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# MESSAGE RENDERING
# ─────────────────────────────────────────────────────────────────

def _format_ai_text(text: str) -> str:
    """
    Convert markdown-ish AI response text to styled HTML for bubble rendering.
    Handles: **bold**, bullet lines starting with •, blank lines.
    """
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    lines = text.split("\n")
    html_parts = []
    for line in lines:
        if line.startswith("• "):
            html_parts.append(
                f'<div style="display:flex;gap:8px;margin:3px 0">'
                f'<span class="bullet">•</span><span>{line[2:]}</span></div>'
            )
        elif line.strip() == "":
            html_parts.append('<div style="margin:4px 0"></div>')
        else:
            html_parts.append(f'<div style="margin:2px 0">{line}</div>')
    return "".join(html_parts)


def render_message(msg: dict, idx: int):
    """
    Render a single message bubble.

    msg keys:
      role        : "user" | "assistant"
      content     : raw text
      result_text : formatted AI response (used over content if present)
      fig         : Plotly Figure or None
    """
    role = msg.get("role")

    if role == "user":
        content = msg.get("content", "")
        st.markdown(
            f'<div class="user-bubble">'
            f'<div class="user-icon">U</div>'
            f'<div class="bubble-text">{content}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    elif role == "assistant":
        content = msg.get("result_text") or msg.get("content") or ""
        formatted = _format_ai_text(content)
        st.markdown(
            f'<div class="ai-bubble">'
            f'<div class="ai-icon">✦</div>'
            f'<div class="bubble-text">{formatted}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        fig = msg.get("fig")
        if fig is not None and hasattr(fig, "data") and len(fig.data) > 0:
            st.plotly_chart(
                fig,
                use_container_width=True,
                config={"displayModeBar": False},
                key=f"fig_{idx}",
            )


def render_messages(messages: list):
    """Render full chat history."""
    for idx, msg in enumerate(messages):
        if msg.get("role"):
            render_message(msg, idx)


# ─────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────

def render_sidebar(
    load_csv_fn,
    load_excel_fn,
    load_sqlite_fn,
    load_postgres_fn,
    get_sqlite_tables_fn,
    file_hash_fn,
    export_md_fn,
    export_pdf_fn,
    postgres_available: bool,
    static_suggestions: list,
):
    """
    Full NOVA sidebar.
    All loader/export functions are injected as arguments so layout.py
    stays fully independent of data.py and utils.py.
    """
    with st.sidebar:

        # ── Data Source ───────────────────────────────────────────
        st.markdown('<span class="nova-label">Data Source</span>', unsafe_allow_html=True)
        source = st.selectbox(
            "", ["CSV / Excel", "SQLite Database", "PostgreSQL"],
            label_visibility="collapsed",
        )

        # ── CSV / Excel — multi-file support ─────────────────────
        if source == "CSV / Excel":
            uploaded_files = st.file_uploader(
                "Drag and drop files here · Limit 200MB each",
                type=["csv", "xlsx"],
                accept_multiple_files=True,
                label_visibility="visible",
            )

            # Init datasets dict if not present
            if "datasets" not in st.session_state:
                st.session_state.datasets = {}  # {filename: df}
            if "active_dataset" not in st.session_state:
                st.session_state.active_dataset = None

            if uploaded_files:
                for uf in uploaded_files:
                    fhash = file_hash_fn(uf)
                    stored = st.session_state.datasets.get(uf.name)
                    # Load only if new or changed
                    if stored is None or stored.get("hash") != fhash:
                        try:
                            df_loaded = (
                                load_csv_fn(uf)
                                if uf.name.endswith(".csv")
                                else load_excel_fn(uf)
                            )
                            st.session_state.datasets[uf.name] = {
                                "df":   df_loaded,
                                "hash": fhash,
                                "size": round(uf.size / 1024 / 1024, 2),
                            }
                            # Auto-select if first file
                            if st.session_state.active_dataset is None:
                                st.session_state.active_dataset = uf.name
                        except Exception as e:
                            st.error(f"Load error ({uf.name}): {e}")

            # Remove datasets that were deselected from uploader
            if uploaded_files is not None:
                current_names = {uf.name for uf in uploaded_files}
                removed = [n for n in list(st.session_state.datasets)
                           if n not in current_names]
                for name in removed:
                    del st.session_state.datasets[name]
                if st.session_state.active_dataset in removed:
                    remaining = list(st.session_state.datasets.keys())
                    st.session_state.active_dataset = remaining[0] if remaining else None

            # Show loaded files + active selector
            if st.session_state.datasets:
                st.markdown("<div style='margin:6px 0 4px'></div>", unsafe_allow_html=True)
                st.markdown('<span class="nova-label">Loaded Files</span>',
                            unsafe_allow_html=True)
                for fname, meta in st.session_state.datasets.items():
                    short = (fname[:20] + "...") if len(fname) > 20 else fname
                    is_active = fname == st.session_state.active_dataset
                    border = "rgba(130,80,230,0.7)" if is_active else "rgba(100,60,200,0.22)"
                    icon   = "🟣" if is_active else "📄"
                    rows_n = len(meta["df"])
                    cols_n = len(meta["df"].columns)
                    col_a, col_b = st.columns([5, 1])
                    with col_a:
                        st.markdown(
                            f'<div style="background:rgba(20,14,42,0.65);border:1px solid {border};'
                            f'border-radius:7px;padding:5px 8px;font-size:9px;'
                            f'color:rgba(190,175,240,0.9);margin-bottom:4px">'
                            f'{icon} <b>{short}</b><br>'
                            f'<span style="color:rgba(130,100,220,0.7)">'
                            f'{rows_n:,} rows · {cols_n} cols · {meta["size"]}MB</span></div>',
                            unsafe_allow_html=True,
                        )
                    with col_b:
                        if not is_active:
                            if st.button("→", key=f"sel_{fname}",
                                         help=f"Switch to {fname}"):
                                st.session_state.active_dataset = fname
                                st.rerun()

            # Sync active df to session_state.df for rest of app
            if st.session_state.active_dataset and st.session_state.datasets:
                st.session_state.df = st.session_state.datasets[
                    st.session_state.active_dataset]["df"]
            elif not st.session_state.datasets:
                st.session_state.pop("df", None)
                st.session_state.active_dataset = None

        # ── SQLite ────────────────────────────────────────────────
        elif source == "SQLite Database":
            db_file = st.file_uploader(
                "Upload .db file", type=["db", "sqlite", "sqlite3"],
                label_visibility="visible",
            )
            if db_file:
                tmp_path = f"/tmp/{db_file.name}"
                with open(tmp_path, "wb") as f:
                    f.write(db_file.read())
                tables = get_sqlite_tables_fn(tmp_path)
                if tables:
                    table = st.selectbox("Table", tables)
                    if st.button("Load Table"):
                        try:
                            st.session_state.df = load_sqlite_fn(tmp_path, table)
                            st.session_state.messages = []
                            st.success(f"Loaded `{table}`")
                        except ValueError as e:
                            st.error(str(e))

        # ── PostgreSQL ────────────────────────────────────────────
        elif source == "PostgreSQL":
            if not postgres_available:
                st.warning("Install psycopg2: `pip install psycopg2-binary`")
            else:
                dsn   = st.text_input("Connection string", placeholder="postgresql://user:pass@host/db")
                table = st.text_input("Table name")
                if st.button("Connect & Load") and dsn and table:
                    try:
                        st.session_state.df = load_postgres_fn(dsn, table)
                        st.session_state.messages = []
                        st.success(f"Loaded `{table}`")
                    except Exception as e:
                        st.error(f"Connection error: {e}")

        st.markdown("<hr style='margin:10px 0'>", unsafe_allow_html=True)

        # ── Active dataset stats ───────────────────────────────────
        st.markdown('<span class="nova-label">Active Dataset</span>', unsafe_allow_html=True)
        df = st.session_state.get("df")

        # Show active file name badge
        active_name = st.session_state.get("active_dataset", "")
        if active_name:
            short_active = (active_name[:24] + "...") if len(active_name) > 24 else active_name
            st.markdown(
                f'<div style="font-size:9px;color:rgba(130,80,230,0.9);'
                f'margin-bottom:6px">🟣 {short_active}</div>',
                unsafe_allow_html=True,
            )

        rows = len(df) if df is not None else 0
        cols = len(df.columns) if df is not None else 0

        c1, c2 = st.columns(2)
        c1.markdown(
            f'<div class="stat-card"><div class="stat-key">ROWS</div>'
            f'<div class="stat-value">{rows:,}</div></div>',
            unsafe_allow_html=True,
        )
        c2.markdown(
            f'<div class="stat-card"><div class="stat-key">COLS</div>'
            f'<div class="stat-value">{cols}</div></div>',
            unsafe_allow_html=True,
        )

        if df is not None:
            st.markdown("<div style='margin:8px 0'></div>", unsafe_allow_html=True)
            with st.expander("Explore Columns"):
                for col in df.columns:
                    st.markdown(
                        f'<div style="color:rgba(150,130,210,0.82);font-size:9px;'
                        f'padding:2px 0;border-bottom:1px solid rgba(80,50,160,0.12)">'
                        f'{col}</div>',
                        unsafe_allow_html=True,
                    )

            # ── Quick queries ─────────────────────────────────────
            st.markdown("<hr style='margin:10px 0'>", unsafe_allow_html=True)
            st.markdown('<span class="nova-label">Quick Queries</span>', unsafe_allow_html=True)

            numeric_cols = df.select_dtypes(include="number").columns
            dynamic = [
                f"Show distribution of {df.columns[0]}",
                f"Find top 5 rows by {numeric_cols[0] if len(numeric_cols) else df.columns[0]}",
            ]
            for q in dynamic + list(static_suggestions):
                if st.button(q, key=f"qq_{q}"):
                    st.session_state.pending_prompt = q

        # ── Export — outside df guard so it always shows ────────
        if st.session_state.get("messages"):
            st.markdown("<hr style='margin:10px 0'>", unsafe_allow_html=True)
            st.markdown('<span class="nova-label">Export</span>', unsafe_allow_html=True)

            st.download_button(
                "📥  Chat log (MD)",
                data=export_md_fn(st.session_state.messages).encode(),
                file_name="nova_chat.md",
                mime="text/markdown",
                use_container_width=True,
            )

            pdf_bytes = st.session_state.get("_pdf_bytes")
            if pdf_bytes:
                st.download_button(
                    "📄  Chat PDF (with charts)",
                    data=pdf_bytes,
                    file_name="nova_report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            elif st.session_state.get("_pdf_error"):
                st.error(f"PDF error: {st.session_state['_pdf_error']}")
            else:
                st.caption("PDF generates after first response.")

        # ── Clear ─────────────────────────────────────────────────
        st.markdown("<hr style='margin:10px 0'>", unsafe_allow_html=True)
        if st.button("🗑  Clear conversation"):
            st.session_state.messages = []
            st.session_state.pop("_pdf_bytes", None)
            st.session_state.pop("_pdf_error", None)
            st.rerun()