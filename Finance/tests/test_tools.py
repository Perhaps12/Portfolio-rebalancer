import pandas as pd

from agents.tools import build_desired_allocation_plan, summarize_portfolio

def test_summarize_portfolio_omits_user_allocation_data():
    portfolio_df = pd.DataFrame(
        [
            {
                "symbol": "AAPL",
                "quantity": 10,
                "avg_cost": 100,
                "current": 120,
                "sector": "Technology",
                "asset_class": "Equity",
            }
        ]
    )

    summary = summarize_portfolio(portfolio_df)

    assert summary["position_count"] == 1
    assert "desired_allocations" not in summary


def test_build_desired_allocation_plan_returns_user_allocations_and_changes():
    summary_data = [
        {
            "asset_class": "Equity",
            "cur_asset_allocation": 60,
            "cur_total_cost": 6000,
        },
        {
            "asset_class": "Bond",
            "cur_asset_allocation": 40,
            "cur_total_cost": 4000,
        },
    ]

    plan = build_desired_allocation_plan(summary_data, [40, 60], user_id="u1")

    assert plan["summary_data"][0]["desired_allocation"] == 40
    assert plan["summary_data"][1]["desired_allocation"] == 60
    assert plan["asset_amount_changes"]["Equity"] == 4000 * (40 / 60 - 1)
    assert plan["asset_amount_changes"]["Bond"] == 4000 * (60 / 40 - 1)
    assert plan["asset_amount_changes"]["user_id"] == "u1"
