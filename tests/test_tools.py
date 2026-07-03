"""Unit tests for the tools module — budget, NGO validator, currency detection."""

import pytest

from grant_writer.tools.budget import calculate_budget_allocation
from grant_writer.tools.ngo_validator import validate_ngo_registration
from grant_writer.tools.currency import detect_currency, extract_budget


# ── Budget Calculator Tests ────────────────────────────────────────


class TestCalculateBudgetAllocation:
    def test_default_categories(self):
        result = calculate_budget_allocation(30000)
        assert "Equipment/Tools" in result
        assert "Operations/Logistics" in result
        assert "30,000" in result

    def test_custom_categories(self):
        result = calculate_budget_allocation(100000, ["Plants", "Tools", "Events", "Admin"])
        assert "Plants" in result
        assert "Tools" in result
        assert "Events" in result
        assert "Admin" in result
        assert "25.0%" in result

    def test_single_category(self):
        result = calculate_budget_allocation(50000, ["Everything"])
        assert "100.0%" in result
        assert "Everything" in result

    def test_empty_categories(self):
        result = calculate_budget_allocation(10000, [])
        assert "Error" in result

    def test_zero_budget(self):
        result = calculate_budget_allocation(0)
        assert "0.00" in result

    def test_string_budget_parsing(self):
        result = calculate_budget_allocation("₹15,00,000")
        assert "1,500,000.00" in result

    def test_invalid_string_budget(self):
        result = calculate_budget_allocation("not a budget")
        assert "0.00" in result


# ── NGO Validator Tests ────────────────────────────────────────────


class TestValidateNgoRegistration:
    def test_valid_id(self):
        result = validate_ngo_registration("MH/2026/012345")
        assert "VALID" in result

    def test_valid_id_delhi(self):
        result = validate_ngo_registration("DL/2026/12345")
        assert "VALID" in result

    def test_invalid_format(self):
        result = validate_ngo_registration("invalid-id")
        assert "INVALID" in result

    def test_lowercase_state_code(self):
        result = validate_ngo_registration("mh/2026/12345")
        assert "INVALID" in result

    def test_empty_string(self):
        result = validate_ngo_registration("")
        assert "Error" in result

    def test_whitespace_handling(self):
        result = validate_ngo_registration("  MH/2026/12345  ")
        assert "VALID" in result


# ── Currency Detection Tests ───────────────────────────────────────


class TestDetectCurrency:
    def test_rupee_symbol(self):
        code, sym = detect_currency("Budget is ₹15,00,000")
        assert code == "INR"
        assert sym == "₹"

    def test_dollar_symbol(self):
        code, sym = detect_currency("Need $25,000 for the project")
        assert code == "USD"
        assert sym == "$"

    def test_word_rupees(self):
        code, sym = detect_currency("We need 15 lakh rupees")
        assert code == "INR"
        assert sym == "₹"

    def test_location_mumbai(self):
        code, sym = detect_currency("Our office is in Mumbai")
        assert code == "INR"
        assert sym == "₹"

    def test_default_inr(self):
        code, sym = detect_currency("Just a regular message")
        assert code == "INR"

    def test_euro(self):
        code, sym = detect_currency("We have €5000")
        assert code == "EUR"
        assert sym == "€"


# ── Budget Extraction Tests ────────────────────────────────────────


class TestExtractBudget:
    def test_rupee_prefix(self):
        assert extract_budget("Budget: ₹15,00,000") == 1500000

    def test_dollar_prefix(self):
        assert extract_budget("Need $25,000") == 25000

    def test_suffix_notation(self):
        assert extract_budget("25000 USD total") == 25000

    def test_lakh_notation(self):
        assert extract_budget("Budget is 15 lakh") == 1500000

    def test_crore_notation(self):
        assert extract_budget("Fund of 2.5 crore") == 25000000

    def test_no_amount(self):
        assert extract_budget("No numbers here") is None

    def test_rs_prefix(self):
        assert extract_budget("Rs. 50,000") == 50000
