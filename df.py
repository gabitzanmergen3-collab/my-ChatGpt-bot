import os
import json
import logging
import openai
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ===================== НАСТРОЙКИ =====================

TELEGRAM_TOKEN = os.getenv("8152914738:AAFFWy_i478GceXKqatLDFa2C3f-kaKGkXg")
OPENAI_API_KEY = os.getenv("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")

if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    raise RuntimeError("❌ Не заданы переменные окружения TELEGRAM_TOKEN или OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

MEMORY_FILE = "memory.json"
MAX_HISTORY = 12          # ограничение памяти
MAX_TOKENS = 400          # длина ответа
TEMPERATURE = 0.6         # креативность

# ===================== ЛОГИ =====================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(name)

# ===================== ПАМЯТЬ =====================

def load_memory() -> dict:
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка чтения памяти: {e}")
    return {}

def save_memory(memory: dict):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения памяти: {e}")

user_memory = load_memory()

# ===================== КОМАНДЫ =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Я ИИ-бот с памятью 🧠\n"
        "Можешь общаться со мной как с ChatGPT.\n\n"
        "Команды:\n"
        "/help — помощь\n"
        "/clear — очистить память"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ Помощь:\n\n"
        "• Просто пиши текст — я отвечу\n"
        "• Я помню контекст диалога\n"
        "• /clear — очистить память\n\n"
        "Работаю стабильно и 24/7 🤖"
    )

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id in user_memory:
        del user_memory[user_id]
        save_memory(user_memory)
    await update.message.reply_text("🧹 Память очищена.")

# ===================== ОСНОВНОЙ ЧАТ =====================

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = str(update.message.from_user.id)
    text = update.message.text.strip()

    if not text:
        await update.message.reply_text("Напиши сообщение 🙂")
        return

    # инициализация памяти
    if user_id not in user_memory:
        user_memory[user_id] = [
            {
                "role": "system",
                "content": (
                    "Ты умный, спокойный и дружелюбный ИИ помощник. "
                    "Отвечай понятно, честно и полезно."
                )
            }
        ]

    user_memory[user_id].append({"role": "user", "content": text})

    # ограничиваем историю
    if len(user_memory[user_id]) > MAX_HISTORY:
        user_memory[user_id] = user_memory[user_id][-MAX_HISTORY:]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=user_memory[user_id],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            timeout=20
        )

        answer = response.choices[0].message.content.strip()

        user_memory[user_id].append(
            {"role": "assistant", "content": answer}
        )

        save_memory(user_memory)

await update.message.reply_text(answer)

except openai.error.RateLimitError:
        await update.message.reply_text("⏳ Слишком много запросов. Подожди немного.")
    except openai.error.Timeout:
        await update.message.reply_text("⌛ Сервер долго отвечает. Попробуй ещё раз.")
    except Exception as e:
        logger.exception("Ошибка в чате")
        await update.message.reply_text("❌ Произошла ошибка. Попробуй позже.")

# ===================== ЗАПУСК =====================

def main():
    logger.info("🤖 Запуск бота")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    app.run_polling()

if name == "main":
    main()
        await update.message.reply_text(answer)
