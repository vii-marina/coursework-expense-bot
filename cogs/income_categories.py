import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
from utils.helpers import load_data, save_data

INCOME_CATEGORIES_FILE = "data/income_categories.json"


class IncomeCategoryManagerView(View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = str(user_id)

        data = load_data(INCOME_CATEGORIES_FILE)
        self.categories = data.get(self.user_id)

        if not self.categories:
            self.categories = ["Інше"]
            data[self.user_id] = self.categories
            save_data(INCOME_CATEGORIES_FILE, data)

        for idx, cat in enumerate(self.categories):
            self.add_item(IncomeCategoryItemButton(cat, idx, self.user_id))

        self.add_item(AddIncomeCategoryButton(self.user_id))


class IncomeCategoryItemButton(Button):
    def __init__(self, category, index, user_id):
        super().__init__(label=category, style=discord.ButtonStyle.secondary)
        self.category = category
        self.index = index
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"🔧 Дія з категорією прибутку **{self.category}**:",
            ephemeral=True,
            view=IncomeCategoryActionsView(self.user_id, self.index)
        )


class AddIncomeCategoryButton(Button):
    def __init__(self, user_id):
        super().__init__(label="➕ Додати категорію", style=discord.ButtonStyle.success)
        self.user_id = str(user_id)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(AddIncomeCategoryModal(self.user_id))


class AddIncomeCategoryModal(Modal, title="Нова категорія прибутку"):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.name = TextInput(label="Назва", placeholder="Наприклад: Зарплата")
        self.add_item(self.name)

    async def on_submit(self, interaction: discord.Interaction):
        name = self.name.value.strip()
        data = load_data(INCOME_CATEGORIES_FILE)
        categories = data.get(self.user_id, [])

        if name in categories:
            await interaction.response.send_message("⚠️ Така категорія вже існує.", ephemeral=True)
            return

        categories.append(name)
        data[self.user_id] = categories
        save_data(INCOME_CATEGORIES_FILE, data)

        await interaction.response.send_message(
            f"✅ Додано категорію **{name}**.",
            ephemeral=True,
            view=IncomeCategoryManagerView(self.user_id)
        )


class IncomeCategoryActionsView(View):
    def __init__(self, user_id, index):
        super().__init__(timeout=None)
        self.user_id = str(user_id)
        self.index = index

    @discord.ui.button(label="✏️ Перейменувати", style=discord.ButtonStyle.primary)
    async def rename(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(RenameIncomeCategoryModal(self.user_id, self.index))

    @discord.ui.button(label="🗑 Видалити", style=discord.ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, button: Button):
        data = load_data(INCOME_CATEGORIES_FILE)
        cats = data.get(self.user_id, [])
        deleted = cats.pop(self.index)
        data[self.user_id] = cats
        save_data(INCOME_CATEGORIES_FILE, data)

        await interaction.response.send_message(
            f"❌ Видалено категорію **{deleted}**.",
            ephemeral=True,
            view=IncomeCategoryManagerView(self.user_id)
        )

    @discord.ui.button(label="⬆️ Вгору", style=discord.ButtonStyle.secondary)
    async def move_up(self, interaction: discord.Interaction, button: Button):
        data = load_data(INCOME_CATEGORIES_FILE)
        cats = data.get(self.user_id, [])

        if self.index == 0:
            await interaction.response.send_message("⚠️ Уже вгорі.", ephemeral=True)
            return

        cats[self.index], cats[self.index - 1] = cats[self.index - 1], cats[self.index]
        data[self.user_id] = cats
        save_data(INCOME_CATEGORIES_FILE, data)

        await interaction.response.send_message("✅ Переміщено вгору.", ephemeral=True,
                                                view=IncomeCategoryManagerView(self.user_id))

    @discord.ui.button(label="⬇️ Вниз", style=discord.ButtonStyle.secondary)
    async def move_down(self, interaction: discord.Interaction, button: Button):
        data = load_data(INCOME_CATEGORIES_FILE)
        cats = data.get(self.user_id, [])

        if self.index >= len(cats) - 1:
            await interaction.response.send_message("⚠️ Уже внизу.", ephemeral=True)
            return

        cats[self.index], cats[self.index + 1] = cats[self.index + 1], cats[self.index]
        data[self.user_id] = cats
        save_data(INCOME_CATEGORIES_FILE, data)

        await interaction.response.send_message("✅ Переміщено вниз.", ephemeral=True,
                                                view=IncomeCategoryManagerView(self.user_id))


class RenameIncomeCategoryModal(Modal, title="Перейменувати категорію"):
    def __init__(self, user_id, index):
        super().__init__()
        self.user_id = str(user_id)
        self.index = index
        self.name = TextInput(label="Нова назва", placeholder="Наприклад: Додатковий дохід")
        self.add_item(self.name)

    async def on_submit(self, interaction: discord.Interaction):
        new_name = self.name.value.strip()
        data = load_data(INCOME_CATEGORIES_FILE)
        cats = data.get(self.user_id, [])
        old_name = cats[self.index]
        cats[self.index] = new_name
        data[self.user_id] = cats
        save_data(INCOME_CATEGORIES_FILE, data)

        await interaction.response.send_message(
            f"✏️ **{old_name}** → **{new_name}**",
            ephemeral=True,
            view=IncomeCategoryManagerView(self.user_id)
        )


class IncomeCategories(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


async def setup(bot):
    await bot.add_cog(IncomeCategories(bot))