"""Prompt templates for the LLM-as-a-Judge security guardrail.

Note: The primary judge prompt is in grant_writer/security/judge.py
since it's tightly coupled with the structured output parsing.
This module holds supplementary prompts for the security workflow.
"""


SECURITY_REVIEW_SUMMARY = """\
You are a security compliance assistant.

A grant proposal draft has been reviewed by the security guardrail.
The judge found the following issues:

{findings}

Write a clear, non-technical summary (under 60 words) explaining what was found \
and why human review is needed. This will be shown to the user for approval.

Summary:"""
