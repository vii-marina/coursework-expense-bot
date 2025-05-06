
import discord
from discord.ui import View, Select
from datetime import datetime
from utils.helpers import load_data, EXPENSES_FILE, INCOME_FILE, AUTO_INCOME_FILE

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
        user_id = str(interaction.user.id)
        incomes = load_data(INCOME_FILE).get(user_id, [])
        auto_incomes = load_data(AUTO_INCOME_FILE).get(user_id, [])
        incomes += auto_incomes
        expenses = load_data(EXPENSES_FILE).get(user_id, [])

        now = datetime.now()
        filtered_incomes = []
        filtered_expenses = []

        for item in incomes:
            try:
                item_date = datetime.strptime(item.get("date", ""), "%d/%m/%Y")
            except Exception:
                continue

            if period_label == "Сьогодні" and item_date.date() == now.date():
                filtered_incomes.append(item)
            elif period_label == "Цей тиждень" and item_date.isocalendar()[1] == now.isocalendar()[1]:
                filtered_incomes.append(item)
            elif period_label == "Цей місяць" and item_date.month == now.month and item_date.year == now.year:
                filtered_incomes.append(item)

        for item in expenses:
            try:
                item_date = datetime.strptime(item.get("date", ""), "%d/%m/%Y")
            except Exception:
                continue

            if period_label == "Сьогодні" and item_date.date() == now.date():
                filtered_expenses.append(item)
            elif period_label == "Цей тиждень" and item_date.isocalendar()[1] == now.isocalendar()[1]:
                filtered_expenses.append(item)
            elif period_label == "Цей місяць" and item_date.month == now.month and item_date.year == now.year:
                filtered_expenses.append(item)

        total_income = sum(float(i.get("amount", 0)) for i in filtered_incomes)
        total_expense = sum(float(e.get("amount", 0)) for e in filtered_expenses)
        balance = total_income - total_expense

        report = (
            f"📋 **Загальний звіт за період: {period_label}**\n\n"
            f"💰 Прибутків: {total_income:.2f} грн\n"
            f"💸 Витрат: {total_expense:.2f} грн\n"
            f"📊 Баланс: {balance:.2f} грн"
        )

        await interaction.response.send_message(content=report, ephemeral=True)
