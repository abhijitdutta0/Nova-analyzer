# ─────────────────────────────────────────────────────────────────
# config.py
#
# ✏️  Edit this file to change app identity, model, and suggestions.
#     All visual/CSS customization lives in layout.py instead.
#
# ⚠️  Do NOT add setup_page() or CSS here — that's layout.py's job.
# ─────────────────────────────────────────────────────────────────

# ── App identity ──────────────────────────────────────────────────
APP_TITLE    = "NOVA"
APP_SUBTITLE = "Natural-language Optimized Visual Architect"
APP_ICON     = "✦"
GEMINI_MODEL = "gemini-2.5-flash"

# ── Quick query suggestions shown in sidebar ──────────────────────
# Dynamic ones (based on actual df columns) are added in layout.py.
# These are the static fallbacks always shown below the dynamic ones.
STATIC_SUGGESTIONS = [
    "Summarize the dataset",
    "Show correlation heatmap",
    "Identify outliers",
    "Show missing values summary",
]