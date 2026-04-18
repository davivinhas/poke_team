import pytest

from src.domain.value_objects.ivs import IVs


def test_create_ivs():
    ivs = IVs(1, 2, 3, 4, 5, 6)
    assert ivs.hp == 1
    assert ivs.attack == 2
    assert ivs.defense == 3
    assert ivs.special_attack == 4
    assert ivs.special_defense == 5
    assert ivs.speed == 6


def test_create_ivs_with_negative_values():
    with pytest.raises(ValueError):
        IVs(-1, 0, 1, 2, 3, 4)
    with pytest.raises(ValueError):
        IVs(0, -1, 1, 2, 3, 4)
    with pytest.raises(ValueError):
        IVs(1, 1, -1, 2, 3, 4)
    with pytest.raises(ValueError):
        IVs(1, 1, 1, -1, 3, 4)
    with pytest.raises(ValueError):
        IVs(1, 1, 1, 1, -1, 4)
    with pytest.raises(ValueError):
        IVs(1, 1, 1, 1, 1, -1)


def test_create_ivs_greather_than_limit():
    with pytest.raises(ValueError):
        IVs(32, 1, 1, 1, 1, 1)
    with pytest.raises(ValueError):
        IVs(1, 32, 1, 1, 1, 1)
    with pytest.raises(ValueError):
        IVs(1, 1, 32, 1, 1, 1)
    with pytest.raises(ValueError):
        IVs(1, 1, 1, 32, 1, 1)
    with pytest.raises(ValueError):
        IVs(1, 1, 1, 1, 32, 1)
    with pytest.raises(ValueError):
        IVs(1, 1, 1, 1, 1, 32)
