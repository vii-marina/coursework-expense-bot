import discord
from discord.ext import commands
from discord.ui import Modal, TextInput, Select, View, Button
from utils.helpers import load_data, save_data, EXPENSES_FILE
from datetime import datetime
from io import BytesIO
import matplotlib.pyplot as plt
from discord import File
from cogs.charts import draw_donut_chart

# --- Додавання витрати ---
class ExpenseModal(Modal, title="Введення витрати"):
    def __init__(self, user_id, category):
        super().__init__()
        self.user_id = str(user_id)
        self.category = category
        self.amount = TextInput(label="Сума", placeholder="Введіть витрати в грн", required=True)
        self.date = TextInput(label="Дата (ДД/ММ/РРРР або 01042025)", placeholder="ДД/ММ/РРРР", required=False)
        self.add_item(self.amount)
        self.add_item(self.date)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount_value = float(self.amount.value)
        except ValueError:
            await interaction.response.send_message("❌ Невірний формат суми.", ephemeral=True)
            return

        raw_date = self.date.value.strip()
        if not raw_date:
            date = datetime.now()
        else:
            if raw_date.isdigit() and len(raw_date) == 8:
                raw_date = f"{raw_date[:2]}/{raw_date[2:4]}/{raw_date[4:]}"
            try:
                date = datetime.strptime(raw_date, "%d/%m/%Y")
            except ValueError:
                await interaction.response.send_message("❌ Невірна дата.", ephemeral=True)
                return

        data = load_data(EXPENSES_FILE)
        user_expenses = data.get(self.user_id, [])
        user_expenses.append({"category": self.category, "amount": amount_value, "date": date.strftime("%d/%m/%Y")})
        data[self.user_id] = user_expenses
        save_data(EXPENSES_FILE, data)

        settings = load_data("data/settings.json")
        user_settings = settings.get(self.user_id, {})
        daily_limit = user_settings.get("daily_limit", None)

        await interaction.response.send_message(
            f"✅ Збережено {amount_value:.2f} грн в категорії **{self.category}** на {date.strftime('%d/%m/%Y')}.",
            ephemeral=True
        )

        if daily_limit is not None:
            today = datetime.now().strftime("%d/%m/%Y")
            today_total = sum(
                float(e["amount"]) for e in user_expenses if e["date"] == today
            )
            if today_total > daily_limit:
                await interaction.followup.send("⚠️ **УВАГА!! Ви використали встановлений ліміт, бережіть свої кошти 😉**")

class SetLimitModal(Modal, title="Встановити ліміт витрат"):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = str(user_id)
        self.limit = TextInput(label="Ліміт (грн)", placeholder="Наприклад: 500", required=True)
        self.add_item(self.limit)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            limit = float(self.limit.value)
        except ValueError:
            await interaction.response.send_message("❌ Введено неправильне число.", ephemeral=True)
            return

        settings = load_data("data/settings.json")
        user_settings = settings.get(self.user_id, {})
        user_settings["daily_limit"] = limit
        settings[self.user_id] = user_settings
        save_data("data/settings.json", settings)

        await interaction.response.send_message(f"✅ Ліміт витрат встановлено: {limit:.2f} грн/день.", ephemeral=True)


class CategorySelectView(View):
    def __init__(self, user_id, categories):
        super().__init__(timeout=60)
        self.add_item(CategorySelect(user_id, categories))

class CategorySelect(Select):
    def __init__(self, user_id, categories):
        self.user_id = str(user_id)
        options = [discord.SelectOption(label=cat) for cat in categories]
        super().__init__(placeholder="Оберіть категорію", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ExpenseModal(self.user_id, self.values[0]))

async def show_expense_report(interaction: discord.Interaction, user_id: str):
    data = load_data(EXPENSES_FILE)
    expenses = data.get(str(user_id), [])
    if not expenses:
        await interaction.response.send_message("📭 Немає витрат для звіту.", ephemeral=True)
        return

    summary = {}
    for e in expenses:
        cat = e["category"]
        summary[cat] = summary.get(cat, 0) + float(e["amount"])

    lines = [f"**{cat}**: {amount:.2f} грн" for cat, amount in summary.items()]
    await interaction.response.send_message("📊 **Звіт про витрати:**\n" + "\n".join(lines), ephemeral=True)

async def show_expense_chart(interaction: discord.Interaction, user_id: str):
    data = load_data(EXPENSES_FILE)
    expenses = data.get(str(user_id), [])
    if not expenses:
        await interaction.response.send_message("📭 Немає даних для діаграми.", ephemeral=True)
        return

    summary = {}
    for e in expenses:
        cat = e["category"]
        summary[cat] = summary.get(cat, 0) + float(e["amount"])

    await draw_donut_chart(interaction, summary, "Розподіл витрат")
