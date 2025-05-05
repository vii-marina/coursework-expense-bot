import discord
from discord.ui import View, Button
from utils.helpers import load_data, EXPENSES_FILE
from .expenses import CategorySelectView, show_expense_report, show_expense_chart, SetLimitModal


class MenuView(View):
    def __init__(self, user_id, categories):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.categories = categories

    @discord.ui.button(label="➕ Нова витрата", style=discord.ButtonStyle.success)
    async def add_expense(self, interaction: discord.Interaction, button: Button):
        if not self.categories:
            await interaction.response.send_message("⚠️ У вас ще немає категорій.", ephemeral=True)
            return

        await interaction.response.send_message(
            "Оберіть категорію:",
            ephemeral=True,
            view=CategorySelectView(self.user_id, self.categories)
        )

    @discord.ui.button(label="🔒 Ліміт витрат", style=discord.ButtonStyle.secondary)
    async def set_limit(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(SetLimitModal(self.user_id))


    @discord.ui.button(label="📊 Звіт", style=discord.ButtonStyle.secondary)
    async def show_report(self, interaction: discord.Interaction, button: Button):
        await show_expense_report(interaction, self.user_id)

    @discord.ui.button(label="📈 Діаграма витрат", style=discord.ButtonStyle.secondary)
    async def show_chart(self, interaction: discord.Interaction, button: Button):
        await show_expense_chart(interaction, self.user_id)

    @discord.ui.button(label="⚙️ Категорії", style=discord.ButtonStyle.secondary)
    async def manage_categories(self, interaction: discord.Interaction, button: Button):
        from cogs.ui.base_category import BaseCategoryManagerView
        CategoryManagerView = lambda user_id: BaseCategoryManagerView(user_id, is_income=False)

        await interaction.response.send_message(
            "🔧 Редагування категорій:",
            ephemeral=True,
            view=CategoryManagerView(self.user_id)
        )
