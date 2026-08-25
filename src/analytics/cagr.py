def calculate_cagr(start, end, years):
    """
    Calculate CAGR for positive starting and ending values.

    Formula:
        ((end / start) ** (1 / years) - 1) * 100

    Returns:
        tuple: (cagr, flag)
    """

    if years <= 0:
        return None, "INSUFFICIENT"

    if start == 0:
        return None, "ZERO_BASE"

    if start < 0 and end < 0:
        return None, "BOTH_NEGATIVE"

    if start < 0 and end > 0:
        return None, "TURNAROUND"

    if start > 0 and end < 0:
        return None, "DECLINE_TO_LOSS"

    if start > 0 and end > 0:
        cagr = ((end / start) ** (1 / years) - 1) * 100
        return cagr, None

    return None, "INSUFFICIENT"


def revenue_cagr(start, end, years):
    return calculate_cagr(start, end, years)


def pat_cagr(start, end, years):
    return calculate_cagr(start, end, years)


def eps_cagr(start, end, years):
    return calculate_cagr(start, end, years)