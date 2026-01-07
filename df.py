import json
import logging
import os
import openai
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ============ НАСТРОЙКИ ============
TELEGRAM_TOKEN = "8152914738:AAFFWy_i478GceXKqatLDFa2C3f-kaKGkXg"
OPENAI_API_KEY = "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"

openai.api_key = OPENAI_API_KEY

MEMORY_FILE = "memory.json"
MAX_HISTORY = 10  # максимум сообщений в памяти

# ============ ЛОГИ ============
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ============ ПАМЯТЬ ============
def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

user_memory = load_memory()

# ============ КОМАНДЫ ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет!\n"
        "Я ИИ-чат бот с памятью 🧠\n"
        "Просто пиши сообщение."
    )

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    user_memory.pop(user_id, None)
    save_memory(user_memory)
    await update.message.reply_text("🧹 Память очищена.")

# ============ ЧАТ ============
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = str(update.message.from_user.id)
    text = update.message.text.strip()

    if not text:
        await update.message.reply_text("Напиши текст 🙂")
        return

    if user_id not in user_memory:
        user_memory[user_id] = [
            {"role": "system", "content": "Ты дружелюбный и полезный ИИ помощник."}
        ]

    user_memory[user_id].append({"role": "user", "content": text})

    # ограничение истории
    if len(user_memory[user_id]) > MAX_HISTORY:
        user_memory[user_id] = user_memory[user_id][-MAX_HISTORY:]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=user_memory[user_id],
            temperature=0.6,
            max_tokens=400,
            timeout=20
        )

        answer = response.choices[0].message.content.strip()
        user_memory[user_id].append({"role": "assistant", "content": answer})

        save_memory(user_memory)
        await update.message.reply_text(answer)

    except openai.error.RateLimitError:
        await update.message.reply_text("⏳ Слишком много запросов. Подожди немного.")
    except openai.error.Timeout:
        await update.message.reply_text("⌛️ Сервер долго отвечает. Попробуй ещё раз.")
    except Exception as e:
        logging.error(e)
        await update.message.reply_text("❌ Ошибка. Попробуй позже.")

# ============ ЗАПУСК ============
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("🤖 Бот запущен и стабилен")
    app.run_polling()

if __name__ == "__main__":
    main()
