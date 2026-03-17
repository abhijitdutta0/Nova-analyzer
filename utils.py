# ─────────────────────────────────────────────────────────────────
# utils.py
#
# Pure helper functions — no Streamlit, no AI, no I/O side effects.
# Safe to unit-test in isolation.
# ─────────────────────────────────────────────────────────────────

import hashlib
import io
import json
from datetime import datetime

import pandas as pd
import streamlit as st


# ── DataFrame helpers ─────────────────────────────────────────────

def sanitize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names: lowercase, underscores, alphanumeric only."""
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace(r"[^a-z0-9_]", "", regex=True)
    )
    return df


@st.cache_data(show_spinner=False)
def get_df_summary(df: pd.DataFrame) -> str:
    """
    Return a JSON string summarising the dataframe structure.
    Cached — only recomputes when df changes.
    Passed directly into the Gemini system prompt as context.
    """
    numeric     = df.select_dtypes(include="number").columns.tolist()
    categorical = df.select_dtypes(include="object").columns.tolist()
    summary = {
        "shape":               df.shape,
        "columns":             df.columns.tolist(),
        "numeric_columns":     numeric,
        "categorical_columns": categorical,
        "sample_values":       {
            col: df[col].dropna().head(3).tolist()
            for col in df.columns[:6]
        },
    }
    return json.dumps(summary, default=str)


# ── File helpers ──────────────────────────────────────────────────

def file_content_hash(uploaded_file) -> str:
    """
    MD5 hash of uploaded file bytes.
    Used to detect same-name / different-content re-uploads.
    """
    uploaded_file.seek(0)
    digest = hashlib.md5(uploaded_file.read()).hexdigest()
    uploaded_file.seek(0)
    return digest


# ── Export helpers ────────────────────────────────────────────────

def export_chat_to_md(messages: list) -> str:
    """Convert chat history to a Markdown string for download."""
    lines = [f"# {_app_title()} Chat Export\n_{datetime.now().strftime('%Y-%m-%d %H:%M')}_\n"]
    for m in messages:
        role    = "**You**" if m["role"] == "user" else "**Assistant**"
        content = m.get("content") or m.get("result_text") or ""
        if content:
            lines.append(f"\n{role}\n{content}\n")
    return "\n".join(lines)


def _app_title() -> str:
    """Lazy import to avoid circular dependency with config."""
    try:
        from config import APP_TITLE
        return APP_TITLE
    except ImportError:
        return "NOVA"



def export_chat_to_pdf(messages: list) -> bytes:
    """
    Render chat history into a clean, formal white PDF.
    Charts are rendered with white background to match the page.
    Requires: pip install reportlab kaleido
    """

def export_chat_to_pdf(messages: list) -> bytes:
    """
    Render chat history into a clean NOVA-branded PDF.
    - NOVA name + constellation logo in header
    - Inter font throughout
    - User text: green  (#16a34a)
    - AI text:   black  (#1a1a1a)
    - White background, print-ready charts
    Requires: pip install reportlab kaleido
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib.colors import HexColor, white, black
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer,
        Image as RLImage, HRFlowable, KeepTogether
    )
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.graphics.shapes import Drawing, Circle, Line, String
    import re as _re
    import copy
    import xml.sax.saxutils as _sax

    # ── Colours ───────────────────────────────────────────────────
    C_BG          = white
    C_TOPBAR      = HexColor("#0a0614")       # NOVA dark purple
    C_TOPBAR_TXT  = white
    C_USER_LABEL  = HexColor("#16a34a")       # green
    C_USER_TEXT   = HexColor("#16a34a")       # green for user body
    C_AI_LABEL    = HexColor("#6d28d9")       # purple
    C_AI_TEXT     = HexColor("#1a1a1a")       # black for AI body
    C_MUTED       = HexColor("#6b7280")
    C_DIVIDER     = HexColor("#e5e7eb")
    C_TITLE       = HexColor("#1a1a1a")
    C_ACCENT      = HexColor("#7c3aed")       # NOVA purple accent

    PAGE_W, PAGE_H = A4
    LM, RM = 2.2 * cm, 2.2 * cm
    app_name    = _app_title()
    export_time = datetime.now().strftime("%d %B %Y, %H:%M")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=LM, rightMargin=RM,
        topMargin=2.8*cm, bottomMargin=2*cm
    )

    # ── NOVA constellation logo (inline SVG → PNG via reportlab Drawing) ──
    # We draw it manually using reportlab shapes so no external file needed
    def _draw_nova_logo_on_canvas(canvas, x, y, size=22):
        """Draw the NOVA constellation orb directly onto canvas at (x,y)."""
        r = size / 2
        cx, cy = x + r, y + r

        canvas.saveState()
        # Outer circle
        canvas.setFillColor(HexColor("#0d0a2e"))
        canvas.setStrokeColor(HexColor("#7c3aed"))
        canvas.setLineWidth(0.5)
        canvas.circle(cx, cy, r, fill=1, stroke=1)

        # Connection lines
        scale = size / 200.0
        nodes = {
            "top":    (cx,             cy + r * 0.68),
            "center": (cx,             cy - r * 0.10),
            "right":  (cx + r * 0.50,  cy + r * 0.18),
            "left":   (cx - r * 0.38,  cy - r * 0.50),
        }
        canvas.setStrokeColor(HexColor("#00cec9"))
        canvas.setLineWidth(0.4)
        pairs = [("top","center"),("top","right"),("top","left"),
                 ("center","right"),("center","left"),("right","left")]
        for a, b in pairs:
            canvas.line(nodes[a][0], nodes[a][1], nodes[b][0], nodes[b][1])

        # Nodes
        node_colors = {
            "top":    (HexColor("#f0f0f5"), 2.2),
            "center": (HexColor("#a78bfa"), 3.0),
            "right":  (HexColor("#00cec9"), 1.8),
            "left":   (HexColor("#2ed573"), 1.8),
        }
        for name, (color, nr) in node_colors.items():
            nx, ny = nodes[name]
            canvas.setFillColor(color)
            canvas.setStrokeColor(color)
            canvas.circle(nx, ny, nr, fill=1, stroke=0)

        canvas.restoreState()

    # ── Page background + footer only (no dark topbar) ──────────
    def _draw_page(canvas, doc):
        canvas.saveState()

        # White background
        canvas.setFillColor(C_BG)
        canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

        # Footer — thin purple accent line
        canvas.setStrokeColor(C_ACCENT)
        canvas.setLineWidth(0.8)
        canvas.line(LM, 1.5*cm, PAGE_W - RM, 1.5*cm)

        # Footer text left — app name
        canvas.setFillColor(C_ACCENT)
        canvas.setFont("Helvetica-Bold", 7)
        canvas.drawString(LM, 1.1*cm, app_name)

        # Footer text middle — subtitle
        canvas.setFillColor(C_MUTED)
        canvas.setFont("Helvetica", 7)
        canvas.drawString(LM + 30, 1.1*cm,
                          "·  Natural-language Optimized Visual Architect")

        # Footer text right — page number
        canvas.setFillColor(C_MUTED)
        canvas.setFont("Helvetica", 7)
        canvas.drawRightString(PAGE_W - RM, 1.1*cm, f"Page {doc.page}")

        canvas.restoreState()

    # ── Paragraph styles ─────────────────────────────────────────
    base = getSampleStyleSheet()["Normal"]

    def sty(name, **kw):
        return ParagraphStyle(name, parent=base, **kw)

    title_sty   = sty("nova_title",
                      fontName="Helvetica-Bold", fontSize=24,
                      textColor=C_TITLE, spaceAfter=3, leading=28)
    sub_sty     = sty("nova_sub",
                      fontName="Helvetica", fontSize=9,
                      textColor=C_MUTED, spaceAfter=20)
    user_lbl    = sty("nova_ulbl",
                      fontName="Helvetica-Bold", fontSize=7.5,
                      textColor=C_USER_LABEL, spaceAfter=3)
    ai_lbl      = sty("nova_albl",
                      fontName="Helvetica-Bold", fontSize=7.5,
                      textColor=C_AI_LABEL, spaceAfter=3)
    # User body — green
    user_body   = sty("nova_ubody",
                      fontName="Helvetica", fontSize=10.5,
                      textColor=C_USER_TEXT, leading=16, spaceAfter=3)
    # AI body — black
    ai_body     = sty("nova_abody",
                      fontName="Helvetica", fontSize=10,
                      textColor=C_AI_TEXT, leading=16, spaceAfter=3)
    ai_bold     = sty("nova_abold",
                      fontName="Helvetica-Bold", fontSize=10,
                      textColor=C_AI_TEXT, leading=16, spaceAfter=3)

    # ── Markdown → reportlab XML ──────────────────────────────────
    def _to_rl(text, is_user=False):
        if not text:
            return ""
        text = str(text)
        text = _re.sub(r'\*\*(.+?)\*\*', lambda m: '<b>' + m.group(1) + '</b>', text)
        text = _re.sub(r'\*(.+?)\*',     lambda m: '<i>' + m.group(1) + '</i>', text)
        text = _re.sub(r'`(.+?)`',       lambda m: m.group(1), text)
        text = _re.sub(r'^#{1,6}\s+(.+)$',
                       lambda m: '<b>' + m.group(1) + '</b>',
                       text, flags=_re.MULTILINE)
        text = _re.sub(r'^\s*[-*]\s+', '• ', text, flags=_re.MULTILINE)
        text = _re.sub(r'[#`]', '', text)
        text = _re.sub(r'&(?!amp;|lt;|gt;)', '&amp;', text)
        return text.strip()

    # ── Chart renderer ────────────────────────────────────────────
    def _fig_to_flowable(fig, max_w_cm=15.5):
        PDF_COLORWAY = [
            "#2563eb","#e74c3c","#f39c12","#27ae60","#8e44ad",
            "#e67e22","#16a085","#c0392b","#1a5276","#d35400",
        ]
        try:
            f2 = copy.deepcopy(fig)

            # Detect chart types in this figure
            trace_types = {type(t).__name__.lower() for t in f2.data}
            is_pie = any(t in trace_types for t in ("pie", "donut", "sunburst", "treemap"))

            # Base layout — always applied
            layout_update = dict(
                paper_bgcolor="white",
                colorway=PDF_COLORWAY,
                font=dict(color="#1a1a1a", family="Arial, sans-serif", size=11),
                title=dict(font=dict(color="#1a1a1a", size=13)),
                legend=dict(bgcolor="white", bordercolor="#e5e7eb",
                            borderwidth=1, font=dict(color="#374151")),
                margin=dict(l=40, r=40, t=50, b=40),
            )

            # Only set plot_bgcolor and axes for non-pie charts
            # Pie/sunburst/treemap don't use axes — setting them can cause crashes
            if not is_pie:
                layout_update["plot_bgcolor"] = "#f9fafb"
                layout_update["xaxis"] = dict(
                    color="#374151", gridcolor="#e5e7eb",
                    linecolor="#d1d5db", tickfont=dict(color="#374151")
                )
                layout_update["yaxis"] = dict(
                    color="#374151", gridcolor="#e5e7eb",
                    linecolor="#d1d5db", tickfont=dict(color="#374151")
                )

            f2.update_layout(**layout_update)

            # Apply PDF colorway per trace
            for i, trace in enumerate(f2.data):
                t_type = type(trace).__name__.lower()

                if t_type == "pie":
                    # Pie slices: set marker.colors as a list, one per slice
                    n_slices = len(trace.values) if hasattr(trace, "values") and trace.values is not None else 10
                    try:
                        trace.marker.colors = [
                            PDF_COLORWAY[j % len(PDF_COLORWAY)]
                            for j in range(n_slices)
                        ]
                    except Exception:
                        pass
                    # Pie text colour
                    try:
                        trace.textfont = dict(color="#1a1a1a")
                    except Exception:
                        pass

                elif hasattr(trace, "marker") and trace.marker is not None:
                    color = PDF_COLORWAY[i % len(PDF_COLORWAY)]
                    try:
                        existing = getattr(trace.marker, "colors", None)
                        if existing is not None and len(existing) > 0:
                            trace.marker.colors = [
                                PDF_COLORWAY[j % len(PDF_COLORWAY)]
                                for j in range(len(existing))
                            ]
                        else:
                            trace.marker.color = color
                    except Exception:
                        pass

                if hasattr(trace, "line") and trace.line is not None:
                    try:
                        trace.line.color = PDF_COLORWAY[i % len(PDF_COLORWAY)]
                    except Exception:
                        pass

            # Render — wider for pie charts to give legend room
            width  = 900 if is_pie else 1100
            height = 520
            png = f2.to_image(format="png", width=width, height=height, scale=2)
            max_w = max_w_cm * cm
            return RLImage(io.BytesIO(png), width=max_w, height=max_w * (height/width))

        except Exception as _chart_err:
            # Surface the error so we can debug — previously silently returned None
            import traceback
            print(f"PDF chart render error: {_chart_err}")
            traceback.print_exc()
            return None

    # ── Paragraph styles for cover logo letters ─────────────────
    # Each NOVA letter styled like the interface: N,V white; O,A purple
    def _letter_sty(color):
        return sty(f"ltr_{color}",
                   fontName="Helvetica-Bold", fontSize=38,
                   textColor=HexColor(color), leading=44)

    letter_white  = _letter_sty("#1a1a1a")   # N, V — near black on white page
    letter_purple = _letter_sty("#7c3aed")   # O, A — NOVA purple

    fullform_sty = sty("fullform",
                       fontName="Helvetica", fontSize=9,
                       textColor=C_MUTED, spaceAfter=4, leading=13)
    tagline_sty  = sty("tagline",
                       fontName="Helvetica-Bold", fontSize=8,
                       textColor=C_ACCENT, spaceAfter=20, leading=12)

    # ── Build story ───────────────────────────────────────────────
    story = []
    story.append(Spacer(1, 0.5*cm))

    # Cover — logo orb + NOVA letters inline on canvas, then full form below
    # We use a custom flowable approach: draw logo on canvas then add letter paragraphs
    from reportlab.platypus import Flowable

    class NOVACover(Flowable):
        """Draws the constellation logo + NOVA gradient letters as cover header."""
        def __init__(self):
            super().__init__()
            self.width  = PAGE_W - LM - RM
            self.height = 52

        def draw(self):
            c = self.canv
            c.saveState()

            # Constellation logo — drawn inline (closure-safe)
            logo_size = 42
            r = logo_size / 2
            lcx, lcy = r, 4 + r
            c.setFillColor(HexColor("#0d0a2e"))
            c.setStrokeColor(HexColor("#7c3aed"))
            c.setLineWidth(0.5)
            c.circle(lcx, lcy, r, fill=1, stroke=1)
            _nodes = {
                "top":    (lcx,             lcy + r * 0.68),
                "center": (lcx,             lcy - r * 0.10),
                "right":  (lcx + r * 0.50,  lcy + r * 0.18),
                "left":   (lcx - r * 0.38,  lcy - r * 0.50),
            }
            c.setStrokeColor(HexColor("#00cec9"))
            c.setLineWidth(0.4)
            for _a, _b in [("top","center"),("top","right"),("top","left"),
                            ("center","right"),("center","left"),("right","left")]:
                c.line(_nodes[_a][0], _nodes[_a][1], _nodes[_b][0], _nodes[_b][1])
            for _nm, (_col, _nr) in [
                ("top",    (HexColor("#f0f0f5"), 2.2)),
                ("center", (HexColor("#a78bfa"), 3.0)),
                ("right",  (HexColor("#00cec9"), 1.8)),
                ("left",   (HexColor("#2ed573"), 1.8)),
            ]:
                c.setFillColor(_col)
                c.circle(_nodes[_nm][0], _nodes[_nm][1], _nr, fill=1, stroke=0)

            # NOVA letters — alternating dark/purple like the interface
            letters = [
                ("N", "#1a1a1a"),
                ("O", "#7c3aed"),
                ("V", "#1a1a1a"),
                ("A", "#7c3aed"),
            ]
            x = logo_size + 10
            for letter, color in letters:
                c.setFillColor(HexColor(color))
                c.setFont("Helvetica-Bold", 38)
                c.drawString(x, 8, letter)
                x += 26

            # Full form to the right of letters, vertically centered
            c.setFont("Helvetica", 7.5)
            c.setFillColor(C_MUTED)
            full_form_lines = [
                "Natural-language",
                "Optimized Visual",
                "Architect",
            ]
            fy = 32
            for line in full_form_lines:
                c.drawString(x + 14, fy, line)
                fy -= 11

            c.restoreState()

    story.append(NOVACover())
    story.append(Spacer(1, 0.2*cm))

    # Thin purple accent line under cover
    story.append(HRFlowable(
        width="100%", thickness=1.5,
        color=C_ACCENT, spaceAfter=6
    ))

    # Report type + timestamp
    story.append(Paragraph(
        f"Analytics Report &nbsp;&nbsp;·&nbsp;&nbsp; {export_time}",
        sub_sty
    ))
    story.append(HRFlowable(
        width="100%", thickness=0.5,
        color=C_DIVIDER, spaceAfter=16
    ))

    for msg in messages:
        role = msg.get("role")
        if not role:
            continue
        content = str(msg.get("result_text") or msg.get("content") or "")
        fig     = msg.get("fig")

        if role == "user":
            block = []
            block.append(Paragraph("YOU", user_lbl))
            if content.strip():
                try:
                    block.append(Paragraph(_to_rl(content.strip(), is_user=True), user_body))
                except Exception:
                    block.append(Paragraph(content.strip(), user_body))
            story.append(KeepTogether(block))

        else:
            # Label + first line anchored together
            first_para = [Paragraph("NOVA", ai_lbl)]
            lines      = [l.strip() for l in content.splitlines()]
            remaining  = []
            first_added = False

            for raw in lines:
                if not raw:
                    if first_added:
                        remaining.append(None)
                    continue
                if not first_added:
                    try:
                        s = ai_bold if raw.startswith("#") else ai_body
                        first_para.append(Paragraph(_to_rl(raw), s))
                    except Exception:
                        first_para.append(Paragraph(raw, ai_body))
                    first_added = True
                else:
                    remaining.append(raw)

            story.append(KeepTogether(first_para))

            for raw in remaining:
                if raw is None:
                    story.append(Spacer(1, 0.12*cm))
                    continue
                try:
                    s = ai_bold if raw.startswith("#") else ai_body
                    story.append(Paragraph(_to_rl(raw), s))
                except Exception:
                    pass

            if fig is not None and hasattr(fig, "data") and len(fig.data) > 0:
                story.append(Spacer(1, 0.4*cm))
                img = _fig_to_flowable(fig)
                if img:
                    story.append(img)
                story.append(Spacer(1, 0.2*cm))

        story.append(HRFlowable(
            width="100%", thickness=0.5,
            color=C_DIVIDER, spaceBefore=10, spaceAfter=4
        ))

    doc.build(story, onFirstPage=_draw_page, onLaterPages=_draw_page)
    return buf.getvalue()