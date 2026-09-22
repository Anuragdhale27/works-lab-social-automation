from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import json
import textwrap
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "data" / "hooks.json"
DESIGNS = ROOT / "data" / "designs.json"
TEMPLATES = ROOT / "assets" / "resume_templates"
OUTPUT = ROOT / "generated_ads"
OUTPUT.mkdir(exist_ok=True)

W = H = 1080

# Runner-safe fonts available on Ubuntu GitHub Actions.
FONTS = {
    "sans": {
        "bold": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "regular": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    },
    "serif": {
        "bold": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "regular": "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    },
    "condensed": {
        "bold": "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf",
        "regular": "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf",
    },
}

CONCEPTS = {
    "giant_type": {
        "bg": (12, 16, 27), "accent": (255, 82, 145),
        "ink": (250, 252, 255), "muted": (181, 191, 207),
        "font": "sans",
    },
    "before_after": {
        "bg": (247, 243, 236), "accent": (220, 60, 54),
        "ink": (28, 29, 32), "muted": (95, 90, 84),
        "font": "serif",
    },
    "phone": {
        "bg": (226, 239, 255), "accent": (37, 86, 214),
        "ink": (12, 24, 52), "muted": (78, 94, 118),
        "font": "sans",
    },
    "career_tip": {
        "bg": (229, 248, 239), "accent": (8, 126, 99),
        "ink": (15, 43, 34), "muted": (74, 103, 94),
        "font": "sans",
    },
    "product_hero": {
        "bg": (57, 31, 83), "accent": (255, 174, 73),
        "ink": (255, 249, 240), "muted": (221, 208, 230),
        "font": "sans",
    },
    "chat": {
        "bg": (239, 230, 255), "accent": (116, 65, 236),
        "ink": (31, 19, 55), "muted": (93, 79, 119),
        "font": "sans",
    },
    "sticker": {
        "bg": (199, 244, 82), "accent": (15, 18, 18),
        "ink": (15, 18, 18), "muted": (53, 56, 43),
        "font": "condensed",
    },
    "xray": {
        "bg": (239, 236, 225), "accent": (23, 89, 148),
        "ink": (16, 31, 43), "muted": (75, 91, 101),
        "font": "serif",
    },
    "question": {
        "bg": (28, 28, 30), "accent": (235, 52, 75),
        "ink": (250, 250, 250), "muted": (175, 175, 180),
        "font": "sans",
    },
    "magazine": {
        "bg": (247, 241, 232), "accent": (31, 31, 33),
        "ink": (24, 24, 25), "muted": (91, 88, 83),
        "font": "serif",
    },
}

CONCEPT_IDS = [
    "giant_type", "before_after", "phone", "career_tip", "product_hero",
    "chat", "sticker", "xray", "question", "magazine",
]


def F(theme, size, bold=True):
    return ImageFont.truetype(
        FONTS[theme["font"]]["bold" if bold else "regular"], size
    )


def rr(d, box, radius, fill, outline=None, width=1):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def text_width(draw, text, font):
    b = draw.textbbox((0, 0), text, font=font)
    return b[2] - b[0]


def wrap_pixels(draw, text, f, max_w):
    words = " ".join(str(text or "").split()).split()
    lines = []
    current = ""
    for word in words:
        candidate = word if not current else current + " " + word
        if text_width(draw, candidate, f) <= max_w:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return "\n".join(lines)


def fit(draw, text, max_w, max_h, start, minimum, theme, bold=True, spacing=7):
    for size in range(start, minimum - 1, -2):
        f = F(theme, size, bold)
        wrapped = wrap_pixels(draw, text, f, max_w)
        b = draw.multiline_textbbox((0, 0), wrapped, font=f, spacing=spacing)
        if (b[2] - b[0]) <= max_w and (b[3] - b[1]) <= max_h:
            return f, wrapped
    f = F(theme, minimum, bold)
    return f, wrap_pixels(draw, text, f, max_w)


def multiline_h(draw, text, f, spacing=7):
    b = draw.multiline_textbbox((0, 0), text, font=f, spacing=spacing)
    return b[3] - b[1]


def base_background(theme, variant):
    img = Image.new("RGB", (W, H), theme["bg"])
    d = ImageDraw.Draw(img, "RGBA")

    if theme["font"] == "serif":
        for i in range(8):
            y = 150 + i * 105
            d.line((70, y, 1000, y), fill=(*theme["accent"], 24), width=1)
    else:
        for i in range(9):
            x = 65 + i * 120
            d.line((x, 90, x, 1005), fill=(255, 255, 255, 11), width=1)

    # Variant changes the decorative anchor so repeated concepts don't look identical.
    if variant == 0:
        d.ellipse((790, -120, 1210, 300), fill=(*theme["accent"], 42))
    elif variant == 1:
        d.ellipse((-150, 720, 360, 1210), fill=(*theme["accent"], 34))
        d.polygon([(0, 0), (300, 0), (0, 300)], fill=(255, 255, 255, 14))
    else:
        d.ellipse((-180, -120, 340, 380), fill=(*theme["accent"], 30))
        d.ellipse((780, 760, 1210, 1180), fill=(255, 255, 255, 15))

    return img


def logo(d, theme):
    d.text((58, 38), "WORKS LAB", font=F(theme, 27, True), fill=theme["ink"])
    d.text((58, 72), "RESUME TEMPLATES", font=F(theme, 16, False), fill=theme["muted"])


def price(d, theme, x, y):
    dark = sum(theme["bg"]) < 170
    fill = (255, 255, 255) if dark else theme["ink"]
    fg = theme["ink"] if dark else (255, 255, 255)
    rr(d, (x, y, x + 164, y + 56), 28, fill)
    f = F(theme, 25, True)
    label = "₹149"
    bb = d.textbbox((0, 0), label, font=f)
    tw = bb[2] - bb[0]
    d.text((x + (164 - tw)//2, y + 12), label, font=f, fill=fg)


def draw_cta(d, item, theme, box):
    rr(d, box, 24, theme["accent"])
    max_w = box[2] - box[0] - 36
    max_h = box[3] - box[1] - 10
    f, t = fit(d, item["cta"], max_w, max_h, 24, 17, theme, True, 4)
    b = d.multiline_textbbox((0, 0), t, font=f, spacing=4)
    tw, th = b[2] - b[0], b[3] - b[1]
    d.multiline_text(
        ((box[0] + box[2] - tw) // 2, (box[1] + box[3] - th) // 2 - 2),
        t, font=f, fill="white", spacing=4, align="center"
    )



def draw_generic_resume(base, box, theme):
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1
    card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card, "RGBA")
    rr(cd, (10, 10, w-10, h-10), 18, (255,255,255,245))
    cd.rectangle((28, 32, w-28, 76), fill=(232,232,232,255))
    cd.ellipse((38, 88, 108, 158), fill=(205,205,205,255))
    cd.rectangle((124, 92, w-38, 105), fill=(190,190,190,255))
    cd.rectangle((124, 116, w-85, 127), fill=(215,215,215,255))
    for yy in range(185, h-45, 34):
        cd.rectangle((38, yy, int(w*0.62), yy+9), fill=(215,215,215,255))
        cd.rectangle((int(w*0.67), yy, w-38, yy+9), fill=(226,226,226,255))
    cd.rectangle((38, 170, int(w*0.45), 182), fill=(170,170,170,255))
    out = Image.new("RGBA", base.size, (0,0,0,0))
    shadow = Image.new("RGBA", card.size, (0,0,0,0))
    sd = ImageDraw.Draw(shadow, "RGBA")
    rr(sd, (10,18,w-10,h-10), 18, (0,0,0,70))
    shadow = shadow.filter(ImageFilter.GaussianBlur(9))
    out.alpha_composite(shadow, (x1,y1))
    out.alpha_composite(card, (x1,y1))
    d = ImageDraw.Draw(out, "RGBA")
    d.text((x1+22, y2+6), "BEFORE • GENERIC FORMAT", font=F(theme, 12, True), fill=theme["muted"])
    base.alpha_composite(out)


def resume_card(base, template, box, angle=0, grayscale=False, label=None):
    t = Image.open(template).convert("RGBA")
    if grayscale:
        gray = ImageOps.grayscale(t).convert("RGBA")
        t = gray

    mw, mh = box[2] - box[0], box[3] - box[1]
    t.thumbnail((mw - 34, mh - 54), Image.Resampling.LANCZOS)

    card = Image.new("RGBA", (t.width + 44, t.height + 62), (0, 0, 0, 0))
    shadow = Image.new("RGBA", card.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    rr(sd, (8, 15, t.width + 36, t.height + 45), 20, (0, 0, 0, 95))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))

    cd = ImageDraw.Draw(card)
    rr(cd, (8, 8, t.width + 36, t.height + 44), 20, (255, 255, 255, 250))
    card.alpha_composite(t, (22, 20))

    if label:
        lf = ImageFont.truetype(FONTS["sans"]["bold"], 12)
        cd.text((22, t.height + 23), label, font=lf, fill=(55, 58, 64))

    out = Image.new("RGBA", card.size, (0, 0, 0, 0))
    out.alpha_composite(shadow)
    out.alpha_composite(card)

    if angle:
        out = out.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)

    x = box[0] + max(0, (mw - out.width) // 2)
    y = box[1] + max(0, (mh - out.height) // 2)
    base.paste(out.convert("RGBA"), (x, y), out.convert("RGBA"))


def hook_highlight(d, item, theme, x, y, max_w, max_h, size):
    f, txt = fit(d, item["hook"], max_w, max_h, size, 40, theme, True, 7)
    lines = txt.split("\n")
    yy = y
    for i, line in enumerate(lines):
        b = d.textbbox((0, 0), line, font=f)
        if i == len(lines) - 1:
            d.rounded_rectangle(
                (x - 6, yy + b[3] - 5, x + (b[2] - b[0]) + 10, yy + b[3] + 7),
                radius=8, fill=theme["accent"]
            )
        d.text((x, yy), line, font=f, fill=theme["ink"])
        yy += (b[3] - b[1]) + 9
    return yy


def body_text(d, item, theme, x, y, max_w, max_h):
    f, t = fit(d, item["body"], max_w, max_h, 29, 18, theme, False, 6)
    d.multiline_text((x, y), t, font=f, fill=theme["muted"], spacing=6)
    return y + multiline_h(d, t, f, 6)


def benefit_chips(d, item, theme, x, y, max_w):
    parts = [p.strip() for p in str(item["value"]).split("•") if p.strip()]
    chip_x = x
    chip_y = y
    accent = theme["accent"]

    for part in parts[:3]:
        pf, pt = fit(d, part, min(215, max_w - 30), 32, 18, 13, theme, False, 3)
        tw = text_width(d, pt, pf)
        bw = min(215, tw + 24)
        if chip_x + bw > x + max_w:
            chip_x = x
            chip_y += 41
        rr(
            d, (chip_x, chip_y, chip_x + bw, chip_y + 34), 17,
            (*accent, 35) if sum(theme["bg"]) < 170 else (255, 255, 255, 210)
        )
        d.text((chip_x + 12, chip_y + 8), pt, font=pf, fill=theme["ink"])
        chip_x += bw + 8

    return chip_y + 36


def render(item, template, concept_name, variant=0):
    theme = CONCEPTS[concept_name]
    img = base_background(theme, variant).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    logo(d, theme)

    if concept_name == "giant_type":
        d.text((58, 132), "RESUME PROBLEM", font=F(theme, 15, True), fill=theme["accent"])
        y = hook_highlight(d, item, theme, 58, 168, 510, 300, 78)
        y = body_text(d, item, theme, 58, y + 18, 470, 95)
        benefit_chips(d, item, theme, 58, 575, 485)
        draw_cta(d, item, theme, (58, 845, 545, 918))
        price(d, theme, 58, 940)
        resume_card(img, template, (610, 160, 1030, 930), -6)

    elif concept_name == "before_after":
        d.text((62, 135), "BEFORE → AFTER", font=F(theme, 16, True), fill=theme["accent"])
        hf, ht = fit(d, item["hook"], 930, 150, 60, 38, theme, True, 8)
        d.multiline_text((62, 168), ht, font=hf, fill=theme["ink"], spacing=8)
        draw_generic_resume(img, (78, 370, 475, 820), theme)
        resume_card(img, template, (560, 330, 980, 820), 5, grayscale=False, label="AFTER")
        d.line((480, 575, 575, 575), fill=theme["accent"], width=6)
        d.polygon([(565, 555), (595, 575), (565, 595)], fill=theme["accent"])
        body_text(d, item, theme, 62, 845, 575, 72)
        draw_cta(d, item, theme, (650, 845, 1010, 915))
        price(d, theme, 62, 932)

    elif concept_name == "phone":
        d.text((58, 138), "RESUME PREVIEW", font=F(theme, 15, True), fill=theme["accent"])
        hf, ht = fit(d, item["hook"], 870, 155, 61, 38, theme, True, 7)
        d.multiline_text((58, 170), ht, font=hf, fill=theme["ink"], spacing=8)
        # Phone frame
        rr(d, (180, 400, 635, 940), 46, (15, 22, 42), outline=theme["accent"], width=4)
        rr(d, (205, 438, 610, 904), 26, (245, 247, 250))
        d.ellipse((368, 412, 448, 426), fill=(5, 7, 12))
        resume_card(img, template, (230, 465, 585, 865), 0)
        rr(d, (665, 430, 1005, 915), 30, (255, 255, 255, 200))
        body_text(d, item, theme, 700, 470, 265, 100)
        benefit_chips(d, item, theme, 700, 600, 260)
        draw_cta(d, item, theme, (695, 790, 980, 858))
        price(d, theme, 700, 885)

    elif concept_name == "career_tip":
        d.text((60, 135), "CAREER TIP", font=F(theme, 18, True), fill=theme["accent"])
        d.ellipse((875, 104, 995, 224), fill=theme["accent"])
        d.text((902, 129), "01", font=F(theme, 30, True), fill="white")
        hf, ht = fit(d, item["hook"], 875, 170, 62, 38, theme, True, 7)
        d.multiline_text((60, 178), ht, font=hf, fill=theme["ink"], spacing=8)
        d.line((60, 365, 1020, 365), fill=theme["accent"], width=3)
        body_text(d, item, theme, 60, 397, 515, 110)
        rr(d, (60, 560, 620, 790), 28, (255,255,255,205))
        d.text((88, 588), "QUICK CHECKLIST", font=F(theme, 15, True), fill=theme["accent"])
        parts = [p.strip() for p in str(item["value"]).split("•") if p.strip()]
        for i, part in enumerate(parts[:3]):
            yy = 636 + i * 48
            d.ellipse((90, yy, 116, yy + 26), outline=theme["accent"], width=3)
            d.text((98, yy + 1), "✓", font=F(theme, 16, True), fill=theme["accent"])
            d.text((132, yy), part, font=F(theme, 18, False), fill=theme["ink"])
        resume_card(img, template, (670, 405, 1015, 800), 4)
        draw_cta(d, item, theme, (60, 835, 620, 905))
        price(d, theme, 60, 930)

    elif concept_name == "product_hero":
        # Product-first composition: the actual resume is the hero.
        d.text((62, 132), "WORKS LAB / TEMPLATE 05", font=F(theme, 15, True), fill=theme["accent"])
        hf, ht = fit(d, item["hook"], 920, 145, 62, 38, theme, True, 7)
        d.multiline_text((62, 168), ht, font=hf, fill=theme["ink"], spacing=8)

        # Large centered product with a clean showroom treatment.
        rr(d, (150, 350, 930, 785), 34, (255,255,255,18))
        resume_card(img, template, (190, 350, 890, 780), -1,
                    label="EDITABLE ATS-FRIENDLY RESUME")

        # Feature strip beneath the product.
        parts = [p.strip() for p in str(item["value"]).split("•") if p.strip()][:3]
        chip_x = 70
        for part in parts:
            pf, pt = fit(d, part, 270, 38, 18, 13, theme, True, 4)
            tw = text_width(d, pt, pf)
            bw = min(285, tw + 30)
            rr(d, (chip_x, 805, chip_x + bw, 854), 20, (255,255,255,28))
            d.text((chip_x + 15, 819), pt, font=pf, fill=theme["ink"])
            chip_x += bw + 12

        price(d, theme, 855, 875)
        draw_cta(d, item, theme, (70, 875, 810, 943))
        d.text((70, 970), "See all templates → resume.workslab.in",
               font=F(theme, 18, False), fill=theme["muted"])

    elif concept_name == "chat":
        # Social/chat creative: conversation bubbles + typing indicator + product reveal.
        d.text((62, 132), "WORKS LAB / DMs", font=F(theme, 15, True), fill=theme["accent"])

        # Chat header
        rr(d, (62, 172, 1018, 228), 20, (255,255,255,175))
        d.ellipse((82, 187, 116, 221), fill=theme["accent"])
        d.text((130, 187), "Recruiter", font=F(theme, 18, True), fill=theme["ink"])
        d.text((132, 209), "online", font=F(theme, 11, False), fill=theme["muted"])

        # Recruiter message
        rr(d, (62, 258, 760, 420), 28, (255,255,255,220))
        d.text((92, 282), "RECRUITER", font=F(theme, 12, True), fill=theme["accent"])
        hf, ht = fit(d, item["hook"], 610, 104, 50, 32, theme, True, 6)
        d.multiline_text((92, 318), ht, font=hf, fill=theme["ink"], spacing=6)

        # Applicant response
        rr(d, (330, 452, 1018, 585), 28, theme["accent"])
        d.text((365, 475), "YOU", font=F(theme, 12, True), fill="white")
        bf, bt = fit(d, item["body"], 585, 74, 28, 18, theme, False, 5)
        d.multiline_text((365, 510), bt, font=bf, fill="white", spacing=5)

        # Typing indicator / transition
        for cx in (96, 113, 130):
            d.ellipse((cx, 616, cx+9, 625), fill=theme["muted"])
        d.text((155, 605), "typing…", font=F(theme, 16, False), fill=theme["muted"])

        # Product reveal
        rr(d, (62, 655, 760, 1000), 34, (255,255,255,215))
        d.text((92, 680), "SENDING A BETTER VERSION →", font=F(theme, 13, True), fill=theme["accent"])
        resume_card(img, template, (145, 710, 670, 980), -2,
                    label="WORKS LAB RESUME")

        # Value chips on the side
        parts = [p.strip() for p in str(item["value"]).split("•") if p.strip()][:3]
        chip_y = 680
        for part in parts:
            pf, pt = fit(d, part, 230, 38, 17, 13, theme, True, 3)
            bw = min(240, text_width(d, pt, pf) + 26)
            rr(d, (790, chip_y, 1018, chip_y + 48), 18, (255,255,255,210))
            d.text((805, chip_y + 13), pt, font=pf, fill=theme["ink"])
            chip_y += 61

        draw_cta(d, item, theme, (790, 875, 1018, 943))
        price(d, theme, 790, 958)

    elif concept_name == "sticker":
        d.text((62, 130), "FRESH TEMPLATE ENERGY", font=F(theme, 17, True), fill=theme["accent"])
        # playful sticker elements
        rr(d, (55, 175, 315, 235), 30, (255,255,255,220))
        d.text((80, 193), "FRESHER • JOB SWITCH • RESTART", font=F(theme, 13, True), fill=theme["ink"])
        resume_card(img, template, (250, 285, 800, 785), -8, label="YOUR NEW RESUME")
        for box, text in [
            ((70, 400, 250, 465), "CLEAN"),
            ((805, 310, 1010, 375), "MODERN"),
            ((800, 500, 1020, 570), "EDITABLE"),
        ]:
            rr(d, box, 18, theme["accent"])
            f = F(theme, 18, True)
            d.text((box[0]+16, box[1]+20), text, font=f, fill="white")
        hf, ht = fit(d, item["hook"], 870, 140, 58, 36, theme, True, 7)
        d.multiline_text((65, 800), ht, font=hf, fill=theme["ink"], spacing=7)
        draw_cta(d, item, theme, (65, 925, 600, 992))
        price(d, theme, 820, 925)

    elif concept_name == "xray":
        d.text((62, 134), "RESUME X-RAY", font=F(theme, 16, True), fill=theme["accent"])
        hf, ht = fit(d, item["hook"], 930, 160, 62, 40, theme, True, 7)
        d.multiline_text((62, 170), ht, font=hf, fill=theme["ink"], spacing=8)
        resume_card(img, template, (70, 400, 520, 900), -3)
        # magnifier
        d.ellipse((610, 395, 930, 715), fill=(255,255,255,155), outline=theme["accent"], width=6)
        d.line((845, 630, 990, 790), fill=theme["accent"], width=18)
        d.ellipse((675, 455, 845, 625), outline=theme["accent"], width=3)
        d.text((695, 490), "CLEAR", font=F(theme, 28, True), fill=theme["ink"])
        d.text((695, 538), "STRUCTURE", font=F(theme, 24, True), fill=theme["ink"])
        d.text((695, 585), "EASY TO SCAN", font=F(theme, 18, False), fill=theme["muted"])
        body_text(d, item, theme, 575, 745, 430, 78)
        draw_cta(d, item, theme, (575, 860, 1010, 930))
        price(d, theme, 575, 945)

    elif concept_name == "question":
        d.text((62, 132), "BE HONEST", font=F(theme, 18, True), fill=theme["accent"])
        hf, ht = fit(d, item["hook"], 920, 225, 82, 45, theme, True, 7)
        d.multiline_text((62, 178), ht, font=hf, fill=theme["ink"], spacing=8)
        resume_card(img, template, (330, 430, 760, 735), 1)
        d.text((62, 755), "Would you shortlist this resume?", font=F(theme, 25, True), fill=theme["ink"])
        rr(d, (62, 815, 300, 885), 24, theme["accent"])
        d.text((132, 835), "YES ✓", font=F(theme, 22, True), fill="white")
        rr(d, (320, 815, 605, 885), 24, (255,255,255,35), outline=(255,255,255,100), width=2)
        d.text((365, 835), "NEEDS WORK", font=F(theme, 19, True), fill=theme["ink"])
        draw_cta(d, item, theme, (660, 815, 1010, 885))
        price(d, theme, 62, 915)

    else:  # magazine
        d.text((62, 132), "CAREER / EDITORIAL", font=F(theme, 15, True), fill=theme["accent"])
        hf, ht = fit(d, item["hook"], 920, 225, 73, 44, theme, True, 8)
        d.multiline_text((62, 168), ht, font=hf, fill=theme["ink"], spacing=10)
        d.line((62, 430, 1018, 430), fill=theme["ink"], width=2)
        body_text(d, item, theme, 62, 458, 455, 105)
        resume_card(img, template, (595, 460, 1010, 900), 2)
        benefit_chips(d, item, theme, 62, 590, 470)
        draw_cta(d, item, theme, (62, 840, 520, 912))
        price(d, theme, 62, 930)

    d.text((60, 1037), "resume.workslab.in", font=F(theme, 16, False), fill=theme["muted"])
    return img.convert("RGB")


def normalize(item):
    out = dict(item or {})
    out["hook"] = out.get("hook", "A better resume starts here.")
    out["body"] = out.get("body", out.get("sub", "Start with a clean professional format."))
    out["value"] = out.get("value", "Easy to edit • Clean structure • Professional look")
    out["cta"] = out.get("cta", "Get yours — ₹149")
    return out


def choose():
    items = json.loads(HOOKS.read_text(encoding="utf-8"))
    cfg = json.loads(DESIGNS.read_text(encoding="utf-8"))
    templates = sorted(TEMPLATES.glob("*.png"))

    if not items:
        raise ValueError("No content entries found.")
    if not templates:
        raise FileNotFoundError("No resume templates found.")

    n = date.today().toordinal()
    concept_name = cfg["rotation"][n % len(cfg["rotation"])]
    variant = (n // len(cfg["rotation"])) % 3
    item = normalize(items[n % len(items)])
    template = templates[(n * 7 + variant) % len(templates)]
    return item, template, concept_name, variant


if __name__ == "__main__":
    today = date.today().isoformat()
    item, template, concept_name, variant = choose()

    image_output = OUTPUT / f"daily-{today}.jpg"
    render(item, template, concept_name, variant).save(
        image_output, quality=95, optimize=True
    )

    caption = (
        f"🚀 {item['hook']}\n\n"
        f"{item['body']}\n\n"
        f"{item['value']}\n\n"
        f"{item['cta']}\n\n"
        "Get yours: https://resume.workslab.in\n\n"
        "#resume #resumetips #jobsearch #careertips #atsresume #resumetemplate"
    )

    metadata = {
        "date": today,
        "hook_id": item.get("id", ""),
        "hook": item["hook"],
        "body": item["body"],
        "value": item["value"],
        "cta": item["cta"],
        "concept": concept_name,
        "variant": variant,
        "template": template.name,
        "image": image_output.name,
        "caption": caption,
    }

    (OUTPUT / f"daily-{today}.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(metadata, ensure_ascii=False))
