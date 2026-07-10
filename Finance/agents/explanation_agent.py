#How should the results be explained?
import json

import pandas as pd

from agents.research_agent import ResearchAgent
from agents.tools import summarize_portfolio


class ExplanationAgent:
    """Specialist agent focused on explaining a user query."""

    def __init__(self, client, model):
        self.client = client
        self.model = model
        self.research_agent = ResearchAgent(client, model)

    def run(self, user_query: str, portfolio_df: pd.DataFrame):
        portfolio_summary = summarize_portfolio(portfolio_df)
        research_context = ""

        lowered_query = user_query.lower()
        research_keywords = [
            "market",
            "news",
            "economic",
            "recession",
            "inflation",
            "interest rate",
            "rates",
            "fed",
            "policy",
            "trend",
            "geopolitical",
            "sector",
            "industry",
            "tariff",
            "currency",
            "commodity",
        ]

        if any(keyword in lowered_query for keyword in research_keywords):
            research_result = self.research_agent.run(user_query, portfolio_df)
            research_context = research_result.get("answer", "")

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a portfolio explanation specialist. Your job is to explain the user's question in a clear, educational, and practical way. "
                    "Interpret the portfolio context, explain what matters most, and connect the answer to the user's holdings when relevant. "
                    "Do not promise returns or give guaranteed buy/sell instructions. "
                    "Keep the answer concise but informative. "
                    "When provided, use the research context to ground your explanation in recent market or economic developments. "
                    "Note that although the user portfolio tickers are valid, the sector and asset class they correspond to is inputted by the user and may be incorrect. Assume that the user inputted data is correct."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"User question:\n{user_query}\n\n"
                    f"Portfolio summary JSON:\n{json.dumps(portfolio_summary, indent=2)}\n\n"
                    f"Research context:\n{research_context if research_context else 'No additional research context provided.'}\n\n"
                    "Please explain the user's question clearly, mention the most relevant portfolio implications, and keep the answer practical and easy to understand."
                ),
            },
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
        )

        return {
            "agent": "Explanation Agent",
            "portfolio_summary": portfolio_summary,
            "research_context": research_context,
            "answer": response.choices[0].message.content,
        }