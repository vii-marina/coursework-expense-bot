import discord
from discord.ext import commands
from discord.ui import Modal, TextInput
from utils.helpers import load_data, save_data, SETTINGS_FILE
from .start_menu import StartView


class UI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_messages = {} 

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.content.startswith("!") or not message.content.strip():
            return
        
        key = (message.channel.id, message.author.id)

        view = StartView(user_id=message.author.id)
        greeting = (
            "Привіт! Я твій бот для покращення фінансової грамотності 🙂\n"
            "Що бажаєш додати?"
        )
        new_msg = await message.channel.send(content=greeting, view=view)
        self.active_messages.setdefault(key, []).append(new_msg.id)


class SetLimitModal(Modal, title="Встановити денний ліміт"):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = str(user_id)
        self.limit = TextInput(label="Сума ліміту (в грн)", placeholder="Наприклад: 200")
        self.add_item(self.limit)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            value = float(self.limit.value)
        except ValueError:
            await interaction.response.send_message("❌ Невірне значення ліміту.", ephemeral=True)
            return

        settings = load_data(SETTINGS_FILE)
        settings.setdefault(self.user_id, {})["daily_limit"] = value
        save_data(SETTINGS_FILE, settings)

        await interaction.response.send_message(f"✅ Ліміт {value:.2f} грн встановлено.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(UI(bot))
