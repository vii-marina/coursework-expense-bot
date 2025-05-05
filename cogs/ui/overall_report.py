import discord
from discord.ui import View, Select
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
        now = datetime.now()
        if period_label == "Сьогодні":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period_label == "Цей тиждень":
            start_date = now - timedelta(days=now.weekday())
        elif period_label == "Цей місяць":
            start_date = now.replace(day=1)
        else:
            await interaction.response.send_message("❌ Невідомий період.", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        incomes = load_data(INCOME_FILE).get(user_id, [])
        expenses = load_data(EXPENSES_FILE).get(user_id, [])

        def in_period(entry):
            try:
                date = datetime.strptime(entry.get("date", ""), "%d/%m/%Y")
                return date >= start_date
            except:
                return False

        income_sum = sum(e["amount"] for e in incomes if in_period(e))
        expense_sum = sum(e["amount"] for e in expenses if in_period(e))
        balance = income_sum - expense_sum

        report = (
            f"📋 **Загальний звіт за період: {period_label}**\n\n"
            f"➕ Прибутки: {income_sum:.2f} грн\n"
            f"➖ Витрати: {expense_sum:.2f} грн\n"
            f"💰 Залишок: {balance:.2f} грн"
        )

        await interaction.response.send_message(report, ephemeral=True)
