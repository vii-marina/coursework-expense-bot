import discord
from discord.ext import commands
from discord.ui import View, Button, Select, Modal, TextInput
from utils.helpers import load_data, save_data, EXPENSES_FILE, CATEGORIES_FILE, SETTINGS_FILE
from .categories import CategoryManagerView


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

        await interaction.response.send_message(
            "Оберіть категорію:",
            ephemeral=True,
            view=CategorySelectView(self.user_id, categories)
        )

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

        await interaction.response.send_message(text, ephemeral=True)

    @discord.ui.button(label="⚙️ Категорії", style=discord.ButtonStyle.secondary)
    async def manage_categories(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(
            "🔧 Редагування категорій:",
            ephemeral=True,
            view=CategoryManagerView(self.user_id)
        )

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

        await interaction.response.send_message(
            f"{emoji} Автоматичні звіти **{status}**.",
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


class ExpenseModal(Modal, title="Додати витрату"):
    def __init__(self, user_id, category):
        super().__init__()
        self.user_id = str(user_id)
        self.category = category
        self.amount = TextInput(label="Сума", placeholder="Введіть витрати в грн", required=True)
        self.add_item(self.amount)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = float(self.amount.value)
        except ValueError:
            await interaction.response.send_message("❌ Невірна сума.", ephemeral=True)
            return

        data = load_data(EXPENSES_FILE)
        expenses = data.get(self.user_id, [])
        expenses.append({"category": self.category, "amount": amount})
        data[self.user_id] = expenses
        save_data(EXPENSES_FILE, data)

        await interaction.response.send_message(
            f"✅ Збережено {amount:.2f} грн в категорії **{self.category}**.",
            ephemeral=True
        )


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
        await message.channel.send(
            "📋 Меню керування витратами:",
            view=MenuView(message.author.id)
        )


async def setup(bot):
    await bot.add_cog(UI(bot))
