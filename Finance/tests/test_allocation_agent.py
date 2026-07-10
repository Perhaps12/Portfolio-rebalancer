import pandas as pd

from agents.allocation_agent import AllocationAgent


def test_allocation_agent_generates_buy_and_sell_actions():
    portfolio_df = pd.DataFrame(
        [
            {"symbol": "AAPL", "quantity": 10, "avg_cost": 100.0, "current": 120.0, "asset_class": "Equities", "sector": "Technology"},
            {"symbol": "MSFT", "quantity": 10, "avg_cost": 100.0, "current": 100.0, "asset_class": "Equities", "sector": "Technology"},
            {"symbol": "TLT", "quantity": 10, "avg_cost": 100.0, "current": 90.0, "asset_class": "Bonds", "sector": "Government"},
        ]
    )

    agent = AllocationAgent()
    result = agent.run(
        "Rebalance to 50% equities and 50% bonds",
        portfolio_df,
        desired_allocations={"Equities": 50, "Bonds": 50},
    )

    assert result["target_allocations"]["Equities"] == 50
    assert result["target_allocations"]["Bonds"] == 50
    assert any(action["action"] == "Sell" for action in result["trade_plan"])
    assert any(action["action"] == "Buy" for action in result["trade_plan"])
