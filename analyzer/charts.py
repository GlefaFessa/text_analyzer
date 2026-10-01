"""Фабрики графиков Plotly для анализатора текста.

Каждая функция принимает уже посчитанные метрики и возвращает
plotly.graph_objects.Figure. UI рендерит их через st.plotly_chart.

Стиль графиков согласован: палитра, размеры, шрифты.
"""

import plotly.graph_objects as go
import plotly.express as px

# Единая палитра — согласована с фиолетовым акцентом Streamlit.
COLORS = [
    "#7c3aed", "#a855f7", "#c084fc", "#d8b4fe",
    "#10b981", "#34d399", "#6ee7b7",
    "#f59e0b", "#fbbf24",
    "#ef4444", "#f87171",
]

# Единый layout — чтобы все графики выглядели как часть одного набора.
LAYOUT = dict(
    font=dict(family="Inter, sans-serif", size=13),
    margin=dict(l=40, r=20, t=50, b=40),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    height=420,
)


def _apply_layout(fig, title: str) -> go.Figure:
    """Применяет единый стиль к фигуре."""
    fig.update_layout(title=title, **LAYOUT)
    return fig


def sentence_length_histogram(sentences: list[int]) -> go.Figure:
    """Гистограмма длин предложений.

    sentences — список длин в словах. Показывает распределение:
    есть ли аномально длинные или короткие предложения.
    """
    fig = go.Figure(data=[go.Histogram(
        x=sentences,
        nbinsx=min(20, max(5, len(sentences) // 3)),
        marker_color=COLORS[0],
        opacity=0.85,
    )])
    fig.update_xaxes(title="Длина предложения, слов")
    fig.update_yaxes(title="Число предложений")
    return _apply_layout(fig, "Распределение длин предложений")


def top_words_bar(words: list[tuple[str, int]], n: int = 25) -> go.Figure:
    """Горизонтальный bar chart топ-N слов текста.

    words — список пар (слово, частота), упорядоченный по убыванию.
    Горизонтальный — потому что слова лучше читаются по горизонтали.
    """
    items = words[:n]
    labels = [w for w, _ in items][::-1]     # разворачиваем: сверху самое частое
    values = [c for _, c in items][::-1]

    fig = go.Figure(data=[go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker_color=COLORS[1],
        text=values,
        textposition="outside",
    )])
    fig.update_xaxes(title="Частота")
    fig.update_yaxes(title="")
    return _apply_layout(fig, f"Топ-{len(items)} слов")


def pos_pie(metrics: dict) -> go.Figure:
    """Круговая диаграмма долей частей речи.

    Показывает, что преобладает: существительные, глаголы, служебные слова.
    Пустые категории (0.0) не показываются, чтобы пирог не был разрезан впустую.
    """
    keys_labels = [
        ("morph.pos_noun_ratio", "Существительные"),
        ("morph.pos_verb_ratio", "Глаголы"),
        ("morph.pos_adj_ratio", "Прилагательные"),
        ("morph.pos_adv_ratio", "Наречия"),
        ("morph.pos_pron_ratio", "Местоимения"),
        ("morph.pos_adp_ratio", "Предлоги"),
        ("morph.pos_cconj_ratio", "Сочинит. союзы"),
        ("morph.pos_sconj_ratio", "Подчинит. союзы"),
        ("morph.pos_part_ratio", "Частицы"),
        ("morph.pos_num_ratio", "Числительные"),
    ]
    labels, values = [], []
    for key, label in keys_labels:
        v = metrics.get(key, 0.0)
        if v and v > 0.005:  # отсекаем шум < 0.5%
            labels.append(label)
            values.append(v)

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.45,               # «бублик» — выглядит современнее пирога
        marker_colors=COLORS,
        textinfo="label+percent",
        textposition="outside",
    )])
    return _apply_layout(fig, "Доли частей речи")


def case_bar(metrics: dict) -> go.Figure:
    """Bar chart долей падежей (только для русского)."""
    keys_labels = [
        ("morph.case_nomn_ratio", "Именительный"),
        ("morph.case_gent_ratio", "Родительный"),
        ("morph.case_datv_ratio", "Дательный"),
        ("morph.case_accs_ratio", "Винительный"),
        ("morph.case_ablt_ratio", "Творительный"),
        ("morph.case_loct_ratio", "Предложный"),
    ]
    labels, values = [], []
    for key, label in keys_labels:
        v = metrics.get(key, 0.0)
        labels.append(label)
        values.append(v)

    fig = go.Figure(data=[go.Bar(
        x=labels,
        y=values,
        marker_color=COLORS[2],
        text=[f"{v:.1%}" for v in values],
        textposition="outside",
    )])
    fig.update_yaxes(title="Доля среди слов с падежом", tickformat=".0%")
    return _apply_layout(fig, "Распределение падежей")


def coverage_pie(metrics: dict) -> go.Figure:
    """Круговая: какая часть текста входит в топ-N частотных слов языка."""
    c100 = metrics.get("lexical.coverage_top100", 0.0)
    c1000 = metrics.get("lexical.coverage_top1000", 0.0)
    c5000 = metrics.get("lexical.coverage_top5000", 0.0)
    c10000 = metrics.get("lexical.coverage_top10000", 0.0)

    # Разница между уровнями — сколько слов в каждой «зоне».
    in_top100 = c100
    in_100_1000 = max(0.0, c1000 - c100)
    in_1000_5000 = max(0.0, c5000 - c1000)
    in_5000_10000 = max(0.0, c10000 - c5000)
    beyond = max(0.0, 1.0 - c10000)

    fig = go.Figure(data=[go.Pie(
        labels=[
            "Топ-100 (очень частые)",
            "100–1000 (частые)",
            "1000–5000 (обычные)",
            "5000–10000 (редкие)",
            "Редкие (>10000)",
        ],
        values=[in_top100, in_100_1000, in_1000_5000, in_5000_10000, beyond],
        hole=0.45,
        marker_colors=COLORS,
        textinfo="label+percent",
        textposition="outside",
    )])
    return _apply_layout(fig, "Покрытие частотных зон")


def readability_bar(metrics: dict, lang: str) -> go.Figure:
    """Горизонтальный bar: индексы читабельности в одной шкале.

    Для английского — textstat-формулы; для русского — ruts.
    Все значения — «класс школы» (Grade Level), чтобы их можно было сравнивать.
    """
    if lang == "ru":
        keys_labels = [
            ("readability.ruts_flesch_kincaid_grade", "Flesch-Kincaid (ruts)"),
            ("readability.ruts_gunning_fog_index", "Gunning Fog (ruts)"),
            ("readability.ruts_smog_index", "SMOG (ruts)"),
            ("readability.ruts_automated_readability_index", "ARI (ruts)"),
            ("readability.ruts_coleman_liau_index", "Coleman-Liau (ruts)"),
            ("readability.ruts_matskovsky_index", "Мацковский"),
            ("readability.ruts_sis_grade", "SIS Grade"),
            ("readability.ruts_consensus_grade", "Consensus Grade"),
        ]
    else:
        keys_labels = [
            ("readability.flesch_kincaid_grade", "Flesch-Kincaid"),
            ("readability.gunning_fog", "Gunning Fog"),
            ("readability.smog", "SMOG"),
            ("readability.ari", "ARI"),
            ("readability.coleman_liau", "Coleman-Liau"),
        ]

    labels, values = [], []
    for key, label in keys_labels:
        v = metrics.get(key)
        if v is None:
            continue
        labels.append(label)
        values.append(v)

    fig = go.Figure(data=[go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker_color=[COLORS[i % len(COLORS)] for i in range(len(labels))],
        text=[f"{v:.1f}" for v in values],
        textposition="outside",
    )])
    fig.update_xaxes(title="Оценка в классах школы (Grade Level)")
    return _apply_layout(fig, "Читабельность — сравнение формул")

def _clip01(x: float) -> float:
    """Обрезает значение в [0, 1]."""
    return max(0.0, min(1.0, x))


def text_profile_radar(metrics: dict, lang: str) -> go.Figure:
    """Лепестковая диаграмма «профиль текста».

    Каждая ось — метрика, нормализованная к 0-1 по эмпирическим порогам.
    Пороги подобраны так, что 0 — «самое простое/минимальное»,
    1 — «самое сложное/максимальное» из встречающихся в реальных текстах.

    Шесть осей:
      - Длина предложений
      - Длина слов
      - Лексическое разнообразие
      - Сложные слова
      - Синтаксическая глубина
      - Лексическая редкость
    """
    avg_sent = metrics.get("basic.avg_sentence_len_words", 0.0)
    avg_word = metrics.get("basic.avg_word_len_chars", 0.0)
    ttr = metrics.get("lexical.ttr", 0.0)
    complex_ratio = metrics.get("basic.complex_words_ratio", 0.0)
    depth = metrics.get("syntax.avg_tree_depth", 0.0)
    rare = metrics.get("lexical.rare_words_ratio", 0.0)

    axes = ["Длина\nпредложений", "Длина\nслов", "Лексическое\nразнообразие",
            "Сложные\nслова", "Глубина\nдерева", "Редкая\nлексика"]

    # Эмпирические пороги: (min, max) для нормализации.
    # Значения подобраны по типичным текстам: от детских сказок до научных статей.
    values = [
        _clip01((avg_sent - 5) / 25),          # 5 → 0, 30 → 1
        _clip01((avg_word - 3) / 5),           # 3 → 0, 8 → 1
        _clip01(ttr / 1.0),                    # 0 → 0, 1.0 → 1
        _clip01(complex_ratio / 0.4),          # 0 → 0, 40% → 1
        _clip01((depth - 1) / 5),              # 1 → 0, 6 → 1
        _clip01(rare / 0.4),                   # 0 → 0, 40% → 1
    ]

    # Замыкаем круг — повторяем первую точку в конце.
    axes_closed = axes + [axes[0]]
    values_closed = values + [values[0]]

    fig = go.Figure(data=[go.Scatterpolar(
        r=values_closed,
        theta=axes_closed,
        fill="toself",
        fillcolor="rgba(124, 58, 237, 0.25)",
        line=dict(color=COLORS[0], width=2),
        name="Профиль текста",
    )])

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True, range=[0, 1],
                showticklabels=False,  # скрываем цифры — они условны
            ),
        ),
        showlegend=False,
        **LAYOUT,
    )
    return _apply_layout(fig, "Профиль текста (все оси: 0 = проще, 1 = сложнее)")

def seo_quality_bar(metrics: dict) -> go.Figure:
    """Bar: SEO-показатели в процентах с зонами нормы."""
    water = metrics.get("seo.water_ratio", 0.0)
    spam = metrics.get("seo.spam_ratio", 0.0)
    academic = metrics.get("seo.academic_nausea", 0.0)

    labels = ["Водность", "Заспамленность", "Академическая тошнота"]
    values = [water, spam, academic]

    # Цвета по норме: зелёный / жёлтый / красный.
    def color(value, good, bad):
        if value <= good:
            return COLORS[4]   # зелёный
        if value <= bad:
            return COLORS[7]   # жёлтый
        return COLORS[9]       # красный

    colors = [
        color(water, 15, 30),
        color(spam, 30, 60),
        color(academic, 15, 30),
    ]

    fig = go.Figure(data=[go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker_color=colors,
        text=[f"{v:.1f}%" for v in values],
        textposition="outside",
    )])
    fig.update_xaxes(title="Процент", range=[0, max(max(values) * 1.3, 40)])
    return _apply_layout(fig, "SEO-показатели (зелёный = норма)")


def keywords_bar(items: list, n: int = 15) -> go.Figure:
    """Bar: топ ключевых слов."""
    items = items[:n]
    labels = [w for w, _ in items][::-1]
    values = [c for _, c in items][::-1]

    fig = go.Figure(data=[go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker_color=COLORS[5],
        text=values,
        textposition="outside",
    )])
    fig.update_xaxes(title="Частота")
    return _apply_layout(fig, f"Топ-{len(items)} ключевых слов")

import os
from wordcloud import WordCloud
import matplotlib.pyplot as plt


def _get_cyrillic_font() -> str | None:
    """Ищет системный шрифт с поддержкой кириллицы.

    WordCloud по умолчанию использует DroidSansMono, который не содержит
    кириллических глифов — русские слова отображаются квадратами.
    """
    candidates = [
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
        r"C:\Windows\Fonts\verdana.ttf",
        r"C:\Windows\Fonts\tahoma.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def wordcloud_figure(items: list, max_words: int = 100) -> plt.Figure:
    """Облако слов из списка (слово, частота).

    items — список пар (слово, частота), упорядоченный по убыванию.
    max_words — сколько слов отрисовать.
    Возвращает matplotlib.figure.Figure для st.pyplot().
    """
    freq = dict(items[:max_words])
    font_path = _get_cyrillic_font()

    wc = WordCloud(
        width=1000,
        height=800,
        background_color=None,
        mode="RGBA",
        font_path=font_path,
        colormap="Purples",
        max_words=max_words,
        prefer_horizontal=0.9,
        relative_scaling=0.5,
        min_font_size=14,
        collocations=False,
    ).generate_from_frequencies(freq)

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    fig.patch.set_alpha(0)
    plt.tight_layout(pad=0)
    return fig