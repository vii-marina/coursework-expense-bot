import discord
from discord.ext import commands
from discord.ui import Modal, TextInput, Select, View, Button
from utils.helpers import load_data, save_data, EXPENSES_FILE, CATEGORIES_FILE
from datetime import datetime

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

        await interaction.response.send_message(
            f"✅ Збережено {amount_value:.2f} грн в категорії **{self.category}** на {date.strftime('%d/%m/%Y')}.",
            ephemeral=True
        )

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

# --- Звіт витрат ---
async def show_expense_report(interaction: discord.Interaction, user_id):
    data = load_data(EXPENSES_FILE)
    expenses = data.get(str(user_id), [])
    if not expenses:
        await interaction.response.send_message("📭 У вас ще немає витрат.", ephemeral=True)
        return

    summary = {}
    for e in expenses:
        category = e.get("category", "Без категорії")
        amount = float(e.get("amount", 0))
        summary[category] = summary.get(category, 0) + amount

    total = sum(summary.values())
    text = "\n".join([f"• **{cat}**: {amt:.2f} грн" for cat, amt in summary.items()])
    text += f"\n\n**Загалом:** {total:.2f} грн"
    await interaction.response.send_message(text, ephemeral=True, view=ExpenseCategorySelectForDetail(user_id))

# --- Вибір категорії ---
class ExpenseCategorySelectForDetail(View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.add_item(ExpenseCategoryDetailDropdown(user_id))

class ExpenseCategoryDetailDropdown(Select):
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
            await interaction.response.send_message("Немає витрат у цій категорії.", ephemeral=True)
            return

        try:
            filtered.sort(key=lambda x: datetime.strptime(x["date"], "%d/%m/%Y"))
        except Exception:
            pass

        details = "\n".join(f"{e['amount']} грн — {e['date']}" for e in filtered)
        options = [
            discord.SelectOption(
                label=f"{e['amount']} грн — {e['date']}",
                value=f"{e['amount']}#{e['date']}#{i}"
            )
            for i, e in enumerate(filtered)
        ]

        view = EditExpenseEntryView(self.user_id, options)
        await interaction.response.send_message(f"📂 **{selected} — деталізація:**\n{details}\n\n🔧 Оберіть витрату для редагування:", ephemeral=True, view=view)

class EditExpenseEntryView(View):
    def __init__(self, user_id, options):
        super().__init__(timeout=60)
        self.add_item(EditExpenseEntryDropdown(user_id, options))

class EditExpenseEntryDropdown(Select):
    def __init__(self, user_id, options):
        self.user_id = user_id
        super().__init__(placeholder="Оберіть витрату", options=options)

    async def callback(self, interaction: discord.Interaction):
        amount, date, _ = self.values[0].split("#")
        await interaction.response.send_message(f"Що бажаєте зробити з витратою {amount} грн — {date}?",
                                                ephemeral=True,
                                                view=ExpenseEditDeleteView(self.user_id, float(amount), date))

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
        entries = data.get(self.user_id, [])
        updated = [e for e in entries if not (float(e["amount"]) == self.old_amount and e["date"] == self.old_date)]
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

        data = load_data(EXPENSES_FILE)
        entries = data.get(self.user_id, [])
        for e in entries:
            if float(e["amount"]) == self.old_amount and e["date"] == self.old_date:
                e["amount"] = new_amount
                e["date"] = date.strftime("%d/%m/%Y")
                break

        data[self.user_id] = entries
        save_data(EXPENSES_FILE, data)
        await interaction.response.send_message("✅ Витрату оновлено.", ephemeral=True)


class Expenses(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

async def setup(bot):
    await bot.add_cog(Expenses(bot))
