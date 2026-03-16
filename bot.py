# -*- coding: utf-8 -*-
import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from aiogram.utils.keyboard import InlineKeyboardBuilder

load_dotenv()
BOT_TOKEN     = os.getenv("BOT_TOKEN")
MAIN_BOT_LINK = os.getenv("MAIN_BOT_LINK", "https://t.me/GuardTunnel_bot")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN ne zadan! Sozdaj .env fajl")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher()


def kb_main() -> InlineKeyboardMarkup:
    btn = InlineKeyboardButton(
        text="🚀 Активировать бесплатный период",
        url=MAIN_BOT_LINK
    )
    btn.model_extra["style"] = "success"
    builder = InlineKeyboardBuilder()
    builder.row(btn)
    return builder.as_markup()


def kb_features() -> InlineKeyboardMarkup:
    btn = InlineKeyboardButton(
        text="🚀 Попробовать бесплатно",
        url=MAIN_BOT_LINK
    )
    btn.model_extra["style"] = "success"
    builder = InlineKeyboardBuilder()
    builder.row(btn)
    return builder.as_markup()


async def set_commands():
    await bot.set_my_commands([
        BotCommand(command="start",    description="🏠 На главную"),
        BotCommand(command="features", description="⭐ Преимущества"),
    ])


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    text = (
        "🛡 <b>Guard Tunnel VPN</b>\n\n"
        "Надёжная защита данных и стабильное соединение в любой точке мира.\n\n"
        "✅ До 10 Gbit/с\n"
        "✅ Шифрование трафика\n"
        "✅ Серверы в 10+ странах\n"
        "✅ Работает на всех устройствах\n"
        "✅ Поддержка 24/7\n\n"
        "🎁 <b>Пробный период — бесплатно.</b>\n"
        "Без привязки карты. Активация за 2 минуты.\n\n"
        "👇 Нажми кнопку и получи доступ прямо сейчас"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=kb_main())


@dp.message(Command("features"))
async def cmd_features(message: types.Message):
    text = (
        "⭐ <b>Почему Guard Tunnel VPN?</b>\n\n"
        "⚡ <b>Скорость до 10 Gbit/с</b>\n"
        "Никаких буферизаций и задержек — стриминг, игры, звонки без лагов.\n\n"
        "🔒 <b>Шифрование трафика</b>\n"
        "Твои данные защищены по протоколу VLESS.\n\n"
        "🌍 <b>Серверы в 10+ странах</b>\n"
        "Выбирай локацию — Европа, Азия, Америка.\n\n"
        "📱 <b>Все устройства</b>\n"
        "iOS, Android, Windows, macOS, Linux — одна подписка на все.\n\n"
        "🎁 <b>Пробный период бесплатно</b>\n"
        "Без привязки карты. Попробуй прямо сейчас.\n\n"
        "🛟 <b>Поддержка 24/7</b>\n"
        "Всегда на связи — ответим в течение нескольких минут."
    )
    await message.answer(text, parse_mode="HTML", reply_markup=kb_features())


@dp.message()
async def any_message(message: types.Message):
    await message.answer(
        "👋 Используй меню или нажми /start",
        reply_markup=kb_main()
    )


async def main():
    await set_commands()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
