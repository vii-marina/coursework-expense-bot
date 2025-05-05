import discord
from discord.ui import View, Button
from utils.helpers import load_data
from .modals import AddIncomeModal, AutoIncomeIntervalView
from .report import IncomeCategorySelectForDetail
from cogs.charts import draw_donut_chart
from cogs.ui.base_category import BaseCategoryManagerView

from discord.ext import commands

INCOME_FILE = "data/income.json"
AUTO_INCOME_FILE = "data/auto_income.json"

IncomeCategoryManagerView = lambda user_id: BaseCategoryManagerView(user_id, is_income=True)
class IncomeUI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


class IncomeMenuView(View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = str(user_id)

    @discord.ui.button(label="➕ Новий прибуток", style=discord.ButtonStyle.success)
    async def add_income(self, interaction: discord.Interaction, button: Button):
        data = load_data("data/income_categories.json")
        categories = data.get(str(self.user_id), [])
        if not categories:
            await interaction.response.send_message("⚠️ У вас ще немає категорій для прибутку. Додайте їх у меню 'Категорії'.", ephemeral=True)
            return

        await interaction.response.send_message("Оберіть категорію:", ephemeral=True, view=IncomeCategorySelectView(self.user_id, categories))
        msg = await interaction.original_response()
        key = (interaction.channel.id, interaction.user.id)
        cog = interaction.client.get_cog("UI")
        cog.active_messages.setdefault(key, []).append(msg.id)

    @discord.ui.button(label="📲 Автоматичні", style=discord.ButtonStyle.secondary)
    async def auto_income(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Оберіть інтервал:", ephemeral=True, view=AutoIncomeIntervalView(self.user_id))
        msg = await interaction.original_response()
        key = (interaction.channel.id, interaction.user.id)
        cog = interaction.client.get_cog("UI")
        cog.active_messages.setdefault(key, []).append(msg.id)

    @discord.ui.button(label="🛠 Керування автоматичними", style=discord.ButtonStyle.secondary)
    async def manage_auto_income(self, interaction: discord.Interaction, button: Button):
        from .auto import AutoIncomeMenuView
        view = AutoIncomeMenuView(self.user_id)
        await view.send_with_summary(interaction)
        msg = await interaction.original_response()
        key = (interaction.channel.id, interaction.user.id)
        cog = interaction.client.get_cog("UI")
        cog.active_messages.setdefault(key, []).append(msg.id)


        
       
    @discord.ui.button(label="📊 Звіт", style=discord.ButtonStyle.secondary)
    async def show_report(self, interaction: discord.Interaction, button: Button):
        data = load_data(INCOME_FILE)
        incomes = data.get(self.user_id, [])
        if not incomes:
            await interaction.response.send_message("📭 У вас ще немає прибутків.", ephemeral=True)
            return

        auto_data = load_data(AUTO_INCOME_FILE)
        auto_map = {}
        for e in auto_data.get(self.user_id, []):
            raw = e["category"]
            interval = e["interval"]
            label = f"{raw} [автоматично - " + {
                "daily": "щодня",
                "weekly": "щотижня",
                "monthly": "щомісяця"
            }.get(interval, interval) + "]"
            auto_map[raw] = label

        summary = {}
        for e in incomes:
            raw_cat = e.get("category", "Без категорії")
            cat = auto_map.get(raw_cat, raw_cat)
            amount = float(e.get("amount", 0))
            summary[cat] = summary.get(cat, 0) + amount

        total = sum(summary.values())
        text = "\n".join([f"• **{cat}**: {amt:.2f} грн" for cat, amt in summary.items()])
        text += f"\n\n**Загалом:** {total:.2f} грн"

        # Правильне завершення interaction
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(text, view=IncomeCategorySelectForDetail(self.user_id))


    @discord.ui.button(label="📈 Діаграма", style=discord.ButtonStyle.secondary)
    async def show_chart(self, interaction: discord.Interaction, button: Button):
        data = load_data(INCOME_FILE)
        incomes = data.get(self.user_id, [])
        if not incomes:
            await interaction.response.send_message("📭 Немає даних для діаграми.", ephemeral=True)
            return

        summary = {}
        for e in incomes:
            cat = e.get("category", "Без категорії")
            summary[cat] = summary.get(cat, 0) + float(e.get("amount", 0))

        await draw_donut_chart(interaction, summary, "Розподіл прибутків")

    @discord.ui.button(label="⚙️ Категорії", style=discord.ButtonStyle.secondary)
    async def manage_categories(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("🔧 Редагування категорій:", ephemeral=True, view=IncomeCategoryManagerView(self.user_id))
        msg = await interaction.original_response()
        key = (interaction.channel.id, interaction.user.id)
        cog = interaction.client.get_cog("UI")
        cog.active_messages.setdefault(key, []).append(msg.id)

class IncomeCategorySelectView(View):
    def __init__(self, user_id, categories):
        super().__init__(timeout=60)
        self.add_item(IncomeCategorySelect(user_id, categories))

class IncomeCategorySelect(discord.ui.Select):
    def __init__(self, user_id, categories):
        self.user_id = str(user_id)
        options = [discord.SelectOption(label=cat) for cat in categories]
        super().__init__(placeholder="Оберіть категорію", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(AddIncomeModal(self.user_id, self.values[0]))


async def setup(bot):
    await bot.add_cog(IncomeUI(bot))
