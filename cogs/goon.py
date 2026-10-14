from discord.ext import commands
import discord

from config import get_command_alias

name = get_command_alias("goon")

class Goon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @discord.slash_command(name=name, description="goons")
    async def code_command(self, ctx: discord.ApplicationContext):
        await ctx.response.send_message("goon", ephemeral=True)

def setup(bot: commands.Bot) -> None:
    bot.add_cog(Goon(bot))