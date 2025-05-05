import discord
from discord.ui import View, Button
from utils.helpers import load_data
from .expense_menu import MenuView
from ..income.menu import IncomeMenuView
from .overall_report import OverallReportView


class StartView(View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = str(user_id)

    @discord.ui.button(label="💰 Прибутки", style=discord.ButtonStyle.success)
    async def income_menu(self, interaction: discord.Interaction, button: Button):
        key = (interaction.channel.id, interaction.user.id)
        cog = interaction.client.get_cog("UI")

        if interaction.response.is_done():
            await interaction.followup.send(
                "📈 Меню керування прибутками:",
                ephemeral=True,
                view=IncomeMenuView(self.user_id)
            )
        else:
            await interaction.response.send_message(
                "📈 Меню керування прибутками:",
                ephemeral=True,
                view=IncomeMenuView(self.user_id)
            )

        msg = await interaction.original_response()
        cog.active_messages.setdefault(key, []).append(msg.id)

    @discord.ui.button(label="💸 Витрати", style=discord.ButtonStyle.primary)
    async def expense_menu(self, interaction: discord.Interaction, button: Button):
        key = (interaction.channel.id, interaction.user.id)
        cog = interaction.client.get_cog("UI")

        data = load_data("data/categories.json")
        categories = data.get(self.user_id, [])
        await interaction.response.send_message(
            "💸 Меню керування витратами:",
            ephemeral=True,
            view=MenuView(self.user_id, categories)
        )

        msg = await interaction.original_response()
        cog.active_messages.setdefault(key, []).append(msg.id)

    @discord.ui.button(label="📋 Загальний звіт", style=discord.ButtonStyle.secondary)
    async def overall_report(self, interaction: discord.Interaction, button: Button):
        key = (interaction.channel.id, interaction.user.id)
        cog = interaction.client.get_cog("UI")

        await interaction.response.send_message(
            "Оберіть період для загального звіту:",
            ephemeral=True,
            view=OverallReportView(self.user_id)
        )
        msg = await interaction.original_response()
        cog.active_messages.setdefault(key, []).append(msg.id)

    @discord.ui.button(label="📄 PDF звіт", style=discord.ButtonStyle.secondary)
    async def static_pdf_report(self, interaction: discord.Interaction, button: Button):
        from utils.pdf_report import send_overall_pdf_report
        await send_overall_pdf_report(interaction)



    @discord.ui.button(label="❓", style=discord.ButtonStyle.secondary)
    async def help_info(self, interaction: discord.Interaction, button: Button):
        key = (interaction.channel.id, interaction.user.id)
        cog = interaction.client.get_cog("UI")

        await interaction.response.send_message(
            content=(
                "📖 Опис можливостей бота:\n"
                "📈 Прибутки — додавання та перегляд доходів.\n"
                "💸 Витрати — додавання та перегляд витрат.\n"
                "📋 Загальний звіт — перегляд балансу.\n"
                "ℹ️ Усі дії через кнопки та вікна!"
            ),
            ephemeral=True
        )
        msg = await interaction.original_response()
        cog.active_messages.setdefault(key, []).append(msg.id)
