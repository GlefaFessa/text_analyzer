"""Пакет анализа текста.

Модули метрик:
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
    language_filter    — правила фильтрации метрик по языку
    lang_detect        — определение языка по алфавиту
    file_parsers       — парсеры файлов (txt, docx) + оценка времени
    genre_presets      — пресеты по жанрам текста

Отдельно (не импортируется автоматически):
    charts             — фабрики графиков Plotly. Не импортируется здесь,
                         потому что тянет plotly (~30 МБ) и нужен только UI.
                         Импортируется явно в app.py.

Главная точка входа:
    >>> from analyzer.report import collect
    >>> metrics = collect(text, lang="ru")
"""

# Явные импорты всех модулей пакета.
#
# Зачем это нужно:
# 1. PyInstaller собирает зависимости, анализируя импорты. Если модуль
#    не импортируется явно, он может не попасть в exe.
# 2. IDE (VSCode/Pylance) лучше подсказывает автодополнение `analyzer.X`.
# 3. Явный список документирует, что за модули есть в пакете.
#
# Тяжёлые зависимости (spaCy, torch, StyloMetrix) не загружаются здесь:
# они импортируются лениво, внутри своих модулей. Так `import analyzer`
# остаётся быстрым.

from . import (
    basic,
    file_parsers,
    genre_presets,
    lang_detect,
    language_filter,
    lexical,
    metric_info,
    morphology,
    readability,
    report,
    stylometry,
    syntax,
    text_utils,
)

__all__ = [
    "basic",
    "file_parsers",
    "genre_presets",
    "lang_detect",
    "language_filter",
    "lexical",
    "metric_info",
    "morphology",
    "readability",
    "report",
    "stylometry",
    "syntax",
    "text_utils",
]