"""Role Model Matching — connects users with famous first-generation academics and leaders."""

from config.prompt_loader import load_agent_config

from src.agents.base import BaseAgent


class RoleModelAgent(BaseAgent):
    def __init__(self):
        cfg = load_agent_config("role_model_matching")
        super().__init__(
            name=cfg["agent"]["name"],
            system_prompt=cfg["system_prompt"],
            reasoning_effort=cfg["agent"]["reasoning_effort"],
            tool_mode=cfg["agent"].get("tool_mode"),
        )
