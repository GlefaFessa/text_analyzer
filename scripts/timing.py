"""Замер времени импорта каждого модуля analyzer."""

import sys
from pathlib import Path

# Добавляем корень проекта в sys.path, чтобы import analyzer работал
# при запуске скрипта из папки scripts.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import importlib
import time

# ... далее как было

"""Замер времени импорта каждого модуля analyzer."""

import importlib
import time

MODULES = [
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

print(f"{'Модуль':<20} {'Время, сек':>10}")
print("-" * 32)

total_start = time.perf_counter()
for name in MODULES:
    start = time.perf_counter()
    try:
        importlib.import_module(f"analyzer.{name}")
    except Exception as e:
        print(f"{name:<20} ОШИБКА: {e}")
        continue
    elapsed = time.perf_counter() - start
    print(f"{name:<20} {elapsed:>10.3f}")

print("-" * 32)
print(f"{'ИТОГО':<20} {time.perf_counter()-total_start:>10.3f}")