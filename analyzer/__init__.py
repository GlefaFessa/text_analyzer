"""Пакет анализа текста.

Модули:
    basic         — счётные метрики (символы, слова, слоги, абзацы)
    lexical       — лексическое разнообразие и частотные характеристики
    readability   — формулы читабельности (textstat + ruts + Оборнева)
    morphology    — морфология (pymorphy3 для ru, spaCy для en)
    syntax        — синтаксис через деревья зависимостей spaCy
    stylometry    — стилометрические метрики StyloMetrix

Инфраструктура:
    report             — оркестратор, собирает метрики всех модулей
    text_utils         — очистка и токенизация текста
    metric_info        — описания метрик для UI
    charts             — фабрики графиков Plotly
    language_filter    — правила фильтрации метрик по языку
    lang_detect        — определение языка по алфавиту
    file_parsers       — парсеры файлов (txt, docx) + оценка времени
    genre_presets      — пресеты по жанрам текста

Главная точка входа:
    >>> from analyzer.report import collect
    >>> metrics = collect(text, lang="ru")
"""

# Явные импорты всех модулей.
#
# Зачем это нужно:
# 1. PyInstaller находит модули по импортам. Если модуль нигде
#    явно не импортируется, он может не попасть в сборку exe.
# 2. IDE (VSCode/Pylance) подсказывает автодополнение для `analyzer.X`.
# 3. Явный список — это документация: что за модули есть в пакете.
#
# Не импортируем тяжёлые зависимости (spaCy, torch, StyloMetrix)
# на уровне пакета — они загружаются лениво внутри своих модулей,
# чтобы `import analyzer` был быстрым.

from . import (
    basic,
    lexical,
    readability,
    morphology,
    syntax,
    stylometry,
    report,
    text_utils,
    metric_info,
    language_filter,
    lang_detect,
    file_parsers,
    genre_presets,
)

# charts импортируется отдельно — он тянет plotly, который
# нужен только UI. Если analyzer используется в CLI без графиков,
# plotly не загружается.
# from . import charts   ← закомментировано намеренно

__all__ = [
    "basic",
    "lexical",
    "readability",
    "morphology",
    "syntax",
    "stylometry",
    "report",
    "text_utils",
    "metric_info",
    "language_filter",
    "lang_detect",
    "file_parsers",
    "genre_presets",
]