import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
from utils.helpers import load_data, save_data, CATEGORIES_FILE


class CategoryManagerView(View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = str(user_id)

        data = load_data(CATEGORIES_FILE)
        self.categories = data.get(self.user_id)

        # Якщо ще немає категорій — створюємо одну за замовчуванням
        if not self.categories:
            self.categories = ["Інше"]
            data[self.user_id] = self.categories
            save_data(CATEGORIES_FILE, data)

        # Кнопки для кожної категорії
        for idx, cat in enumerate(self.categories):
            self.add_item(CategoryItemButton(cat, idx, self.user_id))

        # Кнопка для додавання
        self.add_item(AddCategoryButton(self.user_id))


class CategoryItemButton(Button):
    def __init__(self, category, index, user_id):
        super().__init__(label=category, style=discord.ButtonStyle.secondary)
        self.category = category
        self.index = index
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"🔧 Дія з категорією **{self.category}**:",
            ephemeral=True,
            view=CategoryActionsView(self.user_id, self.index)
        )


class AddCategoryButton(Button):
    def __init__(self, user_id):
        super().__init__(label="➕ Додати категорію", style=discord.ButtonStyle.success)
        self.user_id = str(user_id)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(AddCategoryModal(self.user_id))


class AddCategoryModal(Modal, title="Нова категорія"):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.name = TextInput(label="Назва", placeholder="Наприклад: Підписки")
        self.add_item(self.name)

    async def on_submit(self, interaction: discord.Interaction):
        name = self.name.value.strip()
        data = load_data(CATEGORIES_FILE)
        categories = data.get(self.user_id, [])

        if name in categories:
            await interaction.response.send_message("⚠️ Така категорія вже існує.", ephemeral=True)
            return

        categories.append(name)
        data[self.user_id] = categories
        save_data(CATEGORIES_FILE, data)

        await interaction.response.send_message(
            f"✅ Додано категорію **{name}**.",
            ephemeral=True,
            view=CategoryManagerView(self.user_id)
        )


class CategoryActionsView(View):
    def __init__(self, user_id, index):
        super().__init__(timeout=None)
        self.user_id = str(user_id)
        self.index = index

    @discord.ui.button(label="✏️ Перейменувати", style=discord.ButtonStyle.primary)
    async def rename(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(RenameCategoryModal(self.user_id, self.index))

    @discord.ui.button(label="🗑 Видалити", style=discord.ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, button: Button):
        data = load_data(CATEGORIES_FILE)
        cats = data.get(self.user_id, [])
        deleted = cats.pop(self.index)
        data[self.user_id] = cats
        save_data(CATEGORIES_FILE, data)

        await interaction.response.send_message(
            f"❌ Видалено категорію **{deleted}**.",
            ephemeral=True,
            view=CategoryManagerView(self.user_id)
        )

    @discord.ui.button(label="⬆️ Вгору", style=discord.ButtonStyle.secondary)
    async def move_up(self, interaction: discord.Interaction, button: Button):
        data = load_data(CATEGORIES_FILE)
        cats = data.get(self.user_id, [])

        if self.index == 0:
            await interaction.response.send_message("⚠️ Уже вгорі.", ephemeral=True)
            return

        cats[self.index], cats[self.index - 1] = cats[self.index - 1], cats[self.index]
        data[self.user_id] = cats
        save_data(CATEGORIES_FILE, data)

        await interaction.response.send_message("✅ Переміщено вгору.", ephemeral=True, view=CategoryManagerView(self.user_id))

    @discord.ui.button(label="⬇️ Вниз", style=discord.ButtonStyle.secondary)
    async def move_down(self, interaction: discord.Interaction, button: Button):
        data = load_data(CATEGORIES_FILE)
        cats = data.get(self.user_id, [])

        if self.index >= len(cats) - 1:
            await interaction.response.send_message("⚠️ Уже внизу.", ephemeral=True)
            return

        cats[self.index], cats[self.index + 1] = cats[self.index + 1], cats[self.index]
        data[self.user_id] = cats
        save_data(CATEGORIES_FILE, data)

        await interaction.response.send_message("✅ Переміщено вниз.", ephemeral=True, view=CategoryManagerView(self.user_id))


class RenameCategoryModal(Modal, title="Перейменувати категорію"):
    def __init__(self, user_id, index):
        super().__init__()
        self.user_id = str(user_id)
        self.index = index
        self.name = TextInput(label="Нова назва", placeholder="Наприклад: Розваги")
        self.add_item(self.name)

    async def on_submit(self, interaction: discord.Interaction):
        new_name = self.name.value.strip()
        data = load_data(CATEGORIES_FILE)
        cats = data.get(self.user_id, [])
        old_name = cats[self.index]
        cats[self.index] = new_name
        data[self.user_id] = cats
        save_data(CATEGORIES_FILE, data)

        await interaction.response.send_message(
            f"✏️ **{old_name}** → **{new_name}**",
            ephemeral=True,
            view=CategoryManagerView(self.user_id)
        )


class Categories(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


async def setup(bot):
    await bot.add_cog(Categories(bot))
