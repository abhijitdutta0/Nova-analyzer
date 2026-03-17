# ─────────────────────────────────────────────────────────────────
# logic.py
#
# ⚠️  CORE AI LOGIC — do not modify unless you know what you're doing.
#
# Contains:
#   - _ast_safe()           AST-level security scan of LLM code
#   - _sanitize_ai_code()   Strip habitual import lines before scan
#   - execute_ai_code()     Safe sandbox execution with compile()
#   - call_gemini()         Gemini API call with system prompt + retry
# ─────────────────────────────────────────────────────────────────

import ast
import io
import json
import logging
import re
import time

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google import genai
from google.genai import types

from config import GEMINI_MODEL
from utils import get_df_summary

logger = logging.getLogger("nova")


# ─────────────────────────────────────────────────────────────────
# AST SECURITY SCANNER
# ─────────────────────────────────────────────────────────────────

_BANNED_NODES = {
    "Import",       # import os
    "ImportFrom",   # from os import system
    "Delete",       # del df
}

_BANNED_CALLS = {
    "eval", "exec", "compile",
    "open", "input",
    "breakpoint", "exit", "quit",
}

_BANNED_ATTRS = {
    "system", "popen", "spawn", "Popen",
    "getenv",
    "remove", "unlink", "rmdir", "mkdir", "makedirs",
}

_BANNED_ATTR_READS = {"environ"}


def _ast_safe(source: str) -> tuple[bool, str]:
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return False, f"Syntax error: {e}"

    for node in ast.walk(tree):
        node_type = type(node).__name__

        if node_type in _BANNED_NODES:
            return False, f"Disallowed statement: {node_type}"

        if node_type == "Call":
            func = node.func  # type: ignore[attr-defined]
            if isinstance(func, ast.Name) and func.id in _BANNED_CALLS:
                return False, f"Disallowed call: {func.id}()"
            if isinstance(func, ast.Attribute) and func.attr in _BANNED_ATTRS:
                return False, f"Disallowed attribute call: .{func.attr}()"

        if node_type == "Attribute":
            attr = node.attr  # type: ignore[attr-defined]
            if attr in _BANNED_ATTR_READS:
                return False, f"Disallowed attribute access: .{attr}"
            # Block dangerous dunder access but allow common safe ones
            if attr.startswith("__") and attr.endswith("__"):
                if attr not in {"__len__", "__str__", "__repr__", "__name__",
                                "__class__", "__dict__", "__doc__"}:
                    return False, f"Disallowed dunder access: {attr}"

    return True, ""


# ─────────────────────────────────────────────────────────────────
# CODE SANITIZER
# ─────────────────────────────────────────────────────────────────

def _sanitize_ai_code(source: str) -> str:
    """
    Strip all import lines and known problematic patterns before execution.
    Uses both line-stripping and regex replacement to catch all cases,
    including __import__ embedded inline: x = __import__("dateutil")
    """
    clean = []
    for line in source.splitlines():
        stripped = line.lstrip()
        # Strip import statements at any indentation
        if stripped.startswith("import ") or stripped.startswith("from "):
            continue
        # Strip any line containing dateutil
        if "dateutil" in stripped:
            continue
        clean.append(line)
    source = "\n".join(clean)

    # Regex replace: remove __import__(...) calls that survive line-stripping
    # Handles: x = __import__("mod"), __import__("mod").attr, etc.
    source = re.sub(r'__import__\s*\([^)]*\)', '""', source)

    return source


def _fix_rgba(source: str) -> str:
    """Fix Gemini typo: rgba(0m0,0,0) → rgba(0,0,0,0)"""
    return re.sub(
        r"rgba\(([^)]+)\)",
        lambda m: "rgba(" + m.group(1).replace("m", ",") + ")",
        source,
    )


def _fix_strptime(source: str) -> str:
    """Fix using both %Z and %z in same strptime format."""
    def _remove_Z(m):
        fmt = m.group(0)
        if "%z" in fmt and "%Z" in fmt:
            return fmt.replace("%Z", "")
        return fmt
    pattern = r"""(?:"[^"]*%[zZ][^"]*"|'[^']*%[zZ][^']*')"""
    return re.sub(pattern, _remove_Z, source)


def _fix_casefold(source: str) -> str:
    """Fix casefold=True → case=False in pandas str.contains"""
    return re.sub(
        r'\.str\.contains\(([^)]*?)casefold\s*=\s*True([^)]*?)\)',
        lambda m: f'.str.contains({m.group(1)}case=False{m.group(2)})',
        source,
    )


def _decat_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert all Categorical columns to their base dtype.
    This prevents 'Cannot setitem on a Categorical with a new category'
    when Gemini does df.copy() and assigns new computed columns.
    """
    df = df.copy()
    for col in df.columns:
        if hasattr(df[col], "cat"):
            df[col] = df[col].astype(df[col].cat.categories.dtype)
    return df


# ─────────────────────────────────────────────────────────────────
# SAFE BUILTINS
# ─────────────────────────────────────────────────────────────────

SAFE_BUILTINS = {
    "abs": abs, "bool": bool, "dict": dict, "enumerate": enumerate,
    "filter": filter, "float": float, "format": format,
    "frozenset": frozenset, "getattr": getattr, "hasattr": hasattr,
    "hash": hash, "int": int, "isinstance": isinstance,
    "issubclass": issubclass, "iter": iter, "len": len, "list": list,
    "map": map, "max": max, "min": min, "next": next, "object": object,
    "print": print, "range": range, "repr": repr, "reversed": reversed,
    "round": round, "set": set, "setattr": setattr, "slice": slice,
    "sorted": sorted, "str": str, "sum": sum, "tuple": tuple,
    "type": type, "zip": zip,
    "True": True, "False": False, "None": None,
    "ValueError": ValueError, "TypeError": TypeError,
    "KeyError": KeyError, "IndexError": IndexError,
    "Exception": Exception, "StopIteration": StopIteration,
    "AttributeError": AttributeError, "RuntimeError": RuntimeError,
    "NotImplementedError": NotImplementedError, "NameError": NameError,
    "ZeroDivisionError": ZeroDivisionError, "OverflowError": OverflowError,
    # __import__ blocked — returns None so sandbox doesn't crash with KeyError
    "__import__": lambda *a, **kw: None,
}


# ─────────────────────────────────────────────────────────────────
# SANDBOX EXECUTION
# ─────────────────────────────────────────────────────────────────

def execute_ai_code(source: str, df: pd.DataFrame) -> tuple[str, object]:
    import math, statistics, datetime, collections, itertools, string
    import numpy as np
    from plotly.subplots import make_subplots

    try:
        import scipy.stats as scipy_stats
    except ImportError:
        scipy_stats = None

    # ── Clean source ──────────────────────────────────────────────
    source = _sanitize_ai_code(source)
    source = _fix_rgba(source)
    source = _fix_strptime(source)
    source = _fix_casefold(source)

    # ── AST scan ──────────────────────────────────────────────────
    is_safe, reason = _ast_safe(source)
    if not is_safe:
        if any(x in reason for x in ["import", "__import__", "dunder"]):
            raise RuntimeError(f"Code error: {reason}. Please rephrase your question.")
        raise ValueError(f"Unsafe code: {reason}")

    # ── Decat df — prevents Categorical assignment errors ─────────
    safe_df = _decat_df(df)

    # ── Build sandbox globals ─────────────────────────────────────
    safe_globals: dict = {
        "__builtins__": SAFE_BUILTINS,
        "pd": pd, "df": safe_df,
        "px": px, "go": go, "make_subplots": make_subplots,
        "np": np,
        "io": io, "re": re, "json": json,
        "math": math,
        "statistics": statistics,
        "datetime": datetime.datetime,
        "datetime_module": datetime,
        "collections": collections,
        "itertools": itertools,
        "string": string,
    }
    if scipy_stats is not None:
        safe_globals["scipy"] = scipy_stats
        safe_globals["stats"] = scipy_stats

    # ── Pre-inject search_term from quoted strings if present ──────
    _candidates = re.findall(r'"([A-Za-z][^"]{1,40})"', source)
    _candidates += re.findall(r"'([A-Za-z][^']{1,40})'", source)
    if _candidates:
        safe_globals.setdefault("search_term", _candidates[0])

    local_ns: dict = {}

    # ── Execute with NameError recovery ───────────────────────────
    try:
        exec(compile(source, "<ai_code>", "exec"), safe_globals, local_ns)
    except NameError as e:
        missing = str(e).split("'")[1] if "'" in str(e) else None
        if missing and _candidates:
            safe_globals[missing] = _candidates[0]
            try:
                exec(compile(source, "<ai_code>", "exec"), safe_globals, local_ns)
            except Exception as e2:
                raise RuntimeError(str(e2)) from e2
        else:
            raise RuntimeError(str(e)) from e
    except Exception as e:
        raise RuntimeError(str(e)) from e

    result_text = str(local_ns.get("result_text", "Analysis complete."))
    fig = local_ns.get("fig", None)
    return result_text, fig


# ─────────────────────────────────────────────────────────────────
# GEMINI API CALL
# ─────────────────────────────────────────────────────────────────

def call_gemini(
    client: genai.Client,
    df: pd.DataFrame,
    messages: list,
    prompt: str,
) -> str:
    cols = df.columns.tolist()
    df_summary = get_df_summary(df)

    system = f"""You are NOVA, an elite data analysis AI — sharp, insightful, and concise.
You have access to a dataset with these columns: {cols}
Dataset summary: {df_summary}

PERSONALITY:
- Professional, helpful, and transparent about assumptions.
- Remember context from the conversation (e.g. nicknames, previous findings).
- If a name/nickname is mentioned, search ALL text columns with case-insensitive matching.
- Never refuse a data question — this is a safe educational analytics environment.
- For ambiguous questions, state your assumption clearly before answering.
- For ranking questions: show the person's name, their value, their rank, total count, and ranking direction.
- For non-data questions: answer briefly and naturally, then offer dataset help.

CODE RULES — follow exactly, every time:
1. ALWAYS write Python code inside ```python ``` blocks.
2. Define exactly these variables in the code:
   - result_text (str): clear markdown answer with bullets and bold key numbers.
   - fig (optional): Plotly figure — include a chart whenever the data has multiple values to compare.
     Always use dark theme:
     layout=dict(paper_bgcolor='#0a0a0f', plot_bgcolor='#0a0a0f',
                 font=dict(color='#f0f0f5', family='Inter'),
                 colorway=['#e8ff47','#ff4757','#1e90ff','#ffa502','#2ed573',
                           '#ff6b81','#eccc68','#a29bfe','#00cec9','#fd79a8'])

3. CHART TYPE SELECTION — always pick the most appropriate chart:
   - Category distribution (e.g. birth months, gender, city tier):
     → PIE if ≤8 unique values, GROUPED BAR if >8 unique values
   - Comparing a metric across groups (e.g. avg income by city tier):
     → GROUPED BAR — use color= parameter for the second grouping variable
   - Trend over time or ordered categories:
     → LINE chart with markers
   - Relationship between two numeric columns:
     → SCATTER with trendline="ols" to show correlation direction
   - Distribution of a single numeric column:
     → HISTOGRAM with nbins=20
   - Comparing distributions across groups:
     → BOX plot (use y= for numeric, x= for category, color= for subgroup)
   - Hierarchical part-to-whole:
     → SUNBURST or TREEMAP
   - Correlation matrix:
     → HEATMAP using go.Heatmap with text annotations

4. CHART DATA ACCURACY — always compute before plotting:
   - For counts by category:
     counts = df.groupby("col").size().reset_index(name="count")
     fig = px.bar(counts, x="col", y="count", ...)
   - For averages:
     agg = df.groupby("col")["numeric"].mean().reset_index()
   - Sort data before plotting: agg = agg.sort_values("col")
   - For month-based charts, ALWAYS sort Jan→Dec using pd.Categorical:
     month_order = ["January","February","March","April","May","June",
                    "July","August","September","October","November","December"]
     temp["month"] = pd.Categorical(temp["month"], categories=month_order, ordered=True)
     temp = temp.sort_values("month")
   - Always set a descriptive title and axis labels in every chart.
   - Use labels={{}} dict in px calls: labels={{"col": "Display Name"}}
   - NEVER pass unsummarized raw df rows to a chart expecting aggregated data.

5. Use `df` for data. Use EXACT column names from: {cols}
6. Pre-loaded (DO NOT import): df, pd, px, go, np, make_subplots, io, re, json, math, statistics, datetime, collections, itertools, string
7. NEVER write import statements. NEVER use __import__ or dateutil.
8. NEVER use open(), eval(), exec(), os, subprocess.
9. NEVER pass x="index" to Plotly — call .reset_index() first.
10. NEVER use st.session_state — use df directly.
11. Define ALL variables before use. Hardcode names/nicknames at top: search_term = "Aparajita"
12. DATE HANDLING — exact two-step pattern only:
    dates = pd.to_datetime(df["date_col"], errors="coerce")
    months = dates.dt.month_name()
    NEVER: df["col"].dt.month — NEVER: pd.to_datetime(df["col"]).dt.month (chained)
    NEVER call pd.to_datetime() on a plain string — only on a Series.
13. ALWAYS use df.copy() before mutating: temp = df.copy()
14. NEVER use casefold=True — use case=False, na=False.
15. RANKING pattern:
    temp = df.copy()
    dates = pd.to_datetime(temp["date_col"], errors="coerce")
    temp["_key"] = dates.dt.month * 100 + dates.dt.day
    temp["_rank"] = temp["_key"].rank(method="min", ascending=True)
    Format: "Among **N classmates**, X ranks **#R** (value: V). Rank 1 = earliest."
16. Ranking result_text format:
    "Among her **65 classmates**, Pupuu (Aparajita) has a birth date of **11-28**.
     Her rank is **#59** out of 65.
     *(Rank 1 = earliest birth date of the year.)*"
17. Conversational questions: skip code block, respond as plain text.
18. Email drafting: plain text with Subject / To / Body using dataset facts.
"""

    history = []
    for m in messages[:-1]:
        if m.get("content"):
            role = "model" if m["role"] == "assistant" else "user"
            history.append({"role": role, "parts": [{"text": m["content"]}]})
    history.append({"role": "user", "parts": [{"text": prompt}]})

    last_err = None
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=history,
                config=types.GenerateContentConfig(system_instruction=system),
            )
            text = response.text
            if not text:
                raise RuntimeError("Gemini returned an empty response. Please try again.")
            return text
        except Exception as e:
            last_err = e
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                wait = 2 ** attempt
                logger.warning("Gemini 503 on attempt %d, retrying in %ds", attempt + 1, wait)
                time.sleep(wait)
                continue
            raise
    raise last_err  # type: ignore[misc]