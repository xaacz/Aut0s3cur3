from discord.ext import commands
import discord

from config import get_command_alias, get_config, save_config

name = get_command_alias("set_channel")

class setChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    set = discord.SlashCommandGroup(name)
    @set.command(name="channel", description="Sets your channel ID")
    async def setChannels(
        self, 
        ctx: discord.ApplicationContext, 
        choice: str = discord.Option(description="Choose channel type", choices=["Logs", "Logs (Censored)", "Hits"])

    ):
        if ctx.author.id not in self.bot.admins:
            await ctx.respond("You do not have permission to execute this command!", ephemeral=True)
            return

        newConfig = get_config()

        match choice:
            case "Logs":
                newConfig["discord"]["logs_channel"] = str(ctx.channel_id)
            case "Logs (Censored)":
                newConfig["discord"]["censored_logs_channel"] = str(ctx.channel_id)
            case "Hits":
                newConfig["discord"]["accounts_channel"] = str(ctx.channel_id)

        save_config(newConfig)

        await ctx.respond(f"Successfully set {choice} channel!", ephemeral=True)

def setup(bot: commands.Bot) -> None:
    bot.add_cog(setChannel(bot))