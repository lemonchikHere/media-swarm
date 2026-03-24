import yaml
from pathlib import Path
from typing import Any, Optional

CONFIG_DIR = Path(__file__).parent.parent / "config"

_personas_cache: Optional[dict[str, Any]] = None


def load_personas() -> dict[str, Any]:
    global _personas_cache
    if _personas_cache is None:
        with open(CONFIG_DIR / "personas" / "authors.yaml") as f:
            _personas_cache = yaml.safe_load(f)["personas"]
    return _personas_cache


def get_persona(niche: str) -> Optional[dict[str, Any]]:
    niches = load_niches()
    if niche not in niches:
        raise ValueError(f"Unknown niche: {niche}")
    niche_config = niches[niche]
    persona_key = niche_config.get("persona")
    if not persona_key:
        return None
    personas = load_personas()
    if persona_key not in personas:
        return None
    persona = personas[persona_key]
    return {
        "name": persona.get("name"),
        "model": persona.get("model"),
        "system_prompt": persona.get("system_prompt"),
    }


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
<<<<<<< HEAD
    if config.get("style_prompt") == "" and config.get("persona"):
        persona = get_persona(niche)
        if persona and persona.get("system_prompt"):
            config = dict(config)
            config["style_prompt"] = persona["system_prompt"]
    return config


def load_publishers() -> dict[str, Any]:
    with open(CONFIG_DIR / "publishers.yaml") as f:
        return yaml.safe_load(f)["publishers"]
=======
    if not config.get("style_prompt") and config.get("persona"):
        persona_name = config["persona"]
        persona = get_persona(persona_name)
        config = config.copy()
        config["style_prompt"] = persona.get("system_prompt", "")
        config["_persona"] = persona
    return config
>>>>>>> origin/feat/personas
