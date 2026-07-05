"""
Custom CSS styles for the Eco Grant Writer Streamlit Chat UI.

Design System:
    Primary:    #0F172A  (slate-900)
    Surface:    #1E293B  (slate-800)
    Accent:     #22C55E  (green-500)
    Background: #020617  (slate-950)
    Text:       #F8FAFC  (slate-50)
    Muted:      #94A3B8  (slate-400)
    Typography: Fira Code (headings/mono) + Fira Sans (body)
"""


def get_font_links() -> str:
    """Returns <link> tags for Google Fonts."""
    return (
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link href="https://fonts.googleapis.com/css2?'
        'family=Fira+Code:wght@400;500;600;700'
        '&family=Fira+Sans:wght@300;400;500;600;700'
        '&display=swap" rel="stylesheet">'
    )


def get_styles() -> str:
    """Returns the complete CSS wrapped in a <style> block."""

    return """
<style>

/* ══════════════════════════════════════════════════════════════
   ECO GRANT WRITER — DESIGN TOKENS
   ══════════════════════════════════════════════════════════════ */

:root {
    --bg-deep:      #020617;
    --bg-surface:   #0F172A;
    --bg-card:      #1E293B;
    --bg-elevated:  #273549;
    --accent:       #22C55E;
    --accent-hover: #16A34A;
    --accent-glow:  rgba(34, 197, 94, 0.12);
    --accent-glow2: rgba(34, 197, 94, 0.06);
    --text-primary: #F8FAFC;
    --text-second:  #CBD5E1;
    --text-muted:   #94A3B8;
    --text-dim:     #64748B;
    --border:       #334155;
    --border-light: rgba(51, 65, 85, 0.5);
    --danger:       #EF4444;
    --warning:      #F59E0B;
    --info:         #3B82F6;
    --radius-xs:    6px;
    --radius-sm:    8px;
    --radius-md:    12px;
    --radius-lg:    20px;
    --radius-pill:  100px;
    --transition:   200ms ease;
    --font-body:    'Fira Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-mono:    'Fira Code', 'SF Mono', Consolas, monospace;
}


/* ── Global ──────────────────────────────────────────────── */

.stApp {
    background: var(--bg-deep) !important;
    font-family: var(--font-body) !important;
    color: var(--text-primary) !important;
}

/* Header bar styling - highly specific to override Emotion cache */
.stApp header[data-testid="stHeader"],
.stApp .stHeader,
.stApp header,
.stApp .stAppHeader,
.stApp div[class*="stAppHeader"],
div[class*="st-emotion-cache"] header,
header[class*="st-emotion-cache"] {
    background-color: rgba(2, 6, 23, 0.6) !important;
    backdrop-filter: blur(12px) !important;
    border-bottom: 1px solid var(--border-light) !important;
}

#MainMenu, footer {
    display: none !important;
}

h1, h2, h3, h4, h5, h6 {
    font-family: var(--font-mono) !important;
    color: var(--text-primary) !important;
}

a { color: var(--accent) !important; }


/* ── Scrollbar ───────────────────────────────────────────── */

::-webkit-scrollbar       { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-dim); }


/* ══════════════════════════════════════════════════════════════
   SIDEBAR
   ══════════════════════════════════════════════════════════════ */

section[data-testid="stSidebar"] {
    background: var(--bg-surface) !important;
    border-right: 1px solid var(--border) !important;
}

section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label {
    color: var(--text-second) !important;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    font-family: var(--font-mono) !important;
    color: var(--text-primary) !important;
}


/* ── Phase Tracker ───────────────────────────────────────── */

.phase-tracker { padding: 0 0 0.5rem 0; }

.phase-step {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 9px 14px;
    margin: 1px 0;
    border-radius: var(--radius-sm);
    font-size: 0.84rem;
    font-weight: 500;
    color: var(--text-dim);
    transition: all var(--transition);
}

.phase-step.active {
    background: var(--accent-glow);
    color: var(--accent);
    font-weight: 600;
}

.phase-step.completed { color: var(--accent); opacity: 0.75; }

.phase-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
    border: 2px solid var(--border);
    background: transparent;
}

.phase-step.active .phase-dot {
    border-color: var(--accent);
    background: var(--accent);
    box-shadow: 0 0 8px var(--accent);
    animation: pulseDot 2s infinite;
}

.phase-step.completed .phase-dot {
    border-color: var(--accent);
    background: var(--accent);
}

.phase-connector {
    width: 2px; height: 6px;
    background: var(--border);
    margin-left: 18px;
}
.phase-connector.done { background: var(--accent); }

@keyframes pulseDot {
    0%, 100% { box-shadow: 0 0 4px var(--accent); }
    50%      { box-shadow: 0 0 12px var(--accent), 0 0 24px var(--accent-glow); }
}


/* ── Snapshot Card ───────────────────────────────────────── */

.snapshot-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 14px 16px;
    margin: 10px 0;
}

.snapshot-card .card-title {
    font-family: var(--font-mono);
    font-size: 0.72rem;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 1.4px;
    margin-bottom: 10px;
}

.snap-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding: 5px 0;
    border-bottom: 1px solid var(--border-light);
    font-size: 0.82rem;
}
.snap-row:last-child { border-bottom: none; }

.snap-label { color: var(--text-muted); }

.snap-value {
    color: var(--text-primary);
    font-weight: 500;
    text-align: right;
    max-width: 58%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.snap-value.empty {
    color: var(--text-dim);
    font-style: italic;
    font-weight: 400;
}


/* ══════════════════════════════════════════════════════════════
   CHAT
   ══════════════════════════════════════════════════════════════ */

[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 6px 0 !important;
    animation: msgFadeIn 0.35s ease;
}

[data-testid="stChatMessage"] div,
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] li,
.stMarkdown p,
.stMarkdown li,
.stMarkdown span {
    color: var(--text-second) !important;
    font-size: 0.92rem !important;
    line-height: 1.6 !important;
}

[data-testid="stChatMessage"] h1,
[data-testid="stChatMessage"] h2,
[data-testid="stChatMessage"] h3,
[data-testid="stChatMessage"] h4,
[data-testid="stChatMessage"] strong {
    color: var(--text-primary) !important;
}

[data-testid="stChatMessage"] strong {
    font-weight: 600 !important;
}

@keyframes msgFadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* Bottom container block - highly specific to override Streamlit defaults */
.stApp [data-testid="stBottom"],
.stApp .stBottom,
.stApp div[class*="stBottom"],
.stApp div[class*="stBottomBlockContainer"],
div[class*="st-emotion-cache"] [data-testid="stBottom"],
div[class*="st-emotion-cache"] div[class*="stBottomBlockContainer"] {
    background: transparent !important;
    border: none !important;
}

/* Chat input bar overrides */
.stApp [data-testid="stChatInput"],
.stApp .stChatInput,
.stApp div[class*="stChatInput"],
div[class*="st-emotion-cache"] [data-testid="stChatInput"],
div[class*="st-emotion-cache"] div[class*="stChatInput"] {
    background-color: transparent !important;
    border: none !important;
}

.stApp [data-testid="stChatInput"] > div {
    background: transparent !important;
    background-color: transparent !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4) !important;
}

/* Make all descendants transparent with hyper-specificity and local custom property overrides */
html body .stApp div[data-testid="stChatInput"] *,
html body .stApp div[data-testid="stChatInput"] div,
html body .stApp div[data-testid="stChatInput"] textarea,
html body .stApp textarea[data-testid="stChatInputTextArea"],
html body .stApp [data-testid="stChatInputTextArea"] *,
.stApp div.stChatInput *,
.stApp div.stChatInput div,
.stApp div.stChatInput textarea {
    --secondary-background-color: transparent !important;
    --st-color-secondary-background-color: transparent !important;
    --st-secondary-background-color: transparent !important;
    --st-color-background-secondary: transparent !important;
    --st-background-secondary: transparent !important;
    background: transparent !important;
    background-color: transparent !important;
}

/* Specific text styling with high specificity */
html body .stApp div[data-testid="stChatInput"] textarea,
html body .stApp div[data-testid="stChatInput"] input,
html body .stApp textarea[data-testid="stChatInputTextArea"] {
    color: #FFFFFF !important;
    font-family: var(--font-body) !important;
    caret-color: var(--accent) !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: var(--text-muted) !important;
    opacity: 0.8 !important;
}

[data-testid="stChatInput"] button {
    background-color: transparent !important;
    color: var(--accent) !important;
}

[data-testid="stChatInput"] button:hover {
    color: var(--accent-hover) !important;
}


/* ══════════════════════════════════════════════════════════════
   BUTTONS — Quick-Action Pills
   ══════════════════════════════════════════════════════════════ */

div[data-testid="stChatMessage"] .stButton > button,
div.quick-action-zone .stButton > button {
    background: transparent !important;
    border: 1px solid rgba(34, 197, 94, 0.45) !important;
    color: var(--accent) !important;
    border-radius: var(--radius-pill) !important;
    padding: 5px 18px !important;
    font-family: var(--font-body) !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    transition: all var(--transition) !important;
    cursor: pointer !important;
    min-height: 0 !important;
    line-height: 1.6 !important;
}

div[data-testid="stChatMessage"] .stButton > button:hover,
div.quick-action-zone .stButton > button:hover {
    background: var(--accent) !important;
    color: var(--bg-deep) !important;
    border-color: var(--accent) !important;
    box-shadow: 0 0 18px rgba(34, 197, 94, 0.22) !important;
    transform: translateY(-1px) !important;
}

div[data-testid="stChatMessage"] .stButton > button:active,
div.quick-action-zone .stButton > button:active {
    transform: translateY(0) !important;
}

/* Sidebar buttons — muted style */
section[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--text-muted) !important;
    border-radius: var(--radius-sm) !important;
    width: 100% !important;
    font-size: 0.82rem !important;
    min-height: 0 !important;
    padding: 6px 12px !important;
    transition: all var(--transition) !important;
    cursor: pointer !important;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    background: var(--accent-glow) !important;
    box-shadow: none !important;
    transform: none !important;
}


/* ══════════════════════════════════════════════════════════════
   WELCOME SCREEN
   ══════════════════════════════════════════════════════════════ */

.welcome-hero {
    max-width: 700px;
    margin: 56px auto 24px;
    text-align: center;
    padding: 0 16px;
    animation: msgFadeIn 0.5s ease;
}

.welcome-badge {
    display: inline-block;
    background: var(--accent-glow);
    color: var(--accent);
    font-family: var(--font-mono);
    font-size: 0.7rem;
    font-weight: 600;
    padding: 5px 16px;
    border-radius: var(--radius-pill);
    border: 1px solid rgba(34, 197, 94, 0.25);
    letter-spacing: 1.8px;
    text-transform: uppercase;
    margin-bottom: 18px;
}

.welcome-title {
    font-family: var(--font-mono) !important;
    font-size: 2.6rem !important;
    font-weight: 700 !important;
    margin: 0 0 10px 0 !important;
    line-height: 1.15 !important;
    background: linear-gradient(135deg, var(--text-primary) 30%, var(--accent) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.welcome-sub {
    font-size: 1.05rem;
    color: var(--text-muted);
    line-height: 1.65;
    margin-bottom: 36px;
    max-width: 540px;
    margin-left: auto;
    margin-right: auto;
}


/* ── Template Cards ──────────────────────────────────────── */

.tpl-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 18px 16px 14px;
    text-align: left;
    transition: all var(--transition);
    cursor: pointer;
    height: 100%;
}

.tpl-card:hover {
    border-color: var(--accent);
    box-shadow: 0 4px 24px rgba(34, 197, 94, 0.08);
    transform: translateY(-2px);
}

.tpl-icon { font-size: 1.4rem; margin-bottom: 8px; }

.tpl-title {
    font-family: var(--font-mono);
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 5px;
}

.tpl-desc {
    font-size: 0.76rem;
    color: var(--text-muted);
    line-height: 1.45;
}


/* ══════════════════════════════════════════════════════════════
   DOCUMENT PREVIEW PANEL
   ══════════════════════════════════════════════════════════════ */

.doc-preview {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 18px;
    margin: 10px 0;
    max-height: 380px;
    overflow-y: auto;
    font-size: 0.82rem;
    line-height: 1.75;
    color: var(--text-second);
}

.doc-preview h1, .doc-preview h2 {
    font-family: var(--font-mono);
    color: var(--accent);
    font-size: 0.92rem;
    margin: 14px 0 6px;
}

.doc-preview h3 {
    font-family: var(--font-mono);
    color: var(--text-primary);
    font-size: 0.85rem;
}

.doc-preview strong { color: var(--text-primary); }

.doc-preview hr {
    border-color: var(--border-light) !important;
    margin: 10px 0;
}


/* ── Section Progress ────────────────────────────────────── */

.section-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 10px;
    border-radius: var(--radius-pill);
    font-size: 0.72rem;
    font-family: var(--font-mono);
    margin: 2px 3px;
}

.section-chip.done {
    background: rgba(34, 197, 94, 0.12);
    color: var(--accent);
    border: 1px solid rgba(34, 197, 94, 0.25);
}

.section-chip.pending {
    background: transparent;
    color: var(--text-dim);
    border: 1px solid var(--border);
}

.section-chip.current {
    background: rgba(245, 158, 11, 0.12);
    color: var(--warning);
    border: 1px solid rgba(245, 158, 11, 0.25);
}


/* ── Status Badges ───────────────────────────────────────── */

.badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 10px;
    border-radius: var(--radius-pill);
    font-size: 0.72rem;
    font-weight: 600;
    font-family: var(--font-mono);
}

.badge.pass {
    background: rgba(34, 197, 94, 0.12);
    color: var(--accent);
    border: 1px solid rgba(34, 197, 94, 0.25);
}

.badge.fail {
    background: rgba(239, 68, 68, 0.12);
    color: var(--danger);
    border: 1px solid rgba(239, 68, 68, 0.25);
}

.badge.warn {
    background: rgba(245, 158, 11, 0.12);
    color: var(--warning);
    border: 1px solid rgba(245, 158, 11, 0.25);
}

.badge.info {
    background: rgba(59, 130, 246, 0.12);
    color: var(--info);
    border: 1px solid rgba(59, 130, 246, 0.25);
}


/* ── Expander ────────────────────────────────────────────── */

[data-testid="stExpander"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    background: var(--bg-card) !important;
}

[data-testid="stExpander"] summary {
    font-family: var(--font-mono) !important;
    font-size: 0.82rem !important;
    color: var(--text-second) !important;
}


/* ── Download Button ─────────────────────────────────────── */

.stDownloadButton > button {
    background: var(--accent) !important;
    color: var(--bg-deep) !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-family: var(--font-mono) !important;
    cursor: pointer !important;
    transition: all var(--transition) !important;
}

.stDownloadButton > button:hover {
    background: var(--accent-hover) !important;
    box-shadow: 0 4px 16px rgba(34, 197, 94, 0.25) !important;
}


/* ── Dividers ────────────────────────────────────────────── */

hr { border-color: var(--border) !important; opacity: 0.4 !important; }


/* ── Reduce Motion ───────────────────────────────────────── */

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
    }
}

/* ── Responsive ──────────────────────────────────────────── */

@media (max-width: 768px) {
    .welcome-title { font-size: 1.7rem !important; }
    .welcome-sub   { font-size: 0.92rem; }
}
</style>
"""
