import logging

logger = logging.getLogger(__name__)


def net_profit_margin(net_profit, sales):

#Net Profit Margin = Net Profit / Sales × 100.

    if sales == 0:
        return None

    return (net_profit / sales) * 100


def operating_profit_margin(
    operating_profit,
    sales,
    reported_opm=None,
):
    #Operating Profit Margin = Operating Profit / Sales × 100.

    """If reported OPM is supplied, log a warning when the
    calculated value differs by more than 1 percentage point.
    """
    if sales == 0:
        return None

    calculated_opm = (operating_profit / sales) * 100

    if reported_opm is not None:
        difference = abs(calculated_opm - reported_opm)

        if difference > 1:
            logger.warning(
                "OPM mismatch: calculated=%.2f%% reported=%.2f%% "
                "difference=%.2f percentage points",
                calculated_opm,
                reported_opm,
                difference,
            )

    return calculated_opm


def return_on_equity(net_profit, equity_capital, reserves):

#ROE = Net Profit / (Equity Capital + Reserves) × 100.
    
    equity = equity_capital + reserves

    if equity <= 0:
        return None

    return (net_profit / equity) * 100


def return_on_capital_employed(
    ebit,
    equity_capital,
    reserves,
    borrowings,
):

  #ROCE = EBIT / (Equity + Reserves + Borrowings) × 100.

    capital_employed = (
        equity_capital
        + reserves
        + borrowings
    )

    if capital_employed <= 0:
        return None

    return (ebit / capital_employed) * 100


def roce_benchmark(roce, broad_sector, sector_benchmark=None):

# Use sector-relative benchmark for Financials.
    
    if roce is None:
        return None

    if broad_sector == "Financials":
        return sector_benchmark

    return roce


def return_on_assets(net_profit, total_assets):

    #ROA = Net Profit / Total Assets × 100.

    if total_assets == 0:
        return None

    return (net_profit / total_assets) * 100