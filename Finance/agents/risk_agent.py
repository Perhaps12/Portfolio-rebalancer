import json

import pandas as pd

from agents.tools import summarize_portfolio


class RiskAgent:
    """Specialist agent focused on portfolio risk and diversification."""

    def __init__(self, client, model):
        self.client = client
        self.model = model

    def run(self, user_query: str, portfolio_df: pd.DataFrame):
        portfolio_summary = summarize_portfolio(portfolio_df)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a portfolio risk specialist. Analyze concentration, "
                    "asset-class balance, sector exposure, and obvious data-quality risks. "
                    "Do not promise returns or give guaranteed buy/sell instructions. "
                    "Keep the answer educational and concise."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"User question:\n{user_query}\n\n"
                    f"Portfolio summary JSON:\n{json.dumps(portfolio_summary, indent=2)}"
                ),
            },
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
        )

        return {
            "agent": "Risk Agent",
            "portfolio_summary": portfolio_summary,
            "answer": response.choices[0].message.content,
        }
