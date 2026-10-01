"""Веб-интерфейс анализатора текста на Streamlit.

Запуск: python -m streamlit run app.py
"""

import json
import warnings
from datetime import datetime

import streamlit as st
import matplotlib.pyplot as plt

from analyzer import charts
from analyzer.file_parsers import parse_file
from analyzer.genre_presets import GENRE_PRESETS, get_genre
from analyzer.lang_detect import confidence
from analyzer.lang_detect import detect as detect_lang
from analyzer.language_filter import explain_hidden, filter_by_lang
from analyzer.metric_info import get_direction, get_info
from analyzer.report import MODULES

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*easy words vocabulary.*")

# ============ Настройки страницы ============
st.set_page_config(
    page_title="Анализатор текста",
    page_icon="📝",
    layout="wide",
)


# ============ Константы ============

# Модули анализа по имени.
MODULES_MAP = {m.__name__.split(".")[-1]: m for m in MODULES}

# Подгруппы стилометрии по префиксам имён метрик StyloMetrix.
# Порядок важен — он определяет порядок секций в UI.
STYLOMETRY_SUBGROUPS = [
    ("POS_", "Части речи", "Доли частей речи по разметке StyloMetrix."),
    ("G_", "Грамматика", "Времена, залоги, виды глаголов, причастия, деепричастия."),
    ("L_", "Лексика", "Типы существительных, прилагательных, местоимений, пунктуация."),
    ("SY_", "Синтаксис", "Типы предложений, вводные слова, кавычки, вопросы."),
    ("M_", "Морфология", "Род, число, падеж в разметке StyloMetrix."),
    ("C_", "Стиль", "Стилистические признаки."),
    ("D_", "Словари", "Принадлежность слов к тематическим спискам."),
    ("E_", "Ошибки", "Признаки ошибок и аномалий."),
]

# Русские названия групп.
GROUP_LABELS = {
    "basic": "Базовые",
    "lexical": "Лексика",
    "readability": "Читабельность",
    "morphology": "Морфология",
    "syntax": "Синтаксис",
    "stylometry": "Стилометрия",
    "seo": "SEO-аналитика",
}

# Пресеты — типовые наборы групп.
PRESETS = {
    "Быстрый (~1 сек)": ["basic", "lexical"],
    "Стандартный (~5 сек)": ["basic", "lexical", "readability", "morphology", "syntax"],
    "Полный (~15 сек)": ["basic", "lexical", "readability", "morphology", "syntax", "stylometry", "seo"],
    "SEO (~5 сек)": ["basic", "lexical", "seo"],
}


# ============ Служебные функции ============

@st.cache_data(show_spinner=False)

def render_charts(metrics: dict, text: str, lang: str) -> None:
    """Рендерит вкладку с графиками."""
    from analyzer.lexical import top_words
    from analyzer.text_utils import sentences as sent_split

    # 1. Профиль текста — радар. Самый верхний, потому что самый заметный.
    st.plotly_chart(
        charts.text_profile_radar(metrics, lang),
        use_container_width=True,
    )

    st.divider()

    # 2. Читабельность + покрытие частот — в две колонки.
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(
            charts.readability_bar(metrics, lang),
            use_container_width=True,
        )
    with col2:
        st.plotly_chart(
            charts.coverage_pie(metrics),
            use_container_width=True,
        )

    st.divider()

    # 3. POS + падежи — в две колонки.
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(
            charts.pos_pie(metrics),
            use_container_width=True,
        )
    with col2:
        if lang == "ru":
            st.plotly_chart(
                charts.case_bar(metrics),
                use_container_width=True,
            )
        else:
            st.info("Падежи доступны только для русского языка.")

    st.divider()

    # 4. Гистограмма длин предложений + топ-слов.
    # Длины пересчитываем из текста — они не входят в metrics.
    sent_lengths = [len(s.split()) for s in sent_split(text) if s.split()]
    if sent_lengths:
        st.plotly_chart(
            charts.sentence_length_histogram(sent_lengths),
            use_container_width=True,
        )

    words = top_words(text, 25)
    if words:
        st.plotly_chart(
            charts.top_words_bar(words),
            use_container_width=True, 
        )

def render_group(metrics: dict, precision: int) -> None:
    """Рендерит одну группу метрик: таблицу + раскрывающиеся справки.

    Для stylometry разбивает метрики на подгруппы по префиксам —
    иначе 95+ строк идут сплошной простыней.
    """
    if not metrics:
        st.info("Нет метрик в этой группе.")
        return

    # Спец-обработка стилометрии.
    is_stylometry = all(k.startswith("stylometry.") for k in metrics.keys())
    if is_stylometry:
        subgroups = split_stylometry(metrics)
        for prefix, name, desc, sub_metrics in subgroups:
            st.subheader(name)
            st.caption(desc)
            _render_table(sub_metrics, precision)
            st.write("")  # небольшой отступ между подгруппами
        return

    # Обычная группа — одна таблица.
    _render_table(metrics, precision)

    with st.expander("📖 Полные справки по метрикам группы"):
        for key in sorted(metrics.keys()):
            info = get_info(key)
            if not info:
                continue
            st.markdown(f"**{info.get('name', key)}** — {info.get('short', '')}")
            if info.get("full"):
                st.caption(info["full"])
            if info.get("wiki"):
                st.markdown(f"[Подробнее на Wikipedia →]({info['wiki']})")
            st.divider()

def render_seo(metrics: dict, text: str, lang: str, precision: int) -> None:
    """Рендерит вкладку SEO-аналитики."""
    from analyzer.seo import keywords

    st.subheader("🎯 SEO-аналитика")
    st.caption(
        "Классические метрики из арсенала копирайтеров и SEO-специалистов. "
        "Считаются по леммам: «мама» и «мамы» — одно слово."
    )

    # Плашки ключевых значений.
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Водность",
        f"{metrics.get('seo.water_ratio', 0):.{precision}f}%",
        help="< 15% — хорошо, 15–30% — средне, > 30% — плохо.",
    )
    c2.metric(
        "Заспамленность",
        f"{metrics.get('seo.spam_ratio', 0):.{precision}f}%",
        help="< 30% — хорошо, 30–60% — средне, > 60% — плохо.",
    )
    c3.metric(
        "Классическая тошнота",
        f"{metrics.get('seo.classic_nausea', 0):.{precision}f}",
        help="√(частота топ-слова). Норма до 7.",
    )
    c4.metric(
        "Академическая тошнота",
        f"{metrics.get('seo.academic_nausea', 0):.{precision}f}%",
        help="Доля топ-слова в тексте. Норма 5–15%.",
    )

    # Графики.
    st.divider()
    col_left, col_right = st.columns(2)
    with col_left:
        st.plotly_chart(
            charts.seo_quality_bar(metrics),
            use_container_width=True,
        )
    with col_right:
        kw = keywords(text, lang, top=15)
        if kw:
            st.plotly_chart(
                charts.keywords_bar(kw, 15),
                use_container_width=True,
            )
    # Облако слов — на всю ширину, под двумя графиками.
    st.divider()
    kw_all = keywords(text, lang, top=50)
    if kw_all:
        wc_fig = charts.wordcloud_figure(kw_all, max_words=50)
        if wc_fig is not None:
            st.pyplot(wc_fig, use_container_width=False)
            plt.close(wc_fig)

    # Таблица ключевых слов.
    st.divider()
    st.subheader("Ключевые слова")
    st.caption("Топ-20 слов по частоте, без стоп-слов, с лемматизацией.")
    kw_all = keywords(text, lang, top=20)
    if kw_all:
        rows = [{"Слово": w, "Частота": c} for w, c in kw_all]
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info("Нет ключевых слов — текст пуст или состоит из одних стоп-слов.")

def render_genre(metrics: dict, genre_key: str, precision: int) -> None:
    """Рендерит вкладку с ключевыми метриками выбранного жанра."""
    genre = get_genre(genre_key)
    if not genre:
        return

    # Описание жанра.
    st.subheader(genre["name"])
    st.caption(genre["description"])

    st.divider()

    # Ключевые метрики — карточками в две колонки.
    st.markdown("### Ключевые метрики")
    key_metrics = genre["key_metrics"]

    # Оставляем только те метрики, которые посчитаны (могли попасть в hidden).
    available = [k for k in key_metrics if k in metrics]

    if not available:
        st.warning(
            "Ни одна из ключевых метрик для этого жанра не посчитана. "
            "Проверьте, что выбраны нужные группы метрик."
        )
        return

    # Раскладываем по колонкам — по 2 метрики в ряд.
    for i in range(0, len(available), 2):
        cols = st.columns(2)
        for j, key in enumerate(available[i:i + 2]):
            with cols[j]:
                info = get_info(key)
                name = info.get("name", key.split(".")[-1])
                value = metrics[key]

                if isinstance(value, float):
                    val_str = f"{value:.{precision}f}"
                elif isinstance(value, int):
                    val_str = f"{value:,}"
                else:
                    val_str = str(value)

                st.metric(label=name, value=val_str)

                # Подпись под метрикой — что означает / направление.
                short = info.get("short", "")
                direction = get_direction(key)
                if short or direction:
                    caption = short
                    if direction:
                        caption = f"{direction} · {caption}" if caption else direction
                    st.caption(caption)

    # Подсказки «на что смотреть».
    st.divider()
    st.markdown("### На что смотреть")
    for hint in genre["hints"]:
        st.markdown(f"- {hint}")

def _render_table(metrics: dict, precision: int) -> None:
    """Рендерит одну таблицу метрик."""
    if not metrics:
        return

    rows = []
    for key in sorted(metrics.keys()):
        value = metrics[key]
        info = get_info(key)
        name = info.get("name", key.split(".")[-1])
        short = info.get("short", "")
        direction = get_direction(key)         

        if isinstance(value, float):
            val_str = f"{value:.{precision}f}"
        elif isinstance(value, int):
            val_str = f"{value:,}"
        else:
            val_str = str(value)

        rows.append({                           
            "Метрика": name,
            "Значение": val_str,
            "Шкала": direction,
            "Пояснение": short,
        })

    st.dataframe(rows, use_container_width=True, hide_index=True)

def group_of(key: str) -> str:
    """Определяет группу метрики по её префиксу."""
    prefix = key.split(".", 1)[0]
    return {
        "basic": "basic",
        "lexical": "lexical",
        "readability": "readability",
        "morph": "morphology",
        "syntax": "syntax",
        "stylometry": "stylometry",
    }.get(prefix, "")

def split_stylometry(metrics: dict) -> list[tuple[str, str, str, dict]]:
    """Разбивает метрики stylometry.* на подгруппы по префиксам.

    Возвращает список кортежей:
        (префикс, название, описание, метрики_подгруппы)

    Метрики, не попавшие ни в одну подгруппу (нестандартный префикс),
    собираются в последнюю секцию «Прочее».
    """
    buckets: dict[str, dict] = {prefix: {} for prefix, _, _ in STYLOMETRY_SUBGROUPS}

    for key, value in metrics.items():
        if not key.startswith("stylometry."):
            continue
        short = key[len("stylometry."):]
        placed = False
        for prefix, _, _ in STYLOMETRY_SUBGROUPS:
            if short.startswith(prefix):
                buckets[prefix][key] = value
                placed = True
                break
        if not placed:
            buckets.setdefault("_other", {})[key] = value

    result = []
    for prefix, name, desc in STYLOMETRY_SUBGROUPS:
        if buckets.get(prefix):
            result.append((prefix, name, desc, buckets[prefix]))
    if buckets.get("_other"):
        result.append(("_other", "Прочее", "Метрики с нестандартным префиксом.",
                       buckets["_other"]))
    return result


# ============ Sidebar ============

with st.sidebar:
    st.header("⚙️ Настройки")

    lang_mode = st.selectbox(
        "Язык текста",
        ["ru", "en", "auto"],
        format_func=lambda x: {"ru": "🇷🇺 Русский", "en": "🇬🇧 English", "auto":"Автоматически"}[x],
        help="От языка зависят морфология, стилометрия и часть формул читабельности.",
    )

    genre_key = st.selectbox(
        "Жанр текста (опционально)",
        options=["none"] + list(GENRE_PRESETS.keys()),
        format_func=lambda k: (
            "— без жанра —" if k == "none" else GENRE_PRESETS[k]["name"]
        ),
        help=(
            "Если выбрать жанр — появится вкладка с ключевыми метриками "
            "для этого типа текста и подсказками, на что смотреть."
        ),
    )

    preset = st.radio(
        "Пресет",
        list(PRESETS.keys()),
        index=1,
        help="Готовый набор групп метрик. Можно скорректировать вручную ниже.",
    )

    groups = st.multiselect(
        "Группы метрик",
        options=list(GROUP_LABELS.keys()),
        default=PRESETS[preset],
        format_func=lambda x: GROUP_LABELS[x],
        help="Что считать. Чем больше групп, тем дольше анализ.",
    )

    precision = st.slider(
        "Знаков после запятой",
        0, 6, 3,
        help="Только для отображения. На точность расчётов не влияет.",
    )




# ============ Заголовок ============

st.title("📝 Анализатор текста")
st.caption("Метрики читабельности, лексики, морфологии и синтаксиса")


# ============ Ввод текста ============

tab_file, tab_text = st.tabs(["📄 Загрузить файл", "📋 Вставить текст"])

with tab_file:
    uploaded = st.file_uploader(
        "Выберите файл .txt или .md или .docx",
        type=["txt", "md", "docx"],
        help="Поддерживаются только текстовые форматы. .epub, .fb2 — в разработке.",
    )
    file_text = ""
    if uploaded is not None:
        try:
            file_text = parse_file(uploaded.name, uploaded.read())
            st.success(
                f"Прочитано {len(file_text):,} символов "
                f"из «{uploaded.name}»"
            )
        except ValueError as e:
            st.error(str(e))

with tab_text:
    typed_text = st.text_area(
        "Введите или вставьте текст",
        height=250,
        placeholder="Начните печатать...",
    )

# Если файл загружен — приоритет ему. Иначе — введённый текст.
text = file_text or typed_text

# Кнопка «Анализировать» — под окном с текстом, в основной области.
run_btn = st.button(
    "🔍 Анализировать",
    type="primary",
    use_container_width=True,
)

# --- Оценка времени анализа ---
if text.strip():
    from analyzer.file_parsers import estimate_time, format_time
    from analyzer.lang_detect import detect as detect_lang
    from analyzer.text_utils import words as split_words

    approx_words = len(split_words(text))

    # Определяем язык для оценки скорости:
    # если пользователь выбрал явно — берём его, иначе — детектор.
    if lang_mode in ("ru", "en"):
        est_lang = lang_mode
    else:
        detected = detect_lang(text)
        est_lang = detected if detected in ("ru", "en") else "ru"

    if groups:
        est_seconds = estimate_time(approx_words, groups, est_lang)
        est_str = format_time(est_seconds)

        col_a, col_b, col_c = st.columns([1, 1, 1])
        col_a.metric("Слов в тексте", f"{approx_words:,}")
        col_b.metric("Оценка времени", est_str)
        col_c.metric("Язык", est_lang.upper())

        if est_seconds > 120:
            st.warning(
                "⚠️ Анализ займёт больше двух минут. "
                "Для интерактивной работы выберите меньше групп метрик."
            )
    else:
        st.info("Выберите хотя бы одну группу метрик в настройках слева.")


# ============ Анализ ============

@st.cache_data(show_spinner=False)
def run_module(name: str, text: str, lang: str) -> dict:
    """Вычисляет метрики одного модуля с кэшированием.

    @st.cache_data запоминает результат по ключу (name, text, lang).
    При повторных вызовах с теми же аргументами результат берётся
    из кэша — это критично для stylometry и morphology, которые
    работают 5-15 секунд.
    """
    module = MODULES_MAP[name]
    return module.compute(text, lang)

if run_btn:
    # Валидация.
    if not text.strip():
        st.warning("Введите текст или загрузите файл.")
        st.stop()

    if not groups:
        st.warning("Выберите хотя бы одну группу метрик.")
        st.stop()

        # --- Определение языка ---
    if lang_mode == "auto":
        detected = detect_lang(text)
        conf = confidence(text)
        if detected == "unknown":
            st.warning(
                "Не удалось определить язык"
                "Выберите язык вручную в настройках"
            )
            st.stop()
        lang = detected
        if conf < 0.85:
            st.warning(
                f"Язык определён как **{lang}** с уверенностью {conf:.0%}. "
                "Текст смешанный — возможно, стоит выбрать язык явно."
            )
    else:
        lang = lang_mode

    # Прогресс и анализ по модулям.
    progress = st.progress(0)
    metrics: dict = {}

    with st.status("Анализ текста...", expanded=True) as status:
        n = len(groups)
        for i, group in enumerate(groups, 1):
            label = GROUP_LABELS[group]
            status.write(f"⏳ {label}...")
            try:
                metrics.update(run_module(group, text, lang))
            except Exception as e:
                status.write(f"⚠️ {label}: ошибка — {type(e).__name__}: {e}")
            progress.progress(int(i / n * 100))

        status.update(
            label=f"✅ Готово — {len(metrics)} метрик",
            state="complete",
        )

    # Языковая фильтрация.
    visible, hidden = filter_by_lang(metrics, lang)

    # --- Плашки с ключевыми метриками ---
    st.divider()
    st.subheader("Ключевые показатели")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Слов",
        f"{metrics.get('basic.words', 0):,}",
        help="Слова выделяются регуляркой по буквам. Цифры и пунктуация не считаются.",
    )
    c2.metric(
        "Уникальных",
        f"{metrics.get('basic.unique_words', 0):,}",
        help="Число разных словоформ в нижнем регистре.",
    )
    c3.metric(
        "Предложений",
        f"{metrics.get('basic.sentences', 0):,}",
        help="Число предложений по конечным знакам . ! ? …",
    )
    c4.metric(
        "TTR",
        f"{metrics.get('lexical.ttr', 0.0):.{precision}f}",
        help="Type-Token Ratio = уникальные / все. 1.0 — все слова разные, 0.1 — сплошные повторы.",
    )

    # --- Вкладки с группами метрик ---
    st.divider()
    st.subheader("Все метрики")

    # Раскладываем метрики по группам.
    grouped: dict[str, dict] = {g: {} for g in groups}
    for key, value in metrics.items():
        g = group_of(key)
        if g in grouped:
            grouped[g][key] = value

    # Оставляем только непустые группы, в порядке выбора.
    non_empty = [(g, grouped[g]) for g in groups if grouped.get(g)]

    if non_empty:
        # Собираем список вкладок: графики + (жанр, если выбран) + группы метрик.
        # Определяем, какие спец-вкладки показывать.
        show_genre = genre_key != "none"
        show_seo = "seo" in groups

        # Спец-вкладки исключаются из обычных групп — их содержимое
        # показывается отдельно, не как таблица метрик.
        special_groups = set()
        if show_seo:
            special_groups.add("seo")
        non_empty_filtered = [(g, data) for g, data in non_empty if g not in special_groups]

        # Собираем имена вкладок.
        tab_names = ["📊 Графики"]
        if show_genre:
            tab_names.append("🎭 Жанр")
        if show_seo:
            tab_names.append("🎯 SEO")
        tab_names += [GROUP_LABELS[g] for g, _ in non_empty_filtered]

        tabs = st.tabs(tab_names)

        # Рендер вкладок по порядку.
        idx = 0
        with tabs[idx]:
            render_charts(metrics, text, lang)
        idx += 1

        if show_genre:
            with tabs[idx]:
                render_genre(metrics, genre_key, precision)
            idx += 1

        if show_seo:
            with tabs[idx]:
                render_seo(metrics, text, lang, precision)
            idx += 1

        for tab, (g, data) in zip(tabs[idx:], non_empty_filtered):
            with tab:
                render_group(data, precision)

    # --- Экспорт ---
    st.divider()
    col_dl, col_info = st.columns([1, 3])

    # --- Экспорт ---
    st.divider()
    col_dl, col_info = st.columns([1, 3])

    export = {
        "language": lang,
        "visible": visible,
        "hidden": hidden,
    }

    with col_dl:
        st.download_button(
            "📥 Скачать JSON",
            data=json.dumps(export, ensure_ascii=False, indent=2, default=str),
            file_name=f"metrics_{datetime.now():%Y%m%d_%H%M%S}.json",
            mime="application/json",
            use_container_width=True,
            help="Все метрики в формате JSON. Удобно для дальнейшей обработки.",
        )

    with col_info:
        st.info(
            f"Показано: {len(visible)} метрик · "
            f"скрыто: {len(hidden)} · "
            f"язык: {lang} · "
            f"групп: {len(groups)}"
        )

    # --- Скрытые метрики ---
    if hidden:
        with st.expander(f"🔒 Скрыто для языка ({len(hidden)} метрик)"):
            st.caption(
                "Эти метрики не применяются к выбранному языку. "
                "Наведите на ⓘ в справке группы, чтобы понять причину."
            )
            for key in sorted(hidden.keys()):
                info = get_info(key)
                name = info.get("name", key.split(".")[-1])
                reason = explain_hidden(key, lang)
                value = hidden[key]
                if isinstance(value, float):
                    val_str = f"{value:.{precision}f}"
                else:
                    val_str = str(value)
                st.markdown(f"**{name}** = `{val_str}` — {reason}")