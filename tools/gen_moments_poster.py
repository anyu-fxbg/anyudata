# -*- coding: utf-8 -*-
"""生成 SaaS 朋友圈分享海报（新拟态风格 / 1080x1350 竖版）"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1350
BG = (224, 229, 236)          # #E0E5EC
TEXT = (61, 72, 82)           # #3D4852
MUTED = (93, 102, 115)        # #5D6673
ACCENT = (108, 99, 255)       # #6C63FF
ACCENT_DEEP = (90, 80, 232)   # #5A50E8
WHITE = (255, 255, 255)
SHADOW_DARK = (163, 177, 198)
SHADOW_LIGHT = (255, 255, 255)

REG = r"C:/Windows/Fonts/msyh.ttc"
BOLD = r"C:/Windows/Fonts/msyhbd.ttc"


def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else REG, size)


def rr(draw, box, r, fill):
    draw.rounded_rectangle(box, radius=r, fill=fill)


def neu_card(img, box, r=34, blur=16, off=9):
    x0, y0, x1, y1 = box
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(dark).rounded_rectangle(
        (x0 + off, y0 + off, x1 + off, y1 + off), radius=r, fill=SHADOW_DARK + (255,))
    dark = dark.filter(ImageFilter.GaussianBlur(blur))
    light = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(light).rounded_rectangle(
        (x0 - off, y0 - off, x1 - off, y1 - off), radius=r, fill=SHADOW_LIGHT + (255,))
    light = light.filter(ImageFilter.GaussianBlur(blur))
    base = img.convert("RGBA")
    base.alpha_composite(light)
    base.alpha_composite(dark)
    cd = ImageDraw.Draw(base)
    rr(cd, box, r, BG + (255,))
    img.paste(base.convert("RGB"))
    return ImageDraw.Draw(img)


def gradient_purple(size):
    w, h = size
    g = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        g.putpixel((0, y), tuple(int(ACCENT[i] + (ACCENT_DEEP[i] - ACCENT[i]) * t) for i in range(3)))
    return g.resize((w, h))


def purple_chip(img, box, draw):
    x0, y0, x1, y1 = box
    img.paste(gradient_purple((x1 - x0, y1 - y0)), (x0, y0))
    ImageDraw.Draw(img).rounded_rectangle(box, radius=22, outline=WHITE, width=3)


def draw_icon(draw, kind, cx, cy, s, col):
    if kind == "layers":
        for dy in [s * 0.85, 0, -s * 0.85]:
            rr(draw, (cx - s, cy - s * 0.30 + dy, cx + s, cy + s * 0.30 + dy), 9, col)
    elif kind == "tag":
        rr(draw, (cx - s * 0.55, cy - s * 0.5, cx + s, cy + s * 0.5), 12, col)
        draw.polygon([(cx - s * 0.55, cy - s * 0.5), (cx - s * 1.05, cy),
                      (cx - s * 0.55, cy + s * 0.5)], fill=col)
        draw.ellipse((cx + s * 0.33, cy - s * 0.17, cx + s * 0.67, cy + s * 0.17),
                     outline=WHITE, width=4)
    elif kind == "api":
        draw.line([(cx - 0.42 * s, cy - 0.5 * s), (cx - 0.82 * s, cy),
                   (cx - 0.42 * s, cy + 0.5 * s)], fill=col, width=9, joint="curve")
        draw.line([(cx + 0.42 * s, cy - 0.5 * s), (cx + 0.82 * s, cy),
                   (cx + 0.42 * s, cy + 0.5 * s)], fill=col, width=9, joint="curve")
        draw.line([(cx + 0.26 * s, cy - 0.62 * s), (cx - 0.26 * s, cy + 0.62 * s)],
                  fill=col, width=9)
    elif kind == "phone":
        rr(draw, (cx - 0.58 * s, cy - s, cx + 0.58 * s, cy + s), 14, col)
        rr(draw, (cx - 0.40 * s, cy - 0.68 * s, cx + 0.40 * s, cy + 0.68 * s), 8, BG)
        draw.rectangle((cx - 0.20 * s, cy - 0.90 * s, cx + 0.20 * s, cy - 0.78 * s), fill=col)


def text_w(draw, s, f):
    return draw.textlength(s, font=f)


def center_text(draw, cx, y, s, f, col):
    draw.text((cx - text_w(draw, s, f) / 2, y), s, font=f, fill=col)


def wrap(draw, s, f, maxw):
    lines, cur = [], ""
    for ch in s:
        if text_w(draw, cur + ch, f) > maxw and cur:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


img = Image.new("RGB", (W, H), BG)

# 极淡的紫色柔光（四角），保持 ceramic 底为主
deco = Image.new("RGBA", (W, H), (0, 0, 0, 0))
dd = ImageDraw.Draw(deco)
dd.ellipse([-260, -300, 300, 260], fill=ACCENT + (16,))
dd.ellipse([W - 260, H - 300, W + 300, H + 260], fill=ACCENT + (14,))
deco = deco.filter(ImageFilter.GaussianBlur(80))
img = Image.alpha_composite(img.convert("RGBA"), deco).convert("RGB")
draw = ImageDraw.Draw(img)

# 顶部 emblem
ex0, ey0, ex1, ey1 = 474, 52, 606, 184
purple_chip(img, (ex0, ey0, ex1, ey1), draw)
draw_icon(draw, "layers", (ex0 + ex1) // 2, (ey0 + ey1) // 2, 36, WHITE)

center_text(draw, W // 2, 200, "安遇大数据", font(46, True), TEXT)
center_text(draw, W // 2, 266, "数据查询 SaaS 平台", font(26), MUTED)
center_text(draw, W // 2, 326, "一站式个人数据查询 SaaS", font(50, True), TEXT)

sub = "白标部署 · 自定义域名 · OpenAPI 开放接口 · C 端自助 H5"
yy = 398
for ln in wrap(draw, sub, font(26), 920):
    center_text(draw, W // 2, yy, ln, font(26), MUTED)
    yy += 38

cards = [
    ("layers", "5合1 综合报告", "个人风险 / 司法涉诉 / 婚姻 / 车辆 / 信用分，一次查询全覆盖"),
    ("tag", "租户白标 · 品牌隔离", "自定义域名与品牌，多租户数据严格隔离，独立运营"),
    ("api", "开放 API 接口", "开发者凭 Key 对接，按调用计费，轻松嵌入自有系统"),
    ("phone", "C 端自助查询 H5", "客户自主下单、在线授权、微信支付、即时查看报告"),
]
x0, cw, ch, gap = 60, 960, 150, 20
y = 462
for kind, title, desc in cards:
    cx0, cy0, cx1, cy1 = x0, y, x0 + cw, y + ch
    cd = neu_card(img, (cx0, cy0, cx1, cy1), r=34, blur=16, off=9)
    chip_s = 92
    chip = (cx0 + 28, cy0 + (ch - chip_s) // 2, cx0 + 28 + chip_s, cy0 + (ch - chip_s) // 2 + chip_s)
    purple_chip(img, chip, cd)
    draw_icon(cd, kind, (chip[0] + chip[2]) // 2, (chip[1] + chip[3]) // 2, 28, WHITE)
    tx = chip[2] + 34
    cd.text((tx, cy0 + 26), title, font=font(34, True), fill=TEXT)
    dyy = cy0 + 80
    for ln in wrap(cd, desc, font(24), cx1 - tx - 28):
        cd.text((tx, dyy), ln, font=font(24), fill=MUTED)
        dyy += 33
    y += ch + gap

# 底部 CTA 渐变胶囊
cta = (x0, y + 16, x0 + cw, y + 16 + 88)
img.paste(gradient_purple((cta[2] - cta[0], cta[3] - cta[1])), (cta[0], cta[1]))
cd = ImageDraw.Draw(img)
cd.rounded_rectangle(cta, radius=44, outline=WHITE, width=3)
center_text(cd, W // 2, cta[1] + 24, "标准套餐  ¥22 / 次   即可开通", font(33, True), WHITE)

center_text(cd, W // 2, cta[3] + 16, "让每一次查询，都有据可循", font(26, True), ACCENT_DEEP)
center_text(cd, W // 2, cta[3] + 56, "Powered by 安遇大数据 SaaS", font(22), MUTED)

out = r"E:/安遇大数据新版UI/SaaS/tools/saas_moments_poster.png"
img.save(out, "PNG")
print("SAVED", out, img.size)
