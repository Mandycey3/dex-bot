"""Generate Pump.Fun-style token promotion banners for Telegram orders."""

from io import BytesIO
import logging
from pathlib import Path

import httpx
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

logger = logging.getLogger(__name__)

WIDTH = 1200
HEIGHT = 630
PANEL = (700, 96, 1132, 536)
GRID_SIZE = 64

_FONT_PATHS = {
    "regular": (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ),
    "bold": (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    ),
}


def _font(size: int, bold: bool = False):
    for path in _FONT_PATHS["bold" if bold else "regular"]:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def _fit_name_font(draw, name: str):
    for size in range(92, 43, -2):
        font = _font(size, bold=True)
        if draw.textbbox((0, 0), name, font=font)[2] <= 535:
            return font
    return _font(42, bold=True)


def _fit_single_line(draw, text: str, max_width: int, start_size: int):
    for size in range(start_size, 17, -2):
        font = _font(size, bold=True)
        if draw.textbbox((0, 0), text, font=font)[2] <= max_width:
            return font, text

    font = _font(17, bold=True)
    clipped = text
    while len(clipped) > 1 and draw.textbbox((0, 0), f"{clipped}…", font=font)[2] > max_width:
        clipped = clipped[:-1]
    return font, f"{clipped}…"


def _draw_background():
    image = Image.new("RGB", (WIDTH, HEIGHT), (9, 16, 14))

    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    for box, color in (
        ((810, -120, 1280, 350), (55, 190, 112, 115)),
        ((-170, 420, 360, 860), (14, 111, 67, 110)),
        ((980, 390, 1370, 780), (25, 128, 81, 95)),
    ):
        glow_draw.ellipse(box, fill=color)
    glow = glow.filter(ImageFilter.GaussianBlur(46))
    image = Image.alpha_composite(image.convert("RGBA"), glow)

    grid = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    grid_draw = ImageDraw.Draw(grid)
    for x in range(0, WIDTH + GRID_SIZE, GRID_SIZE):
        grid_draw.line((x, 0, x, HEIGHT), fill=(126, 171, 146, 22), width=1)
    for y in range(0, HEIGHT + GRID_SIZE, GRID_SIZE):
        grid_draw.line((0, y, WIDTH, y), fill=(126, 171, 146, 22), width=1)
    return Image.alpha_composite(image, grid)


def _draw_brand(draw):
    # Small mint capsule mark matching the Pump.Fun-style reference branding.
    draw.rounded_rectangle((78, 66, 105, 96), radius=12, fill=(106, 239, 169))
    draw.line((83, 90, 100, 71), fill=(241, 255, 246), width=6)
    draw.text((126, 62), "Pump.Fun", font=_font(29, bold=True), fill=(246, 249, 247))


def _trim_image_whitespace(image: Image.Image) -> Image.Image:
    """Remove large transparent/white margins around a token logo."""
    rgba = image.convert("RGBA")
    alpha_bbox = rgba.getchannel("A").getbbox()
    if alpha_bbox and alpha_bbox != (0, 0, rgba.width, rgba.height):
        rgba = rgba.crop(alpha_bbox)

    rgb = rgba.convert("RGB")
    difference = ImageChops.difference(
        rgb,
        Image.new("RGB", rgb.size, (255, 255, 255)),
    ).convert("L")
    difference = difference.point(lambda value: 255 if value > 18 else 0)
    bbox = difference.getbbox()
    if not bbox:
        return rgba

    content_width = bbox[2] - bbox[0]
    content_height = bbox[3] - bbox[1]
    # Only trim when the image is mostly blank around its artwork.
    if content_width < rgba.width * 0.82 or content_height < rgba.height * 0.82:
        padding = max(10, min(rgba.width, rgba.height) // 18)
        left = max(0, bbox[0] - padding)
        top = max(0, bbox[1] - padding)
        right = min(rgba.width, bbox[2] + padding)
        bottom = min(rgba.height, bbox[3] + padding)
        return rgba.crop((left, top, right, bottom))
    return rgba


async def _paste_token_art(canvas, image_url: str | None, name: str):
    panel_left, panel_top, panel_right, panel_bottom = PANEL
    panel = Image.new("RGBA", (panel_right - panel_left, panel_bottom - panel_top), (250, 251, 249, 255))

    token_image = None
    if image_url:
        try:
            timeout = httpx.Timeout(12.0, connect=5.0)
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=timeout,
            ) as client:
                response = await client.get(image_url)
                response.raise_for_status()
                token_image = Image.open(BytesIO(response.content)).convert("RGBA")
        except (httpx.HTTPError, OSError, ValueError) as error:
            logger.warning("Could not download Pump.fun token image: %s", error)

    if token_image is not None:
        token_image = _trim_image_whitespace(token_image)
        token_image.thumbnail((350, 350), Image.Resampling.LANCZOS)
        x = (panel.width - token_image.width) // 2
        y = (panel.height - token_image.height) // 2
        panel.alpha_composite(token_image, (x, y))
    else:
        token_draw = ImageDraw.Draw(panel)
        center = (panel.width // 2, panel.height // 2)
        token_draw.ellipse(
            (center[0] - 120, center[1] - 120, center[0] + 120, center[1] + 120),
            fill=(28, 145, 86),
        )
        initial = (name.strip() or "T")[0].upper()
        initial_font = _font(150, bold=True)
        bounds = token_draw.textbbox((0, 0), initial, font=initial_font)
        token_draw.text(
            (
                center[0] - (bounds[2] - bounds[0]) // 2,
                center[1] - (bounds[3] - bounds[1]) // 2 - 12,
            ),
            initial,
            font=initial_font,
            fill=(245, 255, 248),
        )

    mask = Image.new("L", panel.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, panel.width - 1, panel.height - 1),
        radius=28,
        fill=255,
    )
    canvas.paste(panel, (panel_left, panel_top), mask)


async def create_pumpfun_banner(
    image_url: str | None,
    project_name: str | None,
    symbol: str | None = None,
) -> BytesIO:
    """Return a 1200x630 PNG banner in a Telegram-uploadable file object."""
    name = (project_name or symbol or "Unknown Token").strip() or "Unknown Token"
    token_symbol = (symbol or "").strip()

    banner = _draw_background()
    draw = ImageDraw.Draw(banner)
    _draw_brand(draw)

    name_font = _fit_name_font(draw, name)
    draw.text((67, 210), name, font=name_font, fill=(250, 253, 251))

    if token_symbol and token_symbol.casefold() != name.casefold():
        symbol_font, symbol_text = _fit_single_line(draw, token_symbol.upper(), 535, 42)
        draw.text((69, 315), symbol_text, font=symbol_font, fill=(236, 246, 240))

    draw.rounded_rectangle((68, 500, 248, 562), radius=31, fill=(105, 239, 169))
    draw.text((96, 514), "BUY", font=_font(25, bold=True), fill=(5, 42, 26))
    draw.ellipse((195, 512, 238, 555), fill=(18, 72, 48))
    draw.line((207, 534, 224, 517), fill=(229, 255, 237), width=4)
    draw.line((224, 517, 224, 529), fill=(229, 255, 237), width=4)
    draw.line((224, 517, 212, 517), fill=(229, 255, 237), width=4)

    await _paste_token_art(banner, image_url, name)

    output = BytesIO()
    banner.convert("RGB").save(output, format="PNG", optimize=True)
    output.seek(0)
    output.name = "pumpfun-token-banner.png"
    return output