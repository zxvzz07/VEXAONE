import asyncio
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from google import genai
import io
import base64

# 🔑 ТВОИ КЛЮЧИ
TELEGRAM_TOKEN = "8397201025:AAG4QYV-PcOGxFt0P-P1SzTrrK2-Woa9fSw"
GEN_API_KEY = "AIzaSyBrgcQFzbDGoJwPQucMPsmY3THufFChOg4"

# 🔹 Клиент Gemini
client = genai.Client(api_key=GEN_API_KEY)

# 🔹 Система и история чата
SYSTEM_PROMPT = (
    "Ты — умный, дружелюбный Telegram-ассистент, созданный Иманбаевым Марселем, "
    "ему всего 17 лет! Отвечай естественно, кратко, с лёгким юмором, как человек. "
    "Если просят сгенерировать изображение, обязательно используй команду 'нарисуй' или 'сделай картинку'."
)
chat_history = {}

# 💬 Основная функция общения с Gemini
def ask_gemini(user_id, prompt):
    # 🧠 Проверка на вопросы о создателе
    creator_phrases = [
        "кем ты создан", "кто тебя создал", "кто тебя сделал",
        "кем создан", "кто тебя придумал", "чей ты бот", "кто твой создатель"
    ]
    if any(phrase in prompt.lower() for phrase in creator_phrases):
        return "🤖 Меня создал Иманбаев Марсель — мой талантливый разработчик, которому всего 17 лет! 🚀"

    if user_id not in chat_history:
        chat_history[user_id] = []

    # 🔹 Контекст последних сообщений
    context = "\n".join(chat_history[user_id][-5:])
    full_prompt = f"{SYSTEM_PROMPT}\n\n{context}\nUser: {prompt}\nBot:"

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=full_prompt
        )
        reply = response.text

        # 🧾 Сохраняем историю
        chat_history[user_id].append(f"User: {prompt}")
        chat_history[user_id].append(f"Bot: {reply}")

        # Очищаем при длинной истории
        if len(chat_history[user_id]) > 20:
            chat_history[user_id] = chat_history[user_id][-10:]

        return reply

    except Exception as e:
        return f"Ошибка Gemini: {e}"

# 🖼️ Генерация изображений
def generate_image(prompt):
    try:
        image_response = client.models.generate_content(
            model="imagen-3.0-generate",
            contents=prompt
        )
        image_data = image_response.image
        image_bytes = base64.b64decode(image_data)
        return io.BytesIO(image_bytes)
    except Exception as e:
        return None

# 📩 Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.message.chat.id

    await update.message.chat.send_action(action="typing")

    # 🖼️ Если пользователь просит нарисовать
    if any(word in user_text.lower() for word in ["нарисуй", "картинку", "изображение", "сделай картинку"]):
        await update.message.reply_text("🎨 Подожди пару секунд, создаю изображение...")
        image = await asyncio.to_thread(generate_image, user_text)
        if image:
            await update.message.reply_photo(photo=InputFile(image, filename="image.png"))
        else:
            await update.message.reply_text("⚠️ Не удалось создать изображение.")
        return

    # 💬 Иначе обычный текстовый ответ
    reply = await asyncio.to_thread(ask_gemini, user_id, user_text)
    await update.message.reply_text(reply)

# 🚀 Запуск бота
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Бот запущен! Нажми Ctrl+C чтобы остановить.")
    app.run_polling()

if __name__ == "__main__":
    main()
