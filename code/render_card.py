# render_card.py
"""Stage 5: Turn validated text into a finished square image card."""

from __future__ import annotations

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


def _fit_text(
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
    max_lines: int = 12,
) -> str:
    """
    Word-wrap so the text fits inside max_width and does not exceed max_lines.
    Truncates with an ellipsis if still too long.
    """
    # Approximate characters per line from a sample measurement
    sample = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    bbox = font.getbbox(sample)
    avg_char = (bbox[2] - bbox[0]) / len(sample) if bbox else 20
    chars_per_line = max(10, int(max_width / avg_char))

    wrapped = textwrap.fill(text, width=chars_per_line)
    lines = wrapped.splitlines()
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        # Ensure the last line ends with an ellipsis
        last = lines[-1]
        if len(last) > 3:
            lines[-1] = last[:-3].rstrip() + "…"
        else:
            lines[-1] = "…"
    return "\n".join(lines)


def render_card(
    headline: str,
    source_name: str,
    output_path: str = "output_card.png",
) -> str:
    """
    Render a dark square content card (1080×1080).

    Presentation only — never alters the wording beyond visual wrapping
    and optional ellipsis when the text is extremely long.
    Returns the path to the saved image.
    """
    width, height = 1080, 1080
    margin = 80
    bg_color = (18, 18, 20)
    text_color = (240, 240, 240)
    accent_color = (110, 200, 255)

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Adaptive font size: start large, shrink if the text is very long
    base_size = 58
    if len(headline) > 220:
        base_size = 48
    if len(headline) > 360:
        base_size = 40

    headline_font = _load_font(base_size, bold=True)
    source_font = _load_font(32, bold=False)

    usable_width = width - 2 * margin
    max_text_height = 520  # leave room for the source footer

    fitted = _fit_text(headline, headline_font, usable_width, max_lines=12)

    # Measure the block so we can vertically centre it in the upper area
    bbox = draw.multiline_textbbox((0, 0), fitted, font=headline_font, spacing=18)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # Centre horizontally; place vertically in the middle of the upper band
    x = margin + max(0, (usable_width - text_w) // 2)
    # Upper band is roughly from y=120 to y=780
    upper_band_top = 140
    upper_band_height = 640
    y = upper_band_top + max(0, (upper_band_height - text_h) // 2)

    # Clamp so we never collide with the footer
    y = min(y, height - 220 - text_h)

    draw.multiline_text(
        (x, y),
        fitted,
        font=headline_font,
        fill=text_color,
        spacing=18,
        align="left",
    )

    # Footer accent bar + source label
    draw.rectangle([(margin, 880), (margin + 120, 886)], fill=accent_color)
    draw.text(
        (margin, 920),
        f"Source: {source_name}",
        font=source_font,
        fill=accent_color,
    )

    img.save(output_path)
    return output_path
