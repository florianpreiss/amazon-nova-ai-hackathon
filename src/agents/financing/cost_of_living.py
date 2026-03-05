"""Cost of Living Calculator — uses Code Interpreter for city comparisons."""

from config.prompt_loader import load_agent_config

from src.agents.base import BaseAgent


class CostOfLivingAgent(BaseAgent):
    def __init__(self):
        cfg = load_agent_config("cost_of_living")
        super().__init__(
            name=cfg["agent"]["name"],
            system_prompt=cfg["system_prompt"],
            reasoning_effort=cfg["agent"]["reasoning_effort"],
            tool_mode=cfg["agent"].get("tool_mode"),
        )
