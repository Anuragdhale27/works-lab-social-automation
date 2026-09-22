from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import json, textwrap
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "data" / "hooks.json"
DESIGNS = ROOT / "data" / "designs.json"
TEMPLATES = ROOT / "assets" / "resume_templates"
OUTPUT = ROOT / "generated_ads"
OUTPUT.mkdir(exist_ok=True)

W = H = 1080

# Ubuntu GitHub-hosted runners reliably include DejaVu fonts.
# Keep all typography self-contained so the workflow does not depend on
# optional system font packages such as Inter/Lato/Noto.
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

THEMES = {
    "electric": {"bg": (10,15,27), "accent": (255,84,145), "ink": (249,251,255), "muted": (181,191,207), "font": "sans", "layout": "bold_left", "dark": True},
    "cream_red": {"bg": (249,243,232), "accent": (221,61,57), "ink": (28,28,31), "muted": (91,86,80), "font": "serif", "layout": "magazine", "dark": False},
    "neo_mint": {"bg": (226,247,239), "accent": (8,126,99), "ink": (16,39,33), "muted": (72,101,93), "font": "sans", "layout": "sticker", "dark": False},
    "cobalt": {"bg": (231,239,255), "accent": (33,84,220), "ink": (12,22,48), "muted": (71,86,112), "font": "sans", "layout": "browser", "dark": False},
    "sunset_purple": {"bg": (55,30,79), "accent": (255,173,70), "ink": (255,248,239), "muted": (220,205,230), "font": "sans", "layout": "split", "dark": True},
    "paper_ink": {"bg": (245,241,232), "accent": (30,31,34), "ink": (22,22,24), "muted": (92,89,84), "font": "condensed", "layout": "ticket", "dark": False},
    "violet_pop": {"bg": (239,229,255), "accent": (117,65,235), "ink": (30,18,55), "muted": (90,77,118), "font": "sans", "layout": "chat", "dark": False},
    "lime_black": {"bg": (199,244,81), "accent": (14,17,17), "ink": (14,17,17), "muted": (43,48,38), "font": "condensed", "layout": "poster", "dark": False},
    "sky_editorial": {"bg": (218,237,246), "accent": (17,88,148), "ink": (15,33,43), "muted": (70,96,108), "font": "serif", "layout": "highlighter", "dark": False},
    "mono_red": {"bg": (27,27,28), "accent": (235,50,72), "ink": (250,250,250), "muted": (170,170,174), "font": "sans", "layout": "minimal", "dark": True},
}


def F(theme, size, bold=True):
    path = FONTS[theme["font"]]["bold" if bold else "regular"]
    return ImageFont.truetype(path, size)


def rr(d, box, radius, fill, outline=None, width=1):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def wrap_by_pixels(draw, text, f, max_w):
    words = " ".join(str(text or "").split()).split()
    lines, current = [], ""
    for word in words:
        candidate = word if not current else current + " " + word
        if draw.textbbox((0,0), candidate, font=f)[2] <= max_w:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return "\\n".join(lines)


def fit(draw, text, max_w, max_h, start, minimum, theme, bold=True):
    for size in range(start, minimum - 1, -2):
        f = F(theme, size, bold)
        wrapped = wrap_by_pixels(draw, text, f, max_w)
        bb = draw.multiline_textbbox((0,0), wrapped, font=f, spacing=max(5, size//8))
        if bb[2] - bb[0] <= max_w and bb[3] - bb[1] <= max_h:
            return f, wrapped
    f = F(theme, minimum, bold)
    return f, wrap_by_pixels(draw, text, f, max_w)


def gradient(top, bottom):
    img = Image.new("RGB", (W,H))
    px = img.load()
    for y in range(H):
        t = y / (H-1)
        c = tuple(int(top[i]*(1-t)+bottom[i]*t) for i in range(3))
        for x in range(W):
            px[x,y] = c
    return img


def background(theme):
    img = Image.new("RGB", (W,H), theme["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    layout = theme["layout"]

    if layout in {"bold_left","minimal"}:
        for x in range(0,W,72): d.line((x,0,x,H), fill=(255,255,255,14), width=1)
        for y in range(0,H,72): d.line((0,y,W,y), fill=(255,255,255,14), width=1)

    if layout == "magazine":
        d.ellipse((660,-160,1200,380), fill=(*theme["accent"],42))
        d.ellipse((-140,760,260,1160), fill=(255,255,255,20))
    elif layout == "sticker":
        d.ellipse((-150,600,380,1160), fill=(255,255,255,80))
        d.ellipse((770,-140,1200,330), fill=(255,255,255,100))
    elif layout == "browser":
        d.polygon([(0,0),(1080,0),(1080,420),(0,700)], fill=(255,255,255,60))
        for x in range(0,W,120): d.line((x,0,x,H), fill=(*theme["accent"],12), width=1)
    elif layout == "split":
        d.polygon([(0,0),(1080,0),(1080,640),(270,1080),(0,1080)], fill=(116,74,182,95))
        d.ellipse((700,50,1150,500), fill=(*theme["accent"],35))
    elif layout == "ticket":
        for y in (70,1012): d.line((70,y,1010,y), fill=(*theme["accent"],170), width=2)
        for x in range(82,1010,28): d.ellipse((x-2,998,x+2,1002), fill=(*theme["accent"],150))
    elif layout == "chat":
        for y in range(115,980,92): d.rounded_rectangle((760,y,1010,y+42),21,fill=(*theme["accent"],30))
    elif layout == "poster":
        d.polygon([(760,0),(1080,0),(1080,1080),(545,1080)], fill=(255,255,255,48))
    elif layout == "highlighter":
        d.ellipse((750,0,1210,460), fill=(255,255,255,105))
        d.rectangle((60,515,1015,585), fill=(*theme["accent"],25))
    return img


def logo(d, theme):
    d.text((60,40),"WORKS LAB",font=F(theme,27,True),fill=theme["ink"])
    d.text((60,73),"RESUME TEMPLATES",font=F(theme,16,False),fill=theme["muted"])


def price_badge(d, theme, x, y):
    fill = (255,255,255) if theme["dark"] else theme["ink"]
    txt = theme["ink"] if theme["dark"] else (255,255,255)
    rr(d,(x,y,x+174,y+58),29,fill)
    d.text((x+22,y+12),"₹149",font=F(theme,25,True),fill=txt)
    d.text((x+73,y+19),"ATS TEMPLATES",font=F(theme,10,True),fill=txt)


def resume_card(base, template, box, angle=0):
    t = Image.open(template).convert("RGBA")
    mw,mh=box[2]-box[0],box[3]-box[1]
    t.thumbnail((mw-36,mh-36),Image.Resampling.LANCZOS)
    card=Image.new("RGBA",(t.width+46,t.height+62),(0,0,0,0))
    shadow=Image.new("RGBA",card.size,(0,0,0,0))
    sd=ImageDraw.Draw(shadow)
    rr(sd,(9,16,t.width+37,t.height+50),20,(0,0,0,95))
    shadow=shadow.filter(ImageFilter.GaussianBlur(11))
    cd=ImageDraw.Draw(card)
    rr(cd,(8,8,t.width+38,t.height+46),20,(255,255,255,248))
    cd.text((24,t.height+21),"EDITABLE RESUME TEMPLATE",font=F(THEMES["paper_ink"],11,True),fill=(55,58,64))
    card.alpha_composite(t,(21,21))
    out=Image.new("RGBA",card.size,(0,0,0,0))
    out.alpha_composite(shadow); out.alpha_composite(card)
    if angle: out=out.rotate(angle,expand=True,resample=Image.Resampling.BICUBIC)
    x=box[0]+max(0,(mw-out.width)//2); y=box[1]+max(0,(mh-out.height)//2)
    base.alpha_composite(out,(x,y))


def rich_hook(d,item,theme,x,y,max_w,max_h,size=68):
    f,txt=fit(d,item["hook"],max_w,max_h,size,40,theme,True)
    yy=y
    lines=txt.split("\n")
    for i,line in enumerate(lines):
        bb=d.textbbox((0,0),line,font=f)
        if i==len(lines)-1:
            d.rounded_rectangle((x-6,yy+bb[3]-5,x+(bb[2]-bb[0])+10,yy+bb[3]+7),radius=8,fill=theme["accent"])
        d.text((x,yy),line,font=f,fill=theme["ink"])
        yy+=(bb[3]-bb[1])+10
    return yy


def body_value(d,item,theme,x,y,max_w,body_h,value_h=112):
    bf,bt=fit(d,item["body"],max_w,body_h,30,19,theme,False)
    d.multiline_text((x,y),bt,font=bf,fill=theme["muted"],spacing=6)
    bh=d.multiline_textbbox((0,0),bt,font=bf,spacing=6)[3]
    vy=y+bh+18
    bg=(255,255,255,26) if theme["dark"] else (255,255,255,205)
    rr(d,(x,vy,x+max_w,vy+value_h),20,bg)
    d.text((x+16,vy+12),"WHAT YOU GET",font=F(theme,13,True),fill=theme["accent"])
    parts=[p.strip() for p in str(item["value"]).split("•") if p.strip()]
    chip_x=x+14; chip_y=vy+43
    for part in parts[:3]:
        pf,pt=fit(d,part,min(max_w-28,220),value_h-52,18,14,theme,False)
        bw=d.multiline_textbbox((0,0),pt,font=pf,spacing=4)[2]+24
        if chip_x+bw>x+max_w-14:
            chip_x=x+14; chip_y+=38
        rr(d,(chip_x,chip_y,min(chip_x+bw,x+max_w-14),chip_y+34),17,
           (*theme["accent"],32) if theme["dark"] else (240,242,246,230))
        d.text((chip_x+12,chip_y+9),pt,font=pf,fill=theme["ink"])
        chip_x+=bw+8
    return vy+value_h


def cta(d,item,theme,box):
    rr(d,box,26,theme["accent"])
    f,t=fit(d,item["cta"],box[2]-box[0]-36,box[3]-box[1]-12,24,17,theme,True)
    bb=d.multiline_textbbox((0,0),t,font=f,spacing=3)
    tw,th=bb[2]-bb[0],bb[3]-bb[1]
    d.multiline_text(((box[0]+box[2]-tw)//2,(box[1]+box[3]-th)//2),t,font=f,fill="white",spacing=3,align="center")


def normalize(item):
    out=dict(item or {})
    out["hook"]=out.get("hook","A better resume starts here.")
    out["body"]=out.get("body",out.get("sub","Start with a clean professional format."))
    out["value"]=out.get("value","Easy to edit • Clean structure • Professional look")
    out["cta"]=out.get("cta","Get yours — ₹149")
    return out


def render(item,template,theme_name):
    theme=THEMES[theme_name]
    item=normalize(item)
    img=background(theme).convert("RGBA")
    d=ImageDraw.Draw(img,"RGBA")
    logo(d,theme)
    layout=theme["layout"]

    if layout=="bold_left":
        rr(d,(60,126,270,165),20,theme["accent"])
        d.text((77,136),"RESUME PROBLEM",font=F(theme,14,True),fill="white")
        rich_hook(d,item,theme,60,190,520,260,66)
        body_value(d,item,theme,60,505,470,85,118)
        cta(d,item,theme,(60,895,530,965))
        price_badge(d,theme,60,982)
        resume_card(img,template,(620,145,1025,900),-4)
    elif layout=="magazine":
        d.text((60,135),"CAREER / 01",font=F(theme,16,True),fill=theme["accent"])
        f,t=fit(d,item["hook"],920,220,72,42,theme,True)
        d.multiline_text((60,178),t,font=f,fill=theme["ink"],spacing=10)
        d.line((60,420,1020,420),fill=theme["ink"],width=2)
        body_value(d,item,theme,60,450,485,86,112)
        resume_card(img,template,(600,445,1020,905),2)
        cta(d,item,theme,(60,850,560,922))
        price_badge(d,theme,60,940)
    elif layout=="sticker":
        rr(d,(55,140,1025,1016),42,(255,255,255,200))
        rr(d,(95,175,325,220),22,theme["accent"])
        d.text((112,186),"NEW TEMPLATE DROP",font=F(theme,15,True),fill="white")
        resume_card(img,template,(90,270,555,910),-6)
        rich_hook(d,item,theme,590,235,390,245,62)
        body_value(d,item,theme,590,535,375,92,112)
        cta(d,item,theme,(590,835,965,905))
        price_badge(d,theme,590,920)
    elif layout=="browser":
        rr(d,(55,145,1025,1005),30,(255,255,255,230))
        rr(d,(75,165,1005,207),18,theme["accent"])
        for cx in (95,116,137): d.ellipse((cx,181,cx+10,191),fill=(255,255,255,210))
        resume_card(img,template,(95,260,575,925),0)
        d.text((620,250),"RESUME CHECK",font=F(theme,16,True),fill=theme["accent"])
        rich_hook(d,item,theme,620,290,340,245,61)
        body_value(d,item,theme,620,555,335,90,120)
        cta(d,item,theme,(620,850,960,920))
        price_badge(d,theme,620,945)
    elif layout=="split":
        d.text((60,145),"YOUR NEXT",font=F(theme,18,True),fill=theme["accent"])
        d.text((60,180),"APPLICATION",font=F(theme,18,True),fill=theme["ink"])
        rich_hook(d,item,theme,60,245,500,285,70)
        body_value(d,item,theme,60,575,455,92,112)
        cta(d,item,theme,(60,850,515,920))
        price_badge(d,theme,60,935)
        resume_card(img,template,(600,170,1025,925),3)
    elif layout=="ticket":
        rr(d,(70,140,1010,975),34,(255,255,255,228))
        d.text((100,178),"WORKS LAB / CAREER KIT",font=F(theme,15,True),fill=theme["accent"])
        rich_hook(d,item,theme,100,225,840,260,68)
        body_value(d,item,theme,100,520,840,88,115)
        resume_card(img,template,(325,650,755,935),0)
        cta(d,item,theme,(100,885,520,950))
        price_badge(d,theme,810,885)
    elif layout=="chat":
        d.text((70,145),"@WORKSLAB",font=F(theme,15,True),fill=theme["accent"])
        rr(d,(70,200,740,430),28,(255,255,255,220))
        rich_hook(d,item,theme,105,235,560,175,58)
        rr(d,(330,455,1010,580),28,theme["accent"])
        bf,bt=fit(d,item["body"],610,88,30,19,theme,False)
        d.multiline_text((372,482),bt,font=bf,fill="white",spacing=6)
        resume_card(img,template,(305,600,820,915),1)
        parts=[p.strip() for p in str(item["value"]).split("•") if p.strip()][:3]
        for i,part in enumerate(parts):
            rr(d,(70,610+i*57,255,652+i*57),20,(255,255,255,210))
            pf,pt=fit(d,part,150,28,17,13,theme,False)
            d.multiline_text((88,620+i*57),pt,font=pf,fill=theme["ink"])
        cta(d,item,theme,(70,825,430,895))
        price_badge(d,theme,850,825)
    elif layout=="poster":
        d.text((60,145),"01",font=F(theme,106,True),fill=theme["accent"])
        f,t=fit(d,item["hook"],880,270,80,44,theme,True)
        d.multiline_text((60,255),t,font=f,fill=theme["ink"],spacing=8)
        d.line((60,575,1020,575),fill=theme["ink"],width=3)
        bf,bt=fit(d,item["body"],650,110,29,19,theme,False)
        d.multiline_text((60,610),bt,font=bf,fill=theme["muted"],spacing=5)
        resume_card(img,template,(690,600,1015,910),-5)
        cta(d,item,theme,(60,850,600,920))
        price_badge(d,theme,820,850)
        d.text((60,960),"JOB-READY FORMAT  /  EASY TO EDIT",font=F(theme,16,True),fill=theme["accent"])
    elif layout=="highlighter":
        d.text((70,145),"A SMALL UPGRADE CAN CHANGE THE WHOLE LOOK.",font=F(theme,14,True),fill=theme["accent"])
        rich_hook(d,item,theme,70,200,780,270,72)
        resume_card(img,template,(655,370,1020,820),4)
        body_value(d,item,theme,70,540,520,88,120)
        cta(d,item,theme,(70,820,590,890))
        price_badge(d,theme,70,920)
    else:
        d.text((60,145),"WORKS LAB / ₹149",font=F(theme,16,True),fill=theme["accent"])
        f,t=fit(d,item["hook"],520,260,80,44,theme,True)
        d.multiline_text((60,190),t,font=f,fill=theme["ink"],spacing=8)
        d.line((60,505,560,505),fill=theme["accent"],width=5)
        body_value(d,item,theme,60,540,500,88,118)
        cta(d,item,theme,(60,805,560,875))
        price_badge(d,theme,60,915)
        resume_card(img,template,(650,170,1015,900),2)

    d.text((60,1035),"resume.workslab.in",font=F(theme,16,False),fill=theme["muted"])
    return img.convert("RGB")


def choose():
    items=json.loads(HOOKS.read_text(encoding="utf-8"))
    cfg=json.loads(DESIGNS.read_text(encoding="utf-8"))
    templates=sorted(TEMPLATES.glob("*.png"))
    if not items: raise ValueError("No content entries found.")
    if not templates: raise FileNotFoundError("No resume templates found.")

    n=date.today().toordinal()
    item=normalize(items[n % len(items)])
    theme_name=cfg["rotation"][n % len(cfg["rotation"])]
    template=templates[(n*7) % len(templates)]
    return item,template,theme_name


if __name__=="__main__":
    today=date.today().isoformat()
    item,template,theme_name=choose()
    image_output=OUTPUT/f"daily-{today}.jpg"
    render(item,template,theme_name).save(image_output,quality=95,optimize=True)

    caption=(
        f"🚀 {item['hook']}\n\n"
        f"{item['body']}\n\n"
        f"{item['value']}\n\n"
        f"{item['cta']}\n\n"
        "Get yours: https://resume.workslab.in\n\n"
        "#resume #resumetips #jobsearch #careertips #atsresume #resumetemplate"
    )
    meta={
        "date":today,"hook_id":item.get("id",""),"hook":item["hook"],
        "body":item["body"],"value":item["value"],"cta":item["cta"],
        "theme":theme_name,"layout":THEMES[theme_name]["layout"],
        "template":template.name,"image":image_output.name,"caption":caption
    }
    (OUTPUT/f"daily-{today}.json").write_text(
        json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8"
    )
    print(json.dumps(meta,ensure_ascii=False))
