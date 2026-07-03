"""Budget allocation calculator tool."""


def calculate_budget_allocation(
    total_budget: float,
    categories: list[str] | None = None,
) -> str:
    """Calculates a balanced itemized budget allocation table for the proposal.

    Args:
        total_budget: The total budget amount.
        categories: List of categories (e.g. ['plants', 'tools', 'outreach']).
            Defaults to a standard set of three categories.

    Returns:
        A Markdown-formatted budget table string.
    """
    try:
        if isinstance(total_budget, str):
            cleaned = "".join(c for c in total_budget if c.isdigit() or c == ".")
            total_budget = float(cleaned) if cleaned else 0.0
        else:
            total_budget = float(total_budget)
    except Exception:
        total_budget = 0.0

    if categories is None:
        categories = [
            "Equipment/Tools",
            "Operations/Logistics",
            "Community Engagement/Events",
        ]

    if len(categories) == 0:
        return "Error: At least one budget category is required."

    count = len(categories)
    share = round(total_budget / count, 2)
    share_pct = round(100 / count, 1)

    lines = [
        "| Category | Allocation | Share (%) |",
        "| --- | --- | --- |",
    ]
    for cat in categories:
        lines.append(f"| {cat} | {share:,.2f} | {share_pct}% |")
    lines.append(f"| **Total** | **{total_budget:,.2f}** | **100%** |")

    return "\n".join(lines)
