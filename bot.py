import discord
from discord.ext import commands
from config import TOKEN
from utils.helpers import ensure_files

ensure_files()  # ✅ важливо

# 🔥 Очистка старих даних (тимчасово)
# from utils.helpers import save_data, EXPENSES_FILE, CATEGORIES_FILE, SETTINGS_FILE

# save_data(EXPENSES_FILE, {})
# save_data(CATEGORIES_FILE, {})
# save_data(SETTINGS_FILE, {})
# print("🧹 Очищено всі збережені дані.")


import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"✅ Бот увійшов як {bot.user}")
    await bot.tree.sync()


async def load_cogs():
    for file in os.listdir("./cogs"):
        if file.endswith(".py") and file != "__init__.py":
            await bot.load_extension(f"cogs.{file[:-3]}")


@bot.event
async def setup_hook():
    await load_cogs()


bot.run(TOKEN)
