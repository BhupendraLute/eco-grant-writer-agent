"""NGO Darpan registration ID validator tool."""

import re


def validate_ngo_registration(darpan_id: str) -> str:
    """Validates the NGO Darpan Registration number format.

    Expected format: StateCode/Year/Number (e.g. 'MH/2026/012345').
    The state code must be 2 uppercase letters, year 4 digits, and number 1+ digits.

    Args:
        darpan_id: The registration ID to validate.

    Returns:
        A string indicating whether the ID is valid or invalid.
    """
    clean_id = darpan_id.strip()
    if not clean_id:
        return "Error: No registration ID provided."

    if re.match(r"^[A-Z]{2}/\d{4}/\d+$", clean_id):
        return f"NGO Darpan ID '{clean_id}' is VALID. Verification status: Active."
    else:
        return (
            f"NGO Darpan ID '{clean_id}' is INVALID. "
            f"Format must be 'StateCode/Year/Number' (e.g., 'MH/2026/012345')."
        )
