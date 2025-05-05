import discord
from discord.ui import View, Select, Button
from datetime import datetime, timedelta
from utils.helpers import load_data, EXPENSES_FILE, INCOME_FILE

# --- Вибір періоду ---
class OverallReportSelect(Select):
    def __init__(self, user_id: str, on_select_callback):
        self.user_id = str(user_id)
        self.on_select_callback = on_select_callback

        options = [
            discord.SelectOption(label="Сьогодні", value="day"),
            discord.SelectOption(label="Цей тиждень", value="week"),
            discord.SelectOption(label="Цей місяць", value="month")
        ]
        super().__init__(placeholder="Оберіть період", options=options)

    async def callback(self, interaction: discord.Interaction):
        label_map = {
            "day": "Сьогодні",
            "week": "Цей тиждень",
            "month": "Цей місяць"
        }
        selected = self.values[0]
        label = label_map.get(selected, "Невідомо")
        await self.on_select_callback(interaction, label)

# --- Основне вікно вибору ---
class OverallReportView(View):
    def __init__(self, user_id: str):
        super().__init__(timeout=60)
        self.user_id = str(user_id)
        self.select = OverallReportSelect(self.user_id, self.on_period_selected)
        self.add_item(self.select)

    async def on_period_selected(self, interaction: discord.Interaction, period_label: str):
        await interaction.response.send_message(
            f"📋 Обраний період: **{period_label}**. Оберіть дію:",
            ephemeral=True
        )
