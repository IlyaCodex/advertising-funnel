# -*- coding: utf-8 -*-
import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, BotCommand, CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BOT_TOKEN, MAIN_BOT_LINK, SUPPORT_USERNAME, ADMIN_IDS, TARIFFS
from database import (
    init_db, close_db, add_user, is_trial_activated, activate_trial,
    get_referral_count, get_user_count, get_setting, set_setting
)

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Путь к скриншоту инструкции
INSTRUCTION_PHOTO = os.path.join(os.path.dirname(__file__), "instruction.png")

# Демо ключи для выдачи
DEMO_KEYS = [
    "vless://a7c01c26-1634-4b83-aacf-d54d1bec7c8a@194.124.211.206:443?security=reality&encryption=none&flow=xtls-rprx-vision&type=tcp&sni=telegram.org&pbk=OrSSDhr53zEISMa39-0gXDPvRWlDjfSlh44m7YAgGis&sid=9f1042d7#Нидерланды (Дронтен) | TCP",
    "vless://cc313b1f-1bf9-4960-b350-09b50ac03efc@193.23.194.245:443?security=reality&encryption=none&flow=xtls-rprx-vision&type=tcp&sni=telegram.org&pbk=RMz_zUooCvY976lz-35Wh1wP7W_qR4YiWOQ-6m_QM24&sid=64b9f509#Германия | TCP",
]


# ============================================================
# KEYBOARDS
# ============================================================

def kb_start() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(
        text="🆓 Протестировать бесплатно 🆓",
        callback_data="trial"
    ))

    builder.row(InlineKeyboardButton(
        text="💳 Тарифы и оплата",
        callback_data="tariffs"
    ))

    builder.row(InlineKeyboardButton(
        text="📖 Инструкция",
        callback_data="instructions"
    ))

    builder.row(InlineKeyboardButton(
        text="👥 Рекомендовать друзьям",
        callback_data="referral"
    ))

    builder.row(InlineKeyboardButton(
        text="🔑 Мои ключи",
        callback_data="my_keys"
    ))

    builder.row(InlineKeyboardButton(
        text="🛟 Поддержка",
        url=f"https://t.me/{SUPPORT_USERNAME}"
    ))

    return builder.as_markup()


def kb_after_trial() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(
        text="💳 Тарифы и оплата",
        callback_data="tariffs"
    ))

    builder.row(InlineKeyboardButton(
        text="📖 Инструкция",
        callback_data="instructions"
    ))

    builder.row(InlineKeyboardButton(
        text="🔑 Мои ключи",
        callback_data="my_keys"
    ))

    builder.row(InlineKeyboardButton(
        text="👥 Рекомендовать друзьям",
        callback_data="referral"
    ))

    builder.row(InlineKeyboardButton(
        text="🛟 Поддержка",
        url=f"https://t.me/{SUPPORT_USERNAME}"
    ))

    return builder.as_markup()


def kb_tariffs() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, t in TARIFFS.items():
        builder.row(InlineKeyboardButton(
            text=f"{t['emoji']} {t['name']} — {t['price']}",
            callback_data=f"pay_{key}"
        ))
    builder.row(InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_main"
    ))
    return builder.as_markup()


def kb_back() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_main"
    ))
    return builder.as_markup()


def kb_instructions() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(
        text="📥 Скачать v2RayTun (Android)",
        url="https://play.google.com/store/apps/details?id=com.v2ray.client"
    ))

    builder.row(InlineKeyboardButton(
        text="📥 Скачать v2RayTun (iOS)",
        url="https://apps.apple.com/us/app/v2raytun/id6476628951"
    ))

    builder.row(InlineKeyboardButton(
        text="🔑 Мои ключи",
        callback_data="my_keys"
    ))

    builder.row(InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_main"
    ))

    return builder.as_markup()


def kb_admin() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🔴 Включить редирект",
        callback_data="admin_redirect_on"
    ))
    builder.row(InlineKeyboardButton(
        text="🟢 Выключить редирект (полный бот)",
        callback_data="admin_redirect_off"
    ))
    builder.row(InlineKeyboardButton(
        text="📊 Статистика",
        callback_data="admin_stats"
    ))
    return builder.as_markup()


def kb_redirect() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🚀 Активировать бесплатный период",
        url=MAIN_BOT_LINK
    ))
    return builder.as_markup()


# ============================================================
# COMMANDS
# ============================================================

async def set_commands():
    await bot.set_my_commands([
        BotCommand(command="start", description="🏠 Главная"),
        BotCommand(command="features", description="⭐ Преимущества"),
    ])


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user = message.from_user
    ref_id = 0
    if message.text and len(message.text.split()) > 1:
        try:
            ref_id = int(message.text.split()[1])
        except ValueError:
            ref_id = 0

    await add_user(user.id, user.username or "", user.first_name or "", ref_id)

    # Проверяем режим редиректа
    mode = await get_setting("redirect_mode")
    if mode == "1":
        text = (
            "🛡 <b>Guard Tunnel VPN</b>\n\n"
            "Надёжная защита данных и стабильное соединение "
            "в любой точке мира.\n\n"
            "✅ До 10 Gbit/с\n"
            "✅ Обход белых списков (глушилок)\n"
            "✅ Шифрование трафика\n"
            "✅ Серверы в 10+ странах\n"
            "✅ Работает на всех устройствах\n"
            "✅ Поддержка 24/7\n\n"
            "✅ Бесплатные Proxy для стабильной работы Telegram\n\n"
            "🎁 <b>Пробный период — 5 дней бесплатно.</b>\n"
            "Без привязки карты. Активация за 2 минуты.\n\n"
            "👇 Нажми кнопку и получи доступ прямо сейчас"
        )
        await message.answer(text, parse_mode="HTML", reply_markup=kb_redirect())
        return

    text = (
        "🛡 <b>Добро пожаловать в Guard Tunnel VPN!</b>\n\n"
        "💰 Самые <b>низкие цены</b>\n"
        "⛔ <b>Без лимитов</b> на скорость\n"
        "📲 Простая настройка в 3 клика\n"
        "🔏 Конфиденциальность и анонимность\n"
        "🔐 Повышенная безопасность\n"
        "🌐 Новейшие методы шифрования\n"
        "🌍 Сервера по всему миру\n"
        "🔄 Автоматическая замена серверов\n"
        "🌏 Доступ к любым сайтам и приложениям\n"
        "🎁 За каждого приглашенного друга <b>дарим 7 дней</b>\n\n"
        f"‼️ <b>Поддержка:</b> @{SUPPORT_USERNAME}\n\n"
        "🆓 Получите 3 дня бесплатно, чтобы протестировать сервис 👇"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=kb_start())


@dp.message(Command("features"))
async def cmd_features(message: types.Message):
    mode = await get_setting("redirect_mode")
    if mode == "1":
        text = (
            "🛡 <b>Guard Tunnel VPN</b>\n\n"
            "Надёжная защита данных и стабильное соединение "
            "в любой точке мира.\n\n"
            "✅ До 10 Gbit/с\n"
            "✅ Обход белых списков (глушилок)\n"
            "✅ Шифрование трафика\n"
            "✅ Серверы в 10+ странах\n"
            "✅ Работает на всех устройствах\n"
            "✅ Поддержка 24/7\n\n"
            "✅ Бесплатные Proxy для стабильной работы Telegram\n\n"
            "🎁 <b>Пробный период — 5 дней бесплатно.</b>\n"
            "Без привязки карты. Активация за 2 минуты.\n\n"
            "👇 Нажми кнопку и получи доступ прямо сейчас"
        )
        await message.answer(text, parse_mode="HTML", reply_markup=kb_redirect())
        return

    text = (
        "⭐ <b>Преимущества Guard Tunnel VPN</b>\n\n"
        "⚡ <b>Скорость до 10 Gbit/с</b>\n"
        "Стриминг, игры, звонки без лагов.\n\n"
        "🔐 <b>VLESS шифрование</b>\n"
        "Никто не видит что вы делаете в сети.\n\n"
        "🌍 <b>10+ стран</b>\n"
        "Европа, Азия, Америка.\n\n"
        "📱 <b>Все устройства</b>\n"
        "iOS, Android, Windows, macOS, Linux.\n\n"
        "🛟 <b>Поддержка 24/7</b>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=kb_start())


@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    mode = await get_setting("redirect_mode")
    status = "🔴 Редирект" if mode == "1" else "🟢 Полный бот"
    count = await get_user_count()

    text = (
        "🛠 <b>Админ-панель</b>\n\n"
        f"📊 Пользователей: <b>{count}</b>\n"
        f"💡 Режим: <b>{status}</b>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=kb_admin())


# ============================================================
# CALLBACKS
# ============================================================

@dp.callback_query(F.data == "trial")
async def cb_trial(callback: CallbackQuery):
    user_id = callback.from_user.id
    already = await is_trial_activated(user_id)

    if already:
        await callback.answer("✅ Тестовый период уже активирован", show_alert=True)
        return

    await activate_trial(user_id)

    keys_text = "\n\n".join([f"<code>{k}</code>" for k in DEMO_KEYS])
    text = (
        "✅ <b>Тестовый период активирован!</b>\n\n"
        "🗓 Срок: <b>3 дня</b>\n\n"
        "🔑 <b>Ваши ключи:</b>\n\n"
        f"{keys_text}\n\n"
        "👆 Нажмите на ключ чтобы скопировать, затем вставьте в приложение.\n\n"
        "📲 Нажмите <b>📖 Инструкция</b> чтобы узнать как подключиться."
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=kb_after_trial())
    await callback.answer()


@dp.callback_query(F.data == "instructions")
async def cb_instructions(callback: CallbackQuery):
    text = (
        "📖 <b>Инструкция по подключению</b>\n\n"
        "1️⃣ Скачай приложение <b>v2RayTun</b> для своего устройства 👇\n\n"
        "2️⃣ Скопируй ключи из раздела <b>«🔑 Мои ключи»</b>\n\n"
        "3️⃣ Открой приложение <b>v2RayTun</b>, нажми на <b>+</b> "
        "в правом верхнем углу\n\n"
        '4️⃣ Выбери <b>«Импорт из буфера обмена»</b>\n\n'
        "5️⃣ Нажми кнопку подключения ▶️\n\n"
        "✅ Готово! VPN работает."
    )

    # Отправляем фото если файл существует
    if os.path.exists(INSTRUCTION_PHOTO):
        photo = FSInputFile(INSTRUCTION_PHOTO)
        await callback.message.answer_photo(
            photo=photo,
            caption=text,
            parse_mode="HTML",
            reply_markup=kb_instructions()
        )
    else:
        await callback.message.answer(
            text,
            parse_mode="HTML",
            reply_markup=kb_instructions()
        )

    await callback.answer()


@dp.callback_query(F.data == "my_keys")
async def cb_my_keys(callback: CallbackQuery):
    user_id = callback.from_user.id
    already = await is_trial_activated(user_id)

    if not already:
        await callback.answer(
            "❌ У вас нет активных ключей. Сначала активируйте тестовый период!",
            show_alert=True
        )
        return

    keys_text = "\n\n".join([f"<code>{k}</code>" for k in DEMO_KEYS])
    text = (
        "🔑 <b>Ваши ключи:</b>\n\n"
        f"{keys_text}\n\n"
        "👆 Нажмите на ключ чтобы скопировать.\n\n"
        "📲 Не знаете как подключить? Нажмите <b>📖 Инструкция</b>"
    )

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="📖 Инструкция",
        callback_data="instructions"
    ))
    builder.row(InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_main"
    ))

    await callback.message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()


@dp.callback_query(F.data == "referral")
async def cb_referral(callback: CallbackQuery):
    user_id = callback.from_user.id
    count = await get_referral_count(user_id)
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"

    text = (
        "👥 <b>Реферальная программа</b>\n\n"
        "🎁 За каждого приглашенного друга вы получаете <b>+7 дней</b> бесплатно!\n\n"
        f"🔗 <b>Ваша ссылка:</b>\n<code>{ref_link}</code>\n\n"
        f"📊 Приглашено друзей: <b>{count}</b>\n"
        f"🎉 Бонус дней: <b>{count * 7}</b>"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=kb_back())
    await callback.answer()


@dp.callback_query(F.data == "tariffs")
async def cb_tariffs(callback: CallbackQuery):
    text = "💳 <b>Тарифы Guard Tunnel VPN</b>\n\nВыберите подходящий тариф:"
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb_tariffs())
    await callback.answer()


@dp.callback_query(F.data.startswith("pay_"))
async def cb_pay(callback: CallbackQuery):
    tariff_key = callback.data.replace("pay_", "")
    tariff = TARIFFS.get(tariff_key)

    if not tariff:
        await callback.answer("Тариф не найден", show_alert=True)
        return

    text = (
        f"💳 <b>Оплата: {tariff['name']}</b>\n\n"
        f"💰 Стоимость: <b>{tariff['price']}</b>\n\n"
        f"📩 Для оплаты напишите в поддержку: @{SUPPORT_USERNAME}\n"
        "Укажите выбранный тариф — вам пришлют реквизиты."
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb_back())
    await callback.answer()


@dp.callback_query(F.data == "connect_vless")
async def cb_connect(callback: CallbackQuery):
    text = (
        "🔐 <b>Подключение VLESS</b>\n\n"
        "📲 <b>Скачайте приложение:</b>\n"
        "• Android: <b>V2rayNG</b> (Google Play)\n"
        "• iOS: <b>Streisand</b> (App Store)\n"
        "• Windows: <b>V2rayN</b>\n"
        "• macOS: <b>V2rayU</b>\n\n"
        "📋 <b>Инструкция:</b>\n"
        "1. Откройте приложение\n"
        "2. Нажмите + (добавить сервер)\n"
        "3. Вставьте ваш VLESS ключ\n"
        "4. Нажмите подключиться\n\n"
        f"❓ Проблемы? Пишите: @{SUPPORT_USERNAME}"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=kb_back())
    await callback.answer()


@dp.callback_query(F.data == "back_main")
async def cb_back_main(callback: CallbackQuery):
    await cmd_start(callback.message)
    await callback.answer()


# ============================================================
# ADMIN CALLBACKS
# ============================================================

@dp.callback_query(F.data == "admin_redirect_on")
async def cb_admin_redirect_on(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await set_setting("redirect_mode", "1")
    await callback.answer("🔴 Редирект включён", show_alert=True)


@dp.callback_query(F.data == "admin_redirect_off")
async def cb_admin_redirect_off(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await set_setting("redirect_mode", "0")
    await callback.answer("🟢 Полный бот включён", show_alert=True)


@dp.callback_query(F.data == "admin_stats")
async def cb_admin_stats(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    count = await get_user_count()
    mode = await get_setting("redirect_mode")
    status = "🔴 Редирект" if mode == "1" else "🟢 Полный бот"

    text = (
        f"📊 <b>Статистика</b>\n\n"
        f"👥 Пользователей: <b>{count}</b>\n"
        f"💡 Режим: <b>{status}</b>"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=kb_admin())
    await callback.answer()


# ============================================================
# FALLBACK
# ============================================================

@dp.message()
async def any_message(message: types.Message):
    await message.answer(
        "👋 Используй меню или нажми /start",
        reply_markup=kb_start()
    )


# ============================================================
# MAIN
# ============================================================

async def main():
    await init_db()
    await set_commands()
    try:
        await dp.start_polling(bot)
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())