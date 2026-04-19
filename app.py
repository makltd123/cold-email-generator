import os
import streamlit as st

from rag import build_index, retrieve_examples
from generator import generate_email

st.set_page_config(
    page_title="Cold Email Generator",
    page_icon="✉️",
    layout="wide",
)

st.markdown("""
<style>
    /* Global */
    [data-testid="stAppViewContainer"] { background: #0f1117; }
    [data-testid="stSidebar"] { display: none; }
    .block-container { padding: 2rem 3rem; }

    /* Typography */
    h1 { color: #f0f2f6; font-size: 1.8rem; font-weight: 700; margin-bottom: 0.2rem; }
    .subtitle { color: #8b9ab1; font-size: 0.95rem; margin-bottom: 2rem; }

    /* Form card */
    .form-card {
        background: #1a1d27;
        border: 1px solid #2a2d3a;
        border-radius: 12px;
        padding: 1.5rem;
    }

    /* Result card */
    .result-card {
        background: #1a1d27;
        border: 1px solid #2a2d3a;
        border-radius: 12px;
        padding: 1.5rem;
        min-height: 300px;
    }

    /* Subject label */
    .subject-label {
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        color: #5b8dee;
        text-transform: uppercase;
        margin-bottom: 0.3rem;
    }
    .subject-value {
        font-size: 1.05rem;
        font-weight: 600;
        color: #f0f2f6;
        margin-bottom: 1.2rem;
        padding: 0.6rem 0.8rem;
        background: #12151e;
        border-radius: 8px;
        border-left: 3px solid #5b8dee;
    }

    /* Body */
    .body-label {
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        color: #5b8dee;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }

    /* Generate button */
    div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #5b8dee, #3b6fd4);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.4rem;
        font-weight: 600;
        font-size: 0.95rem;
        width: 100%;
        transition: opacity 0.2s;
    }
    div[data-testid="stButton"] > button:hover { opacity: 0.88; }

    /* Labels */
    label { color: #c4cad6 !important; font-size: 0.88rem !important; }

    /* Inputs */
    input, textarea, select {
        background: #12151e !important;
        border: 1px solid #2a2d3a !important;
        border-radius: 8px !important;
        color: #f0f2f6 !important;
    }

    /* Selectbox */
    [data-testid="stSelectbox"] > div > div {
        background: #12151e !important;
        border: 1px solid #2a2d3a !important;
    }

    /* Radio */
    [data-testid="stRadio"] label { color: #c4cad6 !important; }

    /* Expander */
    [data-testid="stExpander"] {
        background: #12151e;
        border: 1px solid #2a2d3a;
        border-radius: 8px;
    }

    /* Divider */
    hr { border-color: #2a2d3a; }

    /* Empty state */
    .empty-state {
        color: #8b9ab1;
        text-align: center;
        padding: 3rem 1rem;
        font-size: 0.95rem;
    }
    .empty-state span { font-size: 2rem; display: block; margin-bottom: 0.8rem; }

    /* Example meta */
    .example-meta {
        font-size: 0.82rem;
        color: #8b9ab1;
        padding: 0.5rem 0;
        border-bottom: 1px solid #2a2d3a;
    }
    .example-meta:last-child { border-bottom: none; }
    .example-badge {
        display: inline-block;
        background: #1f2535;
        border: 1px solid #2a2d3a;
        border-radius: 4px;
        padding: 0.1rem 0.4rem;
        font-size: 0.75rem;
        color: #5b8dee;
        margin-right: 0.4rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def init_rag():
    return build_index()


def check_emails_exist() -> bool:
    emails_path = "./data/emails"
    if not os.path.isdir(emails_path):
        return False
    return any(f.endswith(".json") for f in os.listdir(emails_path))


# ── Header ──────────────────────────────────────────────────────────────────
st.markdown("<h1>✉️ Cold Email Generator</h1>", unsafe_allow_html=True)
st.markdown('<p class="subtitle">RAG-powered персонализация холодных B2B писем</p>', unsafe_allow_html=True)

# ── Layout ───────────────────────────────────────────────────────────────────
col_form, col_result = st.columns([1, 1.3], gap="large")

with col_form:
    st.markdown("**Параметры получателя**")

    niche = st.text_input(
        "Ниша получателя",
        placeholder="например: IT аутсорсинг, e-commerce, SaaS",
        key="niche",
    )
    recipient_type = st.selectbox(
        "Должность получателя",
        options=["CEO", "CMO", "CTO", "CFO", "COO", "HR", "VP Sales", "CPO", "Other"],
        key="recipient_type",
    )
    language = st.radio(
        "Язык письма",
        options=["RU", "EN"],
        horizontal=True,
        key="language",
    )
    product_description = st.text_area(
        "Описание вашего продукта (опционально)",
        placeholder="Кратко опишите что вы предлагаете...",
        height=100,
        key="product_description",
    )
    st.markdown("")
    generate_btn = st.button("Сгенерировать письмо", use_container_width=True)

with col_result:
    if not generate_btn:
        st.markdown(
            '<div class="empty-state"><span>📝</span>Заполните форму слева и нажмите «Сгенерировать письмо»</div>',
            unsafe_allow_html=True,
        )
    else:
        if not check_emails_exist():
            st.warning("Добавьте примеры писем в /data/emails/ (JSON-файлы)")
        else:
            try:
                with st.spinner("Подбираю примеры и генерирую письмо..."):
                    index, _ = init_rag()
                    lang_code = language.lower()
                    examples = retrieve_examples(index, niche, recipient_type, lang_code)
                    result = generate_email(niche, recipient_type, lang_code, product_description, examples)

                subject = result.get("subject", "")
                body = result.get("body", "")

                if subject:
                    st.markdown('<div class="subject-label">Тема письма</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="subject-value">{subject}</div>', unsafe_allow_html=True)

                st.markdown('<div class="body-label">Письмо</div>', unsafe_allow_html=True)
                st.markdown(body)

                st.markdown("---")
                st.markdown("**Скопировать письмо:**")
                copy_text = f"Subject: {subject}\n\n{body}" if subject else body
                st.code(copy_text, language=None)

                if examples:
                    with st.expander("📚 Использованные примеры"):
                        for ex in examples:
                            badge_niche = ex.get("niche", "—")
                            badge_role = ex.get("recipient_type", "—")
                            badge_lang = ex.get("language", "—").upper()
                            subj = ex.get("subject", "")
                            st.markdown(
                                f'<div class="example-meta">'
                                f'<span class="example-badge">{badge_role}</span>'
                                f'<span class="example-badge">{badge_niche}</span>'
                                f'<span class="example-badge">{badge_lang}</span>'
                                f"<br><small>{subj}</small></div>",
                                unsafe_allow_html=True,
                            )

            except Exception as e:
                st.error(f"Ошибка при генерации: {e}")
