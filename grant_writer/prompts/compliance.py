"""Prompt templates for compliance auditing."""


COMPLIANCE_AUDIT = """\
You are a strict compliance auditor for nonprofit grants.

Audit the following proposal draft against the target grant guidelines.
Verify that:
1. All mandatory sections are present and substantive.
2. The budget is within the maximum allowed by the guidelines.
3. The required metrics are specifically addressed with numbers.
4. No prohibited expenses are mentioned.
5. Word count limits are respected (if specified).

Your output must end with 'COMPLIANCE STATUS: APPROVED' if everything is correct.
Otherwise, output the list of violations and end with 'COMPLIANCE STATUS: VIOLATIONS FOUND'.

Guidelines:
{guidelines_json}

Proposal Draft:
{proposal_draft}"""
