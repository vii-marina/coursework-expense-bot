import discord
from discord.ext import commands
from discord.ui import View, Button, Select, Modal, TextInput
from utils.helpers import load_data, save_data, EXPENSES_FILE, CATEGORIES_FILE, SETTINGS_FILE
from .categories import CategoryManagerView
from datetime import datetime


class MenuView(View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = str(user_id)

    @discord.ui.button(label="➕ Додати витрату", style=discord.ButtonStyle.success)
    async def add_expense(self, interaction: discord.Interaction, button: Button):
        data = load_data(CATEGORIES_FILE)
        categories = data.get(self.user_id, [])
        if not categories:
            await interaction.response.send_message("⚠️ У вас ще немає категорій.", ephemeral=True)
            return
        await interaction.response.send_message("Оберіть категорію:", ephemeral=True, view=CategorySelectView(self.user_id, categories))

    @discord.ui.button(label="📊 Показати звіт", style=discord.ButtonStyle.primary)
    async def show_report(self, interaction: discord.Interaction, button: Button):
        data = load_data(EXPENSES_FILE)
        expenses = data.get(self.user_id, [])
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
        view = CategoryDropdownView(self.user_id)

        await interaction.response.send_message(text, ephemeral=True, view=view)

    @discord.ui.button(label="⚙️ Категорії", style=discord.ButtonStyle.secondary)
    async def manage_categories(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("🔧 Редагування категорій:", ephemeral=True, view=CategoryManagerView(self.user_id))

    @discord.ui.button(label="🔔 Автозвіт", style=discord.ButtonStyle.secondary)
    async def toggle_autozvit(self, interaction: discord.Interaction, button: Button):
        settings = load_data(SETTINGS_FILE)
        user_settings = settings.get(self.user_id, {})
        current_status = user_settings.get("autozvit", False)
        new_status = not current_status

        user_settings["autozvit"] = new_status
        settings[self.user_id] = user_settings
        save_data(SETTINGS_FILE, settings)

        emoji = "✅" if new_status else "❌"
        status = "увімкнено" if new_status else "вимкнено"
        await interaction.response.send_message(f"{emoji} Автоматичні звіти **{status}**.", ephemeral=True)


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


class ExpenseModal(Modal, title="Введення витрати"):
    def __init__(self, user_id, category):
        super().__init__()
        self.user_id = str(user_id)
        self.category = category
        self.amount = TextInput(label="Сума", placeholder="Введіть витрати в грн", required=True)
        self.date = TextInput(label="Дата (ДД/ММ/РРРР)", placeholder="ДД/ММ/РРРР", required=False)
        self.add_item(self.amount)
        self.add_item(self.date)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount_value = float(self.amount.value)
        except ValueError:
            await interaction.response.send_message("❌ Невірний формат суми.", ephemeral=True)
            return

        if not self.date.value.strip():
            date = datetime.now()
        else:
            try:
                date = datetime.strptime(self.date.value.strip(), "%d/%m/%Y")
            except ValueError:
                await interaction.response.send_message("❌ Невірний формат дати.", ephemeral=True)
                return

        data = load_data(EXPENSES_FILE)
        user_expenses = data.get(self.user_id, [])
        user_expenses.append({
            "category": self.category,
            "amount": amount_value,
            "date": date.strftime("%d/%m/%Y")
        })
        data[self.user_id] = user_expenses
        save_data(EXPENSES_FILE, data)

        await interaction.response.send_message(
            f"✅ Збережено {amount_value:.2f} грн в категорії **{self.category}** на дату {date.strftime('%d/%m/%Y')}.",
            ephemeral=True
        )


# === НОВИЙ ПІДХІД ДО ДЕТАЛІЗАЦІЇ ===

class CategoryDropdownView(View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.add_item(CategoryDetailDropdown(user_id))


class CategoryDetailDropdown(Select):
    def __init__(self, user_id):
        self.user_id = user_id
        data = load_data(EXPENSES_FILE)
        expenses = data.get(user_id, [])
        categories = sorted(set(e.get("category", "Без категорії") for e in expenses))
        options = [discord.SelectOption(label=cat, value=cat) for cat in categories]
        super().__init__(placeholder="Оберіть категорію для деталей", options=options)

    async def callback(self, interaction: discord.Interaction):
        data = load_data(EXPENSES_FILE)
        expenses = data.get(self.user_id, [])
        filtered = [e for e in expenses if e.get("category") == self.values[0]]
        filtered.sort(key=lambda x: datetime.strptime(x["date"], "%d/%m/%Y"))

        if not filtered:
            await interaction.response.send_message(f"📭 Немає витрат по категорії **{self.values[0]}**.", ephemeral=True)
            return

        lines = [f"{e['amount']:.2f} грн — {e['date']}" for e in filtered]
        text = f"📂 **Повний звіт за категорією {self.values[0]}:**\n" + "\n".join(lines)
        view = EditSelectorView(self.user_id, filtered, self.values[0])

        await interaction.response.send_message(text, ephemeral=True, view=view)


class EditSelectorView(View):
    def __init__(self, user_id, expenses, category):
        super().__init__(timeout=60)
        self.add_item(ExpenseDateSelector(user_id, expenses, category))


class ExpenseDateSelector(Select):
    def __init__(self, user_id, expenses, category):
        self.user_id = user_id
        self.expenses = expenses
        self.category = category

        options = [
            discord.SelectOption(
                label=f"{e['amount']} грн — {e['date']}",
                value=f"{e['date']}#{e['amount']}"
            )
            for e in expenses
        ]
        super().__init__(placeholder="Оберіть дату витрати для редагування/видалення", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_raw = self.values[0]                     # Наприклад: "13/04/2025#300.0"
        selected_date, selected_amount = selected_raw.split("#")
        selected_amount = float(selected_amount)

        selected_expense = next(
            (e for e in self.expenses if e["date"] == selected_date and float(e["amount"]) == selected_amount),
            None
        )


        if not selected_expense:
            await interaction.response.send_message("❌ Витрату не знайдено.", ephemeral=True)
            return

        await interaction.response.send_message(
            f"Що бажаєте зробити з витратою {selected_expense['amount']} грн — {selected_expense['date']}?",
            ephemeral=True,
            view=ExpenseEditDeleteView(self.user_id, selected_expense)
        )


class ExpenseEditDeleteView(View):
    def __init__(self, user_id, expense):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.expense = expense

    @discord.ui.button(label="✏️ Редагувати", style=discord.ButtonStyle.primary)
    async def edit(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(EditExpenseModal(self.user_id, self.expense))

    @discord.ui.button(label="🗑 Видалити", style=discord.ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, button: Button):
        data = load_data(EXPENSES_FILE)
        expenses = data.get(self.user_id, [])
        if self.expense in expenses:
            expenses.remove(self.expense)
            save_data(EXPENSES_FILE, data)
            await interaction.response.send_message("🗑 Витрату видалено.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Витрату не знайдено.", ephemeral=True)


class EditExpenseModal(Modal, title="Редагування витрати"):
    def __init__(self, user_id, expense):
        super().__init__()
        self.user_id = user_id
        self.expense = expense
        self.amount = TextInput(label="Нова сума", default=str(expense["amount"]))
        self.date = TextInput(label="Нова дата (ДД/ММ/РРРР)", default=expense["date"])
        self.add_item(self.amount)
        self.add_item(self.date)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            new_amount = float(self.amount.value)
            new_date = datetime.strptime(self.date.value.strip(), "%d/%m/%Y").strftime("%d/%m/%Y")
        except ValueError:
            await interaction.response.send_message("❌ Невірний формат.", ephemeral=True)
            return

        data = load_data(EXPENSES_FILE)
        expenses = data.get(self.user_id, [])

        for i, e in enumerate(expenses):
            if (
                e.get("category") == self.expense.get("category") and
                e.get("amount") == self.expense.get("amount") and
                e.get("date") == self.expense.get("date")
            ):
                expenses[i] = {
                    "category": self.expense["category"],
                    "amount": new_amount,
                    "date": new_date
                }
                save_data(EXPENSES_FILE, data)
                await interaction.response.send_message("✅ Витрату оновлено.", ephemeral=True)
                return

        await interaction.response.send_message("❌ Витрату не знайдено.", ephemeral=True)


class UI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.recent_menus = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        key = (message.channel.id, message.author.id)
        now = message.created_at
        if key in self.recent_menus and (now - self.recent_menus[key]).total_seconds() < 10:
            return
        self.recent_menus[key] = now
        await message.channel.send("📋 Меню керування витратами:", view=MenuView(message.author.id))


async def setup(bot):
    await bot.add_cog(UI(bot))
