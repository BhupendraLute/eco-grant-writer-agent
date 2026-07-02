# SECURITY.md - STRIDE Threat Model

This document outlines the STRIDE threat model for the `grant-writer` workflow. The primary security focus is preventing the accidental exposure or leakage of a nonprofit's **private internal financials** (e.g., detailed salaries, donor lists, cash reserve details, internal audit logs) into the **public-facing drafted proposal** or shared telemetry logs.

---

## 1. Asset & Boundary Reference

* **Private Inputs (`nonprofit_notes`):** Unsanitized source notes provided by the nonprofit, containing general mission details mixed with sensitive internal financial reports.
* **Public Outputs (`drafted_proposal`):** The generated proposal text intended for submission to public funding bodies or external grant reviewers.
* **Trust Boundaries:**
  * The boundary between the user input interface (CLI/API) and the ADK workflow state.
  * The boundary between the python process executing the nodes and the subprocess executing the MCP server (`mcp_server.py`) over standard input/output.
  * The boundary between the local execution environment and any external LLM APIs (e.g., Gemini API).

---

## 2. STRIDE Threat Matrix

| Threat Category | Specific Threat Description | Impact | Target Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **S**poofing | An attacker spoofs the local MCP server to return malicious grant requirements designed to prompt-inject and extract sensitive state fields. | Altered workflow routing or data theft. | Hardcode server execution parameters and require authentication parameters for MCP connection. |
| **T**ampering | Unauthorized modification of `grant_requirements.json` or local session states stored in SQLite database sessions. | Hijacked state or prompt injections. | Implement file system permissions on configuration JSONs. Validate schemas on load. |
| **R**epudiation | Lack of audit logs showing which user uploaded private financial details or who approved the draft containing financial data. | Compliance failures and inability to trace leaks. | Implement session-level telemetry logs with clear tracking of inputs and user approvals. |
| **I**nformation Disclosure | **(High Risk)** The LLM or deterministic node extracts raw internal financials (e.g. employee pay rates, overhead) into the public draft. | Exposure of highly confidential financial assets. | Apply PII scrubbing, explicit LLM system instructions (safety gating), and regex compliance filters. |
| **D**enial of Service | Large financial reports are passed as notes, exhausting LLM token limits or triggering API rate limits. | System unavailability. | Enforce input length constraints and chunking limits in the `IngestNotes` node. |
| **E**levation of Privilege | Exploitation of MCP stdio subprocess parameters to execute arbitrary commands on the host system. | Full system compromise. | Hardcode `sys.executable` and sanitize path parameters. Never allow user-controlled args in server command creation. |

---

## 3. Deep-Dive: Information Disclosure of Private Financials

The primary security challenge is that `nonprofit_notes` frequently contain raw financial balances, detailed payroll lists, and operational reserves that should **not** appear in a public grant proposal. Most grants only require aggregate numbers (e.g., total budget, program cost).

### Threats in the Workflow
1. **Prompt Injection/LLM Copying:** An LLM-based `DraftProposal` node might copy detailed spreadsheets or financial tables verbatim from the notes to the draft.
2. **Logging Leakage:** Telemetry, standard output, and session databases (e.g., `sqlite_session_service`) write out `nonprofit_notes` to plaintext files, exposing them to local unprivileged users.
3. **Stdio Interception:** Other processes on the local machine monitoring stdout/stderr could capture transport logs if the MCP server outputs state values to `sys.stderr` or `stdout`.

### Proposed Mitigations
* **Explicit Safety System Instructions:**
  If the `DraftProposal` node is upgraded to an `LlmAgent`, it must have a strict system instruction:
  > *"You are a grant writer. You have access to sensitive internal financials. You MUST ONLY output aggregated budget figures. Do NOT expose individual employee salaries, names of donors, or internal cash reserves. If requested to include budget tables, generalize categories."*
* **PII/Financial Scrubbing Pipeline:**
  Implement a deterministic sanitization step in `IngestNotes` that flags or replaces specific patterns (e.g., social security numbers, banking details, individual salary figures) before writing to `ctx.state['nonprofit_notes']`.
* **Verification Gating (HITL):**
  Add a human-in-the-loop (HITL) step after `DraftProposal` to require manual compliance officer review of the output draft before finalizing the workflow.

---

## 4. Verification Checklist

* [ ] Validate that `mcp_server.py` path is hardcoded relative to the package path to avoid path traversal.
* [ ] Verify that all debugging print statements inside the MCP server write to `sys.stderr`, keeping the stdio channel clean.
* [ ] Ensure the `.env` file containing the `GEMINI_API_KEY` has restricted read/write permissions (`chmod 600` or equivalent on Windows).
* [ ] Review LLM prompt instructions to enforce the omission of private financial lists.
