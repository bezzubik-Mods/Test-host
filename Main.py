

import asyncio
import docker 
import asyncssh
from aiogram 
import Bot, Dispatcher, types 
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton 
from aiogram.filters import Command

TOKEN = "BOT_TOKEN_HERE"

bot = Bot(TOKEN) 
dp = Dispatcher()

#================== CONFIG ==================

USERBOTS = { "hikka": { "name": "✨ Hikka Userbot", "image": "ghcr.io/hikariatama/hikka:latest", "login": "https://t.me/hikka_login_bot" }, "ftg": { "name": "⚡ FTG Userbot", "image": "ghcr.io/ftg-userbot/ftg:latest", "login": "https://t.me/ftg_session_bot" } }

Хранилище серверов (лучше заменить на БД)

SERVERS = {} 
USER_STATE = {}

docker_client = docker.from_env()

#================== UI ==================

def servers_menu(): kb = [] for sid in SERVERS: kb.append([InlineKeyboardButton(text=f"🖥 {sid}", callback_data=f"server:{sid}")]) kb.append([InlineKeyboardButton(text="➕ Добавить сервер", callback_data="add_server")]) return InlineKeyboardMarkup(inline_keyboard=kb)

def userbot_menu(server_id): kb = [] for key, ub in USERBOTS.items(): kb.append([ InlineKeyboardButton( text=ub["name"], callback_data=f"install:{server_id}:{key}" ) ]) kb.append([InlineKeyboardButton(text="⬅ Назад", callback_data="back")]) return InlineKeyboardMarkup(inline_keyboard=kb)

#================== COMMANDS ==================

@dp.message(Command("start")) async def start(msg: types.Message): await msg.answer( "🧠 Host Panel\n\n" "Выберите сервер или добавьте новый", parse_mode="Markdown", reply_markup=servers_menu() )

#================== CALLBACKS ==================

@dp.callback_query(lambda c: c.data == "add_server") async def add_server(call: types.CallbackQuery): USER_STATE[call.from_user.id] = "await_server" await call.message.answer( "🔐 Отправь данные сервера в формате:\n" "ip user password", parse_mode="Markdown" )

@dp.message(lambda m: USER_STATE.get(m.from_user.id) == "await_server") async def save_server(msg: types.Message): try: ip, user, password = msg.text.split() server_id = f"srv_{len(SERVERS)+1}"

# проверка SSH
    async with asyncssh.connect(ip, username=user, password=password):
        pass

    SERVERS[server_id] = {
        "ip": ip,
        "user": user,
        "password": password
    }

    USER_STATE.pop(msg.from_user.id)

    await msg.answer(f"✅ Сервер `{server_id}` добавлен", parse_mode="Markdown")
    await start(msg)

except Exception as e:
    await msg.answer(f"❌ Ошибка подключения:\n`{e}`", parse_mode="Markdown")

@dp.callback_query(lambda c: c.data.startswith("server:")) async def server_select(call: types.CallbackQuery): server_id = call.data.split(":")[1]

await call.message.edit_text(
    f"🖥 *{server_id}*\n\nВыбери юзербот:",
    parse_mode="Markdown",
    reply_markup=userbot_menu(server_id)
)

@dp.callback_query(lambda c: c.data.startswith("install:")) async def install_userbot(call: types.CallbackQuery): _, server_id, ub_key = call.data.split(":") ub = USERBOTS[ub_key]

await call.message.edit_text("⏳ Установка юзербота...")

try:
    container = docker_client.containers.run(
        ub["image"],
        detach=True,
        tty=True,
        name=f"{ub_key}_{call.from_user.id}",
        restart_policy={"Name": "always"},
    )

    await call.message.edit_text(
        "✅ *Установка завершена!*\n\n"
        f"🔗 Авторизация:\n{ub['login']}",
        parse_mode="Markdown"
    )

except Exception as e:
    await call.message.edit_text(f"❌ Ошибка:\n`{e}`", parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "back") async def back(call: types.CallbackQuery): await call.message.edit_text( "🧠 Host Panel", parse_mode="Markdown", reply_markup=servers_menu() )

#================== RUN ==================

async def main(): await dp.start_polling(bot)

if name == "main": asyncio.run(main())
