import pandas as pd


def portfolio_to_records(portfolio_df: pd.DataFrame):
    if portfolio_df is None or portfolio_df.empty:
        return []

    return portfolio_df.to_dict(orient="records")


def summarize_portfolio(portfolio_df: pd.DataFrame):
    """Create compact portfolio statistics for agent prompts."""
    if portfolio_df is None or portfolio_df.empty:
        return {
            "total_current_value": 0,
            "position_count": 0,
            "asset_allocation": {},
            "sector_allocation": {},
            "largest_positions": [],
        }

    working = portfolio_df.copy()
    working["market_value"] = working["quantity"] * working["current"]
    total_value = working["market_value"].sum()

    if total_value == 0:
        working["portfolio_weight"] = 0
    else:
        working["portfolio_weight"] = working["market_value"] / total_value

    asset_allocation = (
        working.groupby("asset_class")["market_value"].sum().div(total_value).mul(100).round(2).to_dict()
        if total_value
        else {}
    )
    sector_allocation = (
        working.groupby("sector")["market_value"].sum().div(total_value).mul(100).round(2).to_dict()
        if total_value
        else {}
    )

    largest_positions = (
        working.sort_values("portfolio_weight", ascending=False)
        .head(5)[["symbol", "asset_class", "sector", "market_value", "portfolio_weight"]]
        .assign(portfolio_weight=lambda df: (df["portfolio_weight"] * 100).round(2))
        .to_dict(orient="records")
    )

    return {
        "total_current_value": round(float(total_value), 2),
        "position_count": int(len(working)),
        "asset_allocation": asset_allocation,
        "sector_allocation": sector_allocation,
        "largest_positions": largest_positions,
    }
