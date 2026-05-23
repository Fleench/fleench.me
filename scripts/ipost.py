from __future__ import annotations

from datetime import datetime
from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont


CANVAS_SIZE = 1080
BACKGROUND = "black"
FOREGROUND = "white"
TEXT_PADDING = 110
PAGINATION_PADDING_RIGHT = 110
PAGINATION_PADDING_BOTTOM = 130
MAX_FONT_SIZE = 92
MIN_FONT_SIZE = 24
PAGINATION_FONT_SIZE = 42


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def _text_bbox(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int, int, int]:
    return draw.multiline_textbbox((0, 0), text, font=font, spacing=12, align="center")


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    left, _top, right, _bottom = draw.textbbox((0, 0), text, font=font)
    return right - left


def _break_word_to_width(draw: ImageDraw.ImageDraw, word: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    pieces: list[str] = []
    piece = ""
    for char in word:
        candidate = f"{piece}{char}"
        if piece and _text_width(draw, candidate, font) > max_width:
            pieces.append(piece)
            piece = char
        else:
            piece = candidate
    if piece:
        pieces.append(piece)
    return pieces


def _wrap_text_for_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> str:
    wrapped_lines: list[str] = []
    for raw_line in text.splitlines() or [""]:
        if not raw_line.strip():
            wrapped_lines.append("")
            continue

        words = raw_line.split()
        line = ""
        for word in words:
            if _text_width(draw, word, font) > max_width:
                if line:
                    wrapped_lines.append(line)
                    line = ""
                wrapped_lines.extend(_break_word_to_width(draw, word, font, max_width))
                continue

            candidate = word if not line else f"{line} {word}"
            if _text_width(draw, candidate, font) <= max_width:
                line = candidate
                continue

            if line:
                wrapped_lines.append(line)
            line = word

        if line:
            wrapped_lines.append(line)

    return "\n".join(wrapped_lines)


def _fit_text(draw: ImageDraw.ImageDraw, text: str) -> tuple[str, ImageFont.ImageFont]:
    max_width = CANVAS_SIZE - (TEXT_PADDING * 2)
    max_height = CANVAS_SIZE - (TEXT_PADDING * 2) - PAGINATION_PADDING_BOTTOM

    for size in range(MAX_FONT_SIZE, MIN_FONT_SIZE - 1, -2):
        font = _load_font(size)
        wrapped_text = _wrap_text_for_width(draw, text, font, max_width)
        left, top, right, bottom = _text_bbox(draw, wrapped_text, font)
        if right - left <= max_width and bottom - top <= max_height:
            return wrapped_text, font

    font = _load_font(MIN_FONT_SIZE)
    fallback_lines = []
    for line in text.splitlines():
        fallback_lines.extend(wrap(line, width=34, break_long_words=True, break_on_hyphens=False) or [""])
    return "\n".join(fallback_lines), font


def _draw_slide(text: str, current: int, total: int, output_path: Path) -> None:
    image = Image.new("RGB", (CANVAS_SIZE, CANVAS_SIZE), BACKGROUND)
    draw = ImageDraw.Draw(image)

    wrapped_text, font = _fit_text(draw, text)
    left, top, right, bottom = _text_bbox(draw, wrapped_text, font)
    text_width = right - left
    text_height = bottom - top
    text_x = (CANVAS_SIZE - text_width) / 2 - left
    text_y = (CANVAS_SIZE - text_height) / 2 - top
    draw.multiline_text(
        (text_x, text_y),
        wrapped_text,
        font=font,
        fill=FOREGROUND,
        spacing=12,
        align="center",
    )

    counter = f"{current}/{total}"
    counter_font = _load_font(PAGINATION_FONT_SIZE)
    c_left, c_top, c_right, c_bottom = draw.textbbox((0, 0), counter, font=counter_font)
    counter_x = CANVAS_SIZE - PAGINATION_PADDING_RIGHT - (c_right - c_left)
    counter_y = CANVAS_SIZE - PAGINATION_PADDING_BOTTOM - (c_bottom - c_top)
    draw.text((counter_x, counter_y), counter, font=counter_font, fill=FOREGROUND)

    image.save(output_path, "JPEG", quality=95)


def _read_multiline_slide() -> str:
    print("Enter slide text. Submit an empty line when this slide is done.")
    lines: list[str] = []
    while True:
        try:
            line = input("> ")
        except EOFError:
            if lines:
                break
            raise SystemExit("No slide text entered.") from None
        if line == "":
            if lines:
                break
            print("Slide text cannot be empty.")
            continue
        lines.append(line)
    return "\n".join(lines)


def _collect_slides() -> list[str]:
    slides: list[str] = []
    while True:
        slides.append(_read_multiline_slide())
        answer = input("Add another slide? [y/N] ").strip().lower()
        if answer not in {"y", "yes"}:
            return slides


def _output_dir(config: dict) -> Path:
    root = Path(str(config.get("cross_post_dir", "cross-post")))
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = root / f"post_{stamp}"
    suffix = 1
    while output_dir.exists():
        output_dir = root / f"post_{stamp}_{suffix}"
        suffix += 1
    output_dir.mkdir(parents=True, exist_ok=False)
    return output_dir


def main(config: dict) -> None:
    slides = _collect_slides()
    output_dir = _output_dir(config)
    total = len(slides)

    for index, text in enumerate(slides):
        _draw_slide(text, index + 1, total, output_dir / f"{index}.jpg")

    print(f"Saved {total} slide(s) to {output_dir}")
