"""
Eco Grant Writer — Premium Conversational Chat UI

Streamlit front-end for the Eco Grant Writer ADK agent.
Features conversational chat bubbles, clickable quick-action pills,
a live phase tracker, project snapshot panel, and document preview.
"""

import asyncio
import json
import logging
import time

import streamlit as st

from styles import get_styles, get_font_links

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════
# Page Configuration
# ══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Eco Grant Writer",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(get_font_links(), unsafe_allow_html=True)
st.markdown(get_styles(), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# Constants
# ══════════════════════════════════════════════════════════════

PHASES = [
    ("intake", "Intake Interview"),
    ("matching", "Grant Matching"),
    ("drafting", "Section Drafting"),
    ("review", "Compliance Review"),
    ("complete", "Proposal Complete"),
]

TEMPLATES = [
    {
        "icon": "🏞️",
        "title": "River Cleanup",
        "desc": "Ganga ghats restoration in Varanasi",
        "prompt": (
            "We are CleanWaters NGO based in Varanasi. We want to clean up and "
            "restore the Ganga River ghats by removing plastic waste and debris. "
            "Our budget is around 15,00,000 INR. We have about 200 local volunteers "
            "ready to participate. Our NGO Darpan registration ID is Darpan-12345."
        ),
    },
    {
        "icon": "🌳",
        "title": "Urban Forest",
        "desc": "Nagar Van development in Delhi",
        "prompt": (
            "GreenCity Foundation wants to develop an urban forest (Nagar Van) in a "
            "municipal park in South Delhi. We plan to plant 5,000 indigenous saplings "
            "over 2 years. Our budget estimate is 40,00,000 INR. We have partnerships "
            "with 3 local schools for the maintenance program."
        ),
    },
    {
        "icon": "📚",
        "title": "Climate Education",
        "desc": "Youth workshops in Jaipur schools",
        "prompt": (
            "EcoYouth India wants to run Yuva Jal Vayu climate awareness workshops "
            "in 20 government high schools across Jaipur, Rajasthan. The program "
            "duration is 6 months with a budget of 8,00,000 INR. We will develop "
            "curriculum materials and train 50 student ambassadors."
        ),
    },
]

# ══════════════════════════════════════════════════════════════
# Session State
# ══════════════════════════════════════════════════════════════

_DEFAULTS: dict = {
    "messages": [],  # list[dict] with keys: role, content, options
    "phase": "welcome",
    "pending_input": None,
    "pending_display": None,
    "agent_session_id": None,
    "active_interrupt_id": None,
    # Agent state mirror
    "organization_name": "",
    "project_summary": "",
    "location": "",
    "budget_amount": 0.0,
    "currency": "INR",
    "currency_symbol": "₹",
    "ngo_registration_id": "",
    "project_duration": "",
    "volunteers_count": 0,
    "intake_complete": False,
    "target_grant": "",
    "grant_confirmed": False,
    "mandatory_sections": [],
    "sections_drafted": {},
    "current_section": "",
    "drafted_proposal": "",
    "is_compliant": False,
    "security_approved": False,
}

for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v if not isinstance(_v, (list, dict)) else type(_v)(_v)


# ══════════════════════════════════════════════════════════════
# Agent Integration
# ══════════════════════════════════════════════════════════════

@st.cache_resource
def _init_runner():
    """Initialize the ADK workflow runner and session service.

    Cached across reruns so the runner and in-memory sessions persist.
    """
    from grant_writer.config import load_env

    load_env()

    # Try standard ADK import paths
    try:
        from google.adk.runners import Runner
    except ImportError:
        from google.adk import Runner  # type: ignore[attr-defined]

    try:
        from google.adk.sessions import InMemorySessionService
    except ImportError:
        from google.adk.sessions.in_memory_session_service import InMemorySessionService  # type: ignore

    from grant_writer.agent import root_agent

    svc = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="eco_grant_writer",
        session_service=svc,
    )
    return runner, svc


def _run_sync(coro):
    """Run an async coroutine synchronously (safe inside Streamlit)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _ensure_session(svc) -> str:
    session = await svc.create_session(
        app_name="eco_grant_writer",
        user_id="streamlit_user",
    )
    return session.id


async def _agent_turn(user_input: str, runner, svc, session_id: str) -> tuple[str, dict]:
    """Execute one turn against the ADK workflow and return (response_text, state)."""
    from google.genai import types as gtypes
    from google.adk.events.request_input import RequestInput

    if st.session_state.active_interrupt_id:
        # Wrap response inside a FunctionResponse to resume the execution graph
        part = gtypes.Part(
            function_response=gtypes.FunctionResponse(
                id=st.session_state.active_interrupt_id,
                name=st.session_state.active_interrupt_id,
                response={"result": user_input}
            )
        )
        content = gtypes.Content(
            role="user",
            parts=[part],
        )
        st.session_state.active_interrupt_id = None
    else:
        content = gtypes.Content(
            role="user",
            parts=[gtypes.Part(text=user_input)],
        )

    last_text = ""
    state_deltas: dict = {}

    async for event in runner.run_async(
        session_id=session_id,
        user_id="streamlit_user",
        new_message=content,
    ):
        # 1. Check for RequestInput on the output field (HITL interrupts)
        if hasattr(event, "output") and event.output is not None:
            if isinstance(event.output, RequestInput):
                msg = event.output.message or ""
                last_text = json.dumps({"message": msg, "options": []})
                st.session_state.active_interrupt_id = event.output.interrupt_id

        # 2. Collect text from Content events
        if hasattr(event, "content") and event.content:
            if hasattr(event.content, "parts") and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        last_text = part.text

        # 3. Accumulate state deltas from EventActions
        if hasattr(event, "actions") and event.actions:
            if hasattr(event.actions, "state_delta") and event.actions.state_delta:
                state_deltas.update(event.actions.state_delta)

    # Retrieve full session state after the turn
    state: dict = dict(state_deltas)
    try:
        session = await svc.get_session(
            app_name="eco_grant_writer",
            user_id="streamlit_user",
            session_id=session_id,
        )
        if hasattr(session, "state") and session.state:
            state.update(dict(session.state))
    except Exception:
        pass

    return last_text, state


# ── Helpers ──────────────────────────────────────────────────

def _parse_response(text: str) -> dict:
    """Parse agent response text into {message, options, option_to_val}."""
    if not text:
        return {"message": "Hmm, I didn't get a response. Could you try again?", "options": [], "option_to_val": {}}
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            options = list(data.get("options", []))
            return {
                "message": str(data.get("message", text)),
                "options": options,
                "option_to_val": {o: o for o in options}
            }
    except (json.JSONDecodeError, TypeError):
        pass

    # Parse letter choices (e.g., A) ..., B) ...)
    import re
    options = []
    option_to_val = {}
    matches = re.findall(r'(?:^\s*|[^\w])([A-Z])\)\s*(.+?)(?=\n|$)', text)
    if matches:
        for letter, opt in matches:
            opt_clean = opt.strip()
            if opt_clean and opt_clean not in options:
                options.append(opt_clean)
                option_to_val[opt_clean] = letter

    return {"message": text, "options": options, "option_to_val": option_to_val}


def _sync_state(state: dict) -> None:
    """Mirror relevant agent state fields into Streamlit session state."""
    _fields = [
        "phase", "organization_name", "project_summary", "location",
        "budget_amount", "currency", "currency_symbol", "ngo_registration_id",
        "project_duration", "volunteers_count", "intake_complete",
        "target_grant", "grant_confirmed", "mandatory_sections",
        "sections_drafted", "current_section", "drafted_proposal",
        "is_compliant", "security_approved",
    ]
    for field in _fields:
        if field in state:
            st.session_state[field] = state[field]

    # Also derive phase from state flags if the agent didn't set it explicitly
    if "phase" not in state:
        if state.get("security_approved") or state.get("drafted_proposal"):
            if state.get("is_compliant") and state.get("security_approved"):
                st.session_state.phase = "complete"
        elif state.get("sections_drafted"):
            st.session_state.phase = "drafting"
        elif state.get("grant_confirmed"):
            st.session_state.phase = "drafting"
        elif state.get("intake_complete"):
            st.session_state.phase = "matching"


def _process_input(user_input: str, display_text: str = None) -> None:
    """Run one full agent turn: send input, collect response, update state."""
    if not display_text:
        display_text = user_input
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": display_text,
        "options": [],
        "option_to_val": {},
    })

    if st.session_state.phase == "welcome":
        st.session_state.phase = "intake"

    try:
        runner, svc = _init_runner()
    except Exception as exc:
        st.session_state.messages.append({
            "role": "assistant",
            "content": (
                f"**Agent initialization failed**\n\n`{exc}`\n\n"
                "Please make sure your `.env` file contains a valid `GOOGLE_API_KEY`."
            ),
            "options": ["Try again"],
            "option_to_val": {"Try again": "Try again"},
        })
        return

    try:
        # Ensure session
        if not st.session_state.agent_session_id:
            st.session_state.agent_session_id = _run_sync(_ensure_session(svc))

        response_text, state = _run_sync(
            _agent_turn(user_input, runner, svc, st.session_state.agent_session_id)
        )
    except Exception as exc:
        logger.exception("Agent turn failed")
        # Try creating a new session in case the old one was lost
        try:
            st.session_state.agent_session_id = _run_sync(_ensure_session(svc))
            response_text, state = _run_sync(
                _agent_turn(user_input, runner, svc, st.session_state.agent_session_id)
            )
        except Exception as retry_exc:
            st.session_state.messages.append({
                "role": "assistant",
                "content": (
                    f"**Something went wrong**\n\n`{retry_exc}`\n\n"
                    "The agent encountered an error. Please try again or start a new conversation."
                ),
                "options": ["Try again", "Start over"],
                "option_to_val": {"Try again": "Try again", "Start over": "Start over"},
            })
            return

    parsed = _parse_response(response_text)

    # Inject compliance review choice buttons
    if st.session_state.active_interrupt_id == "compliance_review_choice":
        parsed["options"] = ["Force Approve", "Reject Draft"]
        parsed["option_to_val"] = {
            "Force Approve": "force approve",
            "Reject Draft": "reject"
        }

    st.session_state.messages.append({
        "role": "assistant",
        "content": parsed["message"],
        "options": parsed.get("options", []),
        "option_to_val": parsed.get("option_to_val", {}),
    })
    _sync_state(state)


# ══════════════════════════════════════════════════════════════
# UI Components
# ══════════════════════════════════════════════════════════════


def _set_pending(text: str, display_text: str = None) -> None:
    """Button callback: queue text and optional display text for processing on next rerun."""
    st.session_state.pending_input = text
    st.session_state.pending_display = display_text


def _reset_conversation() -> None:
    """Reset all session state for a fresh conversation."""
    for k, v in _DEFAULTS.items():
        st.session_state[k] = v if not isinstance(v, (list, dict)) else type(v)(v)
    _init_runner.clear()


# ── Sidebar ──────────────────────────────────────────────────

def render_sidebar() -> None:
    with st.sidebar:
        # Logo / title
        st.markdown(
            '<h2 style="margin:0 0 2px 0;font-size:1.15rem;">🌿 Eco Grant Writer</h2>'
            '<p style="color:var(--text-dim);font-size:0.74rem;margin:0 0 16px 0;">'
            "AI-powered grant proposal drafting</p>",
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # ── Phase Tracker ────────────────────────────────────
        st.markdown(
            '<p style="font-family:var(--font-mono);font-size:0.72rem;color:var(--text-dim);'
            'text-transform:uppercase;letter-spacing:1.4px;margin-bottom:8px;">Workflow Progress</p>',
            unsafe_allow_html=True,
        )

        current = st.session_state.phase
        phase_keys = [p[0] for p in PHASES]
        try:
            active_idx = phase_keys.index(current)
        except ValueError:
            active_idx = -1  # welcome

        html_parts = ['<div class="phase-tracker">']
        for i, (key, label) in enumerate(PHASES):
            if i < active_idx:
                cls = "completed"
            elif i == active_idx:
                cls = "active"
            else:
                cls = ""
            dot_check = "✓ " if cls == "completed" else ""
            html_parts.append(f'<div class="phase-step {cls}">')
            html_parts.append(f'  <span class="phase-dot"></span>')
            html_parts.append(f"  {dot_check}{label}")
            html_parts.append("</div>")
            if i < len(PHASES) - 1:
                conn_cls = "done" if i < active_idx else ""
                html_parts.append(f'<div class="phase-connector {conn_cls}"></div>')
        html_parts.append("</div>")
        st.markdown("\n".join(html_parts), unsafe_allow_html=True)

        st.markdown("---")

        # ── Project Snapshot ─────────────────────────────────
        _render_project_snapshot()

        # ── Section Progress ─────────────────────────────────
        mandatory = st.session_state.mandatory_sections
        drafted = st.session_state.sections_drafted
        if mandatory:
            st.markdown("---")
            st.markdown(
                '<p style="font-family:var(--font-mono);font-size:0.72rem;color:var(--text-dim);'
                'text-transform:uppercase;letter-spacing:1.4px;margin-bottom:6px;">Sections</p>',
                unsafe_allow_html=True,
            )
            chips = []
            for s in mandatory:
                if s in drafted:
                    chips.append(f'<span class="section-chip done">✓ {s}</span>')
                elif s == st.session_state.current_section:
                    chips.append(f'<span class="section-chip current">● {s}</span>')
                else:
                    chips.append(f'<span class="section-chip pending">○ {s}</span>')
            st.markdown("".join(chips), unsafe_allow_html=True)

        # ── Document Preview ─────────────────────────────────
        proposal = st.session_state.drafted_proposal
        if proposal:
            st.markdown("---")
            with st.expander("📄 Proposal Preview", expanded=False):
                st.markdown(
                    f'<div class="doc-preview">{_md_to_html(proposal[:3000])}</div>',
                    unsafe_allow_html=True,
                )
                st.download_button(
                    "Download as Markdown",
                    data=proposal,
                    file_name="grant_proposal.md",
                    mime="text/markdown",
                    use_container_width=True,
                )

        # ── Controls ─────────────────────────────────────────
        st.markdown("---")
        if st.session_state.messages:
            st.button("↻ New Conversation", on_click=_reset_conversation, use_container_width=True)


def _render_project_snapshot() -> None:
    """Sidebar card showing extracted project data."""
    rows: list[tuple[str, str]] = [
        ("Organization", st.session_state.organization_name),
        ("Project", st.session_state.project_summary),
        ("Location", st.session_state.location),
        (
            "Budget",
            f"{st.session_state.currency_symbol}{st.session_state.budget_amount:,.0f}"
            if st.session_state.budget_amount
            else "",
        ),
        ("Grant", st.session_state.target_grant),
    ]

    # Only show if at least one field has data
    if not any(v for _, v in rows):
        return

    html = '<div class="snapshot-card"><div class="card-title">Project Snapshot</div>'
    for label, value in rows:
        val_cls = "" if value else "empty"
        display = value or "—"
        html += (
            f'<div class="snap-row">'
            f'  <span class="snap-label">{label}</span>'
            f'  <span class="snap-value {val_cls}">{display}</span>'
            f"</div>"
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def _md_to_html(md: str) -> str:
    """Minimal Markdown → HTML for the document preview panel."""
    import re

    lines = md.split("\n")
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            out.append(f"<h1>{stripped[2:]}</h1>")
        elif stripped.startswith("## "):
            out.append(f"<h2>{stripped[3:]}</h2>")
        elif stripped.startswith("### "):
            out.append(f"<h3>{stripped[4:]}</h3>")
        elif stripped.startswith("---"):
            out.append("<hr>")
        elif stripped.startswith("- "):
            out.append(f"<div style='padding-left:12px;'>• {stripped[2:]}</div>")
        elif stripped == "":
            out.append("<br>")
        else:
            # Bold
            processed = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", stripped)
            out.append(f"<p>{processed}</p>")
    return "\n".join(out)


# ── Welcome Screen ───────────────────────────────────────────

def render_welcome() -> None:
    """Show the branded hero section with quick-start template cards."""
    st.markdown(
        """
        <div class="welcome-hero">
            <div class="welcome-badge">AI-Powered Agent</div>
            <h1 class="welcome-title">Eco Grant Writer</h1>
            <p class="welcome-sub">
                Your intelligent assistant for crafting winning environmental grant proposals.
                Share your project details below and I'll guide you through intake, grant matching,
                section drafting, compliance review, and final assembly.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Template quick-start cards
    st.markdown(
        '<p style="text-align:center;color:var(--text-dim);font-size:0.8rem;'
        'font-family:var(--font-mono);margin-bottom:12px;">Quick Start Templates</p>',
        unsafe_allow_html=True,
    )

    cols = st.columns(3, gap="medium")
    for i, tpl in enumerate(TEMPLATES):
        with cols[i]:
            st.markdown(
                f"""
                <div class="tpl-card">
                    <div class="tpl-icon">{tpl["icon"]}</div>
                    <div class="tpl-title">{tpl["title"]}</div>
                    <div class="tpl-desc">{tpl["desc"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.button(
                f"Start {tpl['title']} →",
                key=f"tpl_{i}",
                on_click=_set_pending,
                args=(tpl["prompt"],),
                use_container_width=True,
            )


# ── Chat Rendering ───────────────────────────────────────────

def render_chat() -> None:
    """Render the full chat history with quick-action buttons on the last assistant message."""
    messages = st.session_state.messages
    last_asst_idx = -1

    # Find the index of the last assistant message
    for i in range(len(messages) - 1, -1, -1):
        if messages[i]["role"] == "assistant":
            last_asst_idx = i
            break

    for i, msg in enumerate(messages):
        avatar = "🌿" if msg["role"] == "assistant" else None
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

            options = msg.get("options", [])
            if not options:
                continue

            if i == last_asst_idx:
                # Active quick-action pills for the latest response
                option_to_val = msg.get("option_to_val", {})
                n_cols = min(len(options), 3)
                btn_cols = st.columns(n_cols)
                for j, opt in enumerate(options):
                    with btn_cols[j % n_cols]:
                        # Handle "Start over" / "Start new proposal" specially
                        if opt.lower() in ("start over", "start new proposal"):
                            st.button(
                                f"↻ {opt}",
                                key=f"qa_{i}_{j}",
                                on_click=_reset_conversation,
                            )
                        else:
                            val_to_send = option_to_val.get(opt, opt)
                            st.button(
                                opt,
                                key=f"qa_{i}_{j}",
                                on_click=_set_pending,
                                args=(val_to_send, opt),
                            )
            else:
                # Show past options as muted text
                opt_text = " · ".join(options)
                st.markdown(
                    f'<div style="font-size:0.72rem;color:var(--text-dim);'
                    f'margin-top:4px;font-family:var(--font-mono);">{opt_text}</div>',
                    unsafe_allow_html=True,
                )


# ══════════════════════════════════════════════════════════════
# Main Flow
# ══════════════════════════════════════════════════════════════

# Step 1: Process any pending input (from button clicks or previous chat_input)
if st.session_state.pending_input:
    user_input = st.session_state.pending_input
    display_text = st.session_state.pending_display
    st.session_state.pending_input = None
    st.session_state.pending_display = None
    with st.spinner(""):
        _process_input(user_input, display_text)

# Step 2: Render sidebar (always visible)
render_sidebar()

# Step 3: Render welcome or chat
if not st.session_state.messages:
    render_welcome()
else:
    render_chat()

    # Show completion banner
    if st.session_state.phase == "complete" and st.session_state.drafted_proposal:
        st.markdown("---")
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(
                '<div class="badge pass" style="font-size:0.82rem;padding:6px 14px;">'
                "✓ Proposal finalized and ready for submission</div>",
                unsafe_allow_html=True,
            )
        with c2:
            st.download_button(
                "⬇ Download Proposal",
                data=st.session_state.drafted_proposal,
                file_name="grant_proposal.md",
                mime="text/markdown",
                use_container_width=True,
            )

# Step 4: Chat input
if prompt := st.chat_input("Describe your project or ask a question…"):
    st.session_state.pending_input = prompt
    st.session_state.pending_display = None
    st.rerun()
