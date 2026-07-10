import os

import aisuite as ai
import pandas as pd

from agents.allocation_agent import AllocationAgent
from agents.explanation_agent import ExplanationAgent
from agents.research_agent import ResearchAgent
from agents.risk_agent import RiskAgent
from agents.simulation_agent import SimulationAgent


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
        self.allocation_agent = AllocationAgent()
        self.research_agent = ResearchAgent(self.client, self.model)
        self.simulation_agent = SimulationAgent(self.client, self.model)
        self.explanation_agent = ExplanationAgent(self.client, self.model)

    def run(self, user_query: str, portfolio_df: pd.DataFrame):
        specialist_results = []
        query = (user_query or "").lower()

        routing_rules = [
            (self.allocation_agent, ["allocate", "allocation", "rebalance", "target allocation", "desired allocation", "percent", "weights"]),
            (self.risk_agent, ["risk", "volatility", "diversify", "concentrat", "correlation", "drawdown", "hedge"]),
            (self.simulation_agent, ["scenario", "simulate", "forecast", "future", "historical", "what if", "stress", "market"]),
            (self.explanation_agent, ["explain", "why", "what does", "meaning", "understand", "clarify", "interpret"]),
            (self.research_agent, ["news", "research", "economic", "inflation", "rates", "fed", "policy", "geopolitical", "trends", "sector"]),
        ]

        selected_agents = []
        for agent, keywords in routing_rules:
            if any(keyword in query for keyword in keywords):
                selected_agents.append(agent)

        if not selected_agents:
            selected_agents = [self.research_agent]

        for agent in selected_agents:
            agent_name = getattr(agent, "name", agent.__class__.__name__)
            try:
                specialist_results.append(agent.run(user_query, portfolio_df))
            except Exception as exc:
                specialist_results.append(
                    {
                        "agent": agent_name,
                        "answer": f"Unable to run {agent_name}: {exc}",
                        "portfolio_summary": {},
                        "error": str(exc),
                    }
                )

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
