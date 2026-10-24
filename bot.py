import os
import re
import json
import time
import ssl
import html
import random
import hashlib
import difflib
import urllib.request
import xml.etree.ElementTree as ET
import http.client
from datetime import datetime
from email.utils import parsedate_to_datetime


# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8879784535:AAFnxUWY0vPQeApWT29pA2v4MH-1WrioOqY"
CHAT_ID = "-1004482881748"  # ID канала

# Habr RSS
RSS_FEED = "https://habr.com/ru/rss/all/"

# AI настройки
AI_HOST = "c5.play2go.cloud"
AI_PORT = 20132
AI_MODEL = "deepseek-chat"

# Настройки парсинга
NEWS_LIMIT = 5
CHECK_INTERVAL = 1800
MIN_POST_LENGTH = 650
MAX_POST_LENGTH = 950
SIMILARITY_LIMIT = 0.72
HISTORY_LIMIT = 12

STATE_FILE = "sent_news.json"
REQUEST_TIMEOUT = 30
TELEGRAM_TIMEOUT = 20
AI_TEMPERATURE = 0.92
AI_MAX_TOKENS = 900
# =====================

# ===== УНИКАЛЬНЫЕ СТИЛИ ФОРМАТИРОВАНИЯ =====
STYLE_LIBRARY = {
    "news_flash": """
СТИЛЬ: «МОЛНИЯ»
Начни резко и конкретно.
Заголовок — короткий.
Дай ощущение важной новости без кликбейта.
После заголовка: что произошло → почему это важно → 2–3 факта → короткий вывод.
Используй эмодзи: ⚡ 🔥 💥 → для динамичности
""",
    "explainer": """
СТИЛЬ: «РАЗБОР»
Начни с простого объяснения, что именно произошло.
Не пересказывай статью подряд.
Объясни механизм/идею человеческим языком.
Факты должны помогать понять новость.
Заверши мыслью о последствиях.
Используй эмодзи: 🔍 📊 💡 ◉ для аналитики
""",
    "curiosity": """
СТИЛЬ: «А ВОТ ИНТЕРЕСНО»
Начни с неожиданного факта или парадокса из исходных данных.
Затем раскрой его.
Избегай дешёвого кликбейта и вопросов ради вопросов.
Финал — одна сильная мысль.
Используй эмодзи: 🤔 ✨ 🧐 ❓ для удивления
""",
    "impact": """
СТИЛЬ: «ЧТО ЭТО МЕНЯЕТ»
Сразу сфокусируйся на практическом эффекте.
Ответь: что произошло, кого затронет, что изменится.
Пиши плотными абзацами, без канцелярита.
Используй эмодзи: 💡 🎯 ⚡ 🔥 для акцента
""",
    "myth_vs_fact": """
СТИЛЬ: «РАЗБОР МИФА»
Если материал позволяет, противопоставь распространённое представление
и то, что реально следует из новости.
Не выдумывай миф. Если его нет в исходных данных, используй формат
«ожидание → реальность» только как риторический приём.
Используй эмодзи: ⚖️ ❌ ✅ 🤔 для сравнения
""",
    "question": """
СТИЛЬ: «ВОПРОС К ЧИТАТЕЛЮ»
Начни с тезиса, который естественно вызывает мнение.
Затем дай факты и контекст.
В конце — один действительно уместный вопрос.
Не заканчивай банальным «А как вы думаете?».
Используй эмодзи: ❓ 💭 🤔 🔍 для вовлечения
""",
    "technical": """
СТИЛЬ: «ТЕХНИЧЕСКИЙ ВЗГЛЯД»
Подчеркни технологическую суть.
Используй точные термины там, где они есть в источнике,
но объясняй сложные вещи простыми словами.
Особенно хорошо подходит для AI, разработки, инфраструктуры и безопасности.
Используй эмодзи: ⚙️ 🔧 💻 🖥️ для техничности
""",
    "story": """
СТИЛЬ: «МИНИ-ИСТОРИЯ»
Построй текст как маленький сюжет:
ситуация → событие → поворот/интересная деталь → значение.
Не используй художественные выдумки.
Только факты из источника + осторожные выводы.
Используй эмодзи: 📖 ✨ 🌟 🎭 для повествования
""",
    "minimalistic": """
СТИЛЬ: «МИНИМАЛИСТИЧНЫЙ»
Сухой, лаконичный, деловой тон.
Короткие предложения, только суть.
Минимум эмодзи (1-2), максимум фактов.
Используй эмодзи: ▫️ → ✦ для сдержанности
""",
    "energetic": """
СТИЛЬ: «ЭНЕРГИЧНЫЙ»
Драйвовый, мотивирующий тон.
Используй сильные формулировки.
Динамичная подача, короткие абзацы.
Используй эмодзи: 🔥 ⚡ 💪 🚀 для энергии
""",
    "intellectual": """
СТИЛЬ: «ИНТЕЛЛЕКТУАЛЬНЫЙ»
Философский, размышляющий тон.
Глубокий анализ, неожиданные параллели.
Сложные идеи простым языком.
Используй эмодзи: 🧠 📚 ✨ 💭 для глубины
""",
    "friendly": """
СТИЛЬ: «ДРУЖЕЛЮБНЫЙ»
Тёплый, разговорный тон.
Обращение к читателю как к другу.
Доступное объяснение сложных вещей.
Используй эмодзи: 🌟 🤝 ✨ 😊 для теплоты
""",
    "cyberpunk": """
СТИЛЬ: «ТЕХНО-КИБЕРПАНК»
Футуристичный, технический тон.
Используй технологические метафоры.
Создавай ощущение будущего.
Используй эмодзи: ◈ ⚡ 🖥️ 🔮 для футуризма
""",
    "historical": """
СТИЛЬ: «ИСТОРИЧЕСКИЙ»
Эпический, повествовательный тон.
Проведи параллели с прошлым.
Рассказывай как историю.
Используй эмодзи: 📜 🏛️ ⚔️ 📖 для эпичности
""",
}

STYLE_SEQUENCE = [
    "news_flash", "explainer", "curiosity", "impact",
    "myth_vs_fact", "question", "technical", "story",
    "minimalistic", "energetic", "intellectual",
    "friendly", "cyberpunk", "historical"
]

# Уникальные приветствия с эмодзи
GREETINGS = [
    "🔍 Вот что привлекло наше внимание:",
    "✨ Свежий взгляд на важную тему:",
    "📰 Новость, которую стоит обсудить:",
    "💡 Что происходит в мире технологий:",
    "🎯 Интересный кейс на ваш суд:",
    "⏰ Время обновить знания:",
    "🌟 Это стоит вашего внимания:",
    "🔬 Разбор актуальной темы:",
    "📊 Технологический дайджест:",
    "🚀 Что изменится в ближайшее время:",
    "⚡ Ключевое событие дня:",
    "🔥 Не пропустите важное:",
    "🎯 Главная новость часа:",
    "💎 Технологический прорыв:",
    "🧠 Инсайт недели:"
]

# Уникальные заключения с эмодзи
CLOSINGS = [
    "🚀 Не пропустите обновления — следите за каналом!",
    "🔔 Будем держать вас в курсе событий.",
    "💬 Делитесь мнением, нам важно ваше мнение!",
    "⏳ Продолжение следует...",
    "🌟 Это только начало больших изменений.",
    "👀 Следите за развитием ситуации вместе с нами.",
    "📈 Больше инсайтов — в наших следующих постах.",
    "🌊 Оставайтесь на волне технологий!",
    "🗣️ Ваш голос важен — выскажитесь!",
    "✨ До новых встреч в эфире!",
    "🎯 Впереди ещё много интересного!",
    "📡 Следите за обновлениями!",
    "💻 Будьте в курсе технологий!",
    "🧠 Развивайтесь вместе с нами!",
    "🚀 До встречи в следующем посте!"
]

# Уникальные хэштег-сеты
HASHTAG_SETS = [
    ["#технологии", "#it", "#новости"],
    ["#dev", "#coding", "#tech"],
    ["#программирование", "#разработка", "#инновации"],
    ["#digital", "#future", "#habr"],
    ["#ai", "#software", "#engineering"],
    ["#startup", "#product", "#design"],
    ["#backend", "#frontend", "#fullstack"],
    ["#cloud", "#data", "#security"],
    ["#opensource", "#community", "#learning"],
    ["#career", "#growth", "#knowledge"],
    ["#python", "#javascript", "#golang"],
    ["#docker", "#kubernetes", "#aws"],
    ["#machinelearning", "#blockchain", "#webdev"],
    ["#architecture", "#testing", "#devops"],
    ["#agile", "#api", "#microservices"]
]

# Эмодзи для разных стилей (используются в промпте)
EMOJI_MAP = {
    "news_flash": {"header": "⚡", "bullet": "→", "divider": "▬▬▬▬▬", "footer": "💥", "list": ["⚡", "🔥", "💥"]},
    "explainer": {"header": "🔍", "bullet": "◉", "divider": "┈┈┈┈┈", "footer": "◇", "list": ["🔍", "📊", "💡"]},
    "curiosity": {"header": "🤔", "bullet": "✦", "divider": "· · · · ·", "footer": "✨", "list": ["🤔", "✨", "🧐", "❓"]},
    "impact": {"header": "💡", "bullet": "▶", "divider": "━━━━━", "footer": "🎯", "list": ["💡", "🎯", "⚡", "🔥"]},
    "myth_vs_fact": {"header": "⚖️", "bullet": "▪", "divider": "═══", "footer": "❓", "list": ["⚖️", "❌", "✅", "🤔"]},
    "question": {"header": "❓", "bullet": "▸", "divider": "─────", "footer": "💭", "list": ["❓", "💭", "🤔", "🔍"]},
    "technical": {"header": "⚙️", "bullet": "◆", "divider": "┄┄┄┄┄", "footer": "🔧", "list": ["⚙️", "🔧", "💻", "🖥️"]},
    "story": {"header": "📖", "bullet": "✧", "divider": "~ ~ ~ ~ ~", "footer": "🌟", "list": ["📖", "✨", "🌟", "🎭"]},
    "minimalistic": {"header": "▫️", "bullet": "→", "divider": "─────", "footer": "✦", "list": ["▫️", "✦"]},
    "energetic": {"header": "🔥", "bullet": "⚡", "divider": "▬▬▬▬▬", "footer": "💪", "list": ["🔥", "⚡", "💪", "🚀"]},
    "intellectual": {"header": "🧠", "bullet": "◉", "divider": "┈┈┈┈┈", "footer": "◇", "list": ["🧠", "📚", "✨", "💭"]},
    "friendly": {"header": "🌟", "bullet": "✨", "divider": "· · · · ·", "footer": "🤝", "list": ["🌟", "🤝", "✨", "😊"]},
    "cyberpunk": {"header": "◈", "bullet": "▸", "divider": "═══", "footer": "◉", "list": ["◈", "⚡", "🖥️", "🔮"]},
    "historical": {"header": "📜", "bullet": "⚔️", "divider": "━━━━━", "footer": "🏛️", "list": ["📜", "🏛️", "⚔️", "📖"]},
}


# ===== HTML / TEXT UTILS =====

def escape_html(text):
    """Безопасное экранирование текста для Telegram HTML."""
    if not text:
        return ""
    return html.escape(str(text), quote=True)


def clean_html(text):
    """Убирает HTML и нормализует пробелы."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def remove_markdown(text):
    """Убирает типичные Markdown-остатки, если модель их всё же вернула."""
    if not text:
        return ""
    text = text.replace("```html", "").replace("```", "")
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"__(.*?)__", r"\1", text)
    text = re.sub(r"(?<!\w)\*(.*?)\*(?!\w)", r"\1", text)
    text = re.sub(r"(?<!\w)_(.*?)_(?!\w)", r"\1", text)
    return text.strip()


def normalize_for_similarity(text):
    """Нормализация для поиска повторов."""
    text = clean_html(text).lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"#[\wа-яё-]+", " ", text)
    text = re.sub(r"[^a-zа-яё0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_intro(text, words=24):
    """Первые слова поста — отдельно сравниваем вступления."""
    normalized = normalize_for_similarity(text)
    return " ".join(normalized.split()[:words])


def similarity(a, b):
    """Коэффициент похожести двух постов."""
    na = normalize_for_similarity(a)
    nb = normalize_for_similarity(b)
    if not na or not nb:
        return 0.0
    return difflib.SequenceMatcher(None, na, nb).ratio()


def post_fingerprint(text):
    normalized = normalize_for_similarity(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def validate_html(text):
    """Базовая проверка HTML, без попытки написать полноценный HTML-парсер."""
    if not text:
        return False

    # Запрещаем потенциально опасные/лишние конструкции.
    if re.search(r"<\s*(script|style|iframe|img|video|form)\b", text, re.I):
        return False

    # Проверяем href только в <a>.
    for href in re.findall(r'<a\b[^>]*href="([^"]+)"', text, re.I):
        if not re.match(r"^https?://", href, re.I):
            return False

    # Не допускаем Markdown.
    if "```" in text:
        return False

    return True


def smart_trim(text, max_length, link):
    """Умная обрезка текста с сохранением HTML-структуры"""
    if len(text) <= max_length:
        return text
    
    # Ищем последнее полное предложение в пределах лимита
    trim_point = max_length - 100
    last_sentence_end = text.rfind('.', trim_point - 200, trim_point)
    
    if last_sentence_end == -1:
        last_sentence_end = text.rfind('!', trim_point - 200, trim_point)
    if last_sentence_end == -1:
        last_sentence_end = text.rfind('?', trim_point - 200, trim_point)
    
    if last_sentence_end != -1:
        result = text[:last_sentence_end + 1]
    else:
        result = text[:trim_point]
    
    result = result.strip() + "..."
    
    # Добавляем ссылку если её нет
    if link and f'href="{link}"' not in result:
        result += f'\n\n<a href="{link}">Читать полностью →</a>'
    
    # Добавляем хэштеги если их нет
    if '#' not in result:
        hashtags = get_random_hashtags()
        result += f'\n\n{hashtags}'
    
    return result


def trim_to_length(text, max_length=MAX_POST_LENGTH):
    """Мягкое сокращение поста."""
    if len(text) <= max_length:
        return text

    link_match = re.search(r'<a\b[^>]*href="([^"]+)"[^>]*>.*?</a>', text, re.I | re.S)
    link = link_match.group(0) if link_match else ""

    body = re.sub(r'\n*<a\b[^>]*>.*?</a>\s*', "", text, flags=re.I | re.S)
    body = body.strip()

    # Удаляем хэштеги, если они мешают влезть.
    hashtags = re.findall(r"#[\wа-яё-]+", body, re.I)
    body_without_tags = re.sub(r"\s*(?:#[\wа-яё-]+(?:\s+|$))+", " ", body, flags=re.I).strip()

    suffix = ""
    if link:
        suffix = "\n\n" + link

    available = max_length - len(suffix)
    if available < 100:
        return body[:max_length]

    candidate = body_without_tags[:available].rstrip()

    # Не режем HTML-тег.
    while candidate.count("<") > candidate.count(">") and candidate:
        candidate = candidate[:-1]

    # Предпочитаем закончить предложение.
    cut_points = [
        candidate.rfind("\n"),
        candidate.rfind(". "),
        candidate.rfind("! "),
        candidate.rfind("? "),
    ]
    best = max(cut_points)

    if best > available * 0.60:
        candidate = candidate[:best + 1].rstrip()

    # Возвращаем максимум 3 хэштега, если есть место.
    if hashtags:
        tag_line = " ".join(dict.fromkeys(hashtags[:3]))
        if len(candidate) + len(tag_line) + 2 + len(suffix) <= max_length:
            candidate += "\n\n" + tag_line

    result = candidate + suffix
    return result[:max_length]


# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ РАЗНООБРАЗИЯ =====

def get_random_greeting():
    """Возвращает случайное приветствие"""
    return random.choice(GREETINGS)


def get_random_closing():
    """Возвращает случайное заключение"""
    return random.choice(CLOSINGS)


def get_random_hashtags():
    """Возвращает случайный набор хэштегов"""
    tags = random.choice(HASHTAG_SETS)
    # Добавляем 1-2 случайных тематических тега
    extra_tags = random.sample([
        "#python", "#javascript", "#golang", "#rust", "#java",
        "#docker", "#kubernetes", "#aws", "#linux", "#database",
        "#machinelearning", "#blockchain", "#webdev", "#mobile",
        "#architecture", "#testing", "#ci_cd", "#agile", "#api",
        "#backend", "#frontend", "#fullstack", "#devops",
        "#security", "#cloud", "#data", "#ai", "#ml"
    ], k=random.randint(1, 2))
    return " ".join(tags + extra_tags)


def get_style_emojis(style_name):
    """Возвращает эмодзи для стиля"""
    return EMOJI_MAP.get(style_name, EMOJI_MAP["minimalistic"])


# ===== TELEGRAM =====

def telegram_request(method, data):
    """Общий POST-запрос к Telegram Bot API."""
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=TELEGRAM_TIMEOUT) as response:
        raw = response.read().decode("utf-8")
        result = json.loads(raw)

    if not result.get("ok"):
        raise RuntimeError(result.get("description", "Telegram API error"))

    return result


def send_single_message(text, chat_id, parse_mode="HTML"):
    """Отправляет одно текстовое сообщение."""
    try:
        telegram_request(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": text,
                "disable_web_page_preview": True,
                "parse_mode": parse_mode,
            },
        )
        return True
    except Exception as exc:
        print(f"[✗] Telegram sendMessage: {exc}")
        return False


def split_text(text, max_length=4096):
    """Разбивает длинный текст по абзацам/предложениям."""
    if len(text) <= max_length:
        return [text]

    chunks = []
    current = ""

    blocks = [b.strip() for b in re.split(r"\n{2,}", text) if b.strip()]

    for block in blocks:
        candidate = f"{current}\n\n{block}".strip()
        if len(candidate) <= max_length:
            current = candidate
            continue

        if current:
            chunks.append(current)

        if len(block) <= max_length:
            current = block
        else:
            sentences = re.split(r"(?<=[.!?])\s+", block)
            current = ""
            for sentence in sentences:
                candidate = f"{current} {sentence}".strip()
                if len(candidate) <= max_length:
                    current = candidate
                else:
                    if current:
                        chunks.append(current)
                    current = sentence[:max_length]

    if current:
        chunks.append(current)

    return chunks


def send_telegram_text(chat_id, text, parse_mode="HTML"):
    """Отправляет текст, при необходимости разбивая на сообщения."""
    parts = split_text(text, 4096)
    ok = True

    for index, part in enumerate(parts, 1):
        if not send_single_message(part, chat_id, parse_mode):
            ok = False
        if index < len(parts):
            time.sleep(0.6)

    return ok


def send_telegram_post(chat_id, photo_url=None, text="", parse_mode="HTML"):
    """Отправляет пост с фото и текстом в одном сообщении."""
    target_chat = chat_id or CHAT_ID

    if photo_url and len(text) <= 1024:
        try:
            telegram_request(
                "sendPhoto",
                {
                    "chat_id": target_chat,
                    "photo": photo_url,
                    "caption": text,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": True,
                },
            )
            return True
        except Exception as exc:
            print(f"[!] sendPhoto не удался: {exc}; отправляю текстом.")

    return send_telegram_text(target_chat, text, parse_mode)


# ===== RSS =====

def extract_image_from_description(description):
    """Извлекает URL первой картинки из HTML-описания."""
    if not description:
        return None
    
    patterns = [
        r'<img[^>]+src=["\']([^"\']+)["\']',
        r'<img[^>]+data-src=["\']([^"\']+)["\']',
    ]

    for pattern in patterns:
        match = re.search(pattern, description, re.I)
        if match:
            url = match.group(1).strip()
            if url.startswith("//"):
                return "https:" + url
            if url.startswith("/"):
                return "https://habr.com" + url
            return url

    return None


def parse_habr():
    """Получает свежие материалы из RSS Habr."""
    try:
        print("[*] Парсим Habr...")

        context = ssl._create_unverified_context()

        request = urllib.request.Request(
            RSS_FEED,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/151 Safari/537.36"
                )
            },
        )

        with urllib.request.urlopen(
            request,
            timeout=15,
            context=context,
        ) as response:
            xml_data = response.read().decode("utf-8", errors="replace")

        root = ET.fromstring(xml_data)
        items = root.findall(".//item")[:NEWS_LIMIT]

        news_list = []

        for item in items:
            title = item.findtext("title", default="Без заголовка").strip()
            link = item.findtext("link", default="").strip()
            pub_date = item.findtext("pubDate", default="").strip()
            guid = item.findtext("guid", default=link).strip()

            description_node = item.find("description")
            description_html = (
                description_node.text
                if description_node is not None and description_node.text
                else ""
            )

            image_url = extract_image_from_description(description_html)

            if not image_url:
                content_encoded = item.find(
                    "{http://purl.org/rss/1.0/modules/content/}encoded"
                )
                if content_encoded is not None and content_encoded.text:
                    image_url = extract_image_from_description(content_encoded.text)

            author = item.findtext("author", default="").strip()
            
            # Извлекаем категории
            categories = []
            for cat in item.findall("category"):
                if cat.text:
                    categories.append(cat.text)

            news_list.append(
                {
                    "title": title,
                    "link": link,
                    "pub_date": pub_date,
                    "description": clean_html(description_html),
                    "image_url": image_url,
                    "guid": guid or link,
                    "author": author,
                    "categories": categories,
                }
            )

        print(f"[✓] Найдено {len(news_list)} новостей")
        return news_list

    except Exception as exc:
        print(f"[✗] Ошибка парсинга Habr: {exc}")
        return []


# ===== STATE =====

def default_state():
    return {
        "sent": [],
        "history": [],
        "style_index": 0,
    }


def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as file:
            state = json.load(file)

        if not isinstance(state, dict):
            return default_state()

        state.setdefault("sent", [])
        state.setdefault("history", [])
        state.setdefault("style_index", 0)
        return state

    except (FileNotFoundError, json.JSONDecodeError):
        return default_state()


def save_state(state):
    temp_file = STATE_FILE + ".tmp"

    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(state, file, ensure_ascii=False, indent=2)

    os.replace(temp_file, STATE_FILE)


def remember_post(state, guid, title, post, style):
    state["sent"].append(guid)
    state["sent"] = state["sent"][-1000:]

    state["history"].append(
        {
            "title": title,
            "style": style,
            "fingerprint": post_fingerprint(post),
            "intro": get_intro(post),
            "text": post,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
    )

    state["history"] = state["history"][-HISTORY_LIMIT:]


def choose_style(state):
    index = int(state.get("style_index", 0))
    style = STYLE_SEQUENCE[index % len(STYLE_SEQUENCE)]
    state["style_index"] = index + 1
    return style


# ===== AI =====

def ai_request(messages, temperature=AI_TEMPERATURE, max_tokens=AI_MAX_TOKENS):
    """Запрос к OpenAI-compatible API."""
    payload = {
        "model": AI_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    conn = http.client.HTTPConnection(AI_HOST, AI_PORT, timeout=REQUEST_TIMEOUT)

    try:
        conn.request(
            "POST",
            "/v1/chat/completions",
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            {"Content-Type": "application/json"},
        )

        response = conn.getresponse()
        raw = response.read().decode("utf-8", errors="replace")

        if response.status != 200:
            raise RuntimeError(f"AI HTTP {response.status}: {raw[:500]}")

        data = json.loads(raw)
        choices = data.get("choices") or []

        if not choices:
            raise RuntimeError("AI не вернул choices")

        return choices[0]["message"]["content"].strip()

    finally:
        conn.close()


def build_history_context(state):
    history = state.get("history", [])[-6:]

    if not history:
        return "История публикаций отсутствует. Можно писать свободно."

    lines = []
    for item in history:
        lines.append(
            f"- стиль: {item.get('style', '?')}; "
            f"заголовок: {item.get('title', '')}; "
            f"начало: {item.get('intro', '')}"
        )

    return "\n".join(lines)


def build_prompt(news, style, state, attempt=1):
    title = clean_html(news.get("title", ""))
    description = clean_html(news.get("description", ""))
    link = news.get("link", "")
    author = clean_html(news.get("author", ""))
    categories = news.get("categories", [])

    # Не даём модели тонну RSS-мусора.
    description = description[:1800]
    
    emojis = get_style_emojis(style)
    greeting = get_random_greeting()
    closing = get_random_closing()
    hashtags = get_random_hashtags()

    history = build_history_context(state)

    extra = ""
    if attempt > 1:
        extra = """
ПРЕДЫДУЩАЯ ПОПЫТКА ПОЛУЧИЛАСЬ СЛИШКОМ ПОХОЖЕЙ НА ИМЕЮЩИЕСЯ ПОСТЫ.
Сейчас полностью поменяй композицию, начало и ритм текста.
Не повторяй клише и первые фразы из истории.
"""

    cat_context = ""
    if categories:
        cat_context = f"Категории: {', '.join(categories[:3])}. "

    style_desc = STYLE_LIBRARY.get(style, STYLE_LIBRARY["minimalistic"])
    
    # Формируем список доступных эмодзи для этого стиля
    available_emojis = ", ".join(emojis.get("list", ["⚡", "🔥", "💡"]))
    
    return f"""
Ты — сильный русскоязычный редактор технологического Telegram-канала.
Твоя задача — превращать исходную новость в короткий самостоятельный пост,
который хочется дочитать.

{style_desc}

ИСХОДНЫЕ ДАННЫЕ:
Заголовок: {title}
Описание: {description}
Автор: {author or "не указан"}
{cat_context}
Ссылка: {link}

ПОСЛЕДНИЕ ПУБЛИКАЦИИ. НЕ ПОВТОРЯЙ ИХ:
{history}

ДОСТУПНЫЕ ЭМОДЗИ ДЛЯ ЭТОГО СТИЛЯ:
{available_emojis}
Ты МОЖЕШЬ и ДОЛЖЕН использовать эти эмодзи в посте, но НЕ ЗЛОУПОТРЕБЛЯЙ (максимум 3-4 штуки на весь пост).

ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ ЭМОДЗИ:
- В начале поста для привлечения внимания: {emojis.get('header', '⚡')} Заголовок
- Для разделения смысловых блоков: {emojis.get('divider', '▬▬▬▬▬')}
- Для выделения важных пунктов: {emojis.get('bullet', '→')} факт
- В конце для завершения: {emojis.get('footer', '💥')} заключение

ТРЕБОВАНИЯ К ТЕКСТУ:
1. Длина готового поста: примерно {MIN_POST_LENGTH}–{MAX_POST_LENGTH} символов.
2. Только русский язык.
3. Пост должен быть уникальным по формулировкам, ритму и композиции.
4. Не начинай каждый пост с «Стало известно», «Компания представила»,
   «Учёные разработали», «В мире технологий» и подобных штампов.
5. Не используй одинаковую схему «заголовок → три пункта → вопрос».
6. Не выдумывай цифры, факты, цитаты, названия продуктов или последствия.
7. Не пересказывай RSS буквально — переформулируй материал.
8. Используй 0–4 эмодзи только там, где они действительно помогают.
9. Абзацы должны быть короткими: 1–3 предложения.
10. Заголовок должен быть частью текста и выделяться <b>.
11. Можно использовать <b>, <i>, <u>, <code> и <a href="...">.
12. Не используй Markdown.
13. Не добавляй отдельную строку «Источник:».
14. В конце обязательно поставь ссылку:
<a href="{escape_html(link)}">Читать полностью →</a>
15. Хэштеги — максимум 3, только релевантные теме.
16. Не добавляй никаких комментариев о том, что ты AI или выполняешь задание.
17. Верни ТОЛЬКО готовый Telegram-пост, без кавычек и без пояснений.

РЕКОМЕНДАЦИИ ПО СТРУКТУРЕ:
- Вступление можно начать с приветствия: {greeting}
- Заключение: {closing}
- Используй эмодзи для оформления

ВАЖНАЯ РЕДАКТОРСКАЯ ЦЕЛЬ:
Человек должен почувствовать, что это не автоматически сгенерированный
шаблонный дайджест, а аккуратно отредактированная заметка живого канала.
Каждый новый пост должен звучать иначе предыдущего.

{extra}
"""


def post_is_too_similar(post, state):
    """Проверяет пост против последних публикаций."""
    for old in state.get("history", [])[-HISTORY_LIMIT:]:
        old_text = old.get("text", "")

        if post_fingerprint(post) == old.get("fingerprint"):
            return True

        full_score = similarity(post, old_text)
        intro_score = similarity(get_intro(post), old.get("intro", ""))

        if full_score >= SIMILARITY_LIMIT or intro_score >= 0.82:
            print(
                f"[!] Найден повтор: full={full_score:.2f}, intro={intro_score:.2f}"
            )
            return True

    return False


def finalize_ai_post(raw_post, link):
    """Приводит AI-ответ к Telegram HTML."""
    post = remove_markdown(raw_post)

    # Удаляем случайные обёртки.
    post = re.sub(r"^\s*<post>\s*", "", post, flags=re.I)
    post = re.sub(r"\s*</post>\s*$", "", post, flags=re.I)
    post = post.strip()

    # Если модель не добавила ссылку — добавляем сами.
    if link and link not in post:
        post += f'\n\n<a href="{escape_html(link)}">Читать полностью →</a>'
    
    # Добавляем хэштеги если их нет
    if '#' not in post:
        hashtags = get_random_hashtags()
        post += f'\n\n{hashtags}'

    if not validate_html(post):
        # Удаляем потенциально проблемные конструкции.
        post = re.sub(
            r"<\s*(script|style|iframe|img|video|form)\b.*?>.*?</\s*\1\s*>",
            "",
            post,
            flags=re.I | re.S,
        )

    return trim_to_length(post, MAX_POST_LENGTH)


def generate_compact_post(news, state):
    """Генерирует пост с несколькими попытками и анти-повтором."""
    style = choose_style(state)

    print(f"[*] AI-стиль: {style}")

    system_prompt = """
Ты — редактор технологического Telegram-канала высокого уровня.
Главные критерии: точность, естественный русский язык, разнообразие,
сильная композиция, отсутствие шаблонности.
Не выдумывай факты.
Возвращай только готовый HTML-текст поста.
ОБЯЗАТЕЛЬНО используй эмодзи в посте (3-4 штуки), следуя указанному стилю.
"""

    for attempt in range(1, 4):
        try:
            prompt = build_prompt(news, style, state, attempt)

            raw = ai_request(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=min(AI_TEMPERATURE + (attempt - 1) * 0.05, 1.0),
            )

            post = finalize_ai_post(raw, news["link"])

            length = len(post)
            print(f"[✓] Попытка {attempt}: {length} символов")

            if length < MIN_POST_LENGTH:
                print("[!] Пост слишком короткий — повторная генерация.")
                continue

            if post_is_too_similar(post, state):
                print("[!] Пост похож на предыдущий — меняем композицию.")
                continue

            return post, style

        except Exception as exc:
            print(f"[✗] AI attempt {attempt}: {exc}")
            time.sleep(1)

    print("[!] AI не дал уникальный вариант — используем fallback.")
    return generate_fallback_post(news), style


def generate_fallback_post(news):
    """Надёжный запасной вариант без AI."""
    title = escape_html(news.get("title", "Без заголовка"))
    description = escape_html(clean_html(news.get("description", ""))[:400])
    link = escape_html(news.get("link", ""))
    
    greeting = get_random_greeting()
    closing = get_random_closing()
    hashtags = get_random_hashtags()
    emojis = get_style_emojis("minimalistic")

    post = (
        f"{emojis['header']} {greeting}\n\n"
        f"<b>{title}</b>\n\n"
        f"{description}\n\n"
        f"{emojis['divider']}\n\n"
        f"{emojis['footer']} {closing}\n\n"
        f"<a href=\"{link}\">Читать полностью →</a>\n\n"
        f"{hashtags}"
    )

    return trim_to_length(post, MAX_POST_LENGTH)


# ===== PUBLISH =====

def process_and_publish_news(news_item, state, chat_id=None):
    """Генерирует и публикует одну новость."""
    print(f"\n[*] Обработка: {news_item['title'][:80]}")

    post_text, style = generate_compact_post(news_item, state)

    success = send_telegram_post(
        chat_id or CHAT_ID,
        news_item.get("image_url"),
        post_text,
        "HTML",
    )

    if success:
        remember_post(
            state,
            news_item["guid"],
            news_item["title"],
            post_text,
            style,
        )
        save_state(state)

        print(
            f"[✓] Опубликовано в канал | "
            f"style={style} | "
            f"length={len(post_text)}"
        )
        return True

    print("[✗] Публикация не удалась")
    return False


def check_for_new(state):
    """Проверяет новые статьи и публикует их."""
    news = parse_habr()

    if not news:
        print("[✓] Новостей нет")
        return

    sent = set(state.get("sent", []))
    new_count = 0

    for item in news:
        guid = item.get("guid", "")

        if not guid or guid in sent:
            continue

        if process_and_publish_news(item, state):
            new_count += 1
            sent.add(guid)

        time.sleep(3)

    if new_count:
        print(f"[✓] Новых публикаций: {new_count}")
    else:
        print("[✓] Новых статей нет")


# ===== INFO =====

def get_my_ip():
    """Определяет внешний IP сервера."""
    try:
        with urllib.request.urlopen("https://api.ipify.org", timeout=5) as response:
            return response.read().decode().strip()
    except Exception:
        return "Не удалось определить"


def send_startup_message():
    """Сообщение о запуске."""
    ip = get_my_ip()
    emojis = get_style_emojis("minimalistic")

    message = (
        f"{emojis['header']} <b>Habr Unique News Bot</b> v3.0\n\n"
        f"{emojis['divider']}\n\n"
        f"📍 <b>Сервер:</b> {escape_html(ip)}\n"
        f"📰 <b>Новости за цикл:</b> {NEWS_LIMIT}\n"
        f"⏰ <b>Интервал:</b> {CHECK_INTERVAL // 60} мин.\n"
        f"✍️ <b>Длина:</b> {MIN_POST_LENGTH}–{MAX_POST_LENGTH} симв.\n"
        f"🎨 <b>Уникальных стилей:</b> {len(STYLE_SEQUENCE)}\n"
        f"🧠 <b>Анти-повтор:</b> включён\n"
        f"🖼️ <b>Изображения:</b> включены\n"
        f"📝 <b>AI генерация:</b> включена\n\n"
        f"{emojis['divider']}\n\n"
        f"✅ <b>Бот запущен.</b>\n"
        f"{emojis['footer']} Каждый пост — уникальный!\n\n"
        f"📢 <b>Канал:</b> https://t.me/your_channel"
    )

    send_telegram_post(CHAT_ID, None, message, "HTML")


def validate_config():
    if not BOT_TOKEN:
        raise RuntimeError(
            "Не задан BOT_TOKEN. "
            "Установите переменную окружения BOT_TOKEN."
        )

    if not CHAT_ID:
        raise RuntimeError(
            "Не задан CHAT_ID. "
            "Установите переменную окружения CHAT_ID."
        )


# ===== MAIN =====

def main():
    validate_config()

    print("=" * 68)
    print("🎨 HABR UNIQUE AI NEWS BOT v3.0")
    print("=" * 68)
    print(f"🌐 AI: {AI_HOST}:{AI_PORT}/{AI_MODEL}")
    print(f"📰 Источник: Habr RSS")
    print(f"📊 Новостей за цикл: {NEWS_LIMIT}")
    print(f"📝 Длина: {MIN_POST_LENGTH}–{MAX_POST_LENGTH}")
    print(f"🎨 Стилей: {len(STYLE_SEQUENCE)}")
    print(f"🧠 Анти-повтор: {SIMILARITY_LIMIT}")
    print(f"⏰ Интервал: {CHECK_INTERVAL // 60} минут")
    print(f"📢 Канал: https://t.me/your_channel")
    print("=" * 68)

    state = load_state()

    try:
        send_startup_message()
    except Exception as exc:
        print(f"[!] Не удалось отправить startup: {exc}")

    print("\n[*] Первая проверка...")
    try:
        check_for_new(state)
    except Exception as exc:
        print(f"[✗] Ошибка первой проверки: {exc}")

    iteration = 0

    while True:
        iteration += 1

        print("\n" + "=" * 68)
        print(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
            f"Проверка #{iteration}"
        )
        print("=" * 68)

        try:
            check_for_new(state)
        except KeyboardInterrupt:
            print("\n[!] Остановка.")
            break
        except Exception as exc:
            print(f"[✗] Критическая ошибка: {exc}")

            try:
                send_telegram_post(
                    CHAT_ID,
                    None,
                    f"⚠️ <b>Ошибка бота</b>\n\n<code>{escape_html(str(exc)[:500])}</code>",
                    "HTML",
                )
            except Exception:
                pass

        print(f"[*] Следующая проверка через {CHECK_INTERVAL // 60} минут")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()