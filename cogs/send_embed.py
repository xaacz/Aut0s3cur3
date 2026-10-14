from discord.ext import commands
import discord

from config import get_command_alias, get_config, get_bot_config
from ui.buttons.link_account import LinkAccountView

name = get_command_alias("send_embed")

def get_embed() -> dict:
    data = get_bot_config()

    embed = data["embeds"]["verification"]["default"]
    return {
        "title": embed.get("title") or "",
        "description": embed.get("description") or "",
        "color": embed.get("color") or 0,
        "fields": embed.get("fields") or [],
        "footer": embed.get("footer") or {},
        "thumbnail": embed.get("thumbnail") or "",
        "ephemeral": data.get("ephemeral", False),
    }

def build_features_embed() -> discord.Embed:
    data = get_bot_config()
    fdata = data.get("embeds", {}).get("features", {}).get("default", {})
    embed = discord.Embed(
        title=fdata.get("title", "aut0 Features"),

        description=fdata.get("description", "The most trusted aut0 Features"),
        color=fdata.get("color", 0x3498DB),
    )
    if fdata.get("thumbnail"):
        embed.set_thumbnail(url=fdata["thumbnail"])
    footer = fdata.get("footer") or {}
    if footer.get("text"):
        embed.set_footer(text=footer["text"], icon_url=footer.get("icon_url") or None)
    for field in fdata.get("fields") or []:
        embed.add_field(
            name=field.get("name") or "\u200b",
            value=field.get("value") or "\u200b",
            inline=bool(field.get("inline")),
        )
    return embed

class sendEmbed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    send = discord.SlashCommandGroup(name)

    @send.command(name="embed", description="Sends the verification embed")
    async def embed_command(self, ctx: discord.ApplicationContext):
        if ctx.author.id not in self.bot.admins and len(self.bot.admins) > 0 and 0 not in self.bot.admins:
            await ctx.respond(
                "You do not have permission to execute this command!", 
                ephemeral=True
            )
            return
        
        config = get_config()
        
        if not config["discord"]["logs_channel"] or not config["discord"]["accounts_channel"]:
            await ctx.respond(
                "You must set the logs and Hits channel first with /set channel!",
                ephemeral=True
            )
            return
        
        embed = get_embed()

        await ctx.defer(ephemeral=True)
        message = discord.Embed(
            title=embed["title"],
            description=embed["description"],
            color=embed["color"],
        )
        if embed.get("thumbnail"):
            message.set_thumbnail(url=embed["thumbnail"])
        footer = embed.get("footer") or {}
        if footer.get("text"):
            message.set_footer(text=footer["text"], icon_url=footer.get("icon_url") or None)
        for field in embed.get("fields") or []:
            message.add_field(
                name=field.get("name") or "\u200b",
                value=field.get("value") or "\u200b",
                inline=bool(field.get("inline")),
            )
        await ctx.channel.send(
            embed=message,
            view=LinkAccountView(),
        )
        
        await ctx.followup.send("Sent!", ephemeral=True)

    @send.command(name="features", description="Gửi bảng tính năng aut0 Features vào kênh")
    async def features_command(self, ctx: discord.ApplicationContext):
        if ctx.author.id not in self.bot.admins and len(self.bot.admins) > 0 and 0 not in self.bot.admins:
            await ctx.respond("Ban khong co quyen su dung lenh nay!", ephemeral=True)
            return
        fembed = build_features_embed()
        await ctx.channel.send(embed=fembed)
        await ctx.respond("Da gui bang aut0 Features thanh cong!", ephemeral=True)

    @discord.slash_command(name="features", description="Xem bảng tính năng & giới thiệu aut0 Features")
    async def direct_features_command(self, ctx: discord.ApplicationContext):
        fembed = build_features_embed()
        await ctx.respond(embed=fembed)

def setup(bot: commands.Bot) -> None:
    bot.add_cog(sendEmbed(bot))