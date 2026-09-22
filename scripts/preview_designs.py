from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json

from generate_ad import make_ad

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "data" / "hooks.json"
DESIGNS = ROOT / "data" / "designs.json"
TEMPLATES = ROOT / "assets" / "resume_templates"
OUT = ROOT / "preview"
OUT.mkdir(exist_ok=True)

items = json.loads(HOOKS.read_text(encoding="utf-8"))
cfg = json.loads(DESIGNS.read_text(encoding="utf-8"))
template = sorted(TEMPLATES.glob("*.png"))[0]
item = items[0]

previews = []

# Compare every layout using one consistent background.
for layout in cfg["layouts"]:
    path = OUT / f"layout-{layout}.jpg"
    make_ad(item, template, "midnight", layout, path)
    previews.append(path)

# Compare every background using one consistent layout.
for bg in cfg["backgrounds"]:
    path = OUT / f"background-{bg}.jpg"
    make_ad(item, template, bg, "editorial", path)
    previews.append(path)

thumb_w, thumb_h = 360, 360
label_h = 42
cols = 3
rows = (len(previews) + cols - 1) // cols
sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + label_h)), "white")
draw = ImageDraw.Draw(sheet)
label_font = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 17
)

for i, path in enumerate(previews):
    img = Image.open(path).convert("RGB")
    img.thumbnail((thumb_w - 12, thumb_h - 12), Image.Resampling.LANCZOS)
    cell = Image.new("RGB", (thumb_w, thumb_h), (242, 242, 242))
    x = (thumb_w - img.width) // 2
    y = (thumb_h - img.height) // 2
    cell.paste(img, (x, y))
    cx = (i % cols) * thumb_w
    cy = (i // cols) * (thumb_h + label_h)
    sheet.paste(cell, (cx, cy))
    name = path.stem.replace("-", " ").upper()
    draw.text((cx + 12, cy + thumb_h + 10), name, fill=(25, 25, 30), font=label_font)

sheet.save(OUT / "design-v2-contact-sheet.jpg", quality=94, optimize=True)
print(f"Created {len(previews)} previews plus contact sheet.")
