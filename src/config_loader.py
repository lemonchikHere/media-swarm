import yaml
from pathlib import Path
from typing import Any

CONFIG_DIR = Path(__file__).parent.parent / "config"


def load_niches() -> dict[str, Any]:
    with open(CONFIG_DIR / "niches.yaml") as f:
        return yaml.safe_load(f)["niches"]


def load_publishers() -> dict[str, Any]:
    with open(CONFIG_DIR / "publishers.yaml") as f:
        return yaml.safe_load(f)["publishers"]


def load_personas() -> dict[str, Any]:
    with open(CONFIG_DIR / "personas" / "authors.yaml") as f:
        return yaml.safe_load(f)["personas"]


def get_persona(name: str) -> dict[str, Any]:
    personas = load_personas()
    if name not in personas:
        raise ValueError(f"Unknown persona: {name}")
    return personas[name]


def get_niche_config(niche: str) -> dict[str, Any]:
    niches = load_niches()
    if niche not in niches:
        raise ValueError(f"Unknown niche: {niche}")
    config = niches[niche]
    if not config.get("style_prompt") and config.get("persona"):
        persona_name = config["persona"]
        persona = get_persona(persona_name)
        config = config.copy()
        config["style_prompt"] = persona.get("system_prompt", "")
        config["_persona"] = persona
    return config
