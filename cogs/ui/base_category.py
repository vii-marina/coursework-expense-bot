import discord
from discord.ui import View, Button, Modal, TextInput
from utils.helpers import load_data, save_data

EXPENSE_CATEGORIES_FILE = "data/categories.json"
INCOME_CATEGORIES_FILE = "data/income_categories.json"

class BaseCategoryManagerView(View):
    def __init__(self, user_id, is_income=False):
        super().__init__(timeout=None)
        self.user_id = str(user_id)
        self.is_income = is_income
        self.file = INCOME_CATEGORIES_FILE if is_income else EXPENSE_CATEGORIES_FILE

        data = load_data(self.file)
        self.categories = data.get(self.user_id)

        if not self.categories:
            self.categories = ["Інше"]
            data[self.user_id] = self.categories
            save_data(self.file, data)

        for idx, cat in enumerate(self.categories):
            self.add_item(BaseCategoryItemButton(cat, idx, self.user_id, self.file, self.is_income))

        self.add_item(AddBaseCategoryButton(self.user_id, self.file, self.is_income))


class BaseCategoryItemButton(Button):
    def __init__(self, category, index, user_id, file, is_income):
        super().__init__(label=category, style=discord.ButtonStyle.secondary)
        self.category = category
        self.index = index
        self.user_id = user_id
        self.file = file
        self.is_income = is_income

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"🔧 Дія з категорією **{self.category}**:",
            ephemeral=True,
            view=BaseCategoryActionsView(self.user_id, self.index, self.file, self.is_income)
        )


class AddBaseCategoryButton(Button):
    def __init__(self, user_id, file, is_income):
        super().__init__(label="➕ Додати категорію", style=discord.ButtonStyle.success)
        self.user_id = str(user_id)
        self.file = file
        self.is_income = is_income

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(AddBaseCategoryModal(self.user_id, self.file, self.is_income))


class AddBaseCategoryModal(Modal, title="Нова категорія"):
    def __init__(self, user_id, file, is_income):
        super().__init__()
        self.user_id = user_id
        self.file = file
        self.is_income = is_income
        self.name = TextInput(label="Назва", placeholder="Наприклад: Зарплата або Продукти")
        self.add_item(self.name)

    async def on_submit(self, interaction: discord.Interaction):
        name = self.name.value.strip()
        data = load_data(self.file)
        categories = data.get(self.user_id, [])

        if name in categories:
            await interaction.response.send_message("⚠️ Така категорія вже існує.", ephemeral=True)
            return

        categories.append(name)
        data[self.user_id] = categories
        save_data(self.file, data)

        await interaction.response.send_message(
            f"✅ Додано категорію **{name}**.",
            ephemeral=True,
            view=BaseCategoryManagerView(self.user_id, self.is_income)
        )


class BaseCategoryActionsView(View):
    def __init__(self, user_id, index, file, is_income):
        super().__init__(timeout=None)
        self.user_id = str(user_id)
        self.index = index
        self.file = file
        self.is_income = is_income

    @discord.ui.button(label="✏️ Перейменувати", style=discord.ButtonStyle.primary)
    async def rename(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(RenameBaseCategoryModal(self.user_id, self.index, self.file, self.is_income))

    @discord.ui.button(label="🗑 Видалити", style=discord.ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, button: Button):
        data = load_data(self.file)
        cats = data.get(self.user_id, [])
        deleted = cats.pop(self.index)
        data[self.user_id] = cats
        save_data(self.file, data)

        await interaction.response.send_message(
            f"❌ Видалено категорію **{deleted}**.",
            ephemeral=True,
            view=BaseCategoryManagerView(self.user_id, self.is_income)
        )

    @discord.ui.button(label="⬆️ Вгору", style=discord.ButtonStyle.secondary)
    async def move_up(self, interaction: discord.Interaction, button: Button):
        data = load_data(self.file)
        cats = data.get(self.user_id, [])

        if self.index == 0:
            await interaction.response.send_message("⚠️ Уже вгорі.", ephemeral=True)
            return

        cats[self.index], cats[self.index - 1] = cats[self.index - 1], cats[self.index]
        data[self.user_id] = cats
        save_data(self.file, data)

        await interaction.response.send_message("✅ Переміщено вгору.", ephemeral=True,
                                                view=BaseCategoryManagerView(self.user_id, self.is_income))

    @discord.ui.button(label="⬇️ Вниз", style=discord.ButtonStyle.secondary)
    async def move_down(self, interaction: discord.Interaction, button: Button):
        data = load_data(self.file)
        cats = data.get(self.user_id, [])

        if self.index >= len(cats) - 1:
            await interaction.response.send_message("⚠️ Уже внизу.", ephemeral=True)
            return

        cats[self.index], cats[self.index + 1] = cats[self.index + 1], cats[self.index]
        data[self.user_id] = cats
        save_data(self.file, data)

        await interaction.response.send_message("✅ Переміщено вниз.", ephemeral=True,
                                                view=BaseCategoryManagerView(self.user_id, self.is_income))


class RenameBaseCategoryModal(Modal, title="Перейменувати категорію"):
    def __init__(self, user_id, index, file, is_income):
        super().__init__()
        self.user_id = str(user_id)
        self.index = index
        self.file = file
        self.is_income = is_income
        self.name = TextInput(label="Нова назва", placeholder="Наприклад: Нове ім'я")
        self.add_item(self.name)

    async def on_submit(self, interaction: discord.Interaction):
        new_name = self.name.value.strip()
        data = load_data(self.file)
        cats = data.get(self.user_id, [])
        old_name = cats[self.index]
        cats[self.index] = new_name
        data[self.user_id] = cats
        save_data(self.file, data)

        await interaction.response.send_message(
            f"✏️ **{old_name}** → **{new_name}**",
            ephemeral=True,
            view=BaseCategoryManagerView(self.user_id, self.is_income)
        )
