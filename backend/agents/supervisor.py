import os

import aisuite as ai
import pandas as pd
from dotenv import load_dotenv

from backend.agents.allocation_agent import AllocationAgent
from backend.agents.explanation_agent import ExplanationAgent
from backend.agents.research_agent import ResearchAgent
from backend.agents.risk_agent import RiskAgent
from backend.agents.simulation_agent import SimulationAgent
from backend.agents.tools import sanitize_streamlit_math


DEFAULT_MODEL = "openai:gemini-3.5-flash-lite"
GEMINI_OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

load_dotenv()


def resolve_gemini_api_key():
    return os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()


class SupervisorAgent:
    """Routes a user question to specialist agents and prepares a final answer."""

    def __init__(self, model=DEFAULT_MODEL):
        self.model = model
        api_key = resolve_gemini_api_key()
        if not api_key:
            raise RuntimeError(
                "Gemini API key is missing. Add GEMINI_API_KEY to the project root .env file."
            )

        self.client = ai.Client(
            provider_configs={
                "openai": {
                    "api_key": api_key,
                    "base_url": GEMINI_OPENAI_BASE_URL,
                }
            }
        )
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
                specialist_result = agent.run(user_query, portfolio_df)
                if isinstance(specialist_result, dict) and isinstance(specialist_result.get("answer"), str):
                    specialist_result["answer"] = sanitize_streamlit_math(specialist_result["answer"])
                specialist_results.append(specialist_result)
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
                    "tax, or legal advice as a certainty. "
                    "Format your final answer for Streamlit: use concise markdown, short paragraphs, and simple bullet points. "
                    "Streamlit renders LaTeX inline in text properly, so you may use $...$ math when helpful. "
                    "However, do not place raw dollar signs directly next to words, numbers, or punctuation without clear separation. "
                    "If a formula or value would otherwise run together, add a line break or separate sentence to keep it readable. "
                    "If you want to show a literal dollar sign, escape it correctly for markdown/LaTeX so it is not mistaken for math delimiters. "
                    "Use inline math where it adds clarity, but avoid heavy display blocks and avoid unescaped math adjacent to plain text unless it is clearly separated."
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
                f"Gemini request failed. Check GEMINI_API_KEY and Gemini model access. Details: {exc}"
            ) from exc

        final_answer = sanitize_streamlit_math(response.choices[0].message.content)

        return {
            "supervisor": "Supervisor Agent",
            "model": self.model,
            "specialist_results": specialist_results,
            "final_answer": final_answer,
        }
