# ─────────────────────────────────────────────────────────────────
# data.py
#
# All data ingestion — file parsing + database connections.
# No UI code here. Each loader raises exceptions on failure;
# the UI layer (ui.py) is responsible for showing error messages.
# ─────────────────────────────────────────────────────────────────

import io
import re
import sqlite3

import pandas as pd

from utils import sanitize_columns

# ── Optional PostgreSQL ───────────────────────────────────────────
try:
    import psycopg2
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


# ── CSV / Excel ───────────────────────────────────────────────────

def load_csv(uploaded_file) -> pd.DataFrame:
    """
    Robustly parse a CSV from a Streamlit UploadedFile.

    Handles:
    - Safari webarchive format (bplist00 wrapper) — extracts CSV from <pre> tag
    - Windows BOM (utf-8-sig)
    - Windows-1252 / Latin-1 encodings
    - Auto-detects delimiter (comma, semicolon, tab, pipe)
    """
    uploaded_file.seek(0)
    raw_bytes = uploaded_file.read()

    # ── Unwrap Safari/browser webarchive ─────────────────────────
    # Files saved via "Save Page As" in Safari start with bplist00
    # (binary plist) and embed the real CSV inside an HTML <pre> tag.
    if raw_bytes[:7] == b"bplist0" or b"<pre" in raw_bytes[:2000]:
        match = re.search(b"<pre[^>]*>(.*?)</pre>", raw_bytes, re.DOTALL)
        if match:
            raw_bytes = match.group(1)
        else:
            raise ValueError(
                "This file looks like a browser-saved web page, not a CSV. "
                "Please download the original CSV file directly."
            )

    # ── Decode bytes ──────────────────────────────────────────────
    # utf-8-sig  → strips BOM that Excel/Notepad prepends on Windows
    # cp1252     → Windows-1252, default on most Windows systems
    # latin-1    → superset of first 256 Unicode points, never fails
    decoded = None
    for enc in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
        try:
            decoded = raw_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue

    if decoded is None:
        raise ValueError("Could not decode file with any supported encoding.")

    # ── Parse with auto-delimiter ─────────────────────────────────
    # sep=None + engine='python' lets pandas detect comma/semicolon/tab/pipe.
    df = pd.read_csv(io.StringIO(decoded), sep=None, engine="python")
    return sanitize_columns(df)


def load_excel(uploaded_file) -> pd.DataFrame:
    return sanitize_columns(pd.read_excel(uploaded_file))


# ── SQLite ────────────────────────────────────────────────────────

def get_sqlite_tables(db_path: str) -> list:
    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    conn.close()
    return tables


def load_from_sqlite(db_path: str, table: str) -> pd.DataFrame:
    """Load a table from SQLite. Table name is whitelisted to prevent injection."""
    allowed = get_sqlite_tables(db_path)
    if table not in allowed:
        raise ValueError(f"Table '{table}' not found in database.")
    conn = sqlite3.connect(db_path)
    df   = pd.read_sql_query(f'SELECT * FROM "{table}"', conn)
    conn.close()
    return sanitize_columns(df)


# ── PostgreSQL ────────────────────────────────────────────────────

def load_from_postgres(dsn: str, table: str) -> pd.DataFrame:
    """Load a table from PostgreSQL. Table name is whitelisted to prevent injection."""
    if not POSTGRES_AVAILABLE:
        raise ImportError("psycopg2 not installed. Run: pip install psycopg2-binary")

    conn = psycopg2.connect(dsn)
    cur  = conn.cursor()
    cur.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
    )
    allowed = [r[0] for r in cur.fetchall()]
    if table not in allowed:
        conn.close()
        raise ValueError(f"Table '{table}' not found in database.")

    df = pd.read_sql_query(f'SELECT * FROM "{table}"', conn)
    conn.close()
    return sanitize_columns(df)
