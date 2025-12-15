# Telegram Userbot Hosting (FREE)
# Роли: Админ / Пользователь
# Админы: серверы + юзерботы
# Пользователи: только установка
# Python 3.10+

# pip install aiogram docker asyncssh

import asyncio
import docker
import asyncssh

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================== НАСТРОЙКИ ==================

TOKEN = "8446018224:AAHlRvnuT-WxvQTHqzJIWcM1686PfqIWtQI"

# 👑 ID АДМИНОВ (узнай через @userinfobot)
ADMINS = {
    6463195623,   # ← сюда впиши свой Telegram ID
}

# ================== ХРАНИЛИЩЕ ==================
# ⚠️ временно в памяти (потом можно SQLite)

SERVERS = {}     # server_id -> {ip, user, password}
USERBOTS = {}    # key -> {name, image, login}
USER_STATE = {}  # user_id -> state

# ================== INIT ==================

bot = Bot(TOKEN)
dp = Dispatcher()
docker_client = docker.from_env()

# ================== HELPERS ==================

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

# ================== UI ==================

def main_menu(user_id):
    kb = []

    kb.append([InlineKeyboardButton("🤖 Установить юзербот", callback_data="install_menu")])

    if is_admin(user_id):
        kb.append([InlineKeyboardButton("🛠 Админ-панель", callback_data="admin_panel")])

    return InlineKeyboardMarkup(inline_keyboard=kb)


def admin_panel():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("➕ Добавить сервер", callback_data="add_server")],
        [InlineKeyboardButton("❌ Удалить сервер", callback_data="del_server")],
        [InlineKeyboardButton("➕ Добавить юзербот", callback_data="add_userbot")],
        [InlineKeyboardButton("❌ Удалить юзербот", callback_data="del_userbot")],
        [InlineKeyboardButton("⬅ Назад", callback_data="back")]
    ])


def userbot_menu():
    kb = []
    for key, ub in USERBOTS.items():
        kb.append([
            InlineKeyboardButton(
                ub["name"],
                callback_data=f"install:{key}"
            )
        ])
    kb.append([InlineKeyboardButton("⬅ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def servers_menu(prefix):
    kb = []
    for sid in SERVERS:
        kb.append([
            InlineKeyboardButton(
                sid,
                callback_data=f"{prefix}:{sid}"
            )
        ])
    kb.append([InlineKeyboardButton("⬅ Назад", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ================== COMMANDS ==================

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🆓 *Free Userbot Hosting*\n\n"
        "Выбери действие:",
        parse_mode="Markdown",
        reply_markup=main_menu(message.from_user.id)
    )

# ================== CALLBACKS ==================

@dp.callback_query(lambda c: c.data == "admin_panel")
async def admin_menu(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    await call.message.edit_text(
        "🛠 *Админ-панель*",
        parse_mode="Markdown",
        reply_markup=admin_panel()
    )

# ----------- SERVERS -----------

@dp.callback_query(lambda c: c.data == "add_server")
async def add_server(call: types.CallbackQuery):
    USER_STATE[call.from_user.id] = "add_server"
    await call.message.answer(
        "Отправь сервер:\n`ip user password`",
        parse_mode="Markdown"
    )

@dp.message(lambda m: USER_STATE.get(m.from_user.id) == "add_server")
async def save_server(message: types.Message):
    try:
        ip, user, password = message.text.split()

        async with asyncssh.connect(ip, username=user, password=password, known_hosts=None):
            pass

        sid = f"server_{len(SERVERS)+1}"
        SERVERS[sid] = {"ip": ip, "user": user, "password": password}

        USER_STATE.pop(message.from_user.id)

        await message.answer(f"✅ Сервер `{sid}` добавлен", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Ошибка:\n`{e}`", parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "del_server")
async def del_server_menu(call: types.CallbackQuery):
    await call.message.edit_text(
        "❌ Выбери сервер:",
        reply_markup=servers_menu("del_server_do")
    )

@dp.callback_query(lambda c: c.data.startswith("del_server_do:"))
async def del_server(call: types.CallbackQuery):
    sid = call.data.split(":")[1]
    SERVERS.pop(sid, None)
    await call.message.edit_text(f"✅ Сервер `{sid}` удалён", parse_mode="Markdown")

# ----------- USERBOTS -----------

@dp.callback_query(lambda c: c.data == "add_userbot")
async def add_userbot(call: types.CallbackQuery):
    USER_STATE[call.from_user.id] = "add_userbot"
    await call.message.answer(
        "Отправь юзербот:\n"
        "`key | name | docker_image | login_link`",
        parse_mode="Markdown"
    )

@dp.message(lambda m: USER_STATE.get(m.from_user.id) == "add_userbot")
async def save_userbot(message: types.Message):
    try:
        key, name, image, login = [x.strip() for x in message.text.split("|")]
        USERBOTS[key] = {"name": name, "image": image, "login": login}
        USER_STATE.pop(message.from_user.id)
        await message.answer("✅ Юзербот добавлен")
    except:
        await message.answer("❌ Неверный формат")

@dp.callback_query(lambda c: c.data == "del_userbot")
async def del_userbot_menu(call: types.CallbackQuery):
    kb = []
    for key in USERBOTS:
        kb.append([InlineKeyboardButton(key, callback_data=f"del_userbot_do:{key}")])
    kb.append([InlineKeyboardButton("⬅ Назад", callback_data="admin_panel")])
    await call.message.edit_text("❌ Выбери юзербот:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(lambda c: c.data.startswith("del_userbot_do:"))
async def del_userbot(call: types.CallbackQuery):
    key = call.data.split(":")[1]
    USERBOTS.pop(key, None)
    await call.message.edit_text(f"✅ Юзербот `{key}` удалён", parse_mode="Markdown")

# ----------- INSTALL -----------

@dp.callback_query(lambda c: c.data == "install_menu")
async def install_menu(call: types.CallbackQuery):
    await call.message.edit_text(
        "🤖 Выбери юзербот:",
        reply_markup=userbot_menu()
    )

@dp.callback_query(lambda c: c.data.startswith("install:"))
async def install(call: types.CallbackQuery):
    key = call.data.split(":")[1]
    ub = USERBOTS[key]

    docker_client.containers.run(
        ub["image"],
        detach=True,
        tty=True,
        name=f"{key}_{call.from_user.id}",
        restart_policy={"Name": "always"}
    )

    await call.message.edit_text(
        f"✅ Установлено!\n\n🔗 Авторизация:\n{ub['login']}"
    )

# ----------- BACK -----------

@dp.callback_query(lambda c: c.data == "back")
async def back(call: types.CallbackQuery):
    await start(call.message)

# ================== RUN ==================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
