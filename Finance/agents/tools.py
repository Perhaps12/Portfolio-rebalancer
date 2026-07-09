import pandas as pd

from services.validation import valid_percent


def portfolio_to_records(portfolio_df: pd.DataFrame):
    if portfolio_df is None or portfolio_df.empty:
        return []

    return portfolio_df.to_dict(orient="records")


def summarize_portfolio(portfolio_df: pd.DataFrame):
    """Create compact portfolio details for agent prompts without target allocations."""
    if portfolio_df is None or portfolio_df.empty:
        return {
            "total_current_value": 0,
            "position_count": 0,
            "tickers": [],
            "stocks_purchased": [],
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

    stocks_purchased = (
        working[["symbol", "quantity", "avg_cost", "current", "market_value", "sector", "asset_class"]]
        .copy()
        .assign(
            avg_cost=lambda df: df["avg_cost"].round(2),
            current=lambda df: df["current"].round(2),
            market_value=lambda df: df["market_value"].round(2),
        )
        .to_dict(orient="records")
    )

    return {
        "total_current_value": round(float(total_value), 2),
        "position_count": int(len(working)),
        "tickers": working["symbol"].astype(str).tolist(),
        "stocks_purchased": stocks_purchased,
        "asset_allocation": asset_allocation,
        "sector_allocation": sector_allocation,
        "largest_positions": largest_positions,
    }


def summarize_portfolio_with_desired_allocations(portfolio_df: pd.DataFrame, desired_allocations=None):
    """Return a portfolio summary without attaching user allocation targets."""
    return summarize_portfolio(portfolio_df)


def build_desired_allocation_plan(summary_data, user_percents, user_id=None):
    """Validate user allocation inputs, store desired targets, and compute trade changes."""
    if summary_data is None:
        raise ValueError("No summary data available")

    if len(summary_data) != len(user_percents):
        raise ValueError("Allocation count does not match the number of asset classes")

    normalized_percents = []
    for percent in user_percents:
        if not valid_percent(percent):
            raise ValueError("One or more fields contained an invalid value")
        normalized_percents.append(float(percent))

    if round(sum(normalized_percents), 2) != 100:
        raise IndexError("Percents must sum to 100")

    updated_summary_data = []
    asset_amount_changes = {}

    for item, desired_percent in zip(summary_data, normalized_percents):
        updated_item = dict(item)
        updated_item["desired_allocation"] = desired_percent
        updated_summary_data.append(updated_item)

        current_allocation = updated_item.get("cur_asset_allocation")
        if current_allocation in (None, 0):
            raise ValueError("Current allocation cannot be zero")

        asset_amount_changes[updated_item["asset_class"]] = updated_item["cur_total_cost"] * (
            desired_percent / current_allocation - 1
        )

    if user_id is not None:
        asset_amount_changes["user_id"] = user_id

    return {
        "summary_data": updated_summary_data,
        "asset_amount_changes": asset_amount_changes,
    }
