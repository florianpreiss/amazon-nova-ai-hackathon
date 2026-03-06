"""
Hidden Curriculum Decoder — KODA's signature feature.

Explains academic terminology and unwritten rules of the university system
in simple, empowering language. Every explanation includes WHY first-gen
students do not know this — it is a systemic gap, not a personal failure.
"""

from config.prompt_loader import load_agent_config

from src.agents.base import BaseAgent


class HiddenCurriculumAgent(BaseAgent):
    def __init__(self):
        cfg = load_agent_config("hidden_curriculum")
        super().__init__(
            name=cfg["agent"]["name"],
            system_prompt=cfg["system_prompt"],
            reasoning_effort=cfg["agent"]["reasoning_effort"],
            tool_mode=cfg["agent"].get("tool_mode"),
        )
