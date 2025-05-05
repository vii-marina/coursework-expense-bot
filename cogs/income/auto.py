import discord
from discord.ext import commands, tasks
from discord.ui import View, Button
from discord import Interaction
from datetime import datetime, timedelta
from utils.helpers import load_data, save_data
from .modals import AutoIncomeModal, AutoDeleteModal
from .menu import IncomeMenuView
from utils.helpers import AUTO_INCOME_FILE 

INCOME_FILE = "data/income.json"
EXPENSES_FILE = "data/expenses.json"
AUTO_INCOME_FILE = "data/auto_income.json"


class AutoIncomeMenuView(View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = str(user_id)

    async def send_with_summary(self, interaction):
        auto_data = load_data(AUTO_INCOME_FILE).get(self.user_id, [])
        if not auto_data:
            content = "📥 Меню автоматичних прибутків:\n*Немає активних автоприбутків.*"
        else:
            interval_map = {'daily': 'щодня', 'weekly': 'щотижня', 'monthly': 'щомісяця'}
            summary = "\n".join([
                f"• **{e['category']}** — {e['amount']} грн ({interval_map.get(e['interval'], e['interval'])})"
                for e in auto_data
            ])
            content = f"📥 Меню автоматичних прибутків:\n{summary}"
        await interaction.response.edit_message(content=content, view=self)

    @discord.ui.button(label="❌ Видалити автоприбуток", style=discord.ButtonStyle.danger)
    async def delete_auto_income(self, interaction: Interaction, button: Button):
        await interaction.response.send_modal(AutoDeleteModal())

    @discord.ui.button(label="🔙 Назад", style=discord.ButtonStyle.secondary)
    async def go_back(self, interaction: Interaction, button: Button):

        await interaction.response.edit_message(content="📥 Меню керування прибутками:", view=IncomeMenuView(interaction.user.id))

class AutoEntries(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_checker.start()

    def cog_unload(self):
        self.auto_checker.cancel()

    @tasks.loop(minutes=1)
    async def auto_checker(self):
        now = datetime.now()
        await self.check_auto(
            bot=self.bot,
            source_file=AUTO_INCOME_FILE,
            target_file=INCOME_FILE,
            entry_type="прибуток",
            now=now,
            time_now=now.strftime("%H:%M"),
            weekday=now.strftime("%A"),
            day=now.day
        )

    async def check_auto(self, bot, source_file, target_file, entry_type, now, time_now, weekday, day):
        data = load_data(source_file)
        target = load_data(target_file)

        for user_id, entries in data.items():
            for e in entries:
                matched = False
                if e["interval"] == "daily" and e.get("time") == time_now:
                    matched = True
                elif e["interval"] == "weekly" and e.get("day_of_week") == weekday and e.get("time") == time_now:
                    matched = True
                elif e["interval"] == "monthly":
                    target_day = e.get("day_of_month")
                    if target_day is None:
                        continue

                    last_day = (now.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
                    actual_day = last_day.day

                    if target_day >= now.day and now.day == actual_day:
                        matched = True
                    elif target_day == now.day:
                        matched = True

                if matched:
                    target.setdefault(user_id, []).append({
                        "category": e["category"],
                        "amount": e["amount"],
                        "date": now.strftime("%d/%m/%Y")
                    })
                    print(f"[✓] Авто-{entry_type} записано для {user_id} → {e['amount']} грн [{e['category']}]")
                    try:
                        user = await bot.fetch_user(int(user_id))
                        await user.send(f"📥 Додано автоматичний **{entry_type}**: {e['category']} — {e['amount']} грн")
                    except:
                        pass

        save_data(target_file, target)



async def setup(bot):
    await bot.add_cog(AutoEntries(bot))
