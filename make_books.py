#!/usr/bin/env python3
"""Robo Learns to See series by Olanite B.A. - three 24-page, 8.5 x 8.5 in picture-book PDFs (ReportLab)."""
import math, re, os, json
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily, stringWidth
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.utils import ImageReader

FD = os.environ.get('POPPINS_DIR', '/usr/share/fonts/truetype/google-fonts/')
for n, f in [('P', 'Poppins-Regular'), ('PM', 'Poppins-Medium'), ('PB', 'Poppins-Bold'),
             ('PL', 'Poppins-Light'), ('PI', 'Poppins-Italic'), ('PBI', 'Poppins-BoldItalic')]:
    pdfmetrics.registerFont(TTFont(n, FD + f + '.ttf'))
registerFontFamily('P', normal='P', bold='PB', italic='PI', boldItalic='PBI')
registerFontFamily('PM', normal='PM', bold='PB', italic='PI', boldItalic='PBI')
from reportlab import rl_config
rl_config.canvas_basefontname = 'P'
ParagraphStyle.defaults['fontName'] = 'P'
ParagraphStyle.defaults['bulletFontName'] = 'PB'

W = H = 8.5 * inch          # trim: 612 x 612 pt
BL = 9                      # 0.125 in bleed
PW, PH = W + BL, H + 2 * BL # page with bleed: 8.625 x 8.75 in
M = 34
OL = '#12365E'
INK = '#1F2A44'
IMG2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img2', 'b2-%s.jpg')
IMG3 = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img3', 'b3-%s.jpg')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
HERE = os.path.dirname(os.path.abspath(__file__))
URLS = json.load(open(os.path.join(HERE, 'urls.json')))
HR = os.path.join(HERE, 'hires'); os.makedirs(HR, exist_ok=True)
os.makedirs(OUT, exist_ok=True)
AUTHOR = 'Olanite B.A.'
YEAR = '2026'


# ------------------------------------------------------------------ helpers
def smart(s):
    s = re.sub(r'(^|[\s(\[>\u2014-])"', lambda m: m.group(1) + '\u201c', s)
    s = s.replace('"', '\u201d').replace("'", '\u2019')
    return s


def fs(c, fill=None, stroke=OL, lw=3):
    if fill:
        c.setFillColor(HexColor(fill))
    if stroke:
        c.setStrokeColor(HexColor(stroke)); c.setLineWidth(lw)
    return (1 if fill else 0), (1 if stroke else 0)


def circ(c, x, y, r, fill=None, stroke=OL, lw=3):
    f, s = fs(c, fill, stroke, lw); c.circle(x, y, r, fill=f, stroke=s)


def rr(c, x, y, w, h, r, fill=None, stroke=OL, lw=3, dash=None):
    f, s = fs(c, fill, stroke, lw)
    if dash:
        c.setDash(*dash)
    c.roundRect(x, y, w, h, r, fill=f, stroke=s)
    c.setDash()


def poly(c, pts, fill=None, stroke=OL, lw=3):
    f, s = fs(c, fill, stroke, lw)
    p = c.beginPath(); p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.close(); c.drawPath(p, fill=f, stroke=s)


CURBG = '#FFFFFF'


def alpha_fill(c, a):
    pass  # KDP wants flattened files: no transparency is ever written


def mix(a, b, t):
    a, b = HexColor(a), HexColor(b)
    return '#%02X%02X%02X' % tuple(int(round((x * t + y * (1 - t)) * 255)) for x, y in ((a.red, b.red), (a.green, b.green), (a.blue, b.blue)))


def hires(path, w_pt, h_pt, dpi=300):
    im = Image.open(path).convert('RGB'); iw, ih = im.size
    eff = 72.0 / max(w_pt / iw, h_pt / ih)
    if eff >= dpi:
        return path
    k = dpi / eff
    out = os.path.join(HR, os.path.basename(os.path.dirname(path)) + '_' + os.path.basename(path))
    if not os.path.exists(out):
        im.resize((round(iw * k), round(ih * k)), Image.LANCZOS).save(out, 'JPEG', quality=93, dpi=(300, 300))
    return out


def qr_draw(c, url, x, y, size, border=4):
    import itertools
    from reportlab.graphics.barcode import qrencoder
    q = qrencoder.QRCode(None, qrencoder.QRErrorCorrectLevel.M); q.addData(url); q.make()
    n = q.getModuleCount(); box = size / (n + 2.0 * border)
    c.setFillColor(HexColor('#000000'))
    for r, row in enumerate(q.modules):
        col = 0
        for dark, grp in itertools.groupby(map(bool, row)):
            cnt = len(list(grp))
            if dark:
                c.rect(x + (col + border) * box, y + size - (r + border + 1) * box, cnt * box + .2, box + .2, fill=1, stroke=0)
            col += cnt


def qr_box(c, url, x, y, size, pad=6):
    rr(c, x - pad, y - pad, size + 2 * pad, size + 2 * pad, 10, '#FFFFFF', '#1F2A44', 2)
    qr_draw(c, url, x, y, size)


def ctext(c, s, x, y, font, size, color):
    c.setFont(font, size); c.setFillColor(HexColor(color)); c.drawCentredString(x, y, s)


def spaced(c, s, x, y, font, size, color, space=1.6, align='left'):
    w = stringWidth(s, font, size) + space * (len(s) - 1)
    if align == 'center':
        x = x - w / 2
    c.saveState()
    t = c.beginText(x, y); t.setFont(font, size); t.setFillColor(HexColor(color)); t.setCharSpace(space)
    t.textOut(s); c.drawText(t)
    c.restoreState()


def make_para(text, font, size, color, w, align=TA_LEFT, lk=1.38, **kw):
    st = ParagraphStyle('s', fontName=font, fontSize=size, leading=size * lk, textColor=HexColor(color),
                        alignment=align, **kw)
    p = Paragraph(text, st); pw, ph = p.wrap(w, 10000)
    return p, ph


def fit_para(c, text, font, size, color, x, y_top, w, max_h, align=TA_LEFT, min_size=7.5, draw=True):
    s = size
    while True:
        p, ph = make_para(text, font, s, color, w, align)
        if ph <= max_h or s <= min_size:
            break
        s -= 0.5
    if draw:
        p.drawOn(c, x, y_top - ph)
    return ph, s


def image_cover(c, path, x, y, w, h, r=0, fx=.5, fy=.5):
    ir = ImageReader(path); iw, ih = ir.getSize()
    s = max(w / iw, h / ih); dw, dh = iw * s, ih * s
    dx = x - (dw - w) * fx; dy = y - (dh - h) * (1 - fy)
    c.saveState(); p = c.beginPath(); p.roundRect(x, y, w, h, r); c.clipPath(p, stroke=0, fill=0)
    c.drawImage(ir, dx, dy, dw, dh); c.restoreState()


def vec_panel(c, fn, x, y, w, h, r=0):
    c.saveState(); p = c.beginPath(); p.roundRect(x, y, w, h, r); c.clipPath(p, stroke=0, fill=0)
    c.translate(x, y); fn(c, w, h); c.restoreState()


def card(c, x, y, w, h, r=22, fill='#FFFFFF', stroke=None, lw=2, a=1.0):
    if a < 1:
        fill = mix(fill, CURBG, a)
    f, s = fs(c, fill, None, lw); c.roundRect(x, y, w, h, r, fill=f, stroke=0)
    if stroke:
        rr(c, x, y, w, h, r, None, stroke, lw)


def deco(c, B, seed):
    """soft confetti dots in page corners"""
    cols = B['confetti']
    pts = [(54, 566), (556, 562), (560, 54), (54, 52), (306, 566), (558, 300), (54, 330)]
    for k, (x, y) in enumerate(pts):
        c.setFillColor(HexColor(mix(cols[(k + seed) % len(cols)], CURBG, .55)))
        c.circle(x, y, 4 + (k + seed) % 3 * 2, fill=1, stroke=0)


# ------------------------------------------------------------------ vector art
def sparkle(c, x, y, r, col='#FFD84A'):
    poly(c, [(x, y + r), (x + r * .28, y + r * .28), (x + r, y), (x + r * .28, y - r * .28), (x, y - r),
             (x - r * .28, y - r * .28), (x - r, y), (x - r * .28, y + r * .28)], col, None)


def sun(c, x, y, r):
    c.setStrokeColor(HexColor('#F5A623')); c.setLineWidth(4); c.setLineCap(1)
    for k in range(10):
        a = k * math.pi / 5
        c.line(x + math.cos(a) * (r + 7), y + math.sin(a) * (r + 7), x + math.cos(a) * (r + 17), y + math.sin(a) * (r + 17))
    circ(c, x, y, r, '#FFD84A', '#F5A623', 3)


def ball(c, x, y, r, col='#E5483D'):
    circ(c, x, y, r, col, OL, 3)
    c.setFillColor(HexColor(mix('#FFFFFF', col, .6)))
    c.circle(x - r * .35, y + r * .35, r * .2, fill=1, stroke=0)


def square(c, x, y, s, col='#2F73C4'):
    rr(c, x - s / 2, y - s / 2, s, s, s * .12, col, OL, 3)


def triangle(c, x, y, s, col='#8E5BD0'):
    poly(c, [(x - s / 2, y - s * .4), (x + s / 2, y - s * .4), (x, y + s * .5)], col, OL, 3)


def cloud(c, x, y, k=1.0):
    c.setFillColor(HexColor('#FFFFFF'))
    for dx, dy, r in [(0, 0, 16), (18, 8, 20), (40, 0, 16), (20, -4, 16)]:
        c.circle(x + dx * k, y + dy * k, r * k, fill=1, stroke=0)


def flower(c, x, y, col='#FF8FB1'):
    c.setStrokeColor(HexColor('#4C9A4A')); c.setLineWidth(3); c.line(x, y, x, y - 18)
    circ(c, x, y, 7, col, None); circ(c, x, y, 3, '#FFE066', None)


def bubble(c, x, y, w, h, text, tail=(0, -14), font='PB', size=13, color=INK, fill='#FFFFFF'):
    rr(c, x, y, w, h, 14, fill, OL, 2.5)
    cx = x + w / 2; tx, ty = cx + tail[0], y + tail[1]
    poly(c, [(cx - 8, y + 1.5), (cx + 8, y + 1.5), (tx, ty)], fill, None)
    c.setStrokeColor(HexColor(OL)); c.setLineWidth(2.5)
    c.line(cx - 8, y + 1.5, tx, ty); c.line(cx + 8, y + 1.5, tx, ty)
    lines = text.split('\n')
    for k, ln in enumerate(lines):
        ctext(c, ln, cx, y + h / 2 + (len(lines) - 1) * size * .55 - k * size * 1.15 - size * .33, font, size, color)


def robot(c, cx, by, s=1.0, eyes='#FFD84A', body='#2F73C4'):
    c.saveState(); c.translate(cx, by); c.scale(s, s)
    circ(c, 0, 14, 14, '#3C4A5E', OL, 3)
    rr(c, -44, 38, 14, 34, 7, body, OL, 3); rr(c, 30, 38, 14, 34, 7, body, OL, 3)
    rr(c, -30, 26, 60, 52, 14, body, OL, 3)
    circ(c, 0, 51, 6, '#FFD84A', OL, 2)
    circ(c, -38, 106, 8, '#244F86', OL, 3); circ(c, 38, 106, 8, '#244F86', OL, 3)
    rr(c, -36, 78, 72, 56, 22, body, OL, 3)
    rr(c, -28, 86, 56, 38, 16, '#10243F', None)
    circ(c, -12, 106, 8.5, eyes, None); circ(c, 12, 106, 8.5, eyes, None)
    c.setStrokeColor(HexColor(eyes)); c.setLineWidth(2.5); c.setLineCap(1)
    c.arc(-8, 93, 8, 104, 205, 130)
    c.setStrokeColor(HexColor(OL)); c.setLineWidth(3); c.line(0, 134, 0, 146)
    circ(c, 0, 149, 5, '#4FA3FF', OL, 2.5)
    c.restoreState()


def echo(c, cx, cy, s=1.0):
    c.saveState(); c.translate(cx, cy); c.scale(s, s)
    circ(c, -33, 0, 9, '#F7943D', '#7A3E12', 2.5); circ(c, 33, 0, 9, '#F7943D', '#7A3E12', 2.5)
    c.setStrokeColor(HexColor('#7A3E12')); c.setLineWidth(2.5); c.line(0, 36, 0, 46)
    circ(c, 0, 49, 4.5, '#F7943D', '#7A3E12', 2)
    f, st = fs(c, '#FFFFFF', '#7A3E12', 3); c.ellipse(-28, -34, 28, 38, fill=f, stroke=st)
    rr(c, -19, -8, 38, 30, 13, '#FF9F4A', '#7A3E12', 2)
    circ(c, -7, 8, 3.6, '#1F2A44', None); circ(c, 7, 8, 3.6, '#1F2A44', None)
    c.setStrokeColor(HexColor('#1F2A44')); c.setLineWidth(2); c.arc(-5, -2, 5, 6, 200, 140)
    circ(c, -10, -32, 6, '#F7943D', '#7A3E12', 2); circ(c, 10, -32, 6, '#F7943D', '#7A3E12', 2)
    c.restoreState()


def note(c, x, y, col='#E86AA6'):
    c.setStrokeColor(HexColor(OL)); c.setLineWidth(2.5); c.line(x + 6, y, x + 6, y + 24)
    c.setLineWidth(3); c.line(x + 6, y + 24, x + 16, y + 19)
    circ(c, x, y, 6, col, OL, 2)


def waves(c, x, y, n=3, col='#F5A623', dirn=1):
    c.setStrokeColor(HexColor(col)); c.setLineWidth(3.5); c.setLineCap(1)
    for k in range(n):
        r = 12 + k * 10
        if dirn > 0:
            c.arc(x - r, y - r, x + r, y + r, -40, 80)
        else:
            c.arc(x - r, y - r, x + r, y + r, 140, 80)


def bg(c, w, h, sky, ground='#BEE3A0', ground_top=120):
    c.setFillColor(HexColor(sky)); c.rect(0, 0, w, h, fill=1, stroke=0)
    c.setFillColor(HexColor(ground)); c.ellipse(-w * .4, ground_top - 330, w * 1.4, ground_top, fill=1, stroke=0)


# ---- Book 1 scenes (290 x 396)
def sc1(c, w, h):
    bg(c, w, h, '#CDEBFF'); sun(c, 225, 330, 34); cloud(c, 40, 320); cloud(c, 150, 262, .7)
    for x, col in [(34, '#FF8FB1'), (254, '#FFFFFF'), (80, '#FFD84A'), (214, '#FF8FB1')]:
        flower(c, x, 98 + (x % 3) * 8, col)
    robot(c, w / 2, 56, 1.25)


def sc2(c, w, h):
    bg(c, w, h, '#FFF1B8'); sun(c, 215, 320, 44); ball(c, 62, 122, 32)
    robot(c, 175, 52, 1.1); sparkle(c, 40, 250, 14); sparkle(c, 120, 330, 10)


def sc3(c, w, h):
    bg(c, w, h, '#D8F0FF'); sun(c, 232, 342, 26); ball(c, 235, 108, 22)
    robot(c, 100, 56, 1.2)
    rr(c, 150, 160, 82, 54, 10, '#2C3E55', OL, 3); rr(c, 168, 210, 30, 12, 4, '#2C3E55', OL, 3)
    circ(c, 191, 187, 17, '#9AD8FF', OL, 3); circ(c, 191, 187, 8, '#2F73C4', None)
    sparkle(c, 226, 245, 22); sparkle(c, 255, 215, 12); sparkle(c, 150, 245, 12)


def sc4(c, w, h):
    bg(c, w, h, '#E6DCFF')
    rr(c, 36, 214, 218, 156, 16, '#FFFFFF', OL, 6)
    rr(c, 50, 228, 190, 128, 8, '#CDEBFF', None)
    c.setFillColor(HexColor('#BEE3A0')); c.rect(50, 228, 190, 36, fill=1, stroke=0)
    sun(c, 200, 322, 16); ball(c, 90, 264, 15)
    robot(c, 78, 40, .95); ball(c, 235, 114, 22); sun(c, 232, 172, 14)


def sc5(c, w, h):
    bg(c, w, h, '#FFE8D6')
    ball(c, 85, 296, 46); sun(c, 205, 238, 44)
    c.setStrokeColor(HexColor('#2F73C4')); c.setLineWidth(3); c.setDash(5, 4)
    c.circle(85, 296, 60); c.circle(205, 238, 62); c.setDash()
    circ(c, 85, 372, 14, '#FFFFFF', OL, 2.5); ctext(c, '1', 85, 367, 'PB', 15, INK)
    circ(c, 258, 300, 14, '#FFFFFF', OL, 2.5); ctext(c, '2', 258, 295, 'PB', 15, INK)
    robot(c, 120, 42, 1.0)


def sc6(c, w, h):
    bg(c, w, h, '#FFE0E0')
    circ(c, 60, 300, 38, '#4FA3FF', OL, 3); square(c, 145, 300, 72, '#E5483D'); triangle(c, 232, 300, 78, '#8E5BD0')
    for x, t in [(60, 'circle'), (145, 'square'), (232, 'triangle')]:
        ctext(c, t, x, 238, 'PB', 11, INK)
    robot(c, w / 2, 40, 1.05)


def sc7(c, w, h):
    bg(c, w, h, '#D9F4F2')
    cols = ['#E5483D', '#2F73C4', '#E5483D', '#2F73C4']
    for k, col in enumerate(cols):
        circ(c, 38 + k * 52, 305, 22, col, OL, 3)
    c.setStrokeColor(HexColor(OL)); c.setLineWidth(2.5); c.setDash(4, 3); c.circle(246, 305, 22); c.setDash()
    ctext(c, '?', 246, 296, 'PB', 24, OL)
    robot(c, 100, 44, 1.05); bubble(c, 160, 150, 100, 44, 'Red!', tail=(-30, -14), size=16)


def sc8(c, w, h):
    bg(c, w, h, '#EADFFF')
    c.setFillColor(HexColor('#FFFFFF')); c.setStrokeColor(HexColor(OL)); c.setLineWidth(3)
    c.ellipse(20, 250, 270, 372, fill=1, stroke=1)
    for x, y, r in [(115, 238, 7), (100, 222, 5)]:
        circ(c, x, y, r, '#FFFFFF', OL, 2.5)
    ball(c, 80, 312, 24); ctext(c, '+', 120, 304, 'PB', 22, OL)
    ctext(c, 'round', 200, 312, 'PB', 15, INK); ctext(c, 'red + round = ?', 145, 266, 'PB', 13, '#2F73C4')
    robot(c, 130, 36, 1.0)


def sc9(c, w, h):
    bg(c, w, h, '#FFF0C9')
    rr(c, 24, 214, 242, 160, 16, '#2C4C7C', OL, 4); rr(c, 36, 226, 218, 136, 8, '#F7F1E4', None)
    cols = ['#E5483D', '#2F73C4', '#F5A623', '#4CAF50', '#8E5BD0', '#E86AA6']
    for k, col in enumerate(cols):
        x = 66 + (k % 3) * 80; y = 322 if k < 3 else 258
        rr(c, x - 28, y - 24, 56, 50, 8, '#FFFFFF', '#CFC6B0', 1.5)
        (ball if k % 3 == 0 else (square if k % 3 == 1 else triangle))(c, x, y, 28 if k % 3 else 20, col) if k % 3 != 0 else ball(c, x, y, 16, col)
    rr(c, 118, 196, 54, 18, 4, '#2C4C7C', OL, 3)
    robot(c, 145, 36, 1.0)


def sc10(c, w, h):
    bg(c, w, h, '#DDF7E8')
    ball(c, 72, 306, 38); ctext(c, 'ball', 72, 250, 'PB', 13, INK)
    square(c, 210, 306, 70, '#2F73C4'); ctext(c, '?', 210, 296, 'PB', 30, '#FFFFFF')
    robot(c, 145, 36, 1.05); bubble(c, 38, 188, 106, 40, 'Is this a ball?', tail=(50, -14), size=11)


def sc11(c, w, h):
    bg(c, w, h, '#FFE9D9')
    ball(c, 60, 130, 28); sun(c, 232, 335, 30)
    c.setStrokeColor(HexColor('#2E9E55')); c.setLineWidth(14); c.setLineCap(1); c.setLineJoin(1)
    p = c.beginPath(); p.moveTo(70, 295); p.lineTo(118, 248); p.lineTo(210, 346); c.drawPath(p, fill=0, stroke=1)
    robot(c, 160, 44, 1.15); circ(c, 238, 176, 15, '#FFFFFF', OL, 2.5); ctext(c, '?', 238, 169, 'PB', 18, OL)


def sc12(c, w, h):
    bg(c, w, h, '#E9F6FF'); sun(c, 225, 332, 32); ball(c, 56, 318, 28); circ(c, 118, 338, 18, '#2F73C4', OL, 3)
    for k, col in enumerate(['#8E5BD0', '#8E5BD0', '#F5A623']):
        circ(c, 70 + k * 22, 250, 8, col, OL, 2.5)
    for k in range(7):
        circ(c, 28 + k * 38, 100, 8, ['#E5483D', '#2F73C4'][k % 2], OL, 2.5)
    robot(c, 150, 44, 1.2)
    circ(c, 238, 210, 24, '#DFF4FF', OL, 4); c.setLineWidth(8); c.setLineCap(1); c.line(255, 192, 278, 168)


# ---- Book 3 new-beat panels
def sc_turns(c, w, h):
    bg(c, w, h, '#DFF5E8')
    robot(c, 78, 50, 1.0); echo(c, 205, 150, 1.25)
    bubble(c, 22, 262, 112, 46, 'Robo talks', tail=(10, -16), size=13)
    bubble(c, 156, 300, 114, 46, 'Echo listens', tail=(10, -16), size=13)
    waves(c, 118, 190, 3, '#2F73C4', 1); waves(c, 222, 130, 0)
    # ear + mouth hints
    circ(c, 238, 232, 11, '#FFD9B8', OL, 2.5); circ(c, 238, 232, 4, None, OL, 2)
    circ(c, 60, 368, 13, '#FFD9B8', OL, 2.5); c.setStrokeColor(HexColor(OL)); c.setLineWidth(2.5); c.arc(54, 362, 66, 372, 200, 140)


def sc_details(c, w, h):
    c.setFillColor(HexColor('#223466')); c.rect(0, 0, w, h, fill=1, stroke=0)
    for x, y, r in [(40, 350, 9), (110, 372, 7), (170, 330, 8), (250, 372, 7), (28, 280, 7)]:
        sparkle(c, x, y, r, '#FFE9A0')
    circ(c, 218, 322, 36, '#FFF1C2', '#E8C65A', 3); circ(c, 236, 332, 30, '#223466', None)
    bubble(c, 22, 214, 120, 40, '“Play a song!”', tail=(-16, -14), size=11.5)
    bubble(c, 150, 150, 124, 40, '“Which one?”', tail=(16, -14), size=11.5, fill='#FFE9C7')
    
    robot(c, 66, -6 + 0, 0.01)  # (no-op keeps layout simple)
    echo(c, 228, 252, 1.0); note(c, 70, 296, '#F7B8DC'); note(c, 120, 330, '#9AD8FF'); note(c, 176, 292, '#C8F3A8')


def sc_wrong(c, w, h):
    bg(c, w, h, '#FFE9EC')
    robot(c, 78, 48, .95); echo(c, 212, 120, 1.2)
    bubble(c, 22, 236, 112, 44, '“bear”', tail=(10, -16), size=15)
    bubble(c, 156, 250, 112, 44, '“pear?”', tail=(-4, -16), size=15, fill='#FFF3C8')
    # bear face
    for dx in (-24, 24):
        circ(c, 78 + dx, 352, 11, '#9C5A2B', OL, 2.5)
    circ(c, 78, 335, 30, '#B46E37', OL, 3); circ(c, 78, 325, 12, '#E9C29A', OL, 2)
    circ(c, 67, 343, 3.4, OL, None); circ(c, 89, 343, 3.4, OL, None); circ(c, 78, 328, 3.4, OL, None)
    # pear
    f, st = fs(c, '#9ACD4A', OL, 3); c.ellipse(190, 296, 236, 348, fill=f, stroke=st)
    circ(c, 213, 356, 14, '#9ACD4A', OL, 3)
    c.setStrokeColor(HexColor(OL)); c.setLineWidth(3); c.line(213, 368, 217, 378)
    poly(c, [(217, 372), (236, 378), (226, 364)], '#4CAF50', OL, 2)
    circ(c, 250, 372, 13, '#FFFFFF', OL, 2.5); ctext(c, '?', 250, 366, 'PB', 16, OL)


# ---- Book 1 cover band (612 x 344)
def cover1(c, w, h):
    bg(c, w, h, '#CDEBFF', '#BEE3A0', 100)
    sun(c, 506, 270, 44); cloud(c, 60, 270, 1.2); cloud(c, 230, 300, .9)
    c.setFillColor(HexColor('#A7D68B')); c.ellipse(-80, -40, 330, 120, fill=1, stroke=0)
    ball(c, 112, 120, 30); square(c, 470, 118, 52, '#2F73C4'); triangle(c, 400, 120, 50, '#8E5BD0')
    robot(c, 300, 52, 1.4)
    for x, col in [(40, '#FF8FB1'), (560, '#FFFFFF'), (210, '#FFD84A'), (80, '#FFFFFF')]:
        flower(c, x, 70 + (x % 5) * 6, col)


# ------------------------------------------------------------------ book data
B1 = dict(
    num=1, file='Robo-Learns-To-See-Book-1.pdf', title='Robo Learns to See', short='Robo Learns to See',
    kicker='BOOK 1', sub='A Little Adventure in Colors, Shapes, and AI',
    accent='#1F5C99', bgs=['#EAF7FF', '#FFF6D6', '#EFE9FF', '#E9F8EC'],
    confetti=['#F5A623', '#4FA3FF', '#E86AA6', '#4CAF50'], cover_bg='#BFE4FF', back_bg='#1F5C99',
    cover_art=('vec', cover1),
    blurb='Robo rolls outside to greet the day and starts to notice colors, shapes, and patterns. '
          'Along the way, Robo learns how a camera sees, how computers learn from many examples, '
          'and why a computer\u2019s answer is a guess to check.',
    beats=[
        ('A New Day', 'Robo rolls outside to greet the day.<br/>\u201cWhat new things will I see today?\u201d',
         'Ask your child to name one thing they notice before Robo does.', sc1),
        ('Look Closely', 'A red ball. A yellow sun.<br/>\u201cOh, look at all the colors! This is fun!\u201d',
         'Point to the ball and sun, and name each color together.', sc2),
        ('Capture', 'Click, click! Robo takes a picture.<br/>\u201cLet\u2019s look a little closer!\u201d',
         'Explain that a camera records an image you can look at later.', sc3),
        ('The Frame', 'The picture shows what\u2019s in the frame.<br/>Robo looks again and names each thing.',
         'Compare the scene with its picture and ask what the camera included or left out.', sc4),
        ('A Shape to Notice', 'The ball is round. The sun is round, too.<br/>Can you spot two circles? One\u2014and two!',
         'Invite your child to find other round objects, such as a plate or a wheel.', sc5),
        ('More Shapes', 'A circle, a square, a triangle to see.<br/>Can you find each shape with me?',
         'Trace each shape with a finger and count its corners together.', sc6),
        ('Find the Pattern', 'Red, blue, red, blue\u2014what comes next?<br/>\u201cRed!\u201d says Robo. \u201cYou\u2019re good at this!\u201d',
         'Cover the last shape in the sequence and ask what belongs next.', sc7),
        ('Clues to Use', 'Colors, shapes, and patterns we see<br/>Give Robo clues: \u201cWhat could it be?\u201d',
         'Describe an object using two clues, such as its color and shape, and guess together.', sc8),
        ('Learning from Examples', 'Robo sees more pictures every day.<br/>Patterns help computers learn along the way.',
         'Explain that computers can learn patterns by looking at many examples.', sc9),
        ('Look Again', '\u201cIs this a ball?\u201d Robo asks with care.<br/>Let\u2019s look again\u2014what clues are there?',
         'Compare the object with a familiar ball and point out clues that match or differ.', sc10),
        ('Computers Can Be Wrong', 'Computers can guess and still get things wrong.<br/>We check together and help them along.',
         'Remind your child that a computer\u2019s answer is a guess to check, not always a fact.', sc11),
        ('A World Full of Clues', 'Find colors, shapes, and patterns with me.<br/>The world is full of clues\u2014look and see!',
         'Go on a clue hunt and spot a color, a shape, and a pattern together.', sc12),
    ],
    welcome=[('p', 'Thank you for reading <b>Robo Learns to See</b> together! This book is made for reading aloud, '
                   'pointing, and talking.'),
             ('bullets', ['Read the story lines first, then pause for the <b>Grown-Up Guide</b> at the bottom of each page.',
                          'Let your child notice something before Robo does\u2014there are no wrong answers.',
                          'Slow down. Pointing at colors, shapes, and patterns is the whole adventure.',
                          'The last activity pages work well on a walk, at the table, or on the floor.'])],
    learn=[('p', 'In this adventure, Robo (and you!) will discover:'),
           ('bullets', ['How to name <b>colors</b>, <b>shapes</b>, and <b>patterns</b>.',
                        'How a <b>camera</b> captures a picture and what a <b>frame</b> leaves out.',
                        'How computers can <b>learn from many examples</b>.',
                        'Why a computer\u2019s answer is a <b>guess to check</b>.'])],
    end=('The End', 'Robo looked closely, found clues, and checked the answers\u2014with your help!'),
    words=[('Camera', 'a tool that records a picture so we can look at it later.'),
           ('Frame', 'the edge of a picture. Only what is inside the frame gets captured.'),
           ('Pattern', 'something that repeats, like red, blue, red, blue.'),
           ('Clue', 'a little fact, such as a color or a shape, that helps us figure something out.'),
           ('Example', 'one picture or thing we look at to learn. Computers learn from many examples.'),
           ('Guess', 'an answer that might be right and might be wrong, so we check it.')],
    talk=['What colors did you spot in Robo\u2019s world?', 'Which shapes can you find in our room right now?',
          'What did the camera leave out of its picture?', 'How can we check if a computer\u2019s answer is right?',
          'What pattern can you make with blocks, snacks, or crayons?'],
    note=['Dear Grown-Up,',
          'Thank you for reading <b>Robo Learns to See</b> with your child. Computers do not see the way we do. They look for '
          'clues\u2014colors, shapes, and patterns\u2014and they learn from many examples.',
          'Robo\u2019s adventure keeps those big ideas small and playful: notice something, look for clues, and remember that a '
          'computer\u2019s answer is a guess to check. The Grown-Up Guides are here to start conversations, so feel free to '
          'change the questions, skip ahead, or linger on a page your child loves.',
          'Curiosity is the best first step into technology. Happy exploring!', '\u2014 Olanite B.A.'],
)

B2_ART = ['006', '011', '016', '021', '025', '031', '036', '041', '046', '051', '056', '058']
B2 = dict(
    num=2, file='Robo-Learns-To-See-Book-2-The-Sorting-Basket.pdf', title='The Sorting Basket', short='The Sorting Basket',
    kicker='ROBO LEARNS TO SEE \u00b7 BOOK 2', sub='A Little Adventure in Algorithms and Sorting',
    accent='#1E4F9C', bgs=['#FDF1E4', '#E8F2E4', '#FBE6D3', '#E6EEF9'],
    confetti=['#E5483D', '#2F73C4', '#F5A623', '#4CAF50'], cover_bg='#FFE9B8', back_bg='#1E4F9C',
    cover_art=('img', IMG2 % '000'),
    blurb='Toys are everywhere! Robo and Byte make a plan, sort by color, catch a mistake, and fix it. '
          'Along the way they learn what an algorithm is, why rules can change, and why finding mistakes helps us improve.',
    beats=[
        ('Notice a Problem', 'Robo and Byte see toys<br/>everywhere on the floor.<br/>"Look at this mess!" says Byte with a roar.',
         'Ask your child: "How can we tell when a room is messy?" Explain that noticing a problem is always the very first step in coming up with an algorithm to solve it.'),
        ('Choosing Steps', '"How can we clean this up?" Robo asks with a grin.<br/>"We make a plan first, then we begin!"',
         'Help your child name the first step they take when cleaning up toys. An algorithm is just a list of steps we follow in order!'),
        ('Sorting by Color', 'First rule: sort by color!<br/>Let\'s find the red.<br/>Into the red basket, just like Byte said.',
         'Ask your child to find all the red objects in the room right now. Grouping items by color is a basic form of data classification.'),
        ('Sorting by Color', 'Now find the blue toys, shining so bright.<br/>Into the blue basket, fitting just right!',
         'Talk about how sorting makes it much easier to find things later. Computers use sorting rules to organize millions of files instantly.'),
        ('Check Our Work', 'Red items are cozy, blue items are neat.<br/>Sorting by color is a wonderful treat!',
         "Ask your child to check if all the items in each basket match the basket's color. Checking our work is an important habit in science and math."),
        ('Finding a Mistake', 'Wait! Look inside the red basket with care...<br/>Oh no! A blue car is hiding in there!',
         'Explain that finding a mistake in code or rules is called "debugging." Everyone makes mistakes\u2014even computers!'),
        ('Fixing a Mistake', 'Mistakes happen sometimes, but we fix them right through.<br/>Take the blue car out and put it in blue!',
         'Ask your child: "How did we fix the mistake?" Emphasize that finding and fixing errors helps us learn and improve.'),
        ('Sorting by Shape', "Now let's change the rule!<br/>Let's sort by shape.<br/>Circles and squares take a brand new shape!",
         'Explain that rules can change depending on what we want to do. Computers also follow different sorting rules based on what we ask them to find.'),
        ('Patterns', 'Circle, square, circle, square\u2014<br/>what comes next?<br/>"A circle!" says Robo, passing the test!',
         'Ask your child what shape comes next in the pattern. Recognizing patterns helps artificial intelligence predict what will happen next.'),
        ('Computers Use Steps', 'Computers use steps just like me and like you,<br/>To sort all our pictures and data right through!',
         "Remind your child that computers don't think like humans; they follow precise step-by-step instructions (algorithms) written by people."),
        ('Your Turn!', "Now it's your turn! Can you sort and align?<br/>Group things together and watch them all shine!",
         'Encourage your child to grab some household items (like buttons or blocks) and sort them by size or color together.'),
        ('Celebrate!', 'Clean rooms and smart sorting are easy to see.<br/>Great job learning algorithms with Robo and me!',
         'Praise your child for completing the sorting adventure. Remind them that learning new technology is fun when we explore together!'),
    ],
    welcome=[('p', 'Thank you for reading <b>The Sorting Basket</b> together! Robo and Byte are about to tidy up a very messy room.'),
             ('bullets', ['Read the story lines, then pause for the <b>Grown-Up Guide</b> at the bottom of each page.',
                          'Have a few small toys, blocks, or buttons nearby so your child can sort along.',
                          'When Robo and Byte make a mistake, celebrate it. Fixing mistakes is how we learn.',
                          'Use the two activity pages near the end to make your own sorting plan.'])],
    learn=[('p', 'In this adventure, Robo and Byte (and you!) will discover:'),
           ('bullets', ['What an <b>algorithm</b> is: a list of steps we follow in order.',
                        'How to <b>sort</b> by a rule, such as color or shape.',
                        'How to <b>check our work</b> and <b>debug</b> a mistake.',
                        'Why rules can change depending on what we want to find.'])],
    end=('The End', 'Robo and Byte noticed a problem, made a plan, sorted, checked, and fixed a mistake. That is an algorithm in action!'),
    words=[('Algorithm', 'a list of steps we follow in order to solve a problem.'),
           ('Sort', 'to put things into groups using a rule, like color or shape.'),
           ('Rule', 'an instruction that tells us how to decide, such as "red goes in the red basket."'),
           ('Debug', 'to find and fix a mistake in code or in a set of rules.'),
           ('Pattern', 'something that repeats in a way we can predict, like circle, square, circle, square.'),
           ('Data', 'information, like pictures, files, or toys we count and sort.')],
    talk=['What was the very first step Robo and Byte took?', 'How did sorting make the room easier to clean?',
          'What mistake did Robo and Byte find, and how did they fix it?', 'What rule would you use to sort your toys?',
          'How could we change the rule to sort by shape instead of color?'],
    note=['Dear Grown-Up,',
          'Thank you for sharing <b>The Sorting Basket</b>. An algorithm sounds like a big word, but children already use algorithms: '
          'notice a problem, make a plan, follow the steps, check the work, and fix mistakes.',
          'Robo and Byte show that sorting is a rule we choose, and that rules can change. When your child finds the blue car hiding '
          'in the red basket, they are practicing debugging, a habit that helps in science, math, and everyday life.',
          'Try the Grown-Up Guides as a springboard, then let your child lead. Sorting socks, snacks, or crayons counts as computer science, too!',
          '\u2014 Olanite B.A.'],
)

B3_ART = {0: '003', 1: '006', 3: '009', 5: '012', 6: '015', 7: '018', 8: '021', 9: '024', 11: '027'}
B3 = dict(
    num=3, file='Robo-Learns-To-See-Book-3-The-Bot-That-Listens.pdf', title='The Bot That Listens', short='The Bot That Listens',
    kicker='ROBO LEARNS TO SEE \u00b7 BOOK 3', sub='A Little Adventure in Sounds, Prompts, and AI',
    accent='#1C4E9F', bgs=['#FFF1CF', '#DDF2E1', '#D9EEF7', '#FBE3D8'],
    confetti=['#F7943D', '#4FA3FF', '#E86AA6', '#4CAF50'], cover_bg='#FFDCC0', back_bg='#1C4E9F',
    cover_art=('img', IMG3 % '000'),
    blurb='Beep, chirp, clap, and hum! Robo meets Echo, a little bot that listens. Together they explore sounds, '
          'clear prompts, noisy rooms, high and low voices, and how computers turn sound into code.',
    beats=[
        ('Sounds All Around', 'Beep, chirp, clap, and hum!<br/>Sounds are everywhere we run!',
         'Ask your child to close their eyes for 5 seconds and name one sound they hear. Computers use microphones like digital ears.'),
        ('Meeting Echo', 'Meet little Echo, ready to hear!<br/>Speak a word soft, speak a word clear.',
         'Speak clearly so a microphone can pick up your voice.'),
        ('Taking Turns', 'Robo talks, then Echo hears.<br/>Echo talks, then Robo hears.<br/>When we take turns, everyone can listen.',
         'Play a talk-and-listen game: one person speaks while the other listens quietly, then switch. Voice assistants wait for you to finish speaking before they answer.'),
        ('Giving a Clear Prompt', '"Play a song!" says Robo with cheer.<br/>Echo listens close and near.<br/>Clear words help Echo know what to do.',
         'The words we say to an AI are called prompts. Specific prompts get better results than "Do something".'),
        ('Adding Details', '"Play a song!" says Robo. "Which one?" Echo asks.<br/>"A slow song about the moon!"<br/>Now Echo knows just what to do.',
         'Details make a prompt stronger: what you want, how, and about what. Try turning "Draw a picture" into "Draw a red kite flying over a green hill."'),
        ('Sound Patterns', '"Woof!" says the dog, "Meow!" says the cat.<br/>Echo learns which sound is that!',
         'Make an animal sound and have your child guess it. AI matches sound waves to pictures.'),
        ('Too Much Noise!', 'Crash, bang, boom! Too loud in the room!<br/>Echo gets confused in all the noise and gloom.',
         'Background noise makes it hard for people and computers to listen accurately.'),
        ('Clearing the Noise', 'Turn off the noise, quiet the room!<br/>Now Echo hears clearly and dispels the gloom.',
         "Ask: what do we do when it's too noisy to hear? Cleaning audio helps AI listen better."),
        ('High, Low, and Sing Along', 'High like a bird, low like a bear!<br/>La-la-la! Echo sings back with a happy beat!',
         'Try a squeaky high voice and a deep low voice. Computers measure pitch as frequency, and AI can make music too.'),
        ('How Computers Listen', 'Words turn to pictures, sounds turn to code,<br/>helping computers down the learning road!',
         'When we speak to a computer, it turns our voice into code so it can understand.'),
        ('Echo Can Be Wrong', 'Robo says \u201cbear.\u201d Echo hears \u201cpear.\u201d<br/>Computers can mishear, too.<br/>We say it again, nice and clear.',
         "Remind your child that a computer's answer is a guess to check. If it mishears, try again with clearer words, less noise, or a different way to say it."),
        ('Your Turn, and Cheers!', "Say hello to Echo! What will you say?<br/>Give a clear prompt to guide the way!<br/>You're a smart AI helper, let's give a big cheer!",
         'Have your child give Echo a clear prompt, like "Echo, make a happy beep!" Clear communication helps people and computers understand each other.'),
    ],
    welcome=[('p', 'Thank you for reading <b>The Bot That Listens</b> together! Robo is about to meet Echo, a little bot with big ears.'),
             ('bullets', ['Read the story lines, then pause for the <b>Grown-Up Guide</b> at the bottom of each page.',
                          'Try the sounds and voices out loud\u2014squeaky, deep, soft, and clear.',
                          'Practice giving Echo clear prompts. Short, specific words work best.',
                          'Find a quiet spot for the activity pages so everyone can listen well.'])],
    learn=[('p', 'In this adventure, Robo and Echo (and you!) will discover:'),
           ('bullets', ['How <b>microphones</b> work like digital ears.',
                        'What a <b>prompt</b> is and how clear words help.',
                        'Why <b>noise</b> makes listening hard, and how to quiet it.',
                        'How computers turn <b>sound into code</b>, and why they can still mishear.'])],
    end=('The End', 'Robo and Echo listened closely, cleared the noise, and learned that clear words help everyone understand.'),
    words=[('Prompt', 'the words we say or type to tell an AI what we want.'),
           ('Microphone', 'a tool that works like a digital ear to pick up sound.'),
           ('Noise', 'extra sounds in the background that make it harder to hear.'),
           ('Pitch', 'how high or low a sound is. Computers measure it as frequency.'),
           ('Code', 'a special set of instructions and numbers a computer can read.'),
           ('Sound pattern', 'a sound we can recognize because it repeats, like a dog\u2019s woof.')],
    talk=['What sounds can you hear right now?', 'What is a prompt, and why does Echo need a clear one?',
          'What happens to Echo when there is too much noise?', 'How can we make a room quiet enough to listen?',
          'What would you say to Echo if you wanted a happy beep?'],
    note=['Dear Grown-Up,',
          'Thank you for sharing <b>The Bot That Listens</b>. Voice assistants and other listening technology are becoming part '
          'of everyday life, and children can start with the basics: sounds are everywhere, a microphone is a digital ear, '
          'and clear words help computers understand us.',
          'Echo also shows two honest lessons. Noise makes listening harder for people and computers alike, and a computer can mishear, '
          'so a computer\u2019s answer is a guess to check.',
          'Use the Grown-Up Guides to talk, listen, and take turns. Your voice and your curiosity are the best teachers here.',
          '\u2014 Olanite B.A.'],
)
BOOKS = [B1, B2, B3]


# ------------------------------------------------------------------ page builders
def page_bg(c, color):
    global CURBG
    CURBG = color
    c.setFillColor(HexColor(color)); c.rect(-BL, -BL, W + 2 * BL, H + 2 * BL, fill=1, stroke=0)


def draw_art(c, B, i, x, y, w, h):
    beat = B['beats'][i]
    r = 24
    c.setFillColor(HexColor(mix('#000000', CURBG, .18)))
    c.roundRect(x + 4, y - 4, w, h, r, fill=1, stroke=0)
    if B['num'] == 1:
        vec_panel(c, beat[3], x, y, w, h, r)
    elif B['num'] == 2:
        image_cover(c, hires(IMG2 % B2_ART[i], w, h), x, y, w, h, r)
    else:
        if i in B3_ART:
            image_cover(c, hires(IMG3 % B3_ART[i], w, h), x, y, w, h, r)
        else:
            vec_panel(c, {2: sc_turns, 4: sc_details, 10: sc_wrong}[i], x, y, w, h, r)
    rr(c, x, y, w, h, r, None, B['accent'], 3)


def story_page(c, B, i):
    title, text, guide = B['beats'][i][:3]
    page_bg(c, B['bgs'][i % len(B['bgs'])]); deco(c, B, i)
    art_w, art_h = 290, 398
    ay = 180; gap = 18; col_w = W - 2 * M - art_w - gap
    left = (i % 2 == 0)
    ax = M if left else W - M - art_w
    tx = M + art_w + gap if left else M
    draw_art(c, B, i, ax, ay, art_w, art_h)
    card(c, tx, ay, col_w, art_h, 24, '#FFFFFF', B['accent'], 2.5)
    inner = col_w - 40
    tp, th = make_para(smart(title), 'PB', 21, B['accent'], inner, lk=1.2)
    bp, bh = make_para(smart(text), 'PM', 15, INK, inner, lk=1.42)
    s = 15
    while bh + th + 40 > art_h - 50 and s > 10:
        s -= .5; bp, bh = make_para(smart(text), 'PM', s, INK, inner, lk=1.42)
    total = 12 + 8 + th + 14 + bh
    y = ay + art_h / 2 + total / 2
    spaced(c, 'PAGE %d' % (i + 1), tx + 20, y - 9, 'PB', 9, '#7A8AA6', 1.8)
    y -= 12 + 8
    tp.drawOn(c, tx + 20, y - th); y -= th + 14
    bp.drawOn(c, tx + 20, y - bh)
    # guide box
    gh = 118; gy = 34
    card(c, M, gy, W - 2 * M, gh, 20, '#FFFFFF', B['accent'], 2, a=.82)
    spaced(c, 'GROWN-UP GUIDE', M + 22, gy + gh - 26, 'PB', 9, B['accent'], 1.8)
    fit_para(c, smart(guide), 'P', 11.5, INK, M + 22, gy + gh - 36, W - 2 * M - 44, gh - 52)


def title_page(c, B):
    page_bg(c, B['cover_bg'])
    band_h = 344; by = H - band_h
    kind, art = B['cover_art']
    if kind == 'img':
        image_cover(c, hires(art, W + 2 * BL, band_h + BL), -BL, by, W + 2 * BL, band_h + BL, 0)
    else:
        c.saveState(); c.translate(0, by)
        c.setFillColor(HexColor('#CDEBFF')); c.rect(-BL, 0, W + 2 * BL, band_h + BL, fill=1, stroke=0)
        art(c, W, band_h + BL); c.restoreState()
    cx, cy, cw, ch = M, 36, W - 2 * M, 260
    c.setFillColor(HexColor(mix('#000000', B['cover_bg'], .2))); c.roundRect(cx + 4, cy - 4, cw, ch, 30, fill=1, stroke=0)
    card(c, cx, cy, cw, ch, 30, '#FFFFFF', B['accent'], 3)
    mid = W / 2
    spaced(c, B['kicker'] if B['num'] > 1 else 'BOOK 1 \u00b7 THE SERIES BEGINS', mid, cy + ch - 34, 'PB', 10.5, '#C06A1C', 2.2, 'center')
    title = B['title'] if B['num'] > 1 else 'Robo Learns to See'
    sz = 40
    while stringWidth(title.upper(), 'PB', sz) > cw - 56 and sz > 20:
        sz -= 1
    ctext(c, title.upper(), mid, cy + ch - 82, 'PB', sz, B['accent'])
    c.setStrokeColor(HexColor('#F5A623')); c.setLineWidth(3); c.setLineCap(1); c.line(mid - 40, cy + ch - 100, mid + 40, cy + ch - 100)
    fit_para(c, B['sub'], 'PM', 16, INK, cx + 30, cy + ch - 114, cw - 60, 44, TA_CENTER)
    ctext(c, 'Written by ' + AUTHOR, mid, cy + 34, 'PM', 14, '#4A5878')


def copyright_page(c, B):
    page_bg(c, '#FFF8EC'); deco(c, B, 3)
    y = H - 150
    ctext(c, 'ROBO LEARNS TO SEE', W / 2, y, 'PB', 22, B['accent'])
    ctext(c, 'Book %d: %s' % (B['num'], B['title']), W / 2, y - 26, 'PM', 14, INK)
    ctext(c, B['sub'], W / 2, y - 46, 'P', 11, '#4A5878')
    c.setStrokeColor(HexColor('#F5A623')); c.setLineWidth(2.5); c.setLineCap(1); c.line(W / 2 - 30, y - 66, W / 2 + 30, y - 66)
    blocks = ['Copyright \u00a9 %s %s. All rights reserved.' % (YEAR, AUTHOR),
              'No part of this book may be reproduced, stored in a retrieval system, or transmitted in any form or by any '
              'means\u2014electronic, mechanical, photocopying, recording, or otherwise\u2014without the prior written permission '
              'of the author, except for brief quotations in reviews.',
              'This book is a work of fiction for young readers. The characters Robo, Byte, and Echo are imaginary.' if B['num'] > 1
              else 'This book is a work of fiction for young readers. The character Robo is imaginary.',
              'Written by %s' % AUTHOR,
              'First edition, %s' % YEAR,
              'Part of the Robo Learns to See series']
    yy = y - 100
    for k, t in enumerate(blocks):
        ph, _ = fit_para(c, t, 'PB' if k in (0, 3) else 'P', 11, INK, 90, yy, W - 180, 80, TA_CENTER)
        yy -= ph + 14


def flow_card(c, B, kicker, title, items, y_top=None, card_h=None, base=17, qr=False):
    page_bg(c, '#FFF6E3' if B['num'] != 3 else '#FFF1CF'); deco(c, B, 5)
    spaced(c, kicker, W / 2, H - 70, 'PB', 10.5, '#D9822B', 2.2, 'center')
    ctext(c, title, W / 2, H - 112, 'PB', 32, B['accent'])
    c.setStrokeColor(HexColor('#F5A623')); c.setLineWidth(3); c.setLineCap(1); c.line(W / 2 - 36, H - 128, W / 2 + 36, H - 128)
    cy, ch = 56, H - 56 - 150
    card(c, M + 6, cy, W - 2 * M - 12, ch, 28, '#FFFFFF', B['accent'], 2.5)
    x0 = M + 6 + 30; w = W - 2 * M - 12 - 60
    size = base
    res = 122 if qr else 0
    while True:
        paras = []
        total = 0
        for kind, data in items:
            if kind == 'p':
                p, ph = make_para(smart(data), 'P', size, INK, w); paras.append((p, ph, 12)); total += ph + 12
            elif kind == 'bullets':
                for b in data:
                    p, ph = make_para(smart(b), 'P', size, INK, w - 22, bulletFontName='PB', bulletFontSize=size,
                                      bulletIndent=2, leftIndent=22)
                    p.bulletText = '\u2022'
                    p.__init__(smart(b), ParagraphStyle('b', fontName='P', fontSize=size, leading=size * 1.38, textColor=HexColor(INK),
                                                         leftIndent=22, bulletIndent=2, bulletFontName='PB', bulletFontSize=size,
                                                         bulletColor=HexColor('#D9822B')), bulletText='\u2022')
                    pw, ph = p.wrap(w, 10000); paras.append((p, ph, 10)); total += ph + 10
            elif kind == 'terms':
                for tm, df in data:
                    p, ph = make_para('<font name="PB" color="%s">%s</font> \u2014 %s' % (B['accent'], tm, smart(df)), 'P', size, INK, w)
                    paras.append((p, ph, 12)); total += ph + 12
            elif kind == 'qs':
                for n, q in enumerate(data, 1):
                    p = Paragraph(smart(q), ParagraphStyle('q', fontName='P', fontSize=size, leading=size * 1.38, textColor=HexColor(INK),
                                                            leftIndent=26, bulletIndent=0, bulletFontName='PB', bulletFontSize=size,
                                                            bulletColor=HexColor('#D9822B')), bulletText='%d.' % n)
                    pw, ph = p.wrap(w, 10000); paras.append((p, ph, 14)); total += ph + 14
        if total <= ch - 56 - res or size <= 9:
            break
        size -= .5
    y = cy + res + (ch - res) / 2 + total / 2
    for p, ph, gap in paras:
        p.drawOn(c, x0, y - ph); y -= ph + gap
    if qr:
        bx, by_, bh = x0, cy + 20, 98
        rr(c, bx, by_, w, bh, 18, '#F1F7FF', B['accent'], 2)
        qr_box(c, URLS[str(B['num'])], bx + 18, by_ + 9, 80, 6)
        fit_para(c, '<b>See it in your room!</b> Scan this code to start the AR adventure. The last page of this book explains how to use it at home or in class.',
                 'P', 12, INK, bx + 124, by_ + bh - 14, w - 140, bh - 24)


def end_page(c, B):
    page_bg(c, B['cover_bg']); deco(c, B, 1)
    for k in range(18):
        a = k * 137.5
        x = 60 + (k * 97) % 490; y = 80 + (k * 61) % 450
        sparkle(c, x, y, 7 + k % 4 * 3, B['confetti'][k % 4])
    card(c, 70, 190, W - 140, 250, 34, '#FFFFFF', B['accent'], 3)
    ctext(c, B['end'][0].upper(), W / 2, 380, 'PB', 44, B['accent'])
    c.setStrokeColor(HexColor('#F5A623')); c.setLineWidth(3); c.setLineCap(1); c.line(W / 2 - 40, 360, W / 2 + 40, 360)
    fit_para(c, smart(B['end'][1]), 'PM', 16, INK, 100, 340, W - 200, 120, TA_CENTER)


# ---- activities
def act_header(c, B, n, title, intro):
    page_bg(c, ['#EAF7FF', '#FDF1E4', '#FFF1CF'][B['num'] - 1]); deco(c, B, n)
    spaced(c, 'ACTIVITY %d' % n, W / 2, H - 56, 'PB', 10.5, '#D9822B', 2.2, 'center')
    ctext(c, title, W / 2, H - 94, 'PB', 32, B['accent'])
    fit_para(c, smart(intro), 'PM', 12.5, INK, 70, H - 108, W - 140, 40, TA_CENTER)


def checkbox(c, x, y, s=18):
    rr(c, x, y, s, s, 4, '#FFFFFF', '#4A5878', 2)


def line_(c, x1, x2, y, col='#9AA7BF'):
    c.setStrokeColor(HexColor(col)); c.setLineWidth(1.3); c.setDash(1, 3); c.line(x1, y, x2, y); c.setDash()


def a1_b1(c, B):
    act_header(c, B, 1, 'Clue Hunt!', 'Hunt with a grown-up. Check each box when you find a clue.')
    rows = [('Something red', 'red'), ('Something round', 'round'), ('A pattern (stripes, dots, ...)', 'pattern'),
            ('A shape with corners', 'corner'), ('Something yellow', 'yellow')]
    y = 466
    for lbl, kind in rows:
        card(c, M, y - 44, W - 2 * M, 52, 18, '#FFFFFF', B['accent'], 1.8)
        ix, iy = M + 34, y - 18
        if kind == 'red': ball(c, ix, iy, 14)
        elif kind == 'round': circ(c, ix, iy, 14, None, B['accent'], 3)
        elif kind == 'pattern':
            for k in range(3): circ(c, ix - 18 + k * 18, iy, 7, ['#E5483D', '#2F73C4'][k % 2], OL, 2)
        elif kind == 'corner': square(c, ix, iy, 26, '#8E5BD0')
        else: circ(c, ix, iy, 14, '#FFD84A', '#F5A623', 3)
        fit_para(c, lbl, 'PB', 12.5, INK, M + 64, y - 6, 190, 30)
        checkbox(c, M + 262, y - 27)
        c.setFont('P', 9.5); c.setFillColor(HexColor('#4A5878')); c.drawString(M + 292, y - 24, 'I found:')
        line_(c, M + 340, W - M - 18, y - 26)
        y -= 62
    rr(c, M, 34, W - 2 * M, 118, 20, '#FFFFFF', B['accent'], 2.5, (6, 4))
    ctext(c, 'Draw your favorite clue here!', W / 2, 128, 'PB', 12, B['accent'])


def a2_b1(c, B):
    act_header(c, B, 2, 'Pattern Time!', 'Draw or color what comes next. Then make a pattern of your own.')
    rows = [[('c', '#E5483D'), ('c', '#2F73C4')] * 2, [('c', '#FFD84A'), ('s', '#8E5BD0')] * 2,
            [('c', '#E5483D'), ('c', '#E5483D'), ('c', '#2F73C4'), ('c', '#E5483D'), ('c', '#E5483D')]]
    y = 462
    for row in rows:
        card(c, M, y - 40, W - 2 * M, 48, 16, '#FFFFFF', B['accent'], 1.8)
        for k, (kind, col) in enumerate(row):
            x = M + 44 + k * 58
            (circ(c, x, y - 16, 15, col, OL, 2.5) if kind == 'c' else square(c, x, y - 16, 28, col))
        x = M + 44 + len(row) * 58
        c.setStrokeColor(HexColor(OL)); c.setLineWidth(2); c.setDash(4, 3); c.circle(x, y - 16, 15); c.setDash()
        ctext(c, '?', x, y - 23, 'PB', 18, OL)
        y -= 54
    card(c, M, 34, W - 2 * M, 262, 24, '#FFFFFF', B['accent'], 2.5)
    ctext(c, 'Make your own pattern', W / 2, 262, 'PB', 15, B['accent'])
    for r_ in range(2):
        for k in range(8):
            c.setStrokeColor(HexColor('#8A97B3')); c.setLineWidth(2); c.setDash(4, 3); c.circle(M + 52 + k * 62, 200 - r_ * 70, 20); c.setDash()
    fit_para(c, 'Color in the circles, then ask a grown-up to guess what comes next.', 'PM', 11.5, INK, M + 30, 98, W - 2 * M - 60, 30, TA_CENTER)


def sortmat(c, x, y, col, label):
    f, s = fs(c, '#D9A25E', '#7A4A1E', 3)
    rr(c, x, y, 150, 74, 12, '#E8B877', '#7A4A1E', 3)
    for k in range(1, 5):
        c.setStrokeColor(HexColor('#B9823F')); c.setLineWidth(1.5); c.line(x + 10, y + 8 + k * 11, x + 140, y + 8 + k * 11)
    rr(c, x - 6, y + 62, 162, 16, 8, col, '#7A4A1E', 3)
    ctext(c, label, x + 75, y - 18, 'PB', 13, INK)


def a1_b2(c, B):
    act_header(c, B, 1, 'Sort It Out!', 'Draw a line from each toy to the basket where it belongs. Use the color rule!')
    items = [(('b', '#E5483D'), 84, 444), (('s', '#2F73C4'), 190, 424), (('t', '#E5483D'), 296, 446), (('c', '#2F73C4'), 402, 420),
             (('s', '#E5483D'), 504, 442), (('b', '#2F73C4'), 138, 350), (('t', '#2F73C4'), 258, 338), (('c', '#E5483D'), 380, 352),
             (('s', '#E5483D'), 482, 336)]
    items = [(k, col, x, y) for ((k, col), x, y) in items]
    for k, col, x, y in items:
        if k == 'b' or k == 'c': ball(c, x, y, 20, col)
        elif k == 's': square(c, x, y, 38, col)
        else: triangle(c, x, y, 42, col)
    sortmat(c, 90, 90, '#E5483D', 'Red basket'); sortmat(c, 372, 90, '#2F73C4', 'Blue basket')
    card(c, M, 220, W - 2 * M, 54, 16, '#FFFFFF', B['accent'], 1.8)
    fit_para(c, 'Check your work! Do all the toys in each basket match the basket\u2019s color? '
                'Then try again and sort by <b>shape</b> instead.', 'P', 11.5, INK, M + 20, 266, W - 2 * M - 40, 40, TA_CENTER)


def a2_b2(c, B):
    act_header(c, B, 2, 'Make a Plan, Find the Bug!', 'Write or draw your steps, then hunt for the bugs.')
    card(c, M, 286, W - 2 * M, 190, 22, '#FFFFFF', B['accent'], 2)
    ctext(c, 'My clean-up algorithm', W / 2, 452, 'PB', 13, B['accent'])
    for k in range(4):
        yy = 420 - k * 38
        circ(c, M + 36, yy + 4, 13, '#FFD84A', '#F5A623', 2.5); ctext(c, str(k + 1), M + 36, yy - 1, 'PB', 13, INK)
        line_(c, M + 62, W - M - 24, yy - 4)
    card(c, M, 34, W - 2 * M, 236, 22, '#FFFFFF', B['accent'], 2)
    ctext(c, 'Bug hunt: circle the one that does not belong', W / 2, 244, 'PB', 13, B['accent'])
    rows = [[('c', '#E5483D')] * 3 + [('c', '#2F73C4')] + [('c', '#E5483D')],
            [('c', '#F5A623')] * 2 + [('s', '#F5A623')] + [('c', '#F5A623')] * 2,
            [('s', '#2F73C4'), ('c', '#2F73C4'), ('s', '#2F73C4'), ('c', '#2F73C4'), ('c', '#2F73C4')]]
    for r_, row in enumerate(rows):
        yy = 204 - r_ * 60
        for k, (kind, col) in enumerate(row):
            x = M + 72 + k * 92
            (circ(c, x, yy, 19, col, OL, 3) if kind == 'c' else square(c, x, yy, 36, col))
    ctext(c, 'Hint: the third row is a pattern. Which one breaks it?', W / 2, 50, 'PI', 9.5, '#4A5878')


def a1_b3(c, B):
    act_header(c, B, 1, 'Sound Hunt!', 'Listen with a grown-up. Check LOUD or QUIET, HIGH or LOW.')
    x0 = M + 8; wcol = 70
    card(c, M, 56, W - 2 * M, 410, 22, '#FFFFFF', B['accent'], 2)
    heads = ['Loud', 'Quiet', 'High', 'Low']
    for k, h_ in enumerate(heads):
        ctext(c, h_, M + 252 + k * 66 + 12, 436, 'PB', 11, B['accent'])
    sounds = ['a clap', 'a whisper', 'a drum', 'a bird\u2019s chirp', 'a bear\u2019s growl', 'a doorbell', 'my own sound: ______']
    y = 412
    for s_ in sounds:
        c.setFont('PM', 12.5); c.setFillColor(HexColor(INK)); c.drawString(M + 24, y - 6, s_)
        for k in range(4):
            checkbox(c, M + 252 + k * 66 + 3, y - 12, 18)
        c.setStrokeColor(HexColor('#E5E9F2')); c.setLineWidth(1); c.line(M + 18, y - 24, W - M - 18, y - 24)
        y -= 44
    fit_para(c, 'Fun fact: computers measure how high or low a sound is as <b>frequency</b>.', 'P', 10.5, '#4A5878', M + 20, 100, W - 2 * M - 40, 30, TA_CENTER)


def a2_b3(c, B):
    act_header(c, B, 2, 'Prompt Practice', 'Rewrite each fuzzy prompt so Echo knows what to do.')
    card(c, M, 372, W - 2 * M, 96, 20, '#FFF1D6', '#F5A623', 2)
    ctext(c, 'EXAMPLE', M + 54, 442, 'PB', 9, '#D9822B')
    c.setFont('P', 12); c.setFillColor(HexColor(INK))
    c.drawString(M + 22, 420, 'Fuzzy:  \u201cDo something!\u201d')
    c.setFont('PB', 12); c.drawString(M + 22, 394, 'Clear:  \u201cEcho, make a happy beep!\u201d')
    y = 342
    for fz in ['\u201cPlay it.\u201d', '\u201cSing.\u201d', '\u201cMake a sound.\u201d']:
        c.setFont('P', 12); c.setFillColor(HexColor(INK)); c.drawString(M + 22, y, 'Fuzzy:  ' + fz)
        c.setFont('PB', 12); c.drawString(M + 22, y - 24, 'Clear:')
        line_(c, M + 70, W - M - 22, y - 26); y -= 54
    card(c, M, 34, W - 2 * M, 130, 20, '#FFFFFF', B['accent'], 2)
    ctext(c, 'Quiet-room checklist', W / 2, 138, 'PB', 13, B['accent'])
    for k, t in enumerate(['Turn off the noise.', 'Get close to the microphone.', 'Speak slowly and clearly.']):
        checkbox(c, M + 36, 100 - k * 26 + 0, 16); c.setFont('PM', 12); c.setFillColor(HexColor(INK)); c.drawString(M + 64, 104 - k * 26 - 4, t)


def author_note(c, B):
    page_bg(c, '#FFF8EC'); deco(c, B, 4)
    spaced(c, 'FROM THE AUTHOR', W / 2, H - 70, 'PB', 10.5, '#D9822B', 2.2, 'center')
    ctext(c, 'Author\u2019s Note', W / 2, H - 112, 'PB', 32, B['accent'])
    c.setStrokeColor(HexColor('#F5A623')); c.setLineWidth(3); c.setLineCap(1); c.line(W / 2 - 36, H - 128, W / 2 + 36, H - 128)
    card(c, M + 6, 56, W - 2 * M - 12, H - 56 - 150, 28, '#FFFFFF', B['accent'], 2.5)
    w = W - 2 * M - 12 - 80; size = 14
    while True:
        ps = []; tot = 0
        for k, t in enumerate(B['note']):
            fnt = 'PI' if k == len(B['note']) - 1 else 'P'
            p, ph = make_para(t, fnt, size, INK, w, TA_LEFT, 1.45); ps.append((p, ph)); tot += ph + 10
        if tot <= H - 56 - 150 - 60 or size <= 9: break
        size -= .5
    y = 56 + (H - 56 - 150) / 2 + tot / 2
    for p, ph in ps:
        p.drawOn(c, M + 6 + 40, y - ph); y -= ph + 10


def series_page(c, B):
    page_bg(c, '#FFF6E3'); deco(c, B, 2)
    spaced(c, 'KEEP EXPLORING', W / 2, H - 70, 'PB', 10.5, '#D9822B', 2.2, 'center')
    ctext(c, 'The Robo Series', W / 2, H - 112, 'PB', 32, B['accent'])
    c.setStrokeColor(HexColor('#F5A623')); c.setLineWidth(3); c.setLineCap(1); c.line(W / 2 - 36, H - 128, W / 2 + 36, H - 128)
    y = H - 160
    for bk in BOOKS:
        cur = bk is B
        card(c, M + 6, y - 112, W - 2 * M - 12, 118, 24, '#FFFFFF', bk['accent'], 3 if cur else 1.8)
        circ(c, M + 60, y - 53, 28, bk['accent'], None); ctext(c, str(bk['num']), M + 60, y - 63, 'PB', 28, '#FFFFFF')
        t = 'Robo Learns to See' if bk['num'] == 1 else bk['title']
        fit_para(c, t, 'PB', 18, bk['accent'], M + 110, y - 26, W - 2 * M - 150, 30)
        fit_para(c, bk['sub'], 'PM', 12, INK, M + 110, y - 54, W - 2 * M - 150, 34)
        fit_para(c, ['Colors, shapes, and how computers see.', 'Algorithms, sorting, and fixing mistakes.',
                     'Sounds, prompts, and how computers listen.'][bk['num'] - 1], 'P', 10.5, '#4A5878', M + 110, y - 82, W - 2 * M - 150, 30)
        if cur:
            spaced(c, 'YOU ARE HERE', W - M - 28, y - 14, 'PB', 7.5, '#D9822B', 1.4, 'left') if False else None
        y -= 132


def back_cover(c, B):
    page_bg(c, B['back_bg'])
    for k in range(14):
        sparkle(c, 40 + (k * 83) % 540, 40 + (k * 71) % 540, 5 + k % 3 * 2, ['#FFD84A', '#FFFFFF', '#9AD8FF'][k % 3])
    kind, art = B['cover_art']
    aw, ah = 300, 170; ax = (W - aw) / 2; ay = H - 70 - ah
    c.saveState(); alpha_fill(c, .25); c.setFillColor(HexColor('#000000')); c.roundRect(ax + 4, ay - 4, aw, ah, 22, fill=1, stroke=0); c.restoreState()
    if kind == 'img':
        image_cover(c, art, ax, ay, aw, ah, 22)
    else:
        vec_panel(c, lambda cc, w, h: (cc.scale(aw / 612.0, ah / 344.0), cover1(cc, 612, 344)), ax, ay, aw, ah, 22)
    rr(c, ax, ay, aw, ah, 22, None, '#FFFFFF', 4)
    ctext(c, 'ROBO LEARNS TO SEE', W / 2, ay - 40, 'PB', 15, '#FFD84A')
    t = 'Book %d: %s' % (B['num'], B['title']) if B['num'] > 1 else 'Book 1'
    ctext(c, t.upper() if B['num'] > 1 else t, W / 2, ay - 66, 'PB', 18 if B['num'] > 1 else 16, '#FFFFFF')
    fit_para(c, B['blurb'], 'PM', 13, '#FFFFFF', 86, ay - 96, W - 172, 150, TA_CENTER)
    ctext(c, 'by ' + AUTHOR, W / 2, 62, 'PB', 13, '#FFFFFF')


def bullets_fit(c, items, x, y_top, w, max_h, size, numbered=False, color=INK, draw=True):
    sz = size
    while True:
        ps = []; tot = 0
        for n, it in enumerate(items, 1):
            p = Paragraph(smart(it), ParagraphStyle('bf', fontName='P', fontSize=sz, leading=sz * 1.3, textColor=HexColor(color),
                                                     leftIndent=16, bulletIndent=0, bulletFontName='PB', bulletFontSize=sz,
                                                     bulletColor=HexColor('#C06A1C')), bulletText=('%d.' % n) if numbered else '\u2022')
            pw, ph = p.wrap(w, 10000); ps.append((p, ph)); tot += ph + 4
        if tot <= max_h or sz <= 8:
            break
        sz -= .5
    if draw:
        y = y_top
        for p, ph in ps:
            p.drawOn(c, x, y - ph); y -= ph + 4
    return sz


def ar_guide(c, B):
    import bookcopy
    D = bookcopy.HUMAN[B['num']]['ar']
    page_bg(c, ['#EAF7FF', '#FDF1E4', '#FFF1CF'][B['num'] - 1]); deco(c, B, 6)
    spaced(c, 'FOR TEACHERS AND FAMILIES', W / 2, 556, 'PB', 9.5, '#C06A1C', 2.0, 'center')
    ctext(c, 'AR Adventure Guide', W / 2, 522, 'PB', 28, B['accent'])
    c.setStrokeColor(HexColor('#F5A623')); c.setLineWidth(3); c.setLineCap(1); c.line(W / 2 - 36, 508, W / 2 + 36, 508)
    url = URLS[str(B['num'])]
    # row 1: QR + steps
    r1y, r1h = 346, 150
    card(c, M, r1y, 186, r1h, 20, '#FFFFFF', B['accent'], 2)
    qr_box(c, url, M + 47, r1y + 46, 92, 5)
    ctext(c, 'Scan to start', M + 93, r1y + 30, 'PB', 11, B['accent'])
    fit_para(c, url.replace('https://', ''), 'PM', 7.5, '#4A5878', M + 6, r1y + 23, 174, 11, TA_CENTER, 7)
    card(c, M + 200, r1y, W - 2 * M - 200, r1h, 20, '#FFFFFF', B['accent'], 2)
    ctext(c, 'Start in four steps', M + 200 + (W - 2 * M - 200) / 2, r1y + r1h - 26, 'PB', 13, B['accent'])
    bullets_fit(c, bookcopy.AR_STEPS, M + 218, r1y + r1h - 40, W - 2 * M - 236, r1h - 52, 11, True)
    # row 2: try it / class routine
    r2y, r2h = 214, 120; cw2 = (W - 2 * M - 14) / 2
    card(c, M, r2y, cw2, r2h, 20, '#FFFFFF', B['accent'], 2)
    ctext(c, 'Try it in AR', M + cw2 / 2, r2y + r2h - 24, 'PB', 13, B['accent'])
    bullets_fit(c, D['try_'], M + 16, r2y + r2h - 36, cw2 - 32, r2h - 44, 10.5)
    card(c, M + cw2 + 14, r2y, cw2, r2h, 20, '#FFFFFF', B['accent'], 2)
    ctext(c, 'A 15-minute class routine', M + cw2 + 14 + cw2 / 2, r2y + r2h - 24, 'PB', 13, B['accent'])
    bullets_fit(c, bookcopy.AR_ROUTINE, M + cw2 + 30, r2y + r2h - 36, cw2 - 32, r2h - 44, 10.5)
    # row 3: practice
    r3y, r3h = 130, 70
    card(c, M, r3y, W - 2 * M, r3h, 20, '#FFFFFF', B['accent'], 2)
    spaced(c, 'CLASS PRACTICE', M + 18, r3y + r3h - 17, 'PB', 9, '#C06A1C', 1.6)
    bullets_fit(c, D['practice'], M + 18, r3y + r3h - 24, W - 2 * M - 36, r3h - 28, 10)
    # row 4: good to know
    r4y, r4h = 36, 82
    card(c, M, r4y, W - 2 * M, r4h, 20, '#F1F7FF', B['accent'], 1.8)
    spaced(c, 'GOOD TO KNOW', M + 18, r4y + r4h - 17, 'PB', 9, '#C06A1C', 1.6)
    fit_para(c, bookcopy.AR_KNOW, 'P', 10, INK, M + 18, r4y + r4h - 24, W - 2 * M - 36, r4h - 30, TA_LEFT, 8)


def qr_cards():
    from reportlab.lib.pagesizes import letter
    path = os.path.join(OUT, 'Robo-AR-Classroom-QR-Cards.pdf')
    c = canvas.Canvas(path, pagesize=letter, initialFontName='P', initialFontSize=12); c.setTitle('Robo Learns to See - AR classroom QR cards'); c.setAuthor(AUTHOR)
    pw, ph = letter
    ctext(c, 'Robo Learns to See: AR Adventures', pw / 2, ph - 54, 'PB', 22, '#1F5C99')
    ctext(c, 'Cut apart and post at a learning station. Scan, tap Start AR, and explore.', pw / 2, ph - 74, 'P', 11, '#4A5878')
    for k, B in enumerate([B1, B2, B3]):
        y = ph - 110 - (k + 1) * 218 + 24
        rr(c, 54, y, pw - 108, 196, 22, '#FFFFFF', B['accent'], 2.5, (6, 4))
        qr_box(c, URLS[str(B['num'])], 78, y + 28, 140, 7)
        ctext(c, 'Book %d' % B['num'], 258, y + 150, 'PB', 11, '#C06A1C') if False else None
        c.setFont('PB', 11); c.setFillColor(HexColor('#C06A1C')); c.drawString(256, y + 160, 'BOOK %d' % B['num'])
        fit_para(c, B['title'] if B['num'] > 1 else 'Robo Learns to See', 'PB', 22, B['accent'], 256, y + 150, pw - 54 - 276 - 20, 60)
        fit_para(c, B['sub'], 'PM', 12, INK, 256, y + 100, pw - 54 - 276 - 20, 40)
        fit_para(c, 'Scan with a phone or tablet camera. ' + URLS[str(B['num'])].replace('https://', ''), 'P', 9, '#4A5878', 256, y + 56, pw - 54 - 276 - 20, 40)
    c.showPage(); c.save(); print('wrote', path)


# ------------------------------------------------------------------ assemble
def build(B):
    path = os.path.join(OUT, B['file'])
    c = canvas.Canvas(path, pagesize=(PW, PH), initialFontName='P', initialFontSize=12)
    c.setTitle('Robo Learns to See - Book %d: %s' % (B['num'], B['title']) if B['num'] > 1 else 'Robo Learns to See')
    c.setAuthor(AUTHOR); c.setSubject(B['sub']); c.setCreator('ReportLab')
    pages = [lambda: title_page(c, B), lambda: copyright_page(c, B),
             lambda: flow_card(c, B, 'BEFORE YOU BEGIN', 'Welcome, Grown-Ups!', B['welcome'], qr=True),
             lambda: flow_card(c, B, 'WHAT WE\u2019LL LEARN', 'Our Big Ideas', B['learn'])]
    pages += [(lambda i=i: story_page(c, B, i)) for i in range(12)]
    acts = {1: (a1_b1, a2_b1), 2: (a1_b2, a2_b2), 3: (a1_b3, a2_b3)}[B['num']]
    pages += [lambda: end_page(c, B),
              lambda: flow_card(c, B, 'LET\u2019S REVIEW', 'Words to Know', [('terms', B['words'])], base=16),
              lambda: flow_card(c, B, 'TALK ABOUT IT', 'Questions to Share', [('qs', B['talk'])], base=17),
              lambda: acts[0](c, B), lambda: acts[1](c, B),
              lambda: author_note(c, B), lambda: series_page(c, B), lambda: ar_guide(c, B)]
    assert len(pages) == 24, len(pages)
    for n, fn in enumerate(pages, 1):
        ox = 0 if n % 2 else BL          # odd (right-hand) pages bleed on the right; even pages on the left
        c.saveState(); c.translate(ox, BL); fn(); c.restoreState()
        try:
            c.setTrimBox((ox, BL, ox + W, BL + H)); c.setBleedBox((0, 0, PW, PH))
        except Exception:
            pass
        c.showPage()
    c.save()
    print('wrote', path)


import bookcopy
for _B in BOOKS:
    _B.update({k: v for k, v in bookcopy.HUMAN[_B['num']].items() if k != 'ar'})

if __name__ == '__main__':
    for B in BOOKS:
        build(B)
    qr_cards()
