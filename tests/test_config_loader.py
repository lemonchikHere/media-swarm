import pytest
from src.config_loader import (
    load_niches,
    get_niche_config,
    load_publishers,
    load_personas,
    get_persona,
)


def test_load_niches_returns_dict():
    niches = load_niches()
    assert isinstance(niches, dict)
    assert "realestate" in niches
    assert "ai_tech" in niches


def test_niche_has_required_fields():
    niche = load_niches()["realestate"]
    assert "name" in niche
    assert "style_prompt" in niche
    assert "sources" in niche
    assert "publish_to" in niche
    assert "post_interval_minutes" in niche
    assert "max_posts_per_day" in niche


def test_get_niche_config_returns_correct_niche():
    cfg = get_niche_config("realestate")
    assert cfg["name"] == "Недвижимость"
    assert cfg["post_interval_minutes"] == 120
    assert cfg["max_posts_per_day"] == 8


def test_get_niche_config_unknown_raises():
    with pytest.raises(ValueError, match="Unknown niche"):
        get_niche_config("unknown_niche")


def test_load_publishers():
    publishers = load_publishers()
    assert "telegram" in publishers
    assert "vk" in publishers
    assert publishers["telegram"]["type"] == "bot"
    assert publishers["vk"]["type"] == "community"


def test_load_personas_returns_5_personas():
    personas = load_personas()
    assert isinstance(personas, dict)
    assert len(personas) == 5
    assert "github_trending_ru" in personas
    assert "vibecoding_ru" in personas
    assert "ai_money_ru" in personas
    assert "ai_startups_ru" in personas
    assert "nocode_build_ru" in personas


def test_get_persona_for_niche_with_persona():
    persona = get_persona("github_trending")
    assert persona is not None
    assert persona["name"] == "Антон Климов"
    assert "model" in persona
    assert "system_prompt" in persona


def test_get_persona_for_niche_without_persona():
    persona = get_persona("realestate")
    assert persona is None


def test_get_niche_config_loads_style_prompt_from_persona():
    cfg = get_niche_config("github_trending")
    assert cfg["style_prompt"] is not None
    assert "Антон Климов" in cfg["style_prompt"] or "backend" in cfg["style_prompt"].lower()


def test_get_niche_config_realestate_uses_own_style_prompt():
    cfg = get_niche_config("realestate")
    assert "недвижимости" in cfg["style_prompt"].lower()
