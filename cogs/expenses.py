import discord
from discord.ext import commands
from discord.ui import Modal, TextInput, Select, View
from utils.helpers import load_data, save_data, EXPENSES_FILE, CATEGORIES_FILE


class ExpenseModal(Modal, title="Введення витрати"):
    def __init__(self, user_id, category):
        super().__init__()
        self.user_id = str(user_id)
        self.category = category
        self.amount = TextInput(label="Сума", placeholder="Введіть витрати в грн", required=True)
        self.add_item(self.amount)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount_value = float(self.amount.value)
        except ValueError:
            await interaction.response.send_message("❌ Невірний формат суми.", ephemeral=True)
            return

        data = load_data(EXPENSES_FILE)
        user_expenses = data.get(self.user_id, [])
        user_expenses.append({"category": self.category, "amount": amount_value})
        data[self.user_id] = user_expenses
        save_data(EXPENSES_FILE, data)

        await interaction.response.send_message(
            f"✅ Збережено {amount_value:.2f} грн в категорії **{self.category}**.",
            ephemeral=True
        )


class CategorySelect(Select):
    def __init__(self, user_id):
        self.user_id = str(user_id)
        data = load_data(CATEGORIES_FILE)
        categories = data.get(self.user_id, ["Інше"])

        options = [discord.SelectOption(label=cat) for cat in categories]
        super().__init__(placeholder="Оберіть категорію", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ExpenseModal(self.user_id, self.values[0]))


class Expenses(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

async def setup(bot):
    await bot.add_cog(Expenses(bot))
