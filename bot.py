# bot.py
import telebot
import os

BOT_TOKEN = "8912269941:AAGkKwNTZOX4nbiuVl5eE9LOtoths3Oqb4c"
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✅ Render पर बोट चल रहा है!")

print("🤖 BOT STARTING ON RENDER...")
bot.polling(none_stop=True)
