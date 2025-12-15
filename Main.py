#Пример: Telegram-бот с красивым интерфейсом (InlineKeyboard)

#который разворачивает Docker-контейнер с Hikka Userbot

#⚠️ Упрощённый, но рабочий шаблон

#Требования:

#pip install aiogram docker

#Docker должен быть установлен на сервере

import asyncio 
import docker 
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton 
from aiogram.filters import Command

TOKEN = "BOT_TOKEN_HERE"

bot = Bot(TOKEN) dp = Dispatcher() docker_client = docker.from_env()

HIKKA_IMAGE = "ghcr.io/hikariatama/hikka:latest"

================= UI =================

def main_menu(): kb = InlineKeyboardMarkup(inline_keyboard=[ [InlineKeyboardButton(text="🖥 Сервер 1", callback_data="server_1")], [InlineKeyboardButton(text="➕ Добавить сервер", callback_data="add_server")] ]) return kb

================= Commands =================

@dp.message(Command("start")) async def start(msg: types.Message): await msg.answer( "✨ Hikka Host Panel\n\n" "Выбери сервер для установки юзербота", parse_mode="Markdown", reply_markup=main_menu() )

================= Callbacks =================

@dp.callback_query(lambda c: c.data.startswith("server_")) async def server_menu(call: types.CallbackQuery): server_id = call.data

kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🐳 Установить Hikka", callback_data=f"install:{server_id}")],
    [InlineKeyboardButton(text="⬅ Назад", callback_data="back")]
])

await call.message.edit_text(
    f"🖥 *{server_id}*\n\nВыбери действие:",
    parse_mode="Markdown",
    reply_markup=kb
)

@dp.callback_query(lambda c: c.data.startswith("install:")) async def install_hikka(call: types.CallbackQuery): await call.message.edit_text("⏳ Установка Hikka Userbot...")

try:
    container = docker_client.containers.run(
        HIKKA_IMAGE,
        detach=True,
        tty=True,
        name=f"hikka_{call.from_user.id}",
        restart_policy={"Name": "always"},
    )

    link = "https://t.me/hikka_login_bot"

    await call.message.edit_text(
        "✅ *Hikka успешно установлен!*\n\n"
        f"🔗 Для подключения юзербота:\n{link}",
        parse_mode="Markdown"
    )

except Exception as e:
    await call.message.edit_text(f"❌ Ошибка установки:\n`{e}`", parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "back") async def back(call: types.CallbackQuery): await call.message.edit_text( "✨ Hikka Host Panel", parse_mode="Markdown", reply_markup=main_menu() )

================= Run =================

async def main(): await dp.start_polling(bot)

if name == "main": asyncio.run(main())
