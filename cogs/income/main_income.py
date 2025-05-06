from discord.ext import commands

class IncomeUI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self):
        pass

async def setup(bot):
    await bot.add_cog(IncomeUI(bot))
