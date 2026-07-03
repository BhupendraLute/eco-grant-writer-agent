"""Prompt templates for the intake interview node."""


EXTRACT_STRUCTURED_DATA = """\
You are an intelligent intake assistant for a grant writing service.

Analyze the following messy notes from a nonprofit organization and extract structured data.
Return a JSON object with exactly these keys (use empty string "" for any field you cannot determine):

{{
  "organization_name": "Name of the nonprofit/NGO",
  "project_summary": "Brief 1-2 sentence summary of what the project does",
  "location": "City, region, or state where the project operates",
  "budget_amount": 0,
  "currency": "INR",
  "ngo_registration_id": "Darpan ID or other registration",
  "project_duration": "Expected timeline (e.g., '6 months', '1 year')",
  "volunteers_count": 0
}}

Notes:
{notes}

JSON:"""


IDENTIFY_MISSING_FIELDS = """\
You are a helpful grant writing assistant conducting an intake interview.

Based on the structured data extracted so far, identify what critical information is still \
missing for a strong grant proposal. The following fields have been gathered:

Organization: {organization_name}
Project: {project_summary}
Location: {location}
Budget: {currency_symbol}{budget_amount:,.0f} {currency}
Registration ID: {ngo_registration_id}
Duration: {project_duration}
Volunteers: {volunteers_count}

Return a JSON object with exactly these keys:
{{
  "message": "A friendly, encouraging message summarizing what you've captured and asking \
about the most important missing piece. Use emoji. Keep it under 100 words.",
  "options": ["Option A for the user to pick", "Option B", "Option C"],
  "missing_fields": ["field1", "field2"]
}}

The options should be helpful suggestions that answer your question, making it easy \
for the user to click and respond quickly.

JSON:"""


FOLLOWUP_QUESTION = """\
You are a grant writing assistant conducting a follow-up interview.

Previous conversation:
{chat_history}

The user just said: "{user_message}"

Current data gathered:
Organization: {organization_name}
Project: {project_summary}
Location: {location}
Budget: {currency_symbol}{budget_amount:,.0f} {currency}
Registration: {ngo_registration_id}
Duration: {project_duration}
Volunteers: {volunteers_count}

Update the structured data based on the user's latest message, then decide:
- If we have enough information (at minimum: project summary, location, and a rough budget), \
set "intake_complete" to true.
- Otherwise, ask ONE more focused follow-up question.

Return a JSON object:
{{
  "intake_complete": false,
  "updated_fields": {{"field_name": "new_value"}},
  "message": "Your friendly response and next question (if any). Use emoji.",
  "options": ["Quick reply option A", "Quick reply option B"]
}}

JSON:"""
