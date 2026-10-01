"""
Метрики стилометрии на основе StyloMetrix.
StyloMetrix возвращает вектор интерпретируемых метрик: доли
грамматических форм, синтаксических конструкций, лексических
признаков. Для русского — ~95 метрик, для английского — ~150.
Каждая метрика нормализована: количество вхождений делённое
на общее число токенов. Это позволяет сравнивать тексты
разной длины.
"""

# Кэш объектов StyloMetrix по языку.
# Создание объекта — дорогая операция (загружает spaCy-модель),
# поэтому делаем это лениво и один раз.
_SM = {}


def _get_sm(lang: str):
    """Ленивая инициализация StyloMetrix для указанного языка."""
    if lang not in ("ru", "en"):
        raise ValueError(f"Неподдерживаемый язык: {lang}")
    if lang not in _SM:
        from stylo_metrix.stylo_metrix import StyloMetrix
        _SM[lang] = StyloMetrix(lang=lang)
    return _SM[lang]


def compute(text: str, lang: str = "ru") -> dict:
    """Стилометрические метрики через StyloMetrix.

    Возвращает плоский словарь с префиксом 'stylometry.'.
    Ключи — оригинальные имена метрик StyloMetrix.
    """
    sm = _get_sm(lang)

    # transform принимает список текстов и возвращает DataFrame.
    # Мы передаём один текст и берём первую строку.
    try:
        df = sm.transform([text])
    except Exception:
        return {}

    if df.empty:
        return {}

    # Берём первую строку (единственный текст) и превращаем в словарь.
    # Отбрасываем колонку 'text' — это исходный текст, не метрика.
    row = df.iloc[0]
    result = {}
    for key, value in row.items():
        if key == "text":
            continue
        try:
            v = float(value)
        except (TypeError, ValueError):
            continue
        # Пропускаем nan и inf
        if v != v or v in (float("inf"), float("-inf")):
            continue
        result[f"stylometry.{key}"] = v

    return result

