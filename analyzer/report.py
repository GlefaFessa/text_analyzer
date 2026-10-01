"""Сборщик отчёта: вызывает все модули метрик и соедииняет результаты."""

from . import basic, lexical, readability, morphology, syntax, stylometry, seo

MODULES = [basic, lexical, readability, morphology, syntax, stylometry, seo]


def collect(text: str, lang: str = "ru", groups: list[str] | None = None) -> dict:
    """Считает все метрики для текста.

    groups — если задан, оставляет только метрики из указанных групп
    (например, ['basic'] или ['basic', 'lexical']).
    """
    result: dict = {}
    for module in MODULES:
        name = module.__name__.split(".")[-1]  # 'basic', 'lexical' и т.д.
        if groups and name not in groups:
            continue
        result.update(module.compute(text, lang))
    return result