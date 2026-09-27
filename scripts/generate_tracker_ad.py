from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "data" / "tracker_hooks.json"
OUTPUT = ROOT / "generated_ads"
OUTPUT.mkdir(exist_ok=True)

W = H = 1080
CREAM = (255, 250, 238)
BROWN = (67, 35, 5)
BROWN_2 = (126, 92, 51)
ORANGE = (239, 126, 0)
ORANGE_2 = (246, 164, 82)
GREEN = (35, 128, 67)
GRID = (238, 217, 176)
WHITE = (255, 255, 255)
MUTED = (151, 119, 78)

FONTS = {
    "serif": {
        "bold": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "regular": "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    },
    "sans": {
        "bold": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "regular": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    },
}


def font(kind, size, bold=True):
    return ImageFont.truetype(FONTS[kind]["bold" if bold else "regular"], size)


def text_width(draw, text, f):
    b = draw.textbbox((0, 0), text, font=f)
    return b[2] - b[0]


def wrap(draw, text, f, max_w):
    words = " ".join(str(text or "").split()).split()
    lines, current = [], ""
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


def fit(draw, text, max_w, max_h, start, minimum, kind="serif", bold=True, spacing=8):
    for size in range(start, minimum - 1, -2):
        f = font(kind, size, bold)
        t = wrap(draw, text, f, max_w)
        b = draw.multiline_textbbox((0, 0), t, font=f, spacing=spacing)
        if b[2] - b[0] <= max_w and b[3] - b[1] <= max_h:
            return f, t
    f = font(kind, minimum, bold)
    return f, wrap(draw, text, f, max_w)


def rr(draw, box, radius=0, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def dotted_background():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    for y in range(34, H, 62):
        for x in range(30, W, 62):
            d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=GRID)
    return img


def header(d):
    d.rectangle((0, 0, W, 104), fill=CREAM)
    d.line((0, 103, W, 103), fill=BROWN, width=2)
    d.rectangle((42, 42, 68, 68), fill=ORANGE)
    d.text((88, 34), "Works Lab", font=font("sans", 28, True), fill=BROWN)
    rr(d, (820, 24, 1025, 82), 0, fill=BROWN)
    d.text((850, 37), "G  Sign in", font=font("sans", 24, True), fill=WHITE)


def footer(d):
    d.text((62, 1018), "tracker.workslab.in", font=font("sans", 18, False), fill=MUTED)


def section_label(d, text, x=62, y=132):
    d.line((x, y + 10, x + 62, y + 10), fill=ORANGE, width=3)
    d.text((x + 82, y), text, font=font("sans", 17, False), fill=MUTED)


def cta(d, text, box):
    rr(d, box, 0, fill=ORANGE)
    f, t = fit(d, text, box[2] - box[0] - 34, box[3] - box[1] - 14, 25, 17, "sans", True, 4)
    b = d.multiline_textbbox((0, 0), t, font=f, spacing=4)
    d.multiline_text(
        ((box[0] + box[2] - (b[2] - b[0])) // 2, (box[1] + box[3] - (b[3] - b[1])) // 2 - 2),
        t, font=f, fill=WHITE, spacing=4, align="center"
    )


def draw_stat(d, x, y, label, value, accent=BROWN, w=300):
    rr(d, (x, y, x + w, y + 112), 0, fill=CREAM, outline=BROWN, width=2)
    d.text((x + 22, y + 17), label, font=font("sans", 16, False), fill=BROWN_2)
    d.text((x + 22, y + 49), value, font=font("serif", 31, True), fill=accent)


def draw_donut(d, cx, cy, r, pct, label):
    d.arc((cx-r, cy-r, cx+r, cy+r), 0, 360, fill=GRID, width=30)
    d.arc((cx-r, cy-r, cx+r, cy+r), -90, -90 + int(360*pct), fill=ORANGE, width=30)
    d.ellipse((cx-r+25, cy-r+25, cx+r-25, cy+r-25), fill=CREAM)
    d.text((cx-35, cy-16), f"{int(pct*100)}%", font=font("serif", 25, True), fill=BROWN)
    d.text((cx-r, cy+r+20), label, font=font("sans", 16, False), fill=BROWN_2)


def draw_tracker_card(d, x, y, w=900, h=420, variant=0):
    rr(d, (x, y, x+w, y+h), 0, fill=CREAM, outline=BROWN, width=2)
    d.text((x+32, y+28), "This month at a glance", font=font("sans", 22, True), fill=BROWN)
    draw_stat(d, x+32, y+82, "In-hand income", "₹85,000", BROWN)
    draw_stat(d, x+354, y+82, "Fixed outgo", "₹38,500", BROWN)
    draw_stat(d, x+32, y+212, "Variable spend", "₹24,800", BROWN)
    draw_stat(d, x+354, y+212, "Saved", "₹21,700", GREEN)
    draw_donut(d, x+760, y+154, 75, 0.26, "Savings rate")
    d.line((x+32, y+362, x+w-32, y+362), fill=GRID, width=2)
    insights = [
        "Great job — you saved 26% of your income this month.",
        "EMIs are visible. Now you can see their share of income.",
        "One screen. Every rupee explained.",
    ]
    d.text((x+32, y+380), insights[variant % 3], font=font("sans", 16, False), fill=BROWN_2)


def draw_breakdown(d, x, y, w=900, h=400):
    rr(d, (x, y, x+w, y+h), 0, fill=CREAM, outline=BROWN, width=2)
    d.text((x+32, y+28), "Expenses breakdown", font=font("sans", 22, True), fill=BROWN)
    cx, cy, r = x+270, y+220, 120
    segments = [(0.26, BROWN), (0.18, ORANGE), (0.14, BROWN_2), (0.12, ORANGE_2),
                (0.10, MUTED), (0.08, (205, 181, 145)), (0.07, (185, 168, 139)), (0.05, (195, 186, 168))]
    start = -90
    for frac, color in segments:
        end = start + frac * 360
        d.pieslice((cx-r, cy-r, cx+r, cy+r), start, end, fill=color)
        start = end + 1.2
    d.ellipse((cx-67, cy-67, cx+67, cy+67), fill=CREAM)
    labels = ["Rent", "EMI", "SIP", "Groceries", "Food delivery", "Fuel & cab", "Shopping", "Bills & OTT"]
    lx, ly = x+470, y+92
    for i, label in enumerate(labels):
        col = segments[i][1]
        yy = ly + (i % 4) * 62
        xx = lx + (i // 4) * 190
        d.rectangle((xx, yy, xx+14, yy+14), fill=col)
        d.text((xx+24, yy-3), label, font=font("sans", 14, False), fill=BROWN_2)


def draw_goal(d, x, y, w=900, h=310):
    rr(d, (x, y, x+w, y+h), 0, fill=CREAM, outline=BROWN, width=2)
    d.text((x+32, y+28), "Goal setter", font=font("serif", 30, True), fill=BROWN)
    d.text((x+32, y+82), "House down payment", font=font("sans", 18, False), fill=MUTED)
    d.text((x+32, y+115), "₹10,00,000", font=font("serif", 36, True), fill=BROWN)
    d.text((x+32, y+176), "Saved  ₹2,50,000", font=font("sans", 18, False), fill=BROWN_2)
    d.rectangle((x+32, y+220, x+w-32, y+244), fill=GRID)
    d.rectangle((x+32, y+220, x+32+(w-64)*0.25, y+244), fill=ORANGE)
    d.text((x+32, y+258), "25% complete", font=font("sans", 15, True), fill=GREEN)


def normalize(item):
    out = dict(item or {})
    out["hook"] = out.get("hook", "Know where your salary goes.")
    out["body"] = out.get("body", "Track income, spending and savings in one place.")
    out["value"] = out.get("value", "Salary • Expenses • Savings")
    out["cta"] = out.get("cta", "Start tracking →")
    return out


def render(item, concept, variant):
    img = dotted_background()
    d = ImageDraw.Draw(img)
    header(d)

    if concept == "hero":
        section_label(d, "Salary & budget tracker · Made for India")
        f, t = fit(d, item["hook"], 900, 180, 66, 42, "serif", True, 9)
        d.multiline_text((62, 170), t, font=f, fill=BROWN, spacing=9)
        bf, bt = fit(d, item["body"], 880, 130, 27, 19, "sans", False, 7)
        d.multiline_text((62, 390), bt, font=bf, fill=BROWN_2, spacing=7)
        cta(d, item["cta"], (62, 555, 520, 625))
        draw_tracker_card(d, 62, 680, 900, 300, variant)
    elif concept == "snapshot":
        section_label(d, "What you see every month")
        f, t = fit(d, item["hook"], 900, 160, 58, 38, "serif", True, 8)
        d.multiline_text((62, 172), t, font=f, fill=BROWN, spacing=8)
        draw_tracker_card(d, 62, 390, 900, 420, variant)
        bf, bt = fit(d, item["body"], 640, 90, 21, 16, "sans", False, 5)
        d.multiline_text((62, 835), bt, font=bf, fill=BROWN_2, spacing=5)
        cta(d, item["cta"], (710, 842, 962, 910))
    elif concept == "emi":
        section_label(d, "Money check")
        f, t = fit(d, item["hook"], 900, 170, 61, 39, "serif", True, 8)
        d.multiline_text((62, 172), t, font=f, fill=BROWN, spacing=8)
        draw_stat(d, 62, 405, "In-hand income", "₹85,000", BROWN)
        draw_stat(d, 384, 405, "EMI load", "11%", ORANGE)
        draw_stat(d, 706, 405, "Savings rate", "26%", GREEN)
        rr(d, (62, 560, 1018, 750), 0, fill=CREAM, outline=BROWN, width=2)
        d.text((94, 595), "A number you can act on.", font=font("serif", 27, True), fill=BROWN)
        bf, bt = fit(d, item["body"], 850, 82, 22, 17, "sans", False, 5)
        d.multiline_text((94, 650), bt, font=bf, fill=BROWN_2, spacing=5)
        cta(d, item["cta"], (62, 810, 430, 880))
    elif concept == "breakdown":
        section_label(d, "Know the leak")
        f, t = fit(d, item["hook"], 900, 150, 58, 38, "serif", True, 8)
        d.multiline_text((62, 170), t, font=f, fill=BROWN, spacing=8)
        draw_breakdown(d, 62, 360, 900, 430)
        cta(d, item["cta"], (62, 830, 420, 900))
    elif concept == "wedding":
        section_label(d, "Wedding planner")
        f, t = fit(d, item["hook"], 900, 160, 55, 37, "serif", True, 8)
        d.multiline_text((62, 170), t, font=f, fill=BROWN, spacing=8)
        rr(d, (62, 380, 1018, 760), 0, fill=CREAM, outline=BROWN, width=2)
        d.text((94, 414), "Wedding budget", font=font("sans", 21, True), fill=BROWN)
        rows = [("Venue", "₹1,50,000", "₹1,62,000"), ("Catering", "₹1,20,000", "₹1,15,000"),
                ("Outfits", "₹80,000", "₹92,000"), ("Decoration", "₹70,000", "₹66,000")]
        y = 470
        for label, est, actual in rows:
            d.line((94, y+45, 986, y+45), fill=GRID, width=2)
            d.text((94, y), label, font=font("sans", 17, False), fill=BROWN_2)
            d.text((530, y), est, font=font("sans", 17, False), fill=MUTED)
            d.text((760, y), actual, font=font("sans", 17, True), fill=BROWN)
            y += 65
        cta(d, item["cta"], (62, 820, 450, 890))
    elif concept == "trip":
        section_label(d, "Trip planner")
        f, t = fit(d, item["hook"], 900, 160, 57, 37, "serif", True, 8)
        d.multiline_text((62, 170), t, font=f, fill=BROWN, spacing=8)
        rr(d, (62, 385, 1018, 770), 0, fill=CREAM, outline=BROWN, width=2)
        d.text((94, 418), "Trip budget", font=font("serif", 29, True), fill=BROWN)
        # Three cards fit exactly inside the 94–986 content area.
        # 280px cards + 26px gaps = 892px total width.
        draw_stat(d, 94, 480, "Budget", "₹50,000", BROWN, 280)
        draw_stat(d, 400, 480, "Spent", "₹31,400", ORANGE, 280)
        draw_stat(d, 706, 480, "Left", "₹18,600", GREEN, 280)
        d.text((94, 625), "Flights   •   Hotels   •   Food   •   Daily allowance",
               font=font("sans", 17, False), fill=BROWN_2)
        bf, bt = fit(d, item["body"], 850, 70, 19, 15, "sans", False, 4)
        d.multiline_text((94, 680), bt, font=bf, fill=MUTED, spacing=4)
        cta(d, item["cta"], (62, 820, 450, 890))
    elif concept == "goal":
        section_label(d, "Goal setter")
        f, t = fit(d, item["hook"], 900, 160, 60, 39, "serif", True, 8)
        d.multiline_text((62, 170), t, font=f, fill=BROWN, spacing=8)
        draw_goal(d, 62, 385, 900, 310)
        bf, bt = fit(d, item["body"], 600, 78, 19, 15, "sans", False, 4)
        d.multiline_text((62, 735), bt, font=bf, fill=BROWN_2, spacing=4)
        cta(d, item["cta"], (700, 742, 1018, 810))
    elif concept == "privacy":
        section_label(d, "Your data, your Drive")
        f, t = fit(d, item["hook"], 900, 170, 59, 38, "serif", True, 8)
        d.multiline_text((62, 172), t, font=f, fill=BROWN, spacing=8)
        cards = [
            ("01", "Sign in with Google", "Create your Works Lab Budget Ecosystem in your Drive."),
            ("02", "Your Sheet", "Your tracker data lives in your Google account."),
            ("03", "No subscription", "Launch offer: first 100 users free forever."),
        ]
        y = 390
        for num, title, body in cards:
            rr(d, (62, y, 1018, y+135), 0, fill=CREAM, outline=BROWN, width=2)
            d.text((92, y+25), num, font=font("serif", 30, True), fill=ORANGE)
            d.text((170, y+24), title, font=font("sans", 20, True), fill=BROWN)
            bf, bt = fit(d, body, 770, 55, 17, 14, "sans", False, 4)
            d.multiline_text((170, y+62), bt, font=bf, fill=BROWN_2, spacing=4)
            y += 155
        cta(d, item["cta"], (62, 870, 470, 940))
    elif concept == "feature":
        section_label(d, "Product feature")
        f, t = fit(d, item["hook"], 900, 160, 57, 37, "serif", True, 8)
        d.multiline_text((62, 170), t, font=f, fill=BROWN, spacing=8)
        features = [("Quick add", "Bought groceries? Tap + and type the amount."),
                    ("Carry forward", "Load salary, rent, EMIs and budgets into a new month."),
                    ("Archive", "Finish a wedding or trip without losing its history.")]
        y = 390
        for title, body in features:
            rr(d, (62, y, 1018, y+125), 0, fill=CREAM, outline=BROWN, width=2)
            d.text((94, y+25), title, font=font("sans", 20, True), fill=BROWN)
            bf, bt = fit(d, body, 830, 58, 18, 14, "sans", False, 4)
            d.multiline_text((94, y+63), bt, font=bf, fill=BROWN_2, spacing=4)
            y += 145
        cta(d, item["cta"], (62, 850, 470, 920))
    elif concept == "editorial":
        section_label(d, "Plain-Hindi-simple insights")
        f, t = fit(d, item["hook"], 900, 180, 64, 41, "serif", True, 9)
        d.multiline_text((62, 172), t, font=f, fill=BROWN, spacing=9)
        rr(d, (62, 405, 1018, 720), 0, fill=CREAM, outline=BROWN, width=2)
        d.text((94, 438), "This month at a glance", font=font("sans", 22, True), fill=BROWN)
        draw_donut(d, 210, 585, 82, 0.26, "Savings rate")
        draw_donut(d, 470, 585, 82, 0.11, "EMI load")
        draw_donut(d, 730, 585, 82, 0.74, "Income used")
        bf, bt = fit(d, item["body"], 820, 78, 19, 15, "sans", False, 4)
        d.multiline_text((94, 760), bt, font=bf, fill=BROWN_2, spacing=4)
        cta(d, item["cta"], (62, 860, 470, 930))
    else:
        section_label(d, "Before vs after")
        f, t = fit(d, item["hook"], 900, 155, 58, 38, "serif", True, 8)
        d.multiline_text((62, 170), t, font=f, fill=BROWN, spacing=8)
        rr(d, (62, 390, 500, 735), 0, fill=CREAM, outline=BROWN, width=2)
        d.text((92, 420), "BEFORE", font=font("sans", 16, True), fill=MUTED)
        for i, txt in enumerate(["Salary ₹85k", "Rent ₹20k", "EMI ₹9k", "UPI ???", "Savings ???"]):
            d.text((92, 485+i*46), txt, font=font("sans", 19, False), fill=BROWN_2)
        rr(d, (580, 390, 1018, 735), 0, fill=CREAM, outline=ORANGE, width=3)
        d.text((610, 420), "AFTER", font=font("sans", 16, True), fill=ORANGE)
        draw_stat(d, 610, 470, "Income", "₹85k", BROWN)
        draw_stat(d, 610, 600, "Saved", "₹21.7k", GREEN)
        cta(d, item["cta"], (62, 810, 470, 880))
        bf, bt = fit(d, item["body"], 500, 90, 18, 15, "sans", False, 4)
        d.multiline_text((550, 810), bt, font=bf, fill=BROWN_2, spacing=4)

    footer(d)
    return img


CONCEPTS = ["hero", "snapshot", "emi", "breakdown", "wedding", "trip", "goal", "privacy", "feature", "editorial", "compare"]


def choose():
    items = json.loads(HOOKS.read_text(encoding="utf-8"))
    if not items:
        raise ValueError("No tracker content entries found.")
    n = date.today().toordinal()
    item = normalize(items[n % len(items)])
    concept = CONCEPTS[n % len(CONCEPTS)]
    variant = (n // len(CONCEPTS)) % 3
    return item, concept, variant


if __name__ == "__main__":
    today = date.today().isoformat()
    item, concept, variant = choose()
    image_output = OUTPUT / f"tracker-daily-{today}.jpg"
    render(item, concept, variant).save(image_output, quality=95, optimize=True)

    value_lines = item["value"].replace(" • ", "\n✓ ")
    caption = (
        f"💰 {item['hook']}\n\n"
        f"{item['body']}\n\n"
        f"✓ {value_lines}\n\n"
        f"{item['cta']}\n\n"
        "Start tracking: https://tracker.workslab.in\n\n"
        "#workslab #budgettracker #salarytracker #personalfinanceindia #moneymanagement #budgeting #savings #financialplanning"
    )

    metadata = {
        "date": today,
        "product": "tracker",
        "website": "https://tracker.workslab.in",
        "hook_id": item.get("id", ""),
        "hook": item["hook"],
        "body": item["body"],
        "value": item["value"],
        "cta": item["cta"],
        "concept": concept,
        "variant": variant,
        "image": image_output.name,
        "caption": caption,
    }
    (OUTPUT / f"tracker-daily-{today}.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(metadata, ensure_ascii=False))
