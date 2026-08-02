# render_card.py
"""Stage 5: Turn validated text into a finished square image card."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import textwrap


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Try common system font paths; fall back to default."""
    candidates = [
        # Linux (Raspberry Pi / Debian / Ubuntu)
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        # macOS
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        # Windows
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def render_card(
    headline: str,
    source_name: str,
    output_path: str = "output_card.png",
) -> str:
    """
    Render a dark square content card (1080×1080).

    Presentation only — never alters the wording.
    Returns the path to the saved image.
    """
    width, height = 1080, 1080
    bg_color = (18, 18, 20)
    text_color = (240, 240, 240)
    accent_color = (110, 200, 255)

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    headline_font = _load_font(58, bold=True)
    source_font = _load_font(32, bold=False)

    # Strip any remaining [citations] for the visual card if desired;
    # here we keep the full validated sentence as-is.
    wrapped = textwrap.fill(headline, width=24)
    draw.multiline_text(
        (80, 320),
        wrapped,
        font=headline_font,
        fill=text_color,
        spacing=18,
    )

    draw.rectangle([(80, 880), (200, 886)], fill=accent_color)
    draw.text(
        (80, 920),
        f"Source: {source_name}",
        font=source_font,
        fill=accent_color,
    )

    img.save(output_path)
    return output_path