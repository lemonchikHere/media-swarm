import pytest
from src.config_loader import load_niches, get_niche_config, load_publishers


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
