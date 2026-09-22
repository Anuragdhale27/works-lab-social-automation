from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json

from generate_ad import THEMES, normalize, render

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "data" / "hooks.json"
DESIGNS = ROOT / "data" / "designs.json"
TEMPLATES = ROOT / "assets" / "resume_templates"
OUT = ROOT / "preview"
OUT.mkdir(exist_ok=True)

items = json.loads(HOOKS.read_text(encoding="utf-8"))
cfg = json.loads(DESIGNS.read_text(encoding="utf-8"))
templates = sorted(TEMPLATES.glob("*.png"))

if not items: raise ValueError("No content entries found.")
if not templates: raise FileNotFoundError("No resume templates found.")

previews = []
for i,name in enumerate(cfg["rotation"]):
    item = normalize(items[i % len(items)])
    template = templates[(i * 2) % len(templates)]
    path = OUT / f"theme-{i+1:02d}-{name}.jpg"
    render(item, template, name).save(path, quality=95, optimize=True)
    previews.append((path,name,item["hook"]))

thumb_w=360
thumb_h=360
label_h=58
cols=3
rows=(len(previews)+cols-1)//cols
sheet=Image.new("RGB",(cols*thumb_w,rows*(thumb_h+label_h)),"white")
draw=ImageDraw.Draw(sheet)
font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",16)
small=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",12)

for i,(path,name,hook) in enumerate(previews):
    im=Image.open(path).convert("RGB")
    im.thumbnail((thumb_w-8,thumb_h-8),Image.Resampling.LANCZOS)
    x=(i%cols)*thumb_w
    y=(i//cols)*(thumb_h+label_h)
    sheet.paste(im,(x+(thumb_w-im.width)//2,y+(thumb_h-im.height)//2))
    draw.text((x+10,y+thumb_h+8),name.upper(),font=font,fill=(20,20,25))
    short=hook if len(hook)<=42 else hook[:39]+"..."
    draw.text((x+10,y+thumb_h+31),short,font=small,fill=(90,90,96))

sheet.save(OUT/"design-v2-contact-sheet.jpg",quality=95,optimize=True)
print(f"Created {len(previews)} full-size theme previews and contact sheet.")
