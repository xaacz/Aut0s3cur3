import io
import os
import logging
import httpx
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from shared.simplify import simplify

log = logging.getLogger("bot")

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")

def _get_font(size: int, bold: bool = True):
    font_candidates = [
        os.path.join(ASSETS_DIR, "Minecraft-Bold.otf"),
        os.path.join(ASSETS_DIR, "Minecraft.otf"),
        os.path.join(ASSETS_DIR, "Silkscreen-Regular.ttf"),
        os.path.join(ASSETS_DIR, "PressStart2P-Regular.ttf"),
    ]
    if os.name == "nt":
        font_candidates.extend([
            "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/consolab.ttf" if bold else "C:/Windows/Fonts/consola.ttf",
        ])
    else:
        font_candidates.extend([
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        ])

    for p in font_candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()

def _mask_username(name: str) -> str:
    if not name or len(name) <= 2:
        return name or "Player"
    if len(name) <= 4:
        return name[:1] + "*" * (len(name) - 1)
    return name[:2] + "*" * (len(name) - 2)

async def _fetch_skin_image(username: str, height: int = 340) -> Image.Image | None:
    # 1. Try online renders
    if username and username.lower() not in {"unknown", "no minecraft", "?", "n/a"}:
        urls = [
            f"https://visage.surgeplay.com/full/{height}/{username}",
            f"https://minotar.net/armor/body/{username}/{height}.png",
        ]
        for url in urls:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(url)
                    if resp.status_code == 200 and len(resp.content) > 500:
                        return Image.open(io.BytesIO(resp.content)).convert("RGBA")
            except Exception:
                continue

    # 2. Local fallback sample skin
    sample_skin_path = os.path.join(ASSETS_DIR, "sample_skin.png")
    if os.path.exists(sample_skin_path):
        try:
            return Image.open(sample_skin_path).convert("RGBA")
        except Exception:
            pass

    return None

def create_hit_card_sync(
    username: str,
    rank: str = "None",
    hstats: dict = None,
    capes: list = None,
    skin_img: Image.Image | None = None
) -> io.BytesIO:
    hstats = hstats or {}
    hyp = hstats.get("hypixel") or {}
    sb = hstats.get("skyblock") or {}
    bw = hstats.get("bedwars") or {}
    
    masked_name = _mask_username(username)
    display_rank = rank if rank and rank.lower() != "non" else "None"
    if not display_rank.startswith("[") and display_rank != "None":
        display_rank = f"[{display_rank}]"
    elif display_rank == "None":
        display_rank = "[None]"

    width = 850
    height = 420
    
    # 1. Background image
    bg_path = os.path.join(ASSETS_DIR, "background.png")
    if os.path.exists(bg_path):
        try:
            card = Image.open(bg_path).convert("RGBA")
            bw_img, bh_img = card.size
            target_ratio = width / height
            if bw_img / bh_img > target_ratio:
                new_w = int(bh_img * target_ratio)
                left = (bw_img - new_w) // 2
                card = card.crop((left, 0, left + new_w, bh_img))
            else:
                new_h = int(bw_img / target_ratio)
                top = (bh_img - new_h) // 2
                card = card.crop((0, top, bw_img, top + new_h))
            card = card.resize((width, height), Image.Resampling.LANCZOS)
        except Exception:
            card = Image.new("RGBA", (width, height), (13, 20, 30, 255))
    else:
        card = Image.new("RGBA", (width, height), (13, 20, 30, 255))

    # Dark overlay for high contrast & atmospheric depth
    overlay = Image.new("RGBA", (width, height), (7, 14, 23, 150))
    card.alpha_composite(overlay)

    draw = ImageDraw.Draw(card)

    # Rounded outer border
    margin = 12
    cw, ch = width - margin * 2, height - margin * 2
    draw.rounded_rectangle([margin, margin, margin + cw, margin + ch], radius=14, outline=(42, 64, 88, 220), width=2)

    # Fonts
    f_title = _get_font(24, bold=True)
    f_sub = _get_font(11, bold=True)
    f_label = _get_font(9, bold=True)
    f_val = _get_font(15, bold=True)
    f_secu = _get_font(12, bold=True)

    def draw_text_shadow(pos, text, font, fill=(255, 255, 255, 255), shadow=(10, 15, 22, 240), offset=(2, 2)):
        x, y = pos
        draw.text((x + offset[0], y + offset[1]), text, font=font, fill=shadow)
        draw.text((x, y), text, font=font, fill=fill)

    # 2. Header
    title_text = f"{display_rank} {masked_name}"
    draw_text_shadow((32, 24), title_text, f_title, (255, 255, 255, 255))

    sub_text = "hypixel - skyblock - bedwars - duels"
    draw.text((32, 56), sub_text, font=f_sub, fill=(115, 142, 168, 255))

    # 3. Stats Data
    nw_val = simplify(sb.get("networth", 0)) if isinstance(sb.get("networth"), (int, float)) else "0"
    nw_display = f"${nw_val}" if nw_val not in ("0", 0, None) else "0"

    sb_lvl = str(sb.get("level", 0))
    net_lvl = str(hyp.get("level", 0))
    bw_lvl = str(bw.get("level") or bw.get("stars") or 0)
    sw_lvl = str(hyp.get("skywars_level", 0))
    duels_kda = str(hyp.get("duels_kda", 0))
    winstreak = str(hyp.get("winstreak", 0))
    gifted = str(hyp.get("gifted", 0))
    plus_colour = str(hyp.get("plus_color") or "null")
    rank_str = str(hyp.get("rank") or rank or "None")
    if rank_str.lower() == "non":
        rank_str = "None"

    col1_stats = [
        ("NETWORK LVL", net_lvl),
        ("SKYBLOCK LVL", sb_lvl),
        ("SKYWARS LVL", sw_lvl),
        ("WINSTREAK", winstreak),
        ("PLUS COLOUR", plus_colour),
    ]

    col2_stats = [
        ("NETWORTH", nw_display),
        ("BEDWARS", bw_lvl),
        ("DUELS KDA", duels_kda),
        ("GIFTED", gifted),
        ("RANK", rank_str),
    ]

    box_w = 205
    box_h = 42
    start_x = 32
    start_y = 80
    gap_x = 12
    gap_y = 7

    # Col 1
    for i, (label, val) in enumerate(col1_stats):
        bx = start_x
        by = start_y + i * (box_h + gap_y)
        draw.rounded_rectangle([bx, by, bx + box_w, by + box_h], radius=6, fill=(12, 20, 32, 175), outline=(38, 58, 82, 200), width=1)
        draw.text((bx + 10, by + 5), label, font=f_label, fill=(110, 136, 162, 255))
        draw_text_shadow((bx + 10, by + 19), str(val), f_val, (255, 255, 255, 255), offset=(1, 1))

    # Col 2
    for i, (label, val) in enumerate(col2_stats):
        bx = start_x + box_w + gap_x
        by = start_y + i * (box_h + gap_y)
        draw.rounded_rectangle([bx, by, bx + box_w, by + box_h], radius=6, fill=(12, 20, 32, 175), outline=(38, 58, 82, 200), width=1)
        draw.text((bx + 10, by + 5), label, font=f_label, fill=(110, 136, 162, 255))
        draw_text_shadow((bx + 10, by + 19), str(val), f_val, (255, 255, 255, 255), offset=(1, 1))

    # 4. Bottom Capes Container
    cape_count = len(capes) if isinstance(capes, list) else 0
    cape_w = box_w * 2 + gap_x
    cape_y = start_y + 5 * (box_h + gap_y)
    cape_h = 46
    draw.rounded_rectangle([start_x, cape_y, start_x + cape_w, cape_y + cape_h], radius=6, fill=(12, 20, 32, 175), outline=(38, 58, 82, 200), width=1)
    draw.text((start_x + 10, cape_y + 5), f"CAPES ({cape_count})", font=f_label, fill=(110, 136, 162, 255))
    for slot in range(10):
        sx = start_x + 10 + slot * 41
        sy = cape_y + 20
        draw.rounded_rectangle([sx, sy, sx + 34, sy + 20], radius=4, fill=(18, 28, 42, 180), outline=(34, 52, 74, 180), width=1)

    # 5. Right side 3D Skin model & Secured Tag
    if skin_img:
        skin_target_h = 320
        sw, sh = skin_img.size
        aspect = sw / float(sh)
        target_w = int(skin_target_h * aspect)
        resized_skin = skin_img.resize((target_w, skin_target_h), Image.Resampling.LANCZOS)
        skin_x = width - margin - target_w - 45
        skin_y = height - margin - skin_target_h - 15
        card.alpha_composite(resized_skin, (skin_x, skin_y))

        secu_text = f"{display_rank} {masked_name} SECURED"
        draw_text_shadow((skin_x - 15, height - margin - 25), secu_text, f_secu, (255, 255, 255, 255), offset=(1, 1))

    buf = io.BytesIO()
    card.convert("RGB").save(buf, format="PNG", quality=95)
    buf.seek(0)
    return buf

async def generate_hit_card(
    username: str,
    rank: str = "None",
    hstats: dict = None,
    capes: list = None
) -> io.BytesIO:
    skin_img = await _fetch_skin_image(username, height=340)
    return create_hit_card_sync(
        username=username,
        rank=rank,
        hstats=hstats,
        capes=capes,
        skin_img=skin_img
    )
