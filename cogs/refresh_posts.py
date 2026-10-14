from discord.ext import commands, tasks
import discord
import json
import logging
import os
import time

from config import get_bot_config

logger = logging.getLogger("bot")

STATE_PATH = "config/refresh_posts_state.json"


def _load_state() -> dict:
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_state(state: dict) -> None:
    tmp = f"{STATE_PATH}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, STATE_PATH)


def _embed_from_dict(raw: dict) -> discord.Embed:
    embed = discord.Embed(
        title=raw.get("title") or None,
        description=raw.get("description") or None,
        color=raw.get("color") or 0,
    )
    if raw.get("thumbnail"):
        embed.set_thumbnail(url=raw["thumbnail"])
    footer = raw.get("footer") or {}
    if footer.get("text"):
        embed.set_footer(text=footer["text"], icon_url=footer.get("icon_url") or None)
    for field in raw.get("fields") or []:
        embed.add_field(
            name=field.get("name") or "\u200b",
            value=field.get("value") or "\u200b",
            inline=bool(field.get("inline")),
        )
    return embed


class RefreshPosts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._loop.start()

    def cog_unload(self):
        self._loop.cancel()

    def _settings(self) -> tuple[list, float]:
        cfg = get_bot_config().get("refresh_posts") or {}
        posts = cfg.get("posts") or []
        hours = float(cfg.get("interval_hours") or 30)
        return posts, max(1.0, hours)

    @tasks.loop(minutes=10)
    async def _loop(self):
        posts, hours = self._settings()
        if not posts:
            return
        state = _load_state()
        last = float(state.get("last_sent") or 0)
        if last and time.time() - last < hours * 3600:
            return
        try:
            await self._refresh(posts, state)
        except Exception:
            logger.exception("refresh_posts failed")

    @_loop.before_loop
    async def _before_loop(self):
        await self.bot.wait_until_ready()

    async def _refresh(self, posts: list, state: dict) -> None:
        sent_total = 0
        channels = dict(state.get("channels") or {})

        for post in posts:
            channel_id = int(post.get("channel_id") or 0)
            embeds_raw = post.get("embeds") or []
            if not channel_id or not embeds_raw:
                continue
            try:
                channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(
                    channel_id
                )
            except discord.HTTPException as exc:
                logger.warning("refresh_posts: cannot fetch channel %s (%s)", channel_id, exc)
                continue
            if not isinstance(channel, discord.TextChannel):
                continue

            sent: list[discord.Message] = []
            for raw in embeds_raw:
                sent.append(await channel.send(embed=_embed_from_dict(raw)))
            sent_total += len(sent)
            new_ids = [m.id for m in sent]
            channels[str(channel_id)] = new_ids
            state["channels"] = channels
            state["last_sent"] = time.time()
            _save_state(state)

            if post.get("pin", True) and sent:
                try:
                    await sent[0].pin()
                except Exception:
                    logger.exception("refresh_posts: pin failed in %s", channel_id)

            keep = set(new_ids)
            try:
                recent = await channel.history(limit=50).flatten()
            except Exception:
                logger.exception("refresh_posts: history failed in %s", channel_id)
                recent = []

            for msg in recent:
                if msg.id in keep or not self.bot.user:
                    continue
                if msg.author.id != self.bot.user.id:
                    continue
                if msg.type == discord.MessageType.pins_add or msg.embeds:
                    try:
                        await msg.delete()
                    except Exception:
                        logger.exception("refresh_posts: delete failed %s", msg.id)

        logger.info("refresh_posts: resent %s message(s)", sent_total)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(RefreshPosts(bot))
