import pytest

from src.domain.value_objects.base_stats import BaseStats


def test_create_base_stats():
    base_stats = BaseStats(1, 2, 3, 4, 5, 6)
    assert base_stats.hp == 1
    assert base_stats.attack == 2
    assert base_stats.defense == 3
    assert base_stats.special_attack == 4
    assert base_stats.special_defense == 5
    assert base_stats.speed == 6


def test_create_base_stats_greather_than_limit():
    with pytest.raises(ValueError):
        BaseStats(256, 2, 3, 4, 5, 6)
    with pytest.raises(ValueError):
        BaseStats(1, 256, 3, 4, 5, 6)
    with pytest.raises(ValueError):
        BaseStats(1, 2, 256, 4, 5, 6)
    with pytest.raises(ValueError):
        BaseStats(1, 2, 3, 256, 5, 6)
    with pytest.raises(ValueError):
        BaseStats(1, 2, 3, 4, 256, 6)
    with pytest.raises(ValueError):
        BaseStats(1, 2, 3, 4, 5, 256)


def test_create_base_stats_with_negative_values():
    with pytest.raises(ValueError):
        BaseStats(-1, 0, 1, 2, 3, 4)
    with pytest.raises(ValueError):
        BaseStats(0, -1, 1, 2, 3, 4)
    with pytest.raises(ValueError):
        BaseStats(1, 1, -1, 2, 3, 4)
    with pytest.raises(ValueError):
        BaseStats(1, 1, 1, -1, 3, 4)
    with pytest.raises(ValueError):
        BaseStats(1, 1, 1, 1, -1, 4)
    with pytest.raises(ValueError):
        BaseStats(1, 1, 1, 1, 1, -1)
