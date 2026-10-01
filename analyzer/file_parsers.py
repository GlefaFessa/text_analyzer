"""Парсеры файлов для импорта текста в анализатор.

Каждый парсер принимает bytes (то, что отдаёт st.file_uploader)
и возвращает plain text. Ошибки парсинга поднимают ValueError
с человекочитаемым сообщением — UI покажет его пользователю.
"""

import io


def parse_txt(data: bytes) -> str:
    """Читает .txt/.md с автоопределением кодировки.

    Пробует по очереди: UTF-8 с BOM, UTF-16, UTF-8, cp1251.
    Последний fallback — latin-1, декодирует любой байт.
    """
    for encoding in ("utf-8-sig", "utf-16", "utf-8", "cp1251"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    # latin-1 не бросает исключений никогда — это страховка от падения.
    return data.decode("latin-1", errors="replace")


def parse_docx(data: bytes) -> str:
    """Извлекает текст из .docx (Word 2007+).

    .docx — это zip-архив с XML внутри. python-docx разбирает его
    и даёт доступ к параграфам и таблицам.

    Абзацы разделяются двойным переводом строки, чтобы структура
    текста сохранилась для метрик вроде basic.paragraphs.
    Таблицы склеиваются в строки через " | " — тоже с пустой строкой
    между блоками.
    """
    try:
        from docx import Document
    except ImportError as e:
        raise ValueError(
            "Для импорта .docx установите python-docx: pip install python-docx"
        ) from e

    try:
        doc = Document(io.BytesIO(data))
    except Exception as e:
        raise ValueError(f"Не удалось открыть .docx: {e}") from e

    parts = []

    # Параграфы — основной текст.
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            parts.append(text)

    # Таблицы — отдельно. Полезно, если в документе есть статистика.
    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            line = " | ".join(c for c in cells if c)
            if line:
                parts.append(line)

    return "\n\n".join(parts)


# Реестр парсеров по расширению.
# Чтобы добавить epub/fb2 — дописать одну строку сюда и написать функцию.
PARSERS = {
    "txt": parse_txt,
    "md": parse_txt,
    "docx": parse_docx,
}


def parse_file(filename: str, data: bytes) -> str:
    """Парсит файл по расширению. ValueError, если формат не поддерживается."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    parser = PARSERS.get(ext)
    if parser is None:
        raise ValueError(
            f"Формат .{ext} не поддерживается. "
            f"Доступные: {', '.join(sorted(PARSERS.keys()))}."
        )
    return parser(data)

# Секунд на 1000 слов для каждого модуля.
# Значения — эмпирические, замерены на русском тексте ~110k слов
# при полном анализе (≈60 секунд суммарно).
# Английский медленнее в 2-4 раза из-за transformer-моделей.
SPEED_PER_1K_WORDS = {
    "basic": 0.005,
    "lexical": 0.02,
    "readability": 0.05,
    "morphology": {"ru": 0.1, "en": 0.5},
    "syntax": {"ru": 0.15, "en": 0.5},
    "stylometry": {"ru": 0.3, "en": 0.7},
}

# Дополнительное время на первую загрузку моделей.
# При повторных запусках результат берётся из кэша, поэтому overhead
# не добавляется — но пользователю важнее знать worst case.
OVERHEAD_SECONDS = {
    "ru": 3.0,   # spaCy ru_core_news_lg
    "en": 8.0,   # torch + en_core_web_trf
}


def estimate_time(words: int, groups: list[str], lang: str) -> float:
    """Оценочное время анализа в секундах.

    words — число слов в тексте (basic.words).
    groups — какие группы выбраны.
    lang — 'ru' или 'en'.

    Возвращает примерное время: сумма по модулям + overhead на модели.
    Может ошибаться в 1.5-2 раза, но порядок величины верный.
    """
    if words <= 0 or not groups:
        return 0.0

    total = 0.0
    for g in groups:
        speed = SPEED_PER_1K_WORDS.get(g, 0.0)
        if isinstance(speed, dict):
            speed = speed.get(lang, 0.5)
        total += speed * (words / 1000)

    # Overhead добавляем, только если выбраны модули, которые грузят модели.
    needs_models = any(g in groups for g in ("morphology", "syntax", "stylometry"))
    if needs_models:
        total += OVERHEAD_SECONDS.get(lang, 5.0)

    return total


def format_time(seconds: float) -> str:
    """Человекочитаемая длительность: 'меньше секунды', '~15 сек', '~2 мин'."""
    if seconds < 1:
        return "меньше секунды"
    if seconds < 60:
        return f"~{int(round(seconds))} сек"
    minutes = seconds / 60
    return f"~{minutes:.1f} мин"