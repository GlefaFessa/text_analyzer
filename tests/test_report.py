"""Интеграционный тест: полный pipeline collect()."""

import pytest

from analyzer.report import collect


@pytest.fixture
def sample_ru():
    """Небольшой русский текст для тестов."""
    return "Мама мыла раму. Папа читал газету. Вечером дети играли во дворе."


@pytest.fixture
def sample_en():
    """Небольшой английский текст."""
    return "The cat sat on the mat. Dogs are barking outside."


def test_collect_ru_returns_all_groups(sample_ru):
    """Для русского — все группы метрик присутствуют."""
    metrics = collect(sample_ru, lang="ru")
    prefixes = {k.split(".")[0] for k in metrics}
    assert "basic" in prefixes
    assert "lexical" in prefixes
    assert "readability" in prefixes
    assert "morph" in prefixes
    assert "syntax" in prefixes
    assert "stylometry" in prefixes


def test_collect_en_returns_all_groups(sample_en):
    """Для английского — те же группы."""
    metrics = collect(sample_en, lang="en")
    prefixes = {k.split(".")[0] for k in metrics}
    assert "basic" in prefixes
    assert "readability" in prefixes
    assert "morph" in prefixes


def test_collect_groups_filter(sample_ru):
    """Если указаны группы — возвращаются только они."""
    metrics = collect(sample_ru, lang="ru", groups=["basic", "lexical"])
    prefixes = {k.split(".")[0] for k in metrics}
    assert prefixes == {"basic", "lexical"}


def test_collect_empty_text():
    """Пустой текст — не падаем."""
    metrics = collect("", lang="ru")
    assert metrics["basic.words"] == 0
    assert metrics["basic.sentences"] == 0


def test_collect_minimal_set(sample_ru):
    """Ключевые метрики точно присутствуют."""
    metrics = collect(sample_ru, lang="ru")
    required = [
        "basic.words",
        "lexical.ttr",
        "readability.oborneva",
        "morph.pos_noun_ratio",
        "syntax.avg_tree_depth",
    ]
    for key in required:
        assert key in metrics, f"Отсутствует метрика {key}"