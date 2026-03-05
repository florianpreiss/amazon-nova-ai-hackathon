"""Study vs. Apprenticeship advisor — honest, balanced, empowering comparison."""

from config.prompt_loader import load_agent_config
from src.agents.base import BaseAgent


class StudyVsApprenticeshipAgent(BaseAgent):
    def __init__(self):
        cfg = load_agent_config("study_vs_apprenticeship")
        super().__init__(
            name=cfg["agent"]["name"],
            system_prompt=cfg["system_prompt"],
            reasoning_effort=cfg["agent"]["reasoning_effort"],
            tool_mode=cfg["agent"].get("tool_mode"),
        )
