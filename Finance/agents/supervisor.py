import aisuite as ai
import pandas as pd

from agents.risk_agent import RiskAgent


DEFAULT_MODEL = "ollama:llama3.1"


class SupervisorAgent:
    """Routes a user question to specialist agents and prepares a final answer."""

    def __init__(self, model=DEFAULT_MODEL):
        self.model = model
        self.client = ai.Client()
        self.risk_agent = RiskAgent(self.client, self.model)

    def run(self, user_query: str, portfolio_df: pd.DataFrame):
        specialist_results = []

        # First specialist implemented. Future route logic can choose among
        # Research, Simulation, Allocation, Explanation, and Compliance agents.
        specialist_results.append(self.risk_agent.run(user_query, portfolio_df))

        messages = [
            {
                "role": "system",
                "content": (
                    "You are the supervisor agent for a portfolio advice system. "
                    "Use the specialist result to answer the user's question. "
                    "Be clear about uncertainty. Do not provide personalized financial, "
                    "tax, or legal advice as a certainty."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"User question:\n{user_query}\n\n"
                    f"Specialist results:\n{specialist_results}"
                ),
            },
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
        )

        return {
            "supervisor": "Supervisor Agent",
            "model": self.model,
            "specialist_results": specialist_results,
            "final_answer": response.choices[0].message.content,
        }
