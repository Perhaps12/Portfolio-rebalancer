#What risks currently exist in the portfolio?

import json

import pandas as pd

from backend.agents.tools import summarize_portfolio


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
                    "You are a portfolio risk specialist, your main task is to determine what risks currently exist in the portfolio. Analyze concentration, "
                    "asset-class balance, sector exposure, and obvious data-quality risks. "
                    "Do not promise returns or give guaranteed buy/sell instructions. "
                    "Keep the answer educational and concise, with brief markdown bullets and short sections suited to Streamlit. "
                    "Streamlit renders LaTeX inline in text properly, so you may use $...$ math when helpful. If a formula or value would otherwise run together, add a line break or separate sentence to keep it readable. "
                    "If you want to show a literal dollar sign, escape it correctly for markdown/LaTeX so it is not mistaken for math delimiters. "
                    "Use inline math rather than heavy display formatting unless necessary. "
                    "Note that although the tickers are valid, the sector and asset class they correspond to is inputted by the user and may be incorrect. Assume that the user inputted data is correct."
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
