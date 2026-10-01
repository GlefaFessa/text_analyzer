"""Удаляет кэш, тесты и метаданные внутри site-packages.

Экономит ~150-250 МБ. Безопасно: Python пересоздаёт .pyc при первом
запуске, а dist-info нужен только для pip uninstall/show.

ВАЖНО: не удаляйте dist-info у пакетов, если планируете их
uninstall позже — pip не сможет их найти.
"""

import shutil
import sys
from pathlib import Path


def find_site_packages() -> Path:
    """Находит site-packages текущего venv."""
    for p in sys.path:
        if p.endswith("site-packages") and "venv" in p.lower():
            return Path(p)
    raise RuntimeError("site-packages не найден. Запустите скрипт внутри venv.")


def human_size(bytes_: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if bytes_ < 1024:
            return f"{bytes_:.1f} {unit}"
        bytes_ /= 1024
    return f"{bytes_:.1f} TB"


def dir_size(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def clean(site: Path) -> None:
    removed_size = 0
    removed_count = 0

    # 1. __pycache__ — кэш байт-кода. Python пересоздаст при запуске.
    for path in site.rglob("__pycache__"):
        if path.is_dir():
            size = dir_size(path)
            shutil.rmtree(path, ignore_errors=True)
            removed_size += size
            removed_count += 1

    # 2. *.pyc и *.pyo — отдельные файлы кэша.
    for ext in ("*.pyc", "*.pyo"):
        for path in site.rglob(ext):
            try:
                removed_size += path.stat().st_size
                path.unlink()
                removed_count += 1
            except OSError:
                pass

    # 3. tests/ внутри пакетов — не нужны в рантайме.
    for path in site.rglob("tests"):
        if path.is_dir() and "site-packages" in str(path):
            # Не трогаем tests самого pytest.
            if "pytest" in str(path).lower():
                continue
            size = dir_size(path)
            shutil.rmtree(path, ignore_errors=True)
            removed_size += size
            removed_count += 1

    print(f"Удалено: {removed_count} объектов, {human_size(removed_size)}")


if __name__ == "__main__":
    site = find_site_packages()
    print(f"site-packages: {site}")
    clean(site)