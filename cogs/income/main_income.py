# cogs/income/main.py
from discord.ext import commands
from .menu import IncomeMenuView

class IncomeUI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        pass

async def setup(bot):
    await bot.add_cog(IncomeUI(bot))
