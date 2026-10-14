from ui.modals.modal_one import MyModalOne
import discord

from config import get_bot_config

styles = {
    "primary":   discord.ButtonStyle.primary,
    "secondary": discord.ButtonStyle.secondary,
    "success":   discord.ButtonStyle.success,
    "danger":    discord.ButtonStyle.danger,
}

def bconfig():
    config = get_bot_config().get("verification_button", {})
    return {
        "text": config.get("text", "Verify"),
        "color": config.get("color", "primary"),
        "emoji": None,
    }

class LinkAccountButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            custom_id="persistent:button_one"
        )

        config = bconfig()
        self.label = config["text"]
        self.style = styles[config["color"]]


    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(MyModalOne())

class LinkAccountView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(LinkAccountButton())