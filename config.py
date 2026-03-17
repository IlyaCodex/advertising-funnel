# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MAIN_BOT_LINK = os.getenv("MAIN_BOT_LINK", "https://t.me/GuardTunnel_bot")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "tut_support")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "0").split(",") if x.strip().isdigit()]
DATABASE_URL = os.getenv("DATABASE_URL")

TARIFFS = {
    "1month":  {"name": "1 месяц",    "price": "149 руб",  "emoji": "📅"},
    "3month":  {"name": "3 месяца",   "price": "399 руб",  "emoji": "📆"},
    "6month":  {"name": "6 месяцев",  "price": "699 руб",  "emoji": "🎯"},
    "12month": {"name": "12 месяцев", "price": "999 руб",  "emoji": "👑"},
}