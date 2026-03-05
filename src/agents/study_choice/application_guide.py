"""Application Guide — step-by-step through the German university application process."""

from config.prompt_loader import load_agent_config
from src.agents.base import BaseAgent


class ApplicationGuideAgent(BaseAgent):
    def __init__(self):
        cfg = load_agent_config("application_guide")
        super().__init__(
            name=cfg["agent"]["name"],
            system_prompt=cfg["system_prompt"],
            reasoning_effort=cfg["agent"]["reasoning_effort"],
            tool_mode=cfg["agent"].get("tool_mode"),
        )
