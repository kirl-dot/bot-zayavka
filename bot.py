import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# =============================================
# ⚙️ НАСТРОЙКИ — ИЗМЕНИ ЭТО
# =============================================
BOT_TOKEN = "8710179420:AAHvhAvT4jLHDPD9pntKeEdtV5VjBTLyZ5E"       # Токен от @BotFather
ADMIN_ID = 7027511136                        # Твой Telegram ID (узнай у @userinfobot)
# =============================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Хранилище заявок
applications: dict = {}
app_counter = 0

# =============================================
# СОСТОЯНИЯ FSM
# =============================================
class ApplicationForm(StatesGroup):
    choosing_role = State()
    custom_role = State()
    filling_name = State()
    filling_minecraft = State()
    filling_age = State()
    filling_experience = State()
    filling_why = State()
    filling_extra = State()

class AdminReply(StatesGroup):
    choosing_app = State()
    writing_message = State()

# =============================================
# ТЕКСТЫ АНКЕТ ПО РОЛЯМ
# =============================================
ROLE_DESCRIPTIONS = {
    "tiktok": "🎵 ТикТокер",
    "youtube": "🎬 Ютюбер",
    "moderator": "🛡 Модератор",
    "player": "⚔️ Игрок",
    "custom": "✨ Своя специальность"
}

ROLE_HINTS = {
    "tiktok": (
        "📋 <b>Формат заполнения анкеты для ТикТокера:</b>\n\n"
        "• Имя — твоё реальное имя или псевдоним\n"
        "• Ник в Майнкрафт — точный никнейм\n"
        "• Возраст — полных лет\n"
        "• Опыт — есть ли у тебя TikTok канал? Сколько подписчиков?\n"
        "• Почему ты? — почему хочешь стать ТикТокером нашего сервера\n"
        "• Доп. инфо — ссылка на канал или любая доп. информация\n\n"
        "Заполняй честно — это влияет на решение! 👇"
    ),
    "youtube": (
        "📋 <b>Формат заполнения анкеты для Ютюбера:</b>\n\n"
        "• Имя — твоё реальное имя или псевдоним\n"
        "• Ник в Майнкрафт — точный никнейм\n"
        "• Возраст — полных лет\n"
        "• Опыт — есть ли у тебя YouTube канал? Сколько подписчиков?\n"
        "• Почему ты? — почему хочешь снимать видео о нашем сервере\n"
        "• Доп. инфо — ссылка на канал или любая доп. информация\n\n"
        "Заполняй честно — это влияет на решение! 👇"
    ),
    "moderator": (
        "📋 <b>Формат заполнения анкеты для Модератора:</b>\n\n"
        "• Имя — твоё реальное имя или псевдоним\n"
        "• Ник в Майнкрафт — точный никнейм\n"
        "• Возраст — полных лет\n"
        "• Опыт — был ли ты модератором раньше? Где?\n"
        "• Почему ты? — почему именно ты должен стать модератором\n"
        "• Доп. инфо — сколько часов в день можешь уделять серверу\n\n"
        "Заполняй честно — это влияет на решение! 👇"
    ),
    "player": (
        "📋 <b>Формат заполнения анкеты для Игрока:</b>\n\n"
        "• Имя — твоё реальное имя или псевдоним\n"
        "• Ник в Майнкрафт — точный никнейм\n"
        "• Возраст — полных лет\n"
        "• Опыт — как давно играешь в Майнкрафт?\n"
        "• Почему ты? — почему хочешь играть на нашем сервере\n"
        "• Доп. инфо — откуда узнал о сервере, есть ли друзья тут\n\n"
        "Заполняй честно — это влияет на решение! 👇"
    ),
    "custom": (
        "📋 <b>Формат заполнения анкеты:</b>\n\n"
        "• Имя — твоё реальное имя или псевдоним\n"
        "• Ник в Майнкрафт — точный никнейм\n"
        "• Возраст — полных лет\n"
        "• Опыт — твой опыт в выбранной специальности\n"
        "• Почему ты? — почему именно ты и чем будешь полезен\n"
        "• Доп. инфо — любая дополнительная информация о себе\n\n"
        "Заполняй честно — это влияет на решение! 👇"
    ),
}

# =============================================
# КЛАВИАТУРЫ
# =============================================
def main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❓ Что это за бот?", callback_data="about")],
        [InlineKeyboardButton(text="📝 Подать заявку", callback_data="apply")],
    ])

def role_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎵 ТикТокер", callback_data="role_tiktok")],
        [InlineKeyboardButton(text="🎬 Ютюбер", callback_data="role_youtube")],
        [InlineKeyboardButton(text="🛡 Модератор", callback_data="role_moderator")],
        [InlineKeyboardButton(text="⚔️ Игрок", callback_data="role_player")],
        [InlineKeyboardButton(text="✨ Своя специальность", callback_data="role_custom")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")],
    ])

def admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Все заявки", callback_data="admin_list")],
        [InlineKeyboardButton(text="✅ Принятые", callback_data="admin_accepted")],
        [InlineKeyboardButton(text="❌ Отклонённые", callback_data="admin_rejected")],
        [InlineKeyboardButton(text="⏳ Ожидающие", callback_data="admin_pending")],
    ])

def app_action_keyboard(app_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_{app_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{app_id}"),
        ],
        [InlineKeyboardButton(text="💬 Написать свой ответ", callback_data=f"custom_reply_{app_id}")],
        [InlineKeyboardButton(text="🔙 К списку", callback_data="admin_list")],
    ])

# =============================================
# СТАРТ
# =============================================
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 <b>Добро пожаловать!</b>\n\n"
        "Это официальный бот сервера для подачи заявок на роли.\n"
        "Выбери, что тебя интересует 👇",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )

# =============================================
# О БОТЕ
# =============================================
@dp.callback_query(F.data == "about")
async def about_bot(call: CallbackQuery):
    await call.message.edit_text(
        "🤖 <b>Что это за бот?</b>\n\n"
        "Этот бот создан для подачи заявок на роли нашего Minecraft сервера.\n\n"
        "<b>Доступные роли:</b>\n"
        "🎵 <b>ТикТокер</b> — снимаешь видосы про сервер в TikTok\n"
        "🎬 <b>Ютюбер</b> — ведёшь YouTube канал о сервере\n"
        "🛡 <b>Модератор</b> — следишь за порядком на сервере\n"
        "⚔️ <b>Игрок</b> — хочешь стать частью нашего сообщества\n"
        "✨ <b>Своя специальность</b> — есть другое предложение? Напиши!\n\n"
        "Нажми <b>«Подать заявку»</b> и следуй инструкциям 🚀",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Подать заявку", callback_data="apply")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")],
        ]),
        parse_mode="HTML"
    )
    await call.answer()

# =============================================
# НАЗАД
# =============================================
@dp.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        "👋 <b>Добро пожаловать!</b>\n\n"
        "Это официальный бот сервера для подачи заявок на роли.\n"
        "Выбери, что тебя интересует 👇",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()

# =============================================
# ВЫБОР РОЛИ
# =============================================
@dp.callback_query(F.data == "apply")
async def choose_role(call: CallbackQuery, state: FSMContext):
    await state.set_state(ApplicationForm.choosing_role)
    await call.message.edit_text(
        "📝 <b>Выбери роль для заявки:</b>\n\n"
        "Нажми на нужную кнопку ниже 👇",
        reply_markup=role_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()

# =============================================
# СВОЯ СПЕЦИАЛЬНОСТЬ
# =============================================
@dp.callback_query(F.data == "role_custom")
async def custom_role_input(call: CallbackQuery, state: FSMContext):
    await state.set_state(ApplicationForm.custom_role)
    await call.message.edit_text(
        "✨ <b>Своя специальность</b>\n\n"
        "Напиши, на какую роль ты хочешь подать заявку.\n"
        "Например: <i>Билдер, Редактор, Стример</i> и т.д.\n\n"
        "✏️ Введи своё предложение:",
        parse_mode="HTML"
    )
    await call.answer()

@dp.message(ApplicationForm.custom_role)
async def save_custom_role(message: Message, state: FSMContext):
    role_name = message.text.strip()
    await state.update_data(role="custom", custom_role_name=role_name)
    hint = ROLE_HINTS["custom"]
    await message.answer(
        f"✨ <b>Твоя специальность: {role_name}</b>\n\n{hint}\n\n"
        "👤 Введи своё <b>имя</b> (реальное или псевдоним):",
        parse_mode="HTML"
    )
    await state.set_state(ApplicationForm.filling_name)

# =============================================
# ВЫБОР РОЛИ — КНОПКИ
# =============================================
@dp.callback_query(F.data.startswith("role_") & ~F.data.in_({"role_custom"}))
async def select_role(call: CallbackQuery, state: FSMContext):
    role = call.data.replace("role_", "")
    if role not in ROLE_DESCRIPTIONS:
        await call.answer("Неизвестная роль")
        return

    await state.update_data(role=role)
    hint = ROLE_HINTS[role]
    role_name = ROLE_DESCRIPTIONS[role]

    await call.message.edit_text(
        f"{role_name}\n\n{hint}\n\n"
        "👤 Введи своё <b>имя</b> (реальное или псевдоним):",
        parse_mode="HTML"
    )
    await state.set_state(ApplicationForm.filling_name)
    await call.answer()

# =============================================
# ЗАПОЛНЕНИЕ АНКЕТЫ
# =============================================
@dp.message(ApplicationForm.filling_name)
async def fill_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer(
        "⛏ Введи свой <b>ник в Майнкрафт</b>:",
        parse_mode="HTML"
    )
    await state.set_state(ApplicationForm.filling_minecraft)

@dp.message(ApplicationForm.filling_minecraft)
async def fill_minecraft(message: Message, state: FSMContext):
    await state.update_data(minecraft=message.text.strip())
    await message.answer(
        "🎂 Введи свой <b>возраст</b> (полных лет):",
        parse_mode="HTML"
    )
    await state.set_state(ApplicationForm.filling_age)

@dp.message(ApplicationForm.filling_age)
async def fill_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text.strip())
    await message.answer(
        "💼 Расскажи о своём <b>опыте</b>:",
        parse_mode="HTML"
    )
    await state.set_state(ApplicationForm.filling_experience)

@dp.message(ApplicationForm.filling_experience)
async def fill_experience(message: Message, state: FSMContext):
    await state.update_data(experience=message.text.strip())
    await message.answer(
        "💬 <b>Почему именно ты?</b> Убеди нас:",
        parse_mode="HTML"
    )
    await state.set_state(ApplicationForm.filling_why)

@dp.message(ApplicationForm.filling_why)
async def fill_why(message: Message, state: FSMContext):
    await state.update_data(why=message.text.strip())
    await message.answer(
        "📎 <b>Дополнительная информация</b> (ссылки, заметки, что угодно).\n"
        "Если нечего добавить — напиши <i>нет</i>",
        parse_mode="HTML"
    )
    await state.set_state(ApplicationForm.filling_extra)

@dp.message(ApplicationForm.filling_extra)
async def fill_extra(message: Message, state: FSMContext):
    global app_counter
    data = await state.get_data()
    await state.update_data(extra=message.text.strip())
    data = await state.get_data()

    app_counter += 1
    app_id = app_counter
    role = data.get("role", "player")
    role_display = data.get("custom_role_name", ROLE_DESCRIPTIONS.get(role, role))

    # Сохраняем заявку
    applications[app_id] = {
        "id": app_id,
        "user_id": message.from_user.id,
        "username": message.from_user.username or "нет",
        "tg_name": message.from_user.full_name,
        "role": role,
        "role_display": role_display,
        "name": data.get("name"),
        "minecraft": data.get("minecraft"),
        "age": data.get("age"),
        "experience": data.get("experience"),
        "why": data.get("why"),
        "extra": data.get("extra"),
        "status": "pending",
        "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
    }

    await state.clear()

    # Подтверждение пользователю
    await message.answer(
        f"✅ <b>Заявка #{app_id} отправлена!</b>\n\n"
        f"Роль: <b>{role_display}</b>\n"
        f"Имя: <b>{data.get('name')}</b>\n"
        f"Ник: <b>{data.get('minecraft')}</b>\n\n"
        "Администратор рассмотрит твою заявку и свяжется с тобой 🙏\n\n"
        "Нажми /start чтобы вернуться в главное меню.",
        parse_mode="HTML"
    )

    # Отправка в админ-панель
    app = applications[app_id]
    admin_text = (
        f"📨 <b>НОВАЯ ЗАЯВКА #{app_id}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📅 Дата: {app['date']}\n"
        f"👤 TG имя: {app['tg_name']}\n"
        f"🔗 TG ник: @{app['username']}\n"
        f"🆔 TG ID: <code>{app['user_id']}</code>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎭 Роль: <b>{app['role_display']}</b>\n"
        f"👤 Имя: {app['name']}\n"
        f"⛏ Ник в Майн: <b>{app['minecraft']}</b>\n"
        f"🎂 Возраст: {app['age']}\n"
        f"💼 Опыт: {app['experience']}\n"
        f"💬 Почему я: {app['why']}\n"
        f"📎 Доп. инфо: {app['extra']}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⏳ Статус: Ожидает решения"
    )

    try:
        await bot.send_message(
            ADMIN_ID,
            admin_text,
            reply_markup=app_action_keyboard(app_id),
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Не удалось отправить заявку админу: {e}")

# =============================================
# АДМИН — КОМАНДА /admin
# =============================================
@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У тебя нет доступа к этой команде.")
        return

    total = len(applications)
    pending = sum(1 for a in applications.values() if a["status"] == "pending")
    accepted = sum(1 for a in applications.values() if a["status"] == "accepted")
    rejected = sum(1 for a in applications.values() if a["status"] == "rejected")

    await message.answer(
        f"🔐 <b>АДМИН-ПАНЕЛЬ</b>\n\n"
        f"📊 Всего заявок: <b>{total}</b>\n"
        f"⏳ Ожидают: <b>{pending}</b>\n"
        f"✅ Принято: <b>{accepted}</b>\n"
        f"❌ Отклонено: <b>{rejected}</b>\n\n"
        "Выбери действие 👇",
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )

# =============================================
# СПИСОК ЗАЯВОК (для админа)
# =============================================
async def send_app_list(call: CallbackQuery, filter_status: str = None, title: str = "Все заявки"):
    if call.from_user.id != ADMIN_ID:
        await call.answer("⛔ Нет доступа", show_alert=True)
        return

    filtered = [a for a in applications.values()
                if filter_status is None or a["status"] == filter_status]

    if not filtered:
        await call.message.edit_text(
            f"📋 <b>{title}</b>\n\nЗаявок нет.",
            reply_markup=admin_keyboard(),
            parse_mode="HTML"
        )
        await call.answer()
        return

    buttons = []
    for app in sorted(filtered, key=lambda x: x["id"], reverse=True):
        status_icon = {"pending": "⏳", "accepted": "✅", "rejected": "❌"}.get(app["status"], "❓")
        buttons.append([InlineKeyboardButton(
            text=f"{status_icon} #{app['id']} {app['role_display']} — {app['minecraft']}",
            callback_data=f"view_app_{app['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")])

    await call.message.edit_text(
        f"📋 <b>{title}</b> ({len(filtered)} шт.)\n\nВыбери заявку:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await call.answer()

@dp.callback_query(F.data == "admin_list")
async def admin_list(call: CallbackQuery):
    await send_app_list(call, None, "Все заявки")

@dp.callback_query(F.data == "admin_pending")
async def admin_pending(call: CallbackQuery):
    await send_app_list(call, "pending", "⏳ Ожидающие заявки")

@dp.callback_query(F.data == "admin_accepted")
async def admin_accepted(call: CallbackQuery):
    await send_app_list(call, "accepted", "✅ Принятые заявки")

@dp.callback_query(F.data == "admin_rejected")
async def admin_rejected(call: CallbackQuery):
    await send_app_list(call, "rejected", "❌ Отклонённые заявки")

@dp.callback_query(F.data == "admin_back")
async def admin_back(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("⛔", show_alert=True)
        return
    total = len(applications)
    pending = sum(1 for a in applications.values() if a["status"] == "pending")
    accepted = sum(1 for a in applications.values() if a["status"] == "accepted")
    rejected = sum(1 for a in applications.values() if a["status"] == "rejected")
    await call.message.edit_text(
        f"🔐 <b>АДМИН-ПАНЕЛЬ</b>\n\n"
        f"📊 Всего заявок: <b>{total}</b>\n"
        f"⏳ Ожидают: <b>{pending}</b>\n"
        f"✅ Принято: <b>{accepted}</b>\n"
        f"❌ Отклонено: <b>{rejected}</b>\n\n"
        "Выбери действие 👇",
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()

# =============================================
# ПРОСМОТР КОНКРЕТНОЙ ЗАЯВКИ
# =============================================
@dp.callback_query(F.data.startswith("view_app_"))
async def view_application(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("⛔", show_alert=True)
        return

    app_id = int(call.data.replace("view_app_", ""))
    app = applications.get(app_id)

    if not app:
        await call.answer("Заявка не найдена", show_alert=True)
        return

    status_text = {"pending": "⏳ Ожидает", "accepted": "✅ Принята", "rejected": "❌ Отклонена"}.get(app["status"])
    text = (
        f"📄 <b>ЗАЯВКА #{app_id}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📅 Дата: {app['date']}\n"
        f"👤 TG имя: {app['tg_name']}\n"
        f"🔗 TG ник: @{app['username']}\n"
        f"🆔 TG ID: <code>{app['user_id']}</code>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎭 Роль: <b>{app['role_display']}</b>\n"
        f"👤 Имя: {app['name']}\n"
        f"⛏ Ник в Майн: <b>{app['minecraft']}</b>\n"
        f"🎂 Возраст: {app['age']}\n"
        f"💼 Опыт: {app['experience']}\n"
        f"💬 Почему я: {app['why']}\n"
        f"📎 Доп. инфо: {app['extra']}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Статус: {status_text}"
    )

    await call.message.edit_text(text, reply_markup=app_action_keyboard(app_id), parse_mode="HTML")
    await call.answer()

# =============================================
# ДЕЙСТВИЯ С ЗАЯВКОЙ
# =============================================
@dp.callback_query(F.data.startswith("accept_"))
async def accept_application(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("⛔", show_alert=True)
        return

    app_id = int(call.data.replace("accept_", ""))
    app = applications.get(app_id)
    if not app:
        await call.answer("Заявка не найдена", show_alert=True)
        return

    app["status"] = "accepted"

    # Уведомление пользователю
    try:
        await bot.send_message(
            app["user_id"],
            f"🎉 <b>Твоя заявка принята!</b>\n\n"
            f"Заявка #{app_id} на роль <b>{app['role_display']}</b>\n"
            f"Ник: <b>{app['minecraft']}</b>\n\n"
            "Поздравляем! Скоро с тобой свяжутся для дальнейших инструкций. 🚀",
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Не удалось отправить уведомление: {e}")

    await call.message.edit_text(
        call.message.text + "\n\n✅ <b>ЗАЯВКА ПРИНЯТА</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К списку", callback_data="admin_list")]
        ]),
        parse_mode="HTML"
    )
    await call.answer("✅ Заявка принята!", show_alert=True)

@dp.callback_query(F.data.startswith("reject_"))
async def reject_application(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("⛔", show_alert=True)
        return

    app_id = int(call.data.replace("reject_", ""))
    app = applications.get(app_id)
    if not app:
        await call.answer("Заявка не найдена", show_alert=True)
        return

    app["status"] = "rejected"

    try:
        await bot.send_message(
            app["user_id"],
            f"😔 <b>Заявка отклонена</b>\n\n"
            f"Заявка #{app_id} на роль <b>{app['role_display']}</b>\n"
            f"Ник: <b>{app['minecraft']}</b>\n\n"
            "К сожалению, на этот раз не получилось. Попробуй снова позже! 💪",
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Не удалось отправить уведомление: {e}")

    await call.message.edit_text(
        call.message.text + "\n\n❌ <b>ЗАЯВКА ОТКЛОНЕНА</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К списку", callback_data="admin_list")]
        ]),
        parse_mode="HTML"
    )
    await call.answer("❌ Заявка отклонена!", show_alert=True)

# =============================================
# СВОЙ ОТВЕТ АДМИНА
# =============================================
@dp.callback_query(F.data.startswith("custom_reply_"))
async def custom_reply_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        await call.answer("⛔", show_alert=True)
        return

    app_id = int(call.data.replace("custom_reply_", ""))
    await state.set_state(AdminReply.writing_message)
    await state.update_data(reply_app_id=app_id)

    await call.message.answer(
        f"✏️ Напиши свой ответ для заявки <b>#{app_id}</b>.\n\n"
        "Это сообщение будет отправлено игроку напрямую:",
        parse_mode="HTML"
    )
    await call.answer()

@dp.message(AdminReply.writing_message)
async def custom_reply_send(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    data = await state.get_data()
    app_id = data.get("reply_app_id")
    app = applications.get(app_id)

    if not app:
        await message.answer("Заявка не найдена.")
        await state.clear()
        return

    try:
        await bot.send_message(
            app["user_id"],
            f"📩 <b>Сообщение от администратора</b>\n"
            f"(Заявка #{app_id} — {app['role_display']})\n\n"
            f"{message.text}",
            parse_mode="HTML"
        )
        await message.answer(f"✅ Сообщение отправлено игроку <b>{app['minecraft']}</b>!", parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❗ Не удалось отправить: {e}")

    await state.clear()

# =============================================
# ЗАПУСК
# =============================================
async def main():
    print("🤖 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
