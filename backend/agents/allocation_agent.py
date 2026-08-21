import re

import pandas as pd


class AllocationAgent:
    """Suggest stock-level buy/sell actions to move a portfolio toward target allocations."""

    def __init__(self):
        self.name = "Allocation Agent"

    def _parse_desired_allocations(self, user_query, desired_allocations=None):
        if desired_allocations:
            normalized = {}
            for asset_class, percent in desired_allocations.items():
                try:
                    normalized[str(asset_class)] = float(percent)
                except (TypeError, ValueError):
                    continue
            if normalized:
                return self._normalize_allocations(normalized)

        matches = re.findall(r"(\d+(?:\.\d+)?)\s*%", user_query or "")
        if not matches:
            return None

        values = [float(value) for value in matches]
        if len(values) == 1:
            values = [values[0], 100 - values[0]]

        if len(values) < 2:
            return None

        # Use the first two percentages as the default target mix.
        return self._normalize_allocations({"Equities": values[0], "Bonds": values[1]})

    def _normalize_allocations(self, allocations):
        total = sum(float(value) for value in allocations.values())
        if total <= 0:
            return allocations
        return {asset_class: round(float(value) / total * 100, 2) for asset_class, value in allocations.items()}

    def _portfolio_allocations(self, portfolio_df):
        if portfolio_df is None or portfolio_df.empty:
            return {}, 0.0, []

        working = portfolio_df.copy()
        if "market_value" not in working.columns:
            working["market_value"] = working["quantity"] * working["current"]

        total_value = float(working["market_value"].sum())
        if total_value <= 0:
            return {}, 0.0, []

        allocations = (
            working.groupby("asset_class")["market_value"].sum().div(total_value).mul(100).round(2).to_dict()
        )
        return allocations, total_value, working.to_dict(orient="records")

    def run(self, user_query: str, portfolio_df: pd.DataFrame, desired_allocations=None):
        allocations, total_value, positions = self._portfolio_allocations(portfolio_df)
        target_allocations = self._parse_desired_allocations(user_query, desired_allocations)

        if not target_allocations:
            return {
                "agent": self.name,
                "message": "No target allocations were provided, so no rebalancing trades could be generated.",
                "current_allocations": allocations,
                "target_allocations": {},
                "trade_plan": [],
                "portfolio_value": round(total_value, 2),
            }

        trade_plan = []
        positions_df = pd.DataFrame(positions)
        if not positions_df.empty:
            positions_df["market_value"] = positions_df["quantity"] * positions_df["current"]
            positions_df["weight_in_class"] = positions_df.groupby("asset_class")["market_value"].transform(
                lambda s: s / s.sum() if s.sum() else 0
            )

        for asset_class, target_pct in target_allocations.items():
            current_pct = allocations.get(asset_class, 0.0)
            gap = round(target_pct - current_pct, 2)
            if gap == 0:
                continue

            class_positions = positions_df[positions_df["asset_class"] == asset_class] if not positions_df.empty else pd.DataFrame()
            if gap < 0:
                remaining_value = abs(gap) / 100 * total_value
                for _, row in class_positions.sort_values("market_value", ascending=False).iterrows():
                    if remaining_value <= 0:
                        break
                    sell_value = min(float(row["market_value"]), remaining_value)
                    if sell_value <= 0:
                        continue
                    shares_to_sell = round(sell_value / float(row["current"]), 4)
                    trade_plan.append(
                        {
                            "action": "Sell",
                            "ticker": row["symbol"],
                            "asset_class": asset_class,
                            "amount_usd": round(sell_value, 2),
                            "estimated_shares": shares_to_sell,
                            "current_price": round(float(row["current"]), 2),
                            "reason": f"Reduce {asset_class} exposure to move toward {target_pct:.2f}% target allocation",
                        }
                    )
                    remaining_value -= sell_value
            else:
                target_value = (gap / 100) * total_value
                if class_positions.empty:
                    trade_plan.append(
                        {
                            "action": "Buy",
                            "ticker": None,
                            "asset_class": asset_class,
                            "amount_usd": round(target_value, 2),
                            "estimated_shares": None,
                            "current_price": None,
                            "reason": f"Open a new position in {asset_class} to reach the {target_pct:.2f}% target",
                        }
                    )
                    continue

                remaining_value = target_value
                for _, row in class_positions.sort_values("market_value", ascending=False).iterrows():
                    if remaining_value <= 0:
                        break
                    buy_value = min(remaining_value, float(row["market_value"]) * 0.5)
                    if buy_value <= 0:
                        continue
                    shares_to_buy = round(buy_value / float(row["current"]), 4)
                    trade_plan.append(
                        {
                            "action": "Buy",
                            "ticker": row["symbol"],
                            "asset_class": asset_class,
                            "amount_usd": round(buy_value, 2),
                            "estimated_shares": shares_to_buy,
                            "current_price": round(float(row["current"]), 2),
                            "reason": f"Increase {asset_class} exposure to move toward {target_pct:.2f}% target allocation",
                        }
                    )
                    remaining_value -= buy_value

        return {
            "agent": self.name,
            "portfolio_value": round(total_value, 2),
            "current_allocations": {k: round(float(v), 2) for k, v in allocations.items()},
            "target_allocations": {k: round(float(v), 2) for k, v in target_allocations.items()},
            "trade_plan": trade_plan,
        }
