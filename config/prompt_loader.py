"""
Utility for loading agent prompt configs from config/prompts/<name>.yaml.

Configs are loaded once and LRU-cached so repeated instantiations of the
same agent class (e.g. via st.cache_resource) incur no extra file I/O.
"""

from functools import lru_cache
from pathlib import Path

import yaml

_PROMPTS_DIR = Path(__file__).parent / "prompts"


@lru_cache(maxsize=None)
def load_agent_config(agent_name: str) -> dict:
    """Load and cache agent config from config/prompts/<agent_name>.yaml.

    Args:
        agent_name: The YAML filename stem (e.g. "compass", "router").

    Returns:
        Parsed YAML dict with at minimum ``agent`` and ``system_prompt`` keys.

    Raises:
        FileNotFoundError: If the YAML file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    path = _PROMPTS_DIR / f"{agent_name}.yaml"
    with open(path) as f:
        return yaml.safe_load(f)
