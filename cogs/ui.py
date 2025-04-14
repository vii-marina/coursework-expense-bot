import discord
from discord.ext import commands
from discord.ui import View, Button, Select, Modal, TextInput
from utils.helpers import load_data, save_data, EXPENSES_FILE, CATEGORIES_FILE, SETTINGS_FILE, INCOME_FILE
from .categories import CategoryManagerView
from .expenses import CategorySelectView, show_expense_report
from .income_ui import IncomeMenuView, IncomeCategoryManagerView
from datetime import datetime, timedelta

# --- Категорія деталізація ---
class MenuView(View):
    def __init__(self, user_id, categories):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.categories = categories

    @discord.ui.button(label="➕ Додати витрату", style=discord.ButtonStyle.success)
    async def add_expense(self, interaction: discord.Interaction, button: Button):
        if not self.categories:
            await interaction.response.send_message("⚠️ У вас ще немає категорій.", ephemeral=True)
            return
        await interaction.response.send_message("Оберіть категорію:", ephemeral=True, view=CategorySelectView(self.user_id, self.categories))

    @discord.ui.button(label="📊 Показати звіт", style=discord.ButtonStyle.primary)
    async def show_report(self, interaction: discord.Interaction, button: Button):
        await show_expense_report(interaction, self.user_id)

    @discord.ui.button(label="⚙️ Категорії", style=discord.ButtonStyle.secondary)
    async def manage_categories(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("🔧 Редагування категорій:", ephemeral=True, view=CategoryManagerView(self.user_id))

class StartView(View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = str(user_id)

    @discord.ui.button(label="💰 Прибуток", style=discord.ButtonStyle.success)
    async def income_menu(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("📈 Меню керування прибутками:", ephemeral=True, view=IncomeMenuView(self.user_id))

    @discord.ui.button(label="💸 Витрата", style=discord.ButtonStyle.primary)
    async def expense_menu(self, interaction: discord.Interaction, button: Button):
        data = load_data("data/categories.json")
        categories = data.get(self.user_id, [])
        await interaction.response.send_message("💸 Меню витрат:", ephemeral=True, view=MenuView(self.user_id, categories))

    @discord.ui.button(label="📋 Загальний звіт", style=discord.ButtonStyle.secondary)
    async def overall_report(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Оберіть період для загального звіту:", ephemeral=True, view=OverallReportView(self.user_id))

class OverallReportView(View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.add_item(OverallReportSelect(user_id))
class OverallReportSelect(Select):
    def __init__(self, user_id):
        self.user_id = user_id
        options = [
            discord.SelectOption(label="Сьогодні", value="day"),
            discord.SelectOption(label="Цей тиждень", value="week"),
            discord.SelectOption(label="Цей місяць", value="month")
        ]
        super().__init__(placeholder="Оберіть період", options=options)

    async def callback(self, interaction: discord.Interaction):
        incomes = load_data(INCOME_FILE).get(self.user_id, [])
        expenses = load_data(EXPENSES_FILE).get(self.user_id, [])

        now = datetime.now()
        period = self.values[0]

        if period == "day":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start = now - timedelta(days=now.weekday())
        else:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        def filter_by_date(data):
            result = 0.0
            for e in data:
                try:
                    date = datetime.strptime(e.get("date", "01/01/2000"), "%d/%m/%Y")
                    if date >= start:
                        result += float(e.get("amount", 0))
                except:
                    continue
            return result

        total_income = filter_by_date(incomes)
        total_expenses = filter_by_date(expenses)
        balance = total_income - total_expenses

        await interaction.response.send_message(
            f"📋 **Загальний звіт ({period.upper()}):**\n"
            f"**Прибуток:** {total_income:.2f} грн\n"
            f"**Витрати:** {total_expenses:.2f} грн\n"
            f"**Залишок:** {balance:.2f} грн",
            ephemeral=True
        )

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
        super().__init__(label="🔧 Натисніть, якщо бажаєте редагувати витрату", style=discord.ButtonStyle.secondary)
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
        await interaction.response.send_message("Оберіть запис для редагування:", ephemeral=True,
                                                view=EditExpenseSelectView(self.user_id, options))

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
        expenses = data.get(self.user_id, [])

        for i in expenses:
            if float(i["amount"]) == self.old_amount and i["date"] == self.old_date:
                i["amount"] = new_amount
                i["date"] = date.strftime("%d/%m/%Y")
                break

        data[self.user_id] = expenses
        save_data(EXPENSES_FILE, data)
        await interaction.response.send_message("✅ Витрату оновлено.", ephemeral=True)

class UI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        view = StartView(user_id=message.author.id)
        greeting = [
            "Привіт! Я твій бот для покращення фінансової грамотності 🙂",
            "Що бажаєш додати?"
        ]
        await message.channel.send("\n".join(greeting), view=view)

async def setup(bot):
    await bot.add_cog(UI(bot))
