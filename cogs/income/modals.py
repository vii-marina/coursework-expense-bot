import discord
from discord.ui import Modal, TextInput
from utils.helpers import load_data, save_data
from datetime import datetime
from discord import Interaction
from discord.ui import View, Select


INCOME_FILE = "data/income.json"
AUTO_INCOME_FILE = "data/auto_income.json"

class AutoIncomeModal(Modal, title="Автоматичний прибуток"):
    def __init__(self, user_id, interval):
        super().__init__()
        self.user_id = str(user_id)
        self.interval = interval

        self.category = TextInput(label="Категорія", placeholder="Наприклад: Стипендія")
        self.amount = TextInput(label="Сума", placeholder="Наприклад: 500.00")
        self.add_item(self.category)
        self.add_item(self.amount)

    async def on_submit(self, interaction: Interaction):
        try:
            amount_value = float(self.amount.value)
        except ValueError:
            await interaction.response.send_message("❌ Невірний формат суми.", ephemeral=True)
            return

        data = load_data(AUTO_INCOME_FILE)
        auto_incomes = data.get(self.user_id, [])
        auto_incomes.append({
            "category": self.category.value.strip(),
            "amount": amount_value,
            "interval": self.interval
        })
        data[self.user_id] = auto_incomes
        save_data(AUTO_INCOME_FILE, data)

        await interaction.response.send_message(
            f"✅ Додано автоматичний прибуток: **{self.category.value.strip()}**, {amount_value:.2f} грн ({self.interval})",
            ephemeral=True
        )
        
class AutoDeleteModal(Modal, title="Видалити автоприбуток"):
    category = TextInput(label="Категорія для видалення")

    async def on_submit(self, interaction: Interaction):
        from utils.helpers import load_data, save_data, AUTO_INCOME_FILE
        user_id = str(interaction.user.id)
        data = load_data(AUTO_INCOME_FILE)
        entries = data.get(user_id, [])
        new_entries = [e for e in entries if e["category"] != self.category.value]
        data[user_id] = new_entries
        save_data(AUTO_INCOME_FILE, data)
        await interaction.response.send_message("🗑️ Прибуток видалено (якщо існував).", ephemeral=True)


class AddIncomeModal(Modal, title="Додавання прибутку"):
    def __init__(self, user_id, category):
        super().__init__()
        self.user_id = str(user_id)
        self.category = category
        self.amount = TextInput(label="Сума", placeholder="Введіть в грн", required=True)
        self.date = TextInput(label="Дата (ДД/ММ/РРРР або 01042025)", placeholder="ДД/ММ/РРРР", required=False)
        self.add_item(self.amount)
        self.add_item(self.date)

    async def on_submit(self, interaction: Interaction):
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

        data = load_data(INCOME_FILE)
        user_incomes = data.get(self.user_id, [])
        user_incomes.append({
            "category": self.category,
            "amount": amount_value,
            "date": date.strftime("%d/%m/%Y")
        })
        data[self.user_id] = user_incomes
        save_data(INCOME_FILE, data)

        await interaction.response.send_message(
            f"✅ Збережено {amount_value:.2f} грн в категорії **{self.category}** на {date.strftime('%d/%m/%Y')}",
            ephemeral=True
        )
class AutoIncomeIntervalView(View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id

        options = [
            discord.SelectOption(label="Щодня", value="daily"),
            discord.SelectOption(label="Щотижня", value="weekly"),
            discord.SelectOption(label="Щомісяця", value="monthly")
        ]
        self.add_item(AutoIntervalDropdown(user_id, options))

class AutoIntervalDropdown(Select):
    def __init__(self, user_id, options):
        self.user_id = str(user_id)
        super().__init__(placeholder="Оберіть інтервал", options=options)

    async def callback(self, interaction: discord.Interaction):
        interval = self.values[0]
        await interaction.response.send_modal(AutoIncomeModal(self.user_id, interval))
