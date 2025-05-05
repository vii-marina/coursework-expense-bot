import discord
from discord.ui import View, Select, Button, Modal, TextInput
from datetime import datetime
from utils.helpers import load_data, save_data, EXPENSES_FILE


class CategoryDropdownView(View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.add_item(CategoryDetailDropdown(user_id))
        self.add_item(EditExpensePrompt(user_id))


class CategoryDetailDropdown(Select):
    def __init__(self, user_id):
        self.user_id = user_id
        data = load_data(EXPENSES_FILE)
        expenses = data.get(self.user_id, [])
        categories = sorted(set(e.get("category", "Без категорії") for e in expenses))
        options = [discord.SelectOption(label=cat) for cat in categories]
        super().__init__(placeholder="Оберіть категорію для деталей", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        data = load_data(EXPENSES_FILE)
        expenses = data.get(self.user_id, [])
        filtered = [e for e in expenses if e.get("category") == selected]

        if not filtered:
            await interaction.response.send_message("Витрат для цієї категорії немає.", ephemeral=True)
            return

        try:
            filtered.sort(key=lambda x: datetime.strptime(x["date"], "%d/%m/%Y"))
        except Exception:
            pass

        details = "\n".join(f"{e['amount']} грн — {e['date']}" for e in filtered)
        await interaction.response.send_message(f"📂 **{selected} — деталізація:**\n{details}", ephemeral=True)


class EditExpensePrompt(Button):
    def __init__(self, user_id):
        super().__init__(label="🔧 Що відредагувати?", style=discord.ButtonStyle.secondary)
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        data = load_data(EXPENSES_FILE)
        expenses = data.get(self.user_id, [])
        if not expenses:
            await interaction.response.send_message("📭 У вас ще немає витрат.", ephemeral=True)
            return

        options = [
            discord.SelectOption(label=f"{e['amount']} грн — {e['date']}", value=f"{e['amount']}#{e['date']}")
            for e in expenses
        ]
        await interaction.response.send_message(
            "Оберіть запис для редагування:",
            ephemeral=True,
            view=EditExpenseSelectView(self.user_id, options)
        )


class EditExpenseSelectView(View):
    def __init__(self, user_id, options):
        super().__init__(timeout=60)
        self.add_item(EditExpenseSelect(user_id, options))


class EditExpenseSelect(Select):
    def __init__(self, user_id, options):
        self.user_id = user_id
        super().__init__(placeholder="Оберіть витрату", options=options)

    async def callback(self, interaction: discord.Interaction):
        raw = self.values[0]
        amount, date = raw.split("#")
        await interaction.response.send_message(
            f"Що бажаєте зробити з витратою {amount} грн — {date}?",
            ephemeral=True,
            view=ExpenseEditDeleteView(self.user_id, float(amount), date)
        )


class ExpenseEditDeleteView(View):
    def __init__(self, user_id, old_amount, old_date):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.old_amount = old_amount
        self.old_date = old_date

    @discord.ui.button(label="✏️ Редагувати", style=discord.ButtonStyle.primary)
    async def edit(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(EditExpenseModal(self.user_id, self.old_amount, self.old_date))

    @discord.ui.button(label="🗑 Видалити", style=discord.ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, button: Button):
        data = load_data(EXPENSES_FILE)
        expenses = data.get(self.user_id, [])
        updated = [e for e in expenses if not (float(e["amount"]) == self.old_amount and e["date"] == self.old_date)]
        data[self.user_id] = updated
        save_data(EXPENSES_FILE, data)
        await interaction.response.send_message("🗑 Витрату видалено.", ephemeral=True)


class EditExpenseModal(Modal, title="Редагування витрати"):
    def __init__(self, user_id, old_amount, old_date):
        super().__init__()
        self.user_id = user_id
        self.old_amount = old_amount
        self.old_date = old_date

        self.amount = TextInput(label="Нова сума", default=str(old_amount))
        self.date = TextInput(label="Нова дата (ДД/ММ/РРРР або 01042025)", default=old_date)
        self.add_item(self.amount)
        self.add_item(self.date)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount_value = float(self.amount.value)
        except ValueError:
            await interaction.response.send_message("❌ Невірний формат суми.", ephemeral=True)
            return

        date_str = self.date.value.replace("/", "")
        if len(date_str) != 8 or not date_str.isdigit():
            await interaction.response.send_message("❌ Невірний формат дати.", ephemeral=True)
            return

        formatted_date = f"{date_str[:2]}/{date_str[2:4]}/{date_str[4:]}"
        try:
            date = datetime.strptime(formatted_date, "%d/%m/%Y")
        except ValueError:
            await interaction.response.send_message("❌ Невірна дата.", ephemeral=True)
            return

        data = load_data(EXPENSES_FILE)
        user_expenses = data.get(self.user_id, [])
        found = False
        for e in user_expenses:
            if float(e["amount"]) == self.old_amount and e["date"] == self.old_date:
                e["amount"] = amount_value
                e["date"] = date.strftime("%d/%m/%Y")
                found = True
                break

        if found:
            data[self.user_id] = user_expenses
            save_data(EXPENSES_FILE, data)
            await interaction.response.send_message(
                f"✅ Витрату оновлено: {amount_value:.2f} грн на {date.strftime('%d/%m/%Y')}.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message("❌ Витрату не знайдено.", ephemeral=True)
