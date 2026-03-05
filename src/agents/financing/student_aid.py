"""Student Aid (BAföG) Agent — uses Code Interpreter for financial calculations."""

from config.prompt_loader import load_agent_config
from src.agents.base import BaseAgent


class StudentAidAgent(BaseAgent):
    def __init__(self):
        cfg = load_agent_config("student_aid")
        super().__init__(
            name=cfg["agent"]["name"],
            system_prompt=cfg["system_prompt"],
            reasoning_effort=cfg["agent"]["reasoning_effort"],
            tool_mode=cfg["agent"].get("tool_mode"),
        )
