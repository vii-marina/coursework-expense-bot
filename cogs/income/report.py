import discord
from discord import ButtonStyle, SelectOption, File
from discord.ui import View, Select, Button, Modal, TextInput
from datetime import datetime
from discord import Interaction
from utils.helpers import load_data, save_data 

INCOME_FILE = "data/income.json"

class IncomeCategorySelectForDetail(View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.add_item(IncomeCategoryDetailDropdown(user_id))

class IncomeCategoryDetailDropdown(Select):
    def __init__(self, user_id):
        self.user_id = user_id
        data = load_data(INCOME_FILE)
        incomes = data.get(self.user_id, [])
        categories = sorted(set(e.get("category", "Без категорії") for e in incomes))
        options = [SelectOption(label=cat) for cat in categories]
        super().__init__(placeholder="Оберіть категорію для деталей", options=options)

    async def callback(self, interaction: Interaction):
        selected = self.values[0]
        data = load_data(INCOME_FILE)
        incomes = data.get(self.user_id, [])
        filtered = [e for e in incomes if e.get("category") == selected]

        if not filtered:
            await interaction.response.send_message("Прибутків для цієї категорії немає.", ephemeral=True)
            return

        try:
            filtered.sort(key=lambda x: datetime.strptime(x["date"], "%d/%m/%Y"))
        except Exception:
            pass

        details = "\n".join(f"{e['amount']} грн — {e['date']}" for e in filtered)
        options = [
            SelectOption(
                label=f"{e['amount']} грн — {e['date']}",
                value=f"{e['amount']}#{e['date']}#{i}"
            ) for i, e in enumerate(filtered)
        ]
        await interaction.response.defer()
        await interaction.channel.send(
            f"📂 **{selected} — деталізація:**\n{details}\n\n🔧 Що відредагувати?",
            view=EditIncomeEntryView(self.user_id, options)
        )

class EditIncomeEntryView(View):
    def __init__(self, user_id, options):
        super().__init__(timeout=60)
        self.add_item(EditIncomeEntryDropdown(user_id, options))

class EditIncomeEntryDropdown(Select):
    def __init__(self, user_id, options):
        self.user_id = user_id
        super().__init__(placeholder="Оберіть запис", options=options)

    async def callback(self, interaction: Interaction):
        raw = self.values[0]
        amount, date, _ = raw.split("#")
        await interaction.response.defer()
        await interaction.channel.send(
            f"Що бажаєте зробити з прибутком {amount} грн — {date}?",
            view=IncomeEditDeleteView(self.user_id, float(amount), date)
        )

class IncomeEditDeleteView(View):
    def __init__(self, user_id, old_amount, old_date):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.old_amount = old_amount
        self.old_date = old_date

    @discord.ui.button(label="✏️ Редагувати", style=ButtonStyle.primary)
    async def edit(self, interaction: Interaction, button: Button):
        await interaction.response.send_modal(EditIncomeModal(self.user_id, self.old_amount, self.old_date))

    @discord.ui.button(label="🗑 Видалити", style=ButtonStyle.danger)
    async def delete(self, interaction: Interaction, button: Button):
        data = load_data(INCOME_FILE)
        incomes = data.get(self.user_id, [])
        updated = [e for e in incomes if not (float(e["amount"]) == self.old_amount and e["date"] == self.old_date)]
        data[self.user_id] = updated
        save_data(INCOME_FILE, data)
        await interaction.response.send_message("🗑 Прибуток видалено.", ephemeral=True)

class EditIncomeModal(Modal, title="Редагування"):
    def __init__(self, user_id, old_amount, old_date):
        super().__init__()
        self.user_id = user_id
        self.old_amount = old_amount
        self.old_date = old_date

        self.amount = TextInput(label="Нова сума", default=str(old_amount))
        self.date = TextInput(label="Нова дата (ДД/ММ/РРРР або 01042025)", default=old_date)
        self.add_item(self.amount)
        self.add_item(self.date)

    async def on_submit(self, interaction: Interaction):
        try:
            new_amount = float(self.amount.value)
        except ValueError:
            await interaction.response.send_message("❌ Невірна сума.", ephemeral=True)
            return

        raw_date = self.date.value.strip()
        if raw_date.isdigit() and len(raw_date) == 8:
            raw_date = f"{raw_date[:2]}/{raw_date[2:4]}/{raw_date[4:]}"

        try:
            date = datetime.strptime(raw_date, "%d/%m/%Y")
        except ValueError:
            await interaction.response.send_message("❌ Невірна дата.", ephemeral=True)
            return

        data = load_data(INCOME_FILE)
        entries = data.get(self.user_id, [])
        for e in entries:
            if float(e["amount"]) == self.old_amount and e["date"] == self.old_date:
                e["amount"] = new_amount
                e["date"] = date.strftime("%d/%m/%Y")
                break
        data[self.user_id] = entries
        save_data(INCOME_FILE, data)
        await interaction.response.send_message("✅ Прибуток оновлено.", ephemeral=True)
