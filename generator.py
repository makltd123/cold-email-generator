from llama_index.llms.nvidia import NVIDIA

from config import NVIDIA_API_KEY, LLM_MODEL

SYSTEM_PROMPT = (
    "Ты эксперт по написанию холодных B2B писем. "
    "Тебе дают примеры успешных писем и параметры получателя. "
    "Напиши персонализированное холодное письмо, вдохновляясь стилем и структурой примеров, но не копируя их. "
    "Письмо должно быть коротким (до 150 слов), содержать конкретный icebreaker, одну боль клиента и чёткий CTA. "
    "Ответь ТОЛЬКО в формате:\nSubject: <тема>\n<тело письма>"
)


def _build_user_prompt(niche: str, recipient_type: str, language: str, product_description: str, examples: list[dict]) -> str:
    lang_label = "ru" if language.lower() == "ru" else "en"
    lang_instruction = "Письмо написать на русском языке." if lang_label == "ru" else "Write the email in English."

    examples_block = ""
    for i, ex in enumerate(examples, 1):
        examples_block += f"\n[Пример {i}]\nТема: {ex.get('subject', '')}\n{ex.get('body', '')}\n---"

    prompt = (
        f"Ниша: {niche}\n"
        f"Должность получателя: {recipient_type}\n"
        f"Язык: {language}. {lang_instruction}\n"
    )
    if product_description:
        prompt += f"Продукт отправителя: {product_description}\n"

    prompt += f"\nПримеры успешных писем:{examples_block}\n\nНапиши тему письма и само письмо."
    return prompt


def _parse_response(text: str) -> dict:
    subject = ""
    body = text.strip()

    lines = text.strip().splitlines()
    for i, line in enumerate(lines):
        if line.lower().startswith("subject:"):
            subject = line[len("subject:"):].strip()
            body = "\n".join(lines[i + 1:]).strip()
            break

    return {"subject": subject, "body": body}


def generate_email(niche: str, recipient_type: str, language: str, product_description: str, examples: list[dict]) -> dict:
    llm = NVIDIA(model=LLM_MODEL, api_key=NVIDIA_API_KEY)

    user_prompt = _build_user_prompt(niche, recipient_type, language, product_description, examples)

    from llama_index.core.llms import ChatMessage, MessageRole
    messages = [
        ChatMessage(role=MessageRole.SYSTEM, content=SYSTEM_PROMPT),
        ChatMessage(role=MessageRole.USER, content=user_prompt),
    ]

    response = llm.chat(messages)
    raw = response.message.content or ""
    return _parse_response(raw)
