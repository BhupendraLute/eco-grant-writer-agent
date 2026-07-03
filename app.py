"""Streamlit frontend for the Eco Grant Writer Agent.

Provides a conversational chat interface with a live document preview panel.
Uses the Google ADK Runner to interact with the workflow agent.
"""

import streamlit as st
import asyncio
import json
import uuid
import os

from google.adk.apps import App
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from grant_writer.config import load_env, resolve_project_path
from grant_writer.agent import root_agent

# Load environment once using shared config
load_env()

# Set page config
st.set_page_config(
    page_title="Eco Grant Writer Assistant",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for modern dark-mode chat aesthetics
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Space+Grotesk:wght@400;500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    h1, h2, h3 {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    .title-text {
        background: linear-gradient(135deg, #10B981 0%, #3B82F6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .subtitle-text {
        color: #94A3B8;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    .document-preview {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 30px;
        max-height: 75vh;
        overflow-y: auto;
        color: #E2E8F0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .warning-card {
        background-color: #451A03;
        border-left: 5px solid #F59E0B;
        color: #FEF3C7;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 15px;
        white-space: pre-wrap;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .success-card {
        background-color: #064E3B;
        border-left: 5px solid #10B981;
        color: #ECFDF5;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 15px;
    }
    .phase-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 10px;
    }
    .phase-intake { background: #1E3A5F; color: #93C5FD; }
    .phase-matching { background: #1E3A3F; color: #6EE7B7; }
    .phase-drafting { background: #2D1B69; color: #C4B5FD; }
    .phase-review { background: #4A2C1A; color: #FCD34D; }
    .phase-complete { background: #064E3B; color: #6EE7B7; }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #0F172A;
        border-radius: 8px 8px 0px 0px;
        padding: 10px 20px;
        border: 1px solid #1E293B;
        border-bottom: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E293B;
        border-top: 2px solid #10B981;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session Service globally in streamlit session state
if 'session_service' not in st.session_state:
    st.session_state.session_service = InMemorySessionService()

# Initialize conversational parameters
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = [
        {"role": "assistant", "content": "Hello! 🌱 I'm your **Eco Grant Writer Assistant**. Paste your messy notes or project ideas below, and I'll guide you through drafting a professional grant proposal!"}
    ]
if 'suggested_options' not in st.session_state:
    st.session_state.suggested_options = []
if 'paused_for_hitl' not in st.session_state:
    st.session_state.paused_for_hitl = False
if 'hitl_message' not in st.session_state:
    st.session_state.hitl_message = ""
if 'status' not in st.session_state:
    st.session_state.status = "idle"
if 'proposal_draft' not in st.session_state:
    st.session_state.proposal_draft = ""
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'active_interrupt_id' not in st.session_state:
    st.session_state.active_interrupt_id = ""
if 'error_message' not in st.session_state:
    st.session_state.error_message = ""
if 'current_phase' not in st.session_state:
    st.session_state.current_phase = "intake"


# Helper to load available grant names dynamically from requirements file
def load_available_grants():
    try:
        req_file = resolve_project_path("grant_requirements.json")
        with open(req_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [g.get("grant_name") for g in data.get("grants", [])]
    except Exception:
        return [
            "National River Conservation and Cleanup Grant",
            "Nagar Van (Urban Forest) Development Scheme",
            "Yuva Jal Vayu (Youth Climate) Action Fund",
            "Sustainable Agriculture & Organic Farming Seed Fund",
            "Gramin Solar Micro-Grid Decentralisation Innovation Fund",
        ]


# Asynchronous workflow execution function
async def run_workflow(user_msg: str, grant_name: str, resume_response: str = None):
    app = App(name="grant-writer-app", root_agent=root_agent)
    runner = Runner(app=app, session_service=st.session_state.session_service)

    # Initialize session if it doesn't exist
    session = await st.session_state.session_service.get_session(
        app_name="grant-writer-app",
        user_id="streamlit-user",
        session_id=st.session_state.session_id,
    )
    if session is None:
        await st.session_state.session_service.create_session(
            app_name="grant-writer-app",
            user_id="streamlit-user",
            session_id=st.session_state.session_id,
        )
        is_new_session = True
    else:
        is_new_session = False

    if resume_response is None:
        content = types.Content(role='user', parts=[types.Part(text=user_msg)])
    else:
        # Resume the existing session with the dynamically captured active interrupt ID
        content = types.Content(
            role='user',
            parts=[
                types.Part(
                    function_response=types.FunctionResponse(
                        id=st.session_state.active_interrupt_id,
                        name="adk_request_input",
                        response={"result": resume_response},
                    )
                )
            ],
        )

    events = []
    try:
        async for event in runner.run_async(
            user_id="streamlit-user",
            session_id=st.session_state.session_id,
            new_message=content,
        ):
            events.append(event)

        # Inspect events for human interruption
        paused = False
        hitl_msg = ""
        active_id = ""
        for event in events:
            if event.long_running_tool_ids:
                paused = True
                for part in event.content.parts:
                    if part.function_call and part.function_call.name == "adk_request_input":
                        hitl_msg = part.function_call.args.get("message", "Input requested")
                        active_id = part.function_call.id

        if paused:
            st.session_state.paused_for_hitl = True
            st.session_state.hitl_message = hitl_msg
            st.session_state.active_interrupt_id = active_id
            st.session_state.status = "paused"
            
            # Map suggested options for chat buttons
            if active_id == "compliance_review_choice":
                st.session_state.suggested_options = []
            elif active_id == "security_financial_review":
                st.session_state.suggested_options = ["Approve", "Reject"]
            elif active_id == "grant_selection":
                session = await st.session_state.session_service.get_session(
                    app_name="grant-writer-app",
                    user_id="streamlit-user",
                    session_id=st.session_state.session_id,
                )
                if session:
                    st.session_state.suggested_options = session.state.get("ranked_grants", [])
                else:
                    st.session_state.suggested_options = []
            else:
                st.session_state.suggested_options = []

            # Append safety warnings or choices to chat messages
            if not any(msg["content"] == hitl_msg for msg in st.session_state.chat_messages):
                st.session_state.chat_messages.append({"role": "assistant", "content": hitl_msg})
        else:
            st.session_state.paused_for_hitl = False
            st.session_state.status = "completed"

            # Fetch the updated state from the session
            session = await st.session_state.session_service.get_session(
                app_name="grant-writer-app",
                user_id="streamlit-user",
                session_id=st.session_state.session_id,
            )
            st.session_state.proposal_draft = session.state.get("drafted_proposal", "")
            st.session_state.current_phase = session.state.get("phase", "intake")

            # Extract final JSON response from the last event with text
            final_response = ""
            for event in events:
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text and '{"message":' in part.text:
                            final_response = part.text

            if final_response:
                try:
                    data = json.loads(final_response)
                    msg_text = data.get("message", "")
                    options = data.get("options", [])
                    st.session_state.chat_messages.append({"role": "assistant", "content": msg_text})
                    st.session_state.suggested_options = options
                except Exception:
                    st.session_state.chat_messages.append({"role": "assistant", "content": final_response})
                    st.session_state.suggested_options = []
            else:
                st.session_state.chat_messages.append({"role": "assistant", "content": "I've updated the proposal."})
                st.session_state.suggested_options = []

    except Exception as e:
        if "rejected" in str(e).lower():
            st.session_state.status = "rejected"
            st.session_state.paused_for_hitl = False
            st.session_state.chat_messages.append(
                {"role": "assistant", "content": "❌ Workflow aborted due to safety/compliance rejection."}
            )
        else:
            st.session_state.status = "error"
            st.session_state.error_message = str(e)
            st.session_state.paused_for_hitl = False
            st.session_state.chat_messages.append(
                {"role": "assistant", "content": f"⚠️ An error occurred: {str(e)}"}
            )


# ==========================================
# UI LAYOUT
# ==========================================

st.markdown('<div class="title-text">🌱 Eco Grant Writer Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle-text">Intelligent guided grant proposal drafting with built-in compliance and security guardrails.</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Settings")

    # Phase indicator
    phase = st.session_state.current_phase
    phase_labels = {
        "intake": ("📋 Intake Interview", "phase-intake"),
        "matching": ("🎯 Grant Matching", "phase-matching"),
        "drafting": ("✍️ Drafting Sections", "phase-drafting"),
        "review": ("🔍 Compliance Review", "phase-review"),
        "complete": ("✅ Complete", "phase-complete"),
    }
    label, css_class = phase_labels.get(phase, ("📋 Intake", "phase-intake"))
    st.markdown(f'<span class="phase-badge {css_class}">{label}</span>', unsafe_allow_html=True)

    grant_choice = st.selectbox("Target Program:", options=load_available_grants())

    if st.button("🔄 Reset Conversation", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# 50/50 Screen Split
col_chat, col_docs = st.columns([1, 1], gap="medium")

# LEFT COLUMN: Chat Interface
with col_chat:
    st.markdown("### 💬 Assistant")

    chat_container = st.container(height=550, border=False)
    with chat_container:
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Handle pending input from option clicks
        if 'pending_input' in st.session_state and st.session_state.pending_input:
            user_input = st.session_state.pending_input
            st.session_state.pending_input = ""
            st.session_state.chat_messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)
            with st.spinner("Processing..."):
                if st.session_state.paused_for_hitl:
                    asyncio.run(run_workflow("", grant_choice, resume_response=user_input))
                else:
                    asyncio.run(run_workflow(user_input, grant_choice))
            st.rerun()

    # Render suggested follow-up options as quick buttons
    if st.session_state.suggested_options:
        cols = st.columns(min(len(st.session_state.suggested_options), 4))
        for idx, opt in enumerate(st.session_state.suggested_options):
            with cols[idx % len(cols)]:
                if st.button(opt, key=f"opt_btn_{idx}", use_container_width=True):
                    st.session_state.pending_input = opt
                    st.session_state.suggested_options = []
                    st.rerun()

    # Chat text input
    if prompt := st.chat_input("Ask a question, or provide raw notes..."):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
        with st.spinner("Processing..."):
            if st.session_state.paused_for_hitl:
                asyncio.run(run_workflow("", grant_choice, resume_response=prompt))
            else:
                asyncio.run(run_workflow(prompt, grant_choice))
        st.rerun()

# RIGHT COLUMN: Document & Security Tabs
with col_docs:
    tab_draft, tab_safety = st.tabs(["📝 Live Draft Proposal", "🛡️ Compliance & Safety Panel"])

    with tab_draft:
        if st.session_state.proposal_draft:
            st.markdown('<div class="document-preview">', unsafe_allow_html=True)
            st.markdown(st.session_state.proposal_draft)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("The proposal draft will appear here as sections are generated.")

    with tab_safety:
        if st.session_state.status == "idle":
            st.info("System logs, compliance reports, and guardrail prompts will display here during execution.")

        elif st.session_state.status == "paused":
            header_title = "⚠️ Human Input Required" if st.session_state.active_interrupt_id == "compliance_review_choice" else "⚠️ Human Approval Required"
            st.markdown(f"""
            <div class="warning-card">
                <h2>{header_title}</h2>
                <hr>
                <p>{st.session_state.hitl_message}</p>
            </div>
            """, unsafe_allow_html=True)

            if st.session_state.active_interrupt_id != "compliance_review_choice":
                bcol1, bcol2 = st.columns(2)
                with bcol1:
                    if st.button("🟢 Force Approve & Continue", use_container_width=True):
                        st.session_state.status = "running"
                        asyncio.run(run_workflow("", grant_choice, resume_response="Approve"))
                        st.rerun()
                with bcol2:
                    if st.button("🔴 Reject & Abort Workflow", type="primary", use_container_width=True):
                        st.session_state.status = "running"
                        asyncio.run(run_workflow("", grant_choice, resume_response="Reject"))
                        st.rerun()

        elif st.session_state.status == "completed":
            st.markdown("""
            <div class="success-card">
                <h4>✅ Security & Compliance Checks Passed</h4>
                <p>All STRIDE threat models and PII scrubbers report a clean draft.</p>
            </div>
            """, unsafe_allow_html=True)

        elif st.session_state.status == "rejected":
            st.error("Workflow was aborted by the user due to safety/compliance violations.")

        elif st.session_state.status == "error":
            st.error(f"Error executing workflow: {st.session_state.error_message}")