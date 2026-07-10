#What could happen under different future or historical scenarios?

import json

import pandas as pd

from agents.research_agent import ResearchAgent
from agents.tools import summarize_portfolio


class SimulationAgent:
    """Specialist agent focused on simulating/predicting user inputted scenarios."""

    def __init__(self, client, model):
        self.client = client
        self.model = model
        self.research_agent = ResearchAgent(client, model)

    def run(self, user_query: str, portfolio_df: pd.DataFrame):
        portfolio_summary = summarize_portfolio(portfolio_df)
        research_context = ""

        if any(keyword in user_query.lower() for keyword in ["market", "news", "economic", "recession", "inflation", "rate", "fed", "policy", "trend", "geopolitical"]):
            research_result = self.research_agent.run(user_query, portfolio_df)
            research_context = research_result.get("answer", "")

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a portfolio simulation specialist, your main task is to determine what could happen under different future or historical scenarios provided in the user quesries."
                    "Do not promise returns or give guaranteed buy/sell instructions. "
                    "Keep the answer educational and concise."
                    "Note that although the user portfolio tickers are valid, the sector and asset class they correspond to is inputted by the user and may be incorrect. Assume that the user inputted data is correct."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"User question:\n{user_query}\n\n"
                    f"Portfolio summary JSON:\n{json.dumps(portfolio_summary, indent=2)}\n\n"
                    f"Research context:\n{research_context if research_context else 'No additional research context provided.'}"
                ),
            },
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
        )

        return {
            "agent": "Simulation Agent",
            "portfolio_summary": portfolio_summary,
            "research_context": research_context,
            "answer": response.choices[0].message.content,
        }