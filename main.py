"""Точка входа: консольный анализатор текста."""

import argparse
import sys
from pathlib import Path

from analyzer.report import collect

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*easy words vocabulary.*")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Анализатор текста: считает базовые метрики."
    )
    parser.add_argument(
        "-f", "--file",
        type=Path,
        help="Путь к файлу с текстом. Если не указан — читается stdin.",
    )
    parser.add_argument(
        "-l", "--lang",
        choices=["ru", "en"],
        default="ru",
        help="Язык текста (по умолчанию ru).",
    )
    parser.add_argument(
        "-g", "--groups",
        nargs="+",
        help="Какие группы метрик считать (например: basic lexical).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Вывести результат как JSON.",
    )
    parser.add_argument("-p", "--precision", type=int, default=4,
                        help="Знаков после запятой (по умолчанию 4).")
    
    parser.add_argument("--top", type=int, default=0,
                        help="Вывести топ-N слов текста (0 — не выводить).")
    return parser.parse_args()

def read_input(path: Path | None) -> str:
    if path is None:
        return sys.stdin.read()
    return path.read_text(encoding="utf-8")

def print_table(metrics: dict, precision: int = 4) -> None:
    """Печатает метрики, округляя float до precision знаков."""
    width = max(len(k) for k in metrics) if metrics else 0
    for key, value in sorted(metrics.items()):
        if isinstance(value, float):
            print(f"{key:<{width}}  {value:>14.{precision}f}")
        else:
            print(f"{key:<{width}}  {value:>14}")

def print_top_words(items: list[tuple[str, int]]) -> None:
    """Печатает список (слово, частота)."""
    print()
    print(f"Топ-{len(items)} слов в тексте:")
    for i, (word, count) in enumerate(items, 1):
        print(f"  {i:>3}. {word:<20} {count}")

def main() -> None:
    args = parse_args()
    text = read_input(args.file)
    metrics = collect(text, lang=args.lang, groups=args.groups)

    if args.json:
        import json
        print(json.dumps(metrics, ensure_ascii=False, indent=2))
    else:
        print_table(metrics, precision=args.precision)
    if args.top > 0:
        from analyzer.lexical import top_words
        print_top_words(top_words(text, args.top))

if __name__ == "__main__":
    main()