# ─────────────────────────────────────────────────────────────────
# app.py
#
# Entry point — run with: streamlit run app.py
#
# Thin orchestrator — wires together all modules:
#   layout.py  ← all UI / NOVA visual code        ✏️ edit freely
#   config.py  ← app name, model, suggestions     ✏️ edit freely
#   data.py    ← CSV / Excel / SQLite / Postgres   ✏️ add sources
#   utils.py   ← helpers, PDF export              ✏️ add helpers
#   logic.py   ← Gemini AI + exec sandbox         ⚠️ don't touch
# ─────────────────────────────────────────────────────────────────

import os
import re

import streamlit as st
from dotenv import load_dotenv
from google import genai

# ── Load API key — works both locally and on Streamlit Cloud ────────
# Local: reads from .env file next to app.py
# Streamlit Cloud: reads from st.secrets (set in app Settings → Secrets)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
# Inject st.secrets into os.environ so the rest of the code works unchanged
try:
    if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
        os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

# ── Local modules ─────────────────────────────────────────────────
from config import GEMINI_MODEL, STATIC_SUGGESTIONS
from data import (
    POSTGRES_AVAILABLE,
    get_sqlite_tables,
    load_csv, load_excel,
    load_from_sqlite, load_from_postgres,
)
from logic import call_gemini, execute_ai_code
from utils import (
    file_content_hash,
    export_chat_to_md,
    export_chat_to_pdf,
)
from layout import (
    nova_page_setup,
    render_topbar,
    render_sidebar,
    render_messages,
    render_empty_state,
    render_message,
)


# ─────────────────────────────────────────────────────────────────
# PAGE SETUP — must be the very first Streamlit call
# ─────────────────────────────────────────────────────────────────
nova_page_setup()


# ─────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "datasets" not in st.session_state:
    st.session_state.datasets = {}
if "active_dataset" not in st.session_state:
    st.session_state.active_dataset = None


# ─────────────────────────────────────────────────────────────────
# GEMINI CLIENT — init once per session, stored in session_state
# Bare globals reset on hot-reload; session_state persists.
# ─────────────────────────────────────────────────────────────────
if "client" not in st.session_state:
    # Check os.environ first (loaded from .env locally),
    # then fall back to st.secrets (Streamlit Cloud deployment)
    API_KEY = os.environ.get("GEMINI_API_KEY")
    if not API_KEY:
        try:
            API_KEY = st.secrets["GEMINI_API_KEY"]
        except (KeyError, FileNotFoundError):
            API_KEY = None
    if not API_KEY:
        st.error(
            "⚠️ GEMINI_API_KEY not found.\n\n"
            "**Local:** Create a `.env` file next to `app.py`:\n"
            "```\nGEMINI_API_KEY=your_key_here\n```\n\n"
            "**Streamlit Cloud:** Go to App Settings → Secrets and add:\n"
            "```\nGEMINI_API_KEY = \"your_key_here\"\n```"
        )
        st.stop()
    st.session_state.client = genai.Client(api_key=API_KEY)


# ─────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────
render_sidebar(
    load_csv_fn=load_csv,
    load_excel_fn=load_excel,
    load_sqlite_fn=load_from_sqlite,
    load_postgres_fn=load_from_postgres,
    get_sqlite_tables_fn=get_sqlite_tables,
    file_hash_fn=file_content_hash,
    export_md_fn=export_chat_to_md,
    export_pdf_fn=export_chat_to_pdf,
    postgres_available=POSTGRES_AVAILABLE,
    static_suggestions=STATIC_SUGGESTIONS,
)


# ─────────────────────────────────────────────────────────────────
# TOPBAR
# ─────────────────────────────────────────────────────────────────
render_topbar()


# ─────────────────────────────────────────────────────────────────
# MAIN AREA
# ─────────────────────────────────────────────────────────────────
# Resolve active df — always from active_dataset for multi-file support
df = None
if st.session_state.get("active_dataset") and st.session_state.get("datasets"):
    entry = st.session_state.datasets.get(st.session_state.active_dataset)
    if entry:
        df = entry["df"]
        st.session_state.df = df  # keep session_state.df in sync
elif st.session_state.get("df") is not None:
    df = st.session_state.df  # fallback for SQLite/Postgres sources

# Empty state — no data loaded yet
if df is None:
    render_empty_state()
    st.stop()

# ── Render existing chat history ──────────────────────────────────
render_messages(st.session_state.messages)

# ── Chat input ────────────────────────────────────────────────────
prompt = st.chat_input("Ask anything about your data...")

# Quick query buttons in sidebar inject via pending_prompt
if not prompt and st.session_state.get("pending_prompt"):
    prompt = st.session_state.pop("pending_prompt")

if prompt:
    # 1. Append + render user message immediately
    st.session_state.messages.append(
        {"role": "user", "content": prompt, "result_text": None, "fig": None}
    )
    render_message(
        {"role": "user", "content": prompt},
        idx=len(st.session_state.messages),
    )

    # 2. Call Gemini + execute generated code
    with st.spinner("Analyzing…"):
        try:
            resp_text = call_gemini(
                st.session_state.client,
                df,
                st.session_state.messages,
                prompt,
            )

            resp_text = resp_text or ""
            code_match  = re.search(r"```[Pp]ython\s*\n(.*?)```", resp_text, re.DOTALL)
            result_text = "Analysis complete."
            current_fig = None

            if code_match:
                try:
                    result_text, current_fig = execute_ai_code(code_match.group(1), df)

                except ValueError as blocked_err:
                    # AST scanner blocked unsafe code — retry once with correction prompt
                    try:
                        retry_resp = call_gemini(
                            st.session_state.client, df,
                            st.session_state.messages,
                            (
                                f"Your previous code was blocked by the safety scanner. "
                                f"Reason: {blocked_err}. "
                                f"Rewrite WITHOUT any import statements, eval(), exec(), "
                                f"open(), or os calls. All libraries (pd, px, go, np, df, "
                                f"make_subplots) are already available. "
                                f"Original request: {prompt}"
                            ),
                        )
                        retry_match = re.search(
                            r"```[Pp]ython\s*\n(.*?)```", retry_resp, re.DOTALL
                        )
                        if retry_match:
                            result_text, current_fig = execute_ai_code(
                                retry_match.group(1), df
                            )
                        else:
                            result_text = retry_resp
                    except Exception:
                        result_text = (
                            "I wasn't able to complete that analysis safely. "
                            "Could you rephrase the request?"
                        )

                except RuntimeError as exec_err:
                    result_text = f"⚠️ Execution error: {exec_err}"

            else:
                # No code block — plain text response
                result_text = resp_text

            # 3. Render assistant bubble immediately
            render_message(
                {
                    "role":        "assistant",
                    "content":     result_text,
                    "result_text": result_text,
                    "fig":         current_fig,
                },
                idx=len(st.session_state.messages) + 1,
            )

            # 4. Commit assistant message to session state
            st.session_state.messages.append({
                "role":        "assistant",
                "content":     result_text,
                "result_text": result_text,
                "fig":         current_fig,
            })

            # 5. Generate PDF after message is fully committed.
            #    st.rerun() follows so the sidebar re-renders with
            #    fresh _pdf_bytes — without rerun the sidebar already
            #    rendered with the previous cached PDF.
            try:
                st.session_state["_pdf_bytes"] = export_chat_to_pdf(
                    st.session_state.messages
                )
                st.session_state.pop("_pdf_error", None)
            except Exception as pdf_err:
                st.session_state["_pdf_error"] = str(pdf_err)
                st.session_state.pop("_pdf_bytes", None)

            st.rerun()

        except Exception as e:
            st.error(f"Agent error: {e}")