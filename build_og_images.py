"""
Generate Open Graph (link preview) images for the landing page.
1200x630 — the dimension Facebook/LinkedIn/iMessage/etc. use for previews.

v2 design (May 2026 spruce-up):
- Headline left-aligned, two-line, Barlow Black — "BOYLE HEIGHTS / WAREHOUSE FIRE"
- Directional gradient (left dark, right reveal) instead of full overlay
- Full-width yellow info bar with conversion hook
- Bottom-right logo+domain, bottom-left trust line (asymmetric energy)
- Top-left small "JUNE 2026" date stamp for recency signal

Output:
  - og-en.jpg  (English, root URL)
  - og-es.jpg  (Spanish, /es/ URL)
"""

from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from pathlib import Path

OUT = Path(__file__).parent
PHOTO_PATH = OUT / "hero.jpg"
LOGO_PATH = OUT / "logo.png"

W, H = 1200, 630

COLORS = {
    "bg_dark": (12, 14, 20),
    "yellow": (255, 209, 0),
    "red": (220, 38, 38),
    "white": (255, 255, 255),
    "gold": (198, 162, 92),
    "muted": (174, 180, 192),
    "black": (0, 0, 0),
}

FONT_BARLOW_BLACK = "/Users/hkitsinian/Library/Fonts/Barlow-Black.otf"
FONT_BARLOW_XBOLD = "/Users/hkitsinian/Library/Fonts/Barlow-ExtraBold.otf"
FONT_INTER_XBOLD = "/Users/hkitsinian/Library/Fonts/Inter-ExtraBold.otf"


def f(path, size):
    return ImageFont.truetype(path, size)


def cap_height(draw, font):
    b = draw.textbbox((0, 0), "H", font=font, anchor="lt")
    return b[3] - b[1]


def draw_cap_centered(draw, cx, cy, text, font, fill):
    ch = cap_height(draw, font)
    top_y = cy - ch // 2
    draw.text((cx, top_y), text, font=font, fill=fill, anchor="mt")


def draw_cap_left(draw, x, cy, text, font, fill):
    ch = cap_height(draw, font)
    top_y = cy - ch // 2
    draw.text((x, top_y), text, font=font, fill=fill, anchor="lt")


def cover_fit(src, w, h):
    sw, sh = src.size
    scale = max(w / sw, h / sh)
    new_w, new_h = int(sw * scale), int(sh * scale)
    img = src.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - w) // 2
    top = (new_h - h) // 2
    return img.crop((left, top, left + w, top + h))


def text_width(draw, text, font):
    b = draw.textbbox((0, 0), text, font=font, anchor="lt")
    return b[2] - b[0]


def build_og(headline_lines, yellow_bar_text, trust_line, domain, output_filename,
             date_text="MAY 2026", head_sizes=None, trust_size=24):
    """v2 layout — left-aligned big headline, yellow info bar, asymmetric footer.
    head_sizes: optional list of per-line font sizes (defaults to 130 for all).
    trust_size: footer trust-line font size (default 24)."""
    if head_sizes is None:
        head_sizes = [130] * len(headline_lines)
    assert len(head_sizes) == len(headline_lines), "head_sizes must match headline_lines length"
    # 1) Background photo (brighten + contrast)
    photo = Image.open(PHOTO_PATH).convert("RGB")
    bg = cover_fit(photo, W, H)
    bg = ImageEnhance.Brightness(bg).enhance(1.10)
    bg = ImageEnhance.Contrast(bg).enhance(1.15)
    img = bg.convert("RGBA")

    # 2) Left-side directional gradient (solid dark on left, fades to clear on right)
    # Solid dark in left 50%, fades to transparent by x=85% — keeps photo visible on right
    grad_strip = Image.new("L", (W, 1), 0)
    for x in range(W):
        if x < int(W * 0.50):
            mask = 235  # near-solid dark on left half
        elif x < int(W * 0.85):
            t = (x - int(W * 0.50)) / (int(W * 0.85) - int(W * 0.50))
            mask = int(235 * (1 - t))  # fade through middle
        else:
            mask = 0  # fully transparent on right 15%
        grad_strip.putpixel((x, 0), mask)
    grad_mask = grad_strip.resize((W, H))
    dark_layer = Image.new("RGBA", (W, H), COLORS["bg_dark"] + (255,))
    dark_layer.putalpha(grad_mask)
    img.alpha_composite(dark_layer)

    # 3) Bottom gradient strip for footer legibility (full-width subtle)
    bot_grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bgd = ImageDraw.Draw(bot_grad)
    for y in range(int(H * 0.78), H):
        t = (y - int(H * 0.78)) / (H - int(H * 0.78))
        a = int(t * 180)
        bgd.line([(0, y), (W, y)], fill=(8, 10, 16, a))
    img.alpha_composite(bot_grad)

    draw = ImageDraw.Draw(img)

    # 4) Top-left date stamp (outlined chip, no fill)
    date_font = f(FONT_INTER_XBOLD, 22)
    date_pad_x, date_pad_y = 18, 10
    date_w = text_width(draw, date_text, date_font) + date_pad_x * 2
    date_h = date_font.size + date_pad_y * 2
    date_x, date_y = 55, 50
    draw.rounded_rectangle(
        [date_x, date_y, date_x + date_w, date_y + date_h],
        radius=6, outline=COLORS["white"], width=2,
    )
    draw_cap_centered(draw, date_x + date_w // 2, date_y + date_h // 2, date_text, date_font, COLORS["white"])

    # 5) Headline (left-aligned, Barlow Black, per-line font sizing)
    head_x = 60
    head_start_y = 165  # cap top of first line
    y_cursor = head_start_y
    for i, (line, size) in enumerate(zip(headline_lines, head_sizes)):
        line_font = f(FONT_BARLOW_BLACK, size)
        ch = cap_height(draw, line_font)
        draw_cap_left(draw, head_x, y_cursor + ch // 2, line, line_font, COLORS["white"])
        y_cursor += size  # use size as line spacing

    # 6) Yellow info bar — full-width strip with conversion hook
    bar_h = 78
    bar_y = y_cursor + 30  # 30px breathing room below headline
    draw.rectangle([0, bar_y, W, bar_y + bar_h], fill=COLORS["yellow"])
    bar_font = f(FONT_BARLOW_BLACK, 38)
    # Nudge text up 3px — cap-centered all-caps reads bottom-heavy at default
    draw_cap_centered(draw, W // 2, bar_y + bar_h // 2 - 3, yellow_bar_text, bar_font, COLORS["black"])

    # 7) Bottom row — asymmetric: trust line left, logo+domain right
    footer_y = H - 50  # vertical mid of footer row
    trust_font = f(FONT_BARLOW_XBOLD, trust_size)
    # Drop trust line 4px to baseline-align with logo+domain block on right
    draw_cap_left(draw, 60, footer_y + 4, trust_line, trust_font, COLORS["gold"])

    # Logo + domain bottom-right
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo_h = 52
        logo_w = int(logo.width * (logo_h / logo.height))
        logo = logo.resize((logo_w, logo_h), Image.LANCZOS)
        domain_font = f(FONT_INTER_XBOLD, 22)
        domain_w = text_width(draw, domain, domain_font)
        gap = 18
        right_edge = W - 60
        # Layout: [logo] | [domain] anchored to right
        block_w = logo_w + gap + 2 + gap + domain_w
        start_x = right_edge - block_w
        y_mid = footer_y
        img.paste(logo, (start_x, y_mid - logo_h // 2), logo)
        # Gold divider
        div_x = start_x + logo_w + gap
        draw.line(
            [(div_x, y_mid - logo_h // 2 + 6), (div_x, y_mid + logo_h // 2 - 6)],
            fill=COLORS["gold"], width=2,
        )
        # Domain in WHITE (not muted — better legibility at thumbnail)
        draw.text(
            (div_x + gap, y_mid), domain,
            font=domain_font, fill=COLORS["white"], anchor="lm",
        )
    except Exception as e:
        print(f"  logo render skipped: {e}")

    out_path = OUT / output_filename
    img.convert("RGB").save(out_path, "JPEG", quality=88, optimize=True)
    print(f"  Wrote {out_path} ({W}x{H})")


def main():
    print("Building OG images (v2 design)...")

    # English — "WAREHOUSE FIRE" sized down to fit on one line at 1200px width.
    # Trust line lengthened to match the compliant phrasing used sitewide; font dropped to 20pt.
    build_og(
        headline_lines=["BOYLE HEIGHTS", "WAREHOUSE FIRE"],
        head_sizes=[120, 110],
        yellow_bar_text="SHELTER-IN-PLACE?  YOU MAY BE OWED COMPENSATION",
        trust_line="FREE CASE REVIEW · NO ATTORNEYS' FEES UNLESS WE RECOVER",
        trust_size=20,
        domain="lineagefire.com",
        output_filename="og-en.jpg",
        date_text="JUNE 2026",
    )

    # Spanish — line 1 "INCENDIO EN BODEGA" sized down (long), line 2 stays big.
    build_og(
        headline_lines=["INCENDIO EN BODEGA", "BOYLE HEIGHTS"],
        head_sizes=[95, 120],
        yellow_bar_text="¿REFUGIO EN CASA?  PUEDE TENER COMPENSACIÓN",
        trust_line="CONSULTA GRATIS · SIN HONORARIOS A MENOS QUE RECUPEREMOS",
        trust_size=20,
        domain="lineagefire.com/es",
        output_filename="og-es.jpg",
        date_text="JUNIO 2026",
    )


if __name__ == "__main__":
    main()
