"""University Finder — compares institution types, locations, support programs."""

from config.prompt_loader import load_agent_config

from src.agents.base import BaseAgent


class UniversityFinderAgent(BaseAgent):
    def __init__(self):
        cfg = load_agent_config("university_finder")
        super().__init__(
            name=cfg["agent"]["name"],
            system_prompt=cfg["system_prompt"],
            reasoning_effort=cfg["agent"]["reasoning_effort"],
            tool_mode=cfg["agent"].get("tool_mode"),
        )
