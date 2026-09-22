from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
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
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def F(path, size):
    return ImageFont.truetype(path, size)


def rr(d, box, radius, fill, outline=None, width=1):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def wrap_to_width(draw, text, font, max_w):
    words = " ".join(text.split()).split(" ")
    lines, current = [], ""
    for word in words:
        candidate = word if not current else current + " " + word
        box = draw.textbbox((0, 0), candidate, font=font)
        if box[2] - box[0] <= max_w:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return "\n".join(lines)


def fit(draw, text, max_w, max_h, start, minimum, bold=False, chars=24):
    path = FONT_BOLD if bold else FONT_REG
    for size in range(start, minimum - 1, -2):
        f = F(path, size)
        wrapped = wrap_to_width(draw, text, f, max_w)
        b = draw.multiline_textbbox((0, 0), wrapped, font=f, spacing=8)
        if b[2] - b[0] <= max_w and b[3] - b[1] <= max_h:
            return f, wrapped
    f = F(path, minimum)
    return f, wrap_to_width(draw, text, f, max_w)


def gradient(top, bottom):
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        t = y / (H - 1)
        c = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        for x in range(W):
            px[x, y] = c
    return img


def background(name):
    if name == "sunset":
        img = gradient((255, 205, 160), (112, 65, 175))
        d = ImageDraw.Draw(img, "RGBA")
        d.ellipse((-170, -150, 430, 450), fill=(255,255,255,55))
        d.ellipse((770, 700, 1220, 1150), fill=(255,80,145,55))
        return img
    if name == "midnight":
        img = Image.new("RGB", (W,H), (12,17,28))
        d = ImageDraw.Draw(img)
        for x in range(0,W,60): d.line((x,0,x,H), fill=(30,39,55))
        for y in range(0,H,60): d.line((0,y,W,y), fill=(30,39,55))
        d.ellipse((760,-120,1220,340), fill=(42,118,255))
        return img
    if name == "paper":
        img = Image.new("RGB", (W,H), (248,246,238))
        d = ImageDraw.Draw(img)
        for y in range(36,H,48):
            for x in range(36,W,48): d.ellipse((x,y,x+3,y+3), fill=(215,210,198))
        return img
    if name == "mint":
        img = gradient((233,250,244), (183,219,255))
        d = ImageDraw.Draw(img,"RGBA")
        d.ellipse((-100,720,420,1220), fill=(0,150,120,35))
        d.ellipse((720,-100,1180,360), fill=(90,125,255,45))
        return img
    if name == "blocks":
        img = Image.new("RGB",(W,H),(246,241,232))
        d = ImageDraw.Draw(img)
        d.rectangle((0,0,410,330), fill=(30,38,65))
        d.polygon([(740,0),(1080,0),(1080,470),(930,330)], fill=(246,102,118))
        d.polygon([(0,820),(260,690),(500,1080),(0,1080)], fill=(105,83,218))
        return img
    if name == "mono":
        img = Image.new("RGB",(W,H),(239,239,235))
        d = ImageDraw.Draw(img)
        d.rectangle((0,0,W,190), fill=(20,20,23))
        d.rectangle((910,0,W,H), fill=(226,226,218))
        for y in range(250,1000,90): d.line((70,y,780,y), fill=(210,210,204))
        return img
    return Image.new("RGB",(W,H),"white")


def logo(d, dark):
    fg = "white" if dark else (20,26,38)
    muted = (198,205,216) if dark else (104,109,120)
    d.text((60,38),"WORKS LAB",font=F(FONT_BOLD,28),fill=fg)
    d.text((60,74),"RESUME TEMPLATES",font=F(FONT_REG,19),fill=muted)


def price(d, x, y, dark):
    rr(d,(x,y,x+178,y+60),28,"white" if dark else (20,26,38))
    d.text((x+27,y+15),"ONLY ₹149",font=F(FONT_BOLD,23),
           fill=(20,26,38) if dark else "white")


def resume_card(base, template, box, angle=0):
    t = Image.open(template).convert("RGBA")
    mw,mh = box[2]-box[0], box[3]-box[1]
    t.thumbnail((mw-40,mh-40),Image.Resampling.LANCZOS)
    card = Image.new("RGBA",(t.width+50,t.height+50),(0,0,0,0))
    shadow = Image.new("RGBA",card.size,(0,0,0,0))
    sd = ImageDraw.Draw(shadow)
    rr(sd,(10,14,t.width+40,t.height+40),22,(0,0,0,65))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    cd = ImageDraw.Draw(card)
    rr(cd,(10,10,t.width+40,t.height+40),22,(255,255,255,248))
    card.alpha_composite(t,(25,25))
    out = Image.new("RGBA",card.size,(0,0,0,0))
    out.alpha_composite(shadow)
    out.alpha_composite(card)
    if angle: out = out.rotate(angle,expand=True,resample=Image.Resampling.BICUBIC)
    x = box[0] + max(0,(mw-out.width)//2)
    y = box[1] + max(0,(mh-out.height)//2)
    base.alpha_composite(out,(x,y))


def copy_block(d,item,box,dark,badge=None):
    x1,y1,x2,y2=box
    fg="white" if dark else (18,24,36)
    muted=(205,211,222) if dark else (90,97,108)
    accent=(255,92,145) if dark else (34,102,232)
    if badge:
        rr(d,(x1,y1,x1+225,y1+40),20,accent)
        d.text((x1+18,y1+9),badge,font=F(FONT_BOLD,16),fill="white")
        y1 += 55
    hf,ht=fit(d,item["hook"],x2-x1,230,62,38,True,22)
    bf,bt=fit(d,item["body"],x2-x1,125,29,20,False,42)
    d.multiline_text((x1,y1),ht,font=hf,fill=fg,spacing=8)
    h=d.multiline_textbbox((0,0),ht,font=hf,spacing=8)[3]
    d.multiline_text((x1,y1+h+22),bt,font=bf,fill=muted,spacing=6)
    return accent


def value_box(d,value,box,dark,accent):
    x1,y1,x2,y2=box
    rr(d,box,22,(255,255,255,30) if dark else (255,255,255,225))
    d.text((x1+22,y1+15),"WHAT YOU GET",font=F(FONT_BOLD,15),fill=accent)
    vf,vt=fit(d,value,x2-x1-44,y2-y1-54,23,18,False,35)
    d.multiline_text((x1+22,y1+47),vt,font=vf,fill="white" if dark else (25,31,43),spacing=7)


def cta(d,text,box,accent):
    rr(d,box,26,accent)
    f,t=fit(d,text,box[2]-box[0]-40,box[3]-box[1]-18,24,18,True,32)
    b=d.multiline_textbbox((0,0),t,font=f,spacing=4)
    tw,th=b[2]-b[0],b[3]-b[1]
    d.multiline_text(((box[0]+box[2]-tw)//2,(box[1]+box[3]-th)//2),t,
                     font=f,fill="white",spacing=4,align="center")


def make_ad(item, template, bg_name, layout_name, output_file):
    img=background(bg_name).convert("RGBA")
    d=ImageDraw.Draw(img,"RGBA")
    dark=bg_name in {"midnight","sunset","mono"}
    fg="white" if dark else (18,24,36)
    muted=(205,211,222) if dark else (90,97,108)
    accent=(255,92,145) if bg_name in {"midnight","sunset"} else (34,102,232)
    logo(d,dark)

    if layout_name=="editorial":
        copy_block(d,item,(60,150,555,610),dark,"RESUME UPGRADE")
        value_box(d,item["value"],(60,655,555,805),dark,accent)
        cta(d,item["cta"],(60,830,555,900),accent)
        price(d,60,925,dark)
        resume_card(img,template,(605,140,1025,925),-3)
    elif layout_name=="split":
        rr(d,(55,135,1025,1005),38,(255,255,255,235) if not dark else (15,19,28,235))
        copy_block(d,item,(95,175,985,495),dark,"YOUR NEXT RESUME")
        resume_card(img,template,(150,495,930,875),2)
        value_box(d,item["value"],(95,900,645,980),dark,accent)
        price(d,805,910,dark)
    elif layout_name=="poster":
        d.text((78,150),"01",font=F(FONT_BOLD,34),fill=accent)
        copy_block(d,item,(78,205,1000,515),dark)
        resume_card(img,template,(245,535,835,915),-2)
        cta(d,item["cta"],(78,940,1002,1010),accent)
    elif layout_name=="card":
        rr(d,(60,130,1020,985),42,(255,255,255,235) if not dark else (16,20,29,240))
        resume_card(img,template,(90,200,590,875),-5)
        copy_block(d,item,(625,195,955,600),dark,"FEATURED TEMPLATE")
        value_box(d,item["value"],(625,630,955,785),dark,accent)
        cta(d,item["cta"],(625,820,955,895),accent)
    elif layout_name=="tip":
        rr(d,(65,135,1015,995),45,(255,255,255,235) if not dark else (16,20,29,240))
        d.ellipse((105,180,205,280),fill=accent)
        d.text((132,199),"01",font=F(FONT_BOLD,32),fill="white")
        copy_block(d,item,(240,175,940,515),dark,"RESUME TIP")
        value_box(d,item["value"],(110,555,970,715),dark,accent)
        resume_card(img,template,(220,700,860,920),2)
        cta(d,item["cta"],(110,935,970,1005),accent)
    elif layout_name=="quote":
        d.text((62,145),"“",font=F(FONT_BOLD,150),fill=accent)
        copy_block(d,item,(125,235,930,620),dark)
        value_box(d,item["value"],(125,675,610,825),dark,accent)
        price(d,125,865,dark)
        resume_card(img,template,(650,680,1015,1015),4)
    elif layout_name=="product":
        resume_card(img,template,(110,145,970,575),0)
        hf,ht=fit(d,item["hook"],900,150,58,38,True,22)
        d.multiline_text((90,600),ht,font=hf,fill=fg,spacing=8)
        bf,bt=fit(d,item["body"],900,85,27,20,False,46)
        d.multiline_text((90,765),bt,font=bf,fill=muted,spacing=5)
        cta(d,item["cta"],(90,875,990,945),accent)
    else:
        d.line((60,135,1020,135),fill=accent,width=5)
        copy_block(d,item,(60,175,590,610),dark)
        value_box(d,item["value"],(60,670,590,810),dark,accent)
        cta(d,item["cta"],(60,845,590,915),accent)
        resume_card(img,template,(650,180,1010,885),2)
        price(d,650,910,dark)

    d.text((60,1038),"resume.workslab.in",font=F(FONT_REG,20),fill=muted)
    img.convert("RGB").save(output_file,quality=95,optimize=True)


def choose():
    items=json.loads(HOOKS.read_text(encoding="utf-8"))
    cfg=json.loads(DESIGNS.read_text(encoding="utf-8"))
    templates=sorted(TEMPLATES.glob("*.png"))
    if not items: raise ValueError("No content found.")
    if not templates: raise FileNotFoundError("No resume templates found.")
    n=date.today().toordinal()
    item=items[n % len(items)].copy()
    item["body"]=item.get("body",item.get("sub",""))
    item["value"]=item.get("value","Professional layout • Easy to edit • Reusable")
    item["cta"]=item.get("cta","Get yours — ₹149")
    bg=cfg["backgrounds"][n % len(cfg["backgrounds"])]
    layout=cfg["layouts"][(n*3) % len(cfg["layouts"])]
    template=templates[(n*5) % len(templates)]
    return item,template,bg,layout


if __name__=="__main__":
    today=date.today().isoformat()
    item,template,bg,layout=choose()
    image_output=OUTPUT/f"daily-{today}.jpg"
    make_ad(item,template,bg,layout,image_output)

    caption=(
        f"🚀 {item['hook']}\n\n"
        f"{item['body']}\n\n"
        f"{item['value']}\n\n"
        f"{item['cta']}\n\n"
        "Get yours:\nhttps://resume.workslab.in\n\n"
        "#resume #resumetips #jobsearch #careertips #atsresume #resumetemplate"
    )
    metadata={
        "date":today,"hook_id":item["id"],"hook":item["hook"],
        "body":item["body"],"value":item["value"],"cta":item["cta"],
        "background":bg,"layout":layout,"template":template.name,
        "image":image_output.name,"caption":caption
    }
    (OUTPUT/f"daily-{today}.json").write_text(
        json.dumps(metadata,ensure_ascii=False,indent=2),encoding="utf-8"
    )
    print(json.dumps(metadata,ensure_ascii=False))
