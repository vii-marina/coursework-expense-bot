from .menu import IncomeUI

async def setup(bot):
    await bot.add_cog(IncomeUI(bot))
