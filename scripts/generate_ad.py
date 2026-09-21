from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import json, os, textwrap
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "data" / "hooks.json"
TEMPLATES = ROOT / "assets" / "resume_templates"
OUTPUT = ROOT / "generated_ads"
OUTPUT.mkdir(exist_ok=True)

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def choose_item():
    hooks = json.loads(HOOKS.read_text(encoding="utf-8"))
    day = date.today().toordinal()
    item = hooks[day % len(hooks)]
    templates = sorted(TEMPLATES.glob("*.png"))
    template = templates[day % len(templates)]
    return item, template

def make_ad(item, template, output_file):
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    bold = ImageFont.truetype(FONT_BOLD, 62)
    body = ImageFont.truetype(FONT_REG, 30)
    small = ImageFont.truetype(FONT_REG, 24)
    cta = ImageFont.truetype(FONT_BOLD, 32)

    d.text((60, 45), "WORKS LAB", font=ImageFont.truetype(FONT_BOLD, 30), fill=(20,30,50))
    d.text((60, 92), "ATS RESUME TEMPLATES", font=small, fill=(70,80,100))
    d.line((60, 135, 1020, 135), fill=(220,225,232), width=3)

    hook = item["hook"]
    sub = item["sub"]
    d.multiline_text((60, 165), textwrap.fill(hook, width=24), font=bold,
                     fill=(15,24,38), spacing=8)
    d.multiline_text((60, 340), textwrap.fill(sub, width=46), font=body,
                     fill=(65,75,90), spacing=6)

    t = Image.open(template).convert("RGB")
    t.thumbnail((720, 440))
    x = (W - t.width) // 2
    y = 485
    shadow = Image.new("RGBA", (t.width+40, t.height+40), (0,0,0,0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((18,18,t.width+20,t.height+20), radius=18, fill=(0,0,0,45))
    shadow = shadow.filter(ImageFilter.GaussianBlur(8))
    img.paste(shadow.convert("RGB"), (x-20,y-20))
    img.paste(t, (x,y))

    d.rounded_rectangle((60,955,1020,1030), radius=22, fill=(20,92,230))
    d.text((90,973), "Professional • Easy to Edit • ATS-Friendly", font=cta, fill="white")
    d.text((60,1040), "resume.workslab.in  •  Only ₹149", font=small, fill=(20,30,50))

    img.save(output_file, quality=95)

if __name__ == "__main__":
    item, template = choose_item()
    output = OUTPUT / f"daily-{date.today().isoformat()}.jpg"
    make_ad(item, template, output)
    print(json.dumps({"hook_id": item["id"], "hook": item["hook"], "image": str(output)}, ensure_ascii=False))
