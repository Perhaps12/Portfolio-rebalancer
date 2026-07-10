#What is happening in the market?

import json

import pandas as pd

from agents.tools import search_web, summarize_portfolio


class ResearchAgent:
    """Specialist agent focused on researching what happens in the market and how it may affect the portfolio."""

    def __init__(self, client, model):
        self.client = client
        self.model = model

    def run(self, user_query: str, portfolio_df: pd.DataFrame):
        portfolio_summary = summarize_portfolio(portfolio_df)

        planning_messages = [
            {
                "role": "system",
                "content": (
                    "You are a market research specialist. Turn the user's question into a concise, high-signal web-search query. "
                    "Return only the final search query, without explanation."
                ),
            },
            {
                "role": "user",
                "content": f"User question:\n{user_query}",
            },
        ]

        search_query_response = self.client.chat.completions.create(
            model=self.model,
            messages=planning_messages,
            temperature=0.2,
        )
        search_query = search_query_response.choices[0].message.content.strip()

        web_context = search_web(search_query, max_results=3)
        web_context_text = ""
        if web_context:
            web_context_text = "\n".join(
                f"- {item['title']} | {item['url']} | {item['snippet']}" for item in web_context
            )

        answer_messages = [
            {
                "role": "system",
                "content": (
                    "You are a market research specialist, your main task is to investigate what is happening in the market and how it may affect the portfolio. Analyze economic indicators, industry trends, and geopolitical events. "
                    "Do not promise returns or give guaranteed buy/sell instructions. "
                    "Keep the answer educational and concise."
                    "Use the web context supplied below when it helps answer the question."
                    "Note that although the tickers are valid, the sector and asset class they correspond to is inputted by the user and may be incorrect. Assume that the user inputted data is correct."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"User question:\n{user_query}\n\n"
                    f"Portfolio summary JSON:\n{json.dumps(portfolio_summary, indent=2)}\n\n"
                    f"Search query used:\n{search_query}\n\n"
                    f"Web context:\n{web_context_text if web_context_text else 'No web context available.'}"
                ),
            },
        ]

        answer_response = self.client.chat.completions.create(
            model=self.model,
            messages=answer_messages,
            temperature=0.2,
        )

        return {
            "agent": "Research Agent",
            "portfolio_summary": portfolio_summary,
            "search_query": search_query,
            "answer": answer_response.choices[0].message.content,
        }
