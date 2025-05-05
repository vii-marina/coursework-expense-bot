import discord
from discord.ext import commands
from config import TOKEN
from utils.helpers import ensure_files

ensure_files()  # ✅ важливо

import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"✅ Бот увійшов як {bot.user}")
    await bot.tree.sync()


async def load_cogs():
    await bot.load_extension("cogs.ui.ui")
    await bot.load_extension("cogs.income.menu")


@bot.event
async def setup_hook():
    await load_cogs()


bot.run(TOKEN)
