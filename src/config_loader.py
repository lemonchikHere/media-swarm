import yaml
from pathlib import Path
from typing import Any

CONFIG_DIR = Path(__file__).parent.parent / "config"


def load_niches() -> dict[str, Any]:
    with open(CONFIG_DIR / "niches.yaml") as f:
        return yaml.safe_load(f)["niches"]


def get_niche_config(niche: str) -> dict[str, Any]:
    niches = load_niches()
    if niche not in niches:
        raise ValueError(f"Unknown niche: {niche}")
    return niches[niche]


def load_publishers() -> dict[str, Any]:
    with open(CONFIG_DIR / "publishers.yaml") as f:
        return yaml.safe_load(f)["publishers"]
