"""
Anti-Impostor Agent — structural reframing of impostor feelings.

Uses Jo Phelan's (2024) concept of "impostorization" to reframe:
the problem is in the system, not in the student.
"""

from config.prompt_loader import load_agent_config

from src.agents.base import BaseAgent


class AntiImpostorAgent(BaseAgent):
    def __init__(self):
        cfg = load_agent_config("anti_impostor")
        super().__init__(
            name=cfg["agent"]["name"],
            system_prompt=cfg["system_prompt"],
            reasoning_effort=cfg["agent"]["reasoning_effort"],
            tool_mode=cfg["agent"].get("tool_mode"),
        )
