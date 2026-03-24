import pytest
from src.config_loader import load_niches, get_niche_config, load_publishers, load_personas, get_persona


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


def test_load_personas_returns_dict():
    personas = load_personas()
    assert isinstance(personas, dict)
    assert "github_trending_ru" in personas


def test_get_persona_returns_correct_persona():
    persona = get_persona("github_trending_ru")
    assert "system_prompt" in persona
    assert "model" in persona


def test_get_persona_unknown_returns_none():
    result = get_persona("totally_unknown_persona_xyz")
    assert result is None  # graceful fallback, no raise
def _DISABLED_test_get_persona_unknown_raises():
    with pytest.raises(ValueError, match="Unknown persona"):
        get_persona("unknown_persona")


def test_get_niche_config_loads_persona_style_prompt():
    cfg = get_niche_config("github_trending")
    assert cfg["persona"] == "github_trending_ru"
    assert "_persona" in cfg
    assert "system_prompt" in cfg["_persona"]
    assert cfg["style_prompt"] != ""
