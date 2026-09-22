from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import json, textwrap, math
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "data" / "hooks.json"
DESIGNS = ROOT / "data" / "designs.json"
TEMPLATES = ROOT / "assets" / "resume_templates"
OUT = ROOT / "generated_ads"
OUT.mkdir(exist_ok=True)

W = H = 1080
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def F(path, size):
    return ImageFont.truetype(path, size)


def wrap_fit(draw, text, max_w, max_h, start, min_size, bold=False, chars=24):
    path = BOLD if bold else REG
    for size in range(start, min_size - 1, -2):
        f = F(path, size)
        txt = textwrap.fill(" ".join(text.split()), width=chars)
        bb = draw.multiline_textbbox((0, 0), txt, font=f, spacing=7)
        if bb[2] - bb[0] <= max_w and bb[3] - bb[1] <= max_h:
            return f, txt
        chars += 1
    f = F(path, min_size)
    return f, textwrap.fill(" ".join(text.split()), width=chars)


def rr(d, box, radius, fill, outline=None, width=1):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def gradient(a, b):
    img = Image.new("RGB", (W, H))
    p = img.load()
    for y in range(H):
        t = y / (H - 1)
        c = tuple(int(a[i]*(1-t) + b[i]*t) for i in range(3))
        for x in range(W):
            p[x, y] = c
    return img


def make_bg(name):
    if name == "sunset":
        img = gradient((255, 201, 154), (120, 70, 180))
        d = ImageDraw.Draw(img, "RGBA")
        d.ellipse((-160, -130, 430, 460), fill=(255, 255, 255, 55))
        d.ellipse((770, 690, 1220, 1140), fill=(255, 80, 140, 55))
        return img
    if name == "midnight":
        img = Image.new("RGB", (W, H), (14, 18, 28))
        d = ImageDraw.Draw(img)
        for x in range(0, W, 60): d.line((x,0,x,H), fill=(32,40,56))
        for y in range(0, H, 60): d.line((0,y,W,y), fill=(32,40,56))
        d.ellipse((760,-120,1220,340), fill=(44,117,255))
        return img
    if name == "paper":
        img = Image.new("RGB", (W, H), (248, 246, 238))
        d = ImageDraw.Draw(img)
        for y in range(36, H, 48):
            for x in range(36, W, 48): d.ellipse((x,y,x+3,y+3), fill=(217,211,199))
        return img
    if name == "mint":
        img = gradient((232, 250, 244), (182, 218, 255))
        d = ImageDraw.Draw(img, "RGBA")
        d.ellipse((-80, 720, 420, 1200), fill=(0, 150, 120, 35))
        d.ellipse((720, -100, 1180, 360), fill=(88, 128, 255, 45))
        return img
    if name == "blocks":
        img = Image.new("RGB", (W, H), (246, 241, 232))
        d = ImageDraw.Draw(img)
        d.rectangle((0,0,410,330), fill=(30,38,65))
        d.polygon([(740,0),(1080,0),(1080,470),(930,330)], fill=(247,103,119))
        d.polygon([(0,820),(260,690),(500,1080),(0,1080)], fill=(105,83,218))
        return img
    if name == "mono":
        img = Image.new("RGB", (W, H), (239,239,235))
        d = ImageDraw.Draw(img)
        d.rectangle((0,0,W,190), fill=(20,20,23))
        d.rectangle((910,0,W,H), fill=(226,226,218))
        for y in range(250,1000,90): d.line((70,y,780,y), fill=(210,210,204))
        return img
    return Image.new("RGB", (W, H), "white")


def logo(d, dark):
    fg = "white" if dark else (20,26,38)
    muted = (200,205,216) if dark else (105,109,120)
    d.text((60,40), "WORKS LAB", font=F(BOLD,28), fill=fg)
    d.text((60,76), "RESUME TEMPLATES", font=F(REG,19), fill=muted)


def price(d, x, y, dark):
    rr(d, (x,y,x+176,y+60), 28, "white" if dark else (20,26,38))
    d.text((x+27,y+15), "ONLY ₹149", font=F(BOLD,23), fill=(20,26,38) if dark else "white")


def resume(base, path, box, angle=0):
    t = Image.open(path).convert("RGBA")
    mw, mh = box[2]-box[0], box[3]-box[1]
    t.thumbnail((mw-50, mh-50), Image.Resampling.LANCZOS)
    card = Image.new("RGBA", (t.width+50, t.height+50), (0,0,0,0))
    cd = ImageDraw.Draw(card)
    rr(cd, (10,10,t.width+40,t.height+40), 22, (0,0,0,55))
    card = card.filter(ImageFilter.GaussianBlur(10))
    sharp = Image.new("RGBA", (t.width+50,t.height+50), (0,0,0,0))
    sd = ImageDraw.Draw(sharp)
    rr(sd, (10,10,t.width+40,t.height+40), 22, (255,255,255,245))
    sharp.alpha_composite(t, (25,25))
    out = Image.new("RGBA", card.size, (0,0,0,0))
    out.alpha_composite(card)
    out.alpha_composite(sharp)
    if angle: out = out.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
    x = box[0] + (mw-out.width)//2
    y = box[1] + (mh-out.height)//2
    base.alpha_composite(out, (x,y))


def copy_block(d, item, area, dark, badge=None, center=False):
    x1,y1,x2,y2 = area
    fg = "white" if dark else (18,24,36)
    muted = (205,211,222) if dark else (91,97,108)
    accent = (255,92,145) if dark else (34,102,232)
    if badge:
        rr(d, (x1,y1,x1+230,y1+40), 20, accent)
        d.text((x1+18,y1+9), badge, font=F(BOLD,16), fill="white")
        y1 += 58
    hf, ht = wrap_fit(d, item["hook"], x2-x1, 230, 64, 40, True, 22)
    bf, bt = wrap_fit(d, item["body"], x2-x1, 125, 29, 20, False, 42)
    anchor = "mm" if center else "la"
    hx = (x1+x2)//2 if center else x1
    d.multiline_text((hx,y1), ht, font=hf, fill=fg, spacing=8, align="center" if center else "left")
    h = d.multiline_textbbox((0,0), ht, font=hf, spacing=8)[3]
    by = y1 + h + 24
    d.multiline_text((hx,by), bt, font=bf, fill=muted, spacing=6, align="center" if center else "left")
    return accent


def value_box(d, value, box, dark, accent):
    x1,y1,x2,y2 = box
    bg = (255,255,255,28) if dark else (255,255,255,225)
    fg = "white" if dark else (25,31,43)
    rr(d, box, 24, bg)
    d.text((x1+22,y1+16), "WHAT YOU GET", font=F(BOLD,15), fill=accent)
    vf, vt = wrap_fit(d, value, x2-x1-44, y2-y1-55, 24, 18, False, 35)
    d.multiline_text((x1+22,y1+48), vt, font=vf, fill=fg, spacing=7)


def cta(d, text, box, accent):
    rr(d, box, 26, accent)
    f, txt = wrap_fit(d, text, box[2]-box[0]-40, box[3]-box[1]-16, 24, 18, True, 32)
    bb = d.multiline_textbbox((0,0), txt, font=f, spacing=4)
    tw, th = bb[2]-bb[0], bb[3]-bb[1]
    d.multiline_text(((box[0]+box[2]-tw)//2,(box[1]+box[3]-th)//2), txt, font=f, fill="white", spacing=4, align="center")


def make_ad(item, template, bg_name, layout_name, out):
    img = make_bg(bg_name).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    dark = bg_name in {"midnight","sunset","mono"}
    fg = "white" if dark else (18,24,36)
    muted = (205,211,222) if dark else (90,97,109)
    accent = (255,92,145) if bg_name in {"midnight","sunset"} else (34,102,232)

    logo(d, dark)

    if layout_name == "editorial":
        copy_block(d,item,(60,155,560,620),dark,"RESUME UPGRADE")
        value_box(d,item["value"],(60,665,560,815),dark,accent)
        cta(d,item["cta"],(60,845,560,915),accent)
        price(d,60,940,dark)
        resume(img,template,(610,145,1020,930),-3)
    elif layout_name == "split":
        rr(d,(55,140,1025,1010),38,(255,255,255,235) if not dark else (16,20,29,235))
        copy_block(d,item,(95,175,985,500),dark,"YOUR NEXT RESUME")
        resume(img,template,(160,500,920,885),2)
        value_box(d,item["value"],(95,915,640,990),dark,accent)
        price(d,800,923,dark)
    elif layout_name == "poster":
        d.text((78,150),"01",font=F(BOLD,34),fill=accent)
        copy_block(d,item,(78,205,1000,520),dark)
        resume(img,template,(245,540,835,920),-2)
        cta(d,item["cta"],(78,945,1002,1015),accent)
    elif layout_name == "card":
        rr(d,(60,130,1020,985),42,(255,255,255,235) if not dark else (16,20,29,240))
        resume(img,template,(90,205,590,885),-5)
        copy_block(d,item,(625,200,955,610),dark,"FEATURED TEMPLATE")
        value_box(d,item["value"],(625,640,955,790),dark,accent)
        cta(d,item["cta"],(625,825,955,900),accent)
    elif layout_name == "tip":
        rr(d,(65,135,1015,990),45,(255,255,255,235) if not dark else (16,20,29,240))
        d.ellipse((105,180,205,280),fill=accent)
        d.text((132,199),"01",font=F(BOLD,32),fill="white")
        copy_block(d,item,(240,175,940,520),dark,"RESUME TIP")
        value_box(d,item["value"],(110,560,970,720),dark,accent)
        resume(img,template,(220,705,860,925),2)
        cta(d,item["cta"],(110,935,970,1005),accent)
    elif layout_name == "quote":
        d.text((62,145),"“",font=F(BOLD,150),fill=accent)
        copy_block(d,item,(125,235,920,625),dark,center=True)
        value_box(d,item["value"],(125,680,610,835),dark,accent)
        price(d,125,875,dark)
        resume(img,template,(650,690,1015,1015),4)
    elif layout_name == "product":
        resume(img,template,(110,145,970,585),0)
        hf,ht = wrap_fit(d,item["hook"],900,150,58,38,True,22)
        d.multiline_text((90,610),ht,font=hf,fill=fg,spacing=8)
        bf,bt = wrap_fit(d,item["body"],900,90,27,20,False,46)
        d.multiline_text((90,775),bt,font=bf,fill=muted,spacing=5)
        cta(d,item["cta"],(90,885,990,955),accent)
    else:
        d.line((60,135,1020,135),fill=accent,width=5)
        copy_block(d,item,(60,175,590,620),dark)
        value_box(d,item["value"],(60,680,590,820),dark,accent)
        cta(d,item["cta"],(60,855,590,925),accent)
        resume(img,template,(650,180,1010,885),2)
        price(d,650,915,dark)

    d.text((60,1038),"resume.workslab.in",font=F(REG,20),fill=muted)
    img.convert("RGB").save(out,quality=95,optimize=True)


def choose():
    items = json.loads(HOOKS.read_text(encoding="utf-8"))
    cfg = json.loads(DESIGNS.read_text(encoding="utf-8"))
    n = date.today().toordinal()
    files = sorted(TEMPLATES.glob("*.png"))
    if not items: raise ValueError("No content entries found.")
    if not files: raise FileNotFoundError("No resume templates found.")
    item = items[n % len(items)].copy()
    item["body"] = item.get("body", item.get("sub",""))
    item["value"] = item.get("value","Professional layout • Easy to edit • Reusable")
    item["cta"] = item.get("cta","Get yours — ₹149")
    bg = cfg["backgrounds"][n % len(cfg["backgrounds"])]
    layout = cfg["layouts"][(n*3) % len(cfg["layouts"])]
    template = files[(n*5) % len(files)]
    return item, template, bg, layout


if __name__ == "__main__":
    today = date.today().isoformat()
    item, template, bg, layout = choose()
    image = OUT / f"daily-{today}.jpg"
    make_ad(item,template,bg,layout,image)

    caption = (
        f"🚀 {item['hook']}\n\n"
        f"{item['body']}\n\n"
        f"{item['value']}\n\n"
        f"{item['cta']}\n\n"
        "Get yours:\nhttps://resume.workslab.in\n\n"
        "#resume #resumetips #jobsearch #careertips #atsresume #resumetemplate"
    )

    meta = {
        "date":today, "hook_id":item["id"], "hook":item["hook"],
        "body":item["body"], "value":item["value"], "cta":item["cta"],
        "background":bg, "layout":layout, "template":template.name,
        "image":image.name, "caption":caption
    }
    (OUT / f"daily-{today}.json").write_text(
        json.dumps(meta,ensure_ascii=False,indent=2), encoding="utf-8"
    )
    print(json.dumps(meta,ensure_ascii=False))
