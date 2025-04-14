import discord
from discord.ext import commands
from discord.ui import View, Button, Select, Modal, TextInput
from utils.helpers import load_data, save_data
from .income_categories import IncomeCategoryManagerView
from datetime import datetime

INCOME_FILE = "data/income.json"
INCOME_CATEGORIES_FILE = "data/income_categories.json"

# --- Головне меню прибутків ---
class IncomeMenuView(View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = str(user_id)

    @discord.ui.button(label="➕ Додати прибуток", style=discord.ButtonStyle.success)
    async def add_income(self, interaction: discord.Interaction, button: Button):
        data = load_data(INCOME_CATEGORIES_FILE)
        categories = data.get(self.user_id, [])
        if not categories:
            await interaction.response.send_message("⚠️ У вас ще немає категорій прибутків.", ephemeral=True)
            return
        await interaction.response.send_message("Оберіть категорію прибутку:", ephemeral=True, view=IncomeCategorySelectView(self.user_id, categories))

    @discord.ui.button(label="📊 Показати звіт", style=discord.ButtonStyle.primary)
    async def show_report(self, interaction: discord.Interaction, button: Button):
        data = load_data(INCOME_FILE)
        incomes = data.get(self.user_id, [])
        if not incomes:
            await interaction.response.send_message("📭 У вас ще немає прибутків.", ephemeral=True)
            return

        summary = {}
        for e in incomes:
            category = e.get("category", "Без категорії")
            amount = float(e.get("amount", 0))
            summary[category] = summary.get(category, 0) + amount

        total = sum(summary.values())
        text = "\n".join([f"• **{cat}**: {amt:.2f} грн" for cat, amt in summary.items()])
        text += f"\n\n**Загалом:** {total:.2f} грн"
        await interaction.response.send_message(text, ephemeral=True, view=IncomeCategorySelectForDetail(self.user_id))

    @discord.ui.button(label="⚙️ Категорії прибутків", style=discord.ButtonStyle.secondary)
    async def manage_categories(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("🔧 Редагування категорій прибутків:", ephemeral=True, view=IncomeCategoryManagerView(self.user_id))

# --- Додавання прибутку ---
class IncomeCategorySelectView(View):
    def __init__(self, user_id, categories):
        super().__init__(timeout=60)
        self.add_item(IncomeCategorySelect(user_id, categories))

class IncomeCategorySelect(Select):
    def __init__(self, user_id, categories):
        self.user_id = str(user_id)
        options = [discord.SelectOption(label=cat) for cat in categories]
        super().__init__(placeholder="Оберіть категорію", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(AddIncomeModal(self.user_id, self.values[0]))

class AddIncomeModal(Modal, title="Додавання прибутку"):
    def __init__(self, user_id, category):
        super().__init__()
        self.user_id = str(user_id)
        self.category = category
        self.amount = TextInput(label="Сума", placeholder="Введіть прибуток в грн", required=True)
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
            f"✅ Збережено {amount_value:.2f} грн в категорії **{self.category}** на дату {date.strftime('%d/%m/%Y')}",
            ephemeral=True
        )

# --- Категорія деталізації звіту з кнопкою редагування ---
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
        options = [discord.SelectOption(label=cat) for cat in categories]
        super().__init__(placeholder="Оберіть категорію для деталей", options=options)

    async def callback(self, interaction: discord.Interaction):
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
            discord.SelectOption(
                label=f"{e['amount']} грн — {e['date']}",
                value=f"{e['amount']}#{e['date']}#{i}"
            )
            for i, e in enumerate(filtered)
        ]
        await interaction.response.send_message(f"📂 **{selected} — деталізація:**\n{details}\n\n🔧 Оберіть прибуток для редагування:", ephemeral=True, view=EditIncomeEntryView(self.user_id, options))

class EditIncomeEntryView(View):
    def __init__(self, user_id, options):
        super().__init__(timeout=60)
        self.add_item(EditIncomeEntryDropdown(user_id, options))

class EditIncomeEntryDropdown(Select):
    def __init__(self, user_id, options):
        self.user_id = user_id
        super().__init__(placeholder="Оберіть запис", options=options)

    async def callback(self, interaction: discord.Interaction):
        raw = self.values[0]
        amount, date, _ = raw.split("#")
        await interaction.response.send_message(f"Що бажаєте зробити з прибутком {amount} грн — {date}?",
                                                ephemeral=True,
                                                view=IncomeEditDeleteView(self.user_id, float(amount), date))

class IncomeEditDeleteView(View):
    def __init__(self, user_id, old_amount, old_date):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.old_amount = old_amount
        self.old_date = old_date

    @discord.ui.button(label="✏️ Редагувати", style=discord.ButtonStyle.primary)
    async def edit(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(EditIncomeModal(self.user_id, self.old_amount, self.old_date))

    @discord.ui.button(label="🗑 Видалити", style=discord.ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, button: Button):
        data = load_data(INCOME_FILE)
        incomes = data.get(self.user_id, [])
        updated = [e for e in incomes if not (float(e["amount"]) == self.old_amount and e["date"] == self.old_date)]
        data[self.user_id] = updated
        save_data(INCOME_FILE, data)
        await interaction.response.send_message("🗑 Прибуток видалено.", ephemeral=True)

class EditIncomeModal(Modal, title="Редагування прибутку"):
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

class IncomeUI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        pass

async def setup(bot):
    await bot.add_cog(IncomeUI(bot))
