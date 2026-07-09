import os

import aisuite as ai
import pandas as pd

from agents.risk_agent import RiskAgent


DEFAULT_MODEL = "ollama:llama3.1"
DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"


def resolve_ollama_base_url(explicit=None):
    if explicit:
        return explicit

    for env_name in ("OLLAMA_BASE_URL", "OLLAMA_HOST"):
        value = os.getenv(env_name, "").strip()
        if not value:
            continue
        if value.startswith("http://") or value.startswith("https://"):
            return value
        if value.startswith("0.0.0.0") or value.startswith("::"):
            return value.replace("0.0.0.0", "127.0.0.1").replace("::", "127.0.0.1")
        return f"http://{value}"

    return DEFAULT_OLLAMA_BASE_URL


class SupervisorAgent:
    """Routes a user question to specialist agents and prepares a final answer."""

    def __init__(self, model=DEFAULT_MODEL, base_url=None):
        self.model = model
        self.base_url = resolve_ollama_base_url(base_url)
        os.environ["OLLAMA_BASE_URL"] = self.base_url
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

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Ollama request failed. Check that Ollama is running and the model is installed. Details: {exc}"
            ) from exc

        return {
            "supervisor": "Supervisor Agent",
            "model": self.model,
            "specialist_results": specialist_results,
            "final_answer": response.choices[0].message.content,
        }
