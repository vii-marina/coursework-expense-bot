import discord
from discord.ext import commands, tasks
from utils.helpers import load_data, EXPENSES_FILE
from datetime import datetime, timedelta


class AutoReport(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.report_task.start()

    def cog_unload(self):
        self.report_task.cancel()

    @tasks.loop(hours=24)
    async def report_task(self):
        await self.bot.wait_until_ready()
        now = datetime.now()

        if now.hour != 9:
            return  # Надсилаємо звіти лише о 9 ранку

        expenses_data = load_data(EXPENSES_FILE)

        for user_id, expenses in expenses_data.items():
            if not expenses:
                continue

            # Рахуємо тільки за останні 24 години
            # Поки що без дати — надсилаємо повний список
            summary = {}
            for entry in expenses:
                category = entry.get("category", "Інше")
                amount = float(entry.get("amount", 0))
                summary[category] = summary.get(category, 0) + amount

            text = "\n".join([f"• {cat}: {amt:.2f} грн" for cat, amt in summary.items()])
            total = sum(summary.values())
            text += f"\n\nЗагалом: {total:.2f} грн"

            user = self.bot.get_user(int(user_id))
            if user:
                try:
                    await user.send(f"📊 **Ваш звіт за сьогодні:**\n{text}")
                except discord.Forbidden:
                    print(f"❌ Не вдалося надіслати звіт користувачу {user_id} — DM закриті")

    @report_task.before_loop
    async def before_report(self):
        await self.bot.wait_until_ready()

    @commands.command(name="тест_звіт")
    async def test_report(self, ctx):
        """Примусовий запуск звіту (для тестування)"""
        expenses_data = load_data(EXPENSES_FILE)
        user_id = str(ctx.author.id)
        user_expenses = expenses_data.get(user_id, [])

        if not user_expenses:
            await ctx.author.send("📭 У вас ще немає витрат.")
            return

        summary = {}
        for entry in user_expenses:
            category = entry.get("category", "Інше")
            amount = float(entry.get("amount", 0))
            summary[category] = summary.get(category, 0) + amount

        text = "\n".join([f"• {cat}: {amt:.2f} грн" for cat, amt in summary.items()])
        total = sum(summary.values())
        text += f"\n\nЗагалом: {total:.2f} грн"

        await ctx.author.send(f"📊 **Ваш тестовий звіт:**\n{text}")


async def setup(bot):
    await bot.add_cog(AutoReport(bot))

