# -*- coding: utf-8 -*-
"""
Generator for Guilherme Damasceno's Cyberpunk Tactical GitHub Profile SVGs.
Usage:
  pip install fonttools
  python scripts/build_svgs.py
"""

import os
import re
import urllib.request
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = str(ROOT / "assets" / "profile-readme")
FONT_DIR = ROOT / ".cache" / "fonts"
FONT_DIR.mkdir(parents=True, exist_ok=True)

FONT_URLS = {
    "ChakraPetch-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/chakrapetch/ChakraPetch-Bold.ttf",
    "ChakraPetch-SemiBold.ttf": "https://github.com/google/fonts/raw/main/ofl/chakrapetch/ChakraPetch-SemiBold.ttf",
    "JetBrainsMono-Regular.ttf": "https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/ttf/JetBrainsMono-Regular.ttf",
    "JetBrainsMono-SemiBold.ttf": "https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/ttf/JetBrainsMono-SemiBold.ttf",
    "JetBrainsMono-Bold.ttf": "https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/ttf/JetBrainsMono-Bold.ttf",
}

for fname, url in FONT_URLS.items():
    fpath = FONT_DIR / fname
    if not fpath.exists():
        urllib.request.urlretrieve(url, fpath)

FONTS = {
    "display_bold": TTFont(str(FONT_DIR / "ChakraPetch-Bold.ttf")),
    "display_semi": TTFont(str(FONT_DIR / "ChakraPetch-SemiBold.ttf")),
    "mono_reg": TTFont(str(FONT_DIR / "JetBrainsMono-Regular.ttf")),
    "mono_semi": TTFont(str(FONT_DIR / "JetBrainsMono-SemiBold.ttf")),
    "mono_bold": TTFont(str(FONT_DIR / "JetBrainsMono-Bold.ttf")),
}

NIGHT = "#06060b"
PANEL = "#0b0d16"
LINE = "#232842"
TEXT = "#f4f3ee"
MUTED = "#bdbfd0"
DIM = "#85889c"
YELLOW = "#fcee0a"
CYAN = "#00f0ff"
MAGENTA = "#ff2a6d"
EMERALD = "#00ff9d"


def round_svg_path(d: str) -> str:
    return re.sub(r"-?\d+\.\d+", lambda m: f"{float(m.group(0)):.1f}".rstrip("0").rstrip("."), d)


def measure_text(text: str, font_key: str, size: float, tracking: float = 0.0) -> float:
    font = FONTS[font_key]
    upem = font["head"].unitsPerEm
    scale = size / upem
    cmap = font.getBestCmap()
    hmtx = font["hmtx"].metrics
    total = 0.0
    for idx, ch in enumerate(text):
        gname = cmap.get(ord(ch)) or cmap.get(ord(" ")) or ".notdef"
        adv, _ = hmtx.get(gname, (upem * 0.5, 0))
        total += adv * scale
        if idx + 1 < len(text):
            total += tracking
    return total


def text_to_path_d(
    text: str,
    x: float,
    y: float,
    font_key: str,
    size: float,
    tracking: float = 0.0,
    align: str = "left",
    max_right: float = None,
) -> str:
    if not text:
        return ""
    w = measure_text(text, font_key, size, tracking)
    if align == "center":
        x -= w / 2.0
    elif align == "right":
        x -= w

    if max_right is not None and (x + w) > max_right + 1.0:
        raise ValueError(f"Text overflow ({x+w:.1f} > {max_right}): {text!r}")

    font = FONTS[font_key]
    upem = font["head"].unitsPerEm
    scale = size / upem
    cmap = font.getBestCmap()
    glyph_set = font.getGlyphSet()
    hmtx = font["hmtx"].metrics

    pen = SVGPathPen(glyph_set)
    cur_x = x
    for idx, ch in enumerate(text):
        gname = cmap.get(ord(ch))
        if not gname or gname not in glyph_set:
            adv, _ = hmtx.get(cmap.get(ord(" "), ".notdef"), (upem * 0.5, 0))
            cur_x += adv * scale + tracking
            continue
        adv, _ = hmtx[gname]
        if ch != " ":
            tpen = TransformPen(pen, (scale, 0.0, 0.0, -scale, cur_x, y))
            glyph_set[gname].draw(tpen)
        cur_x += adv * scale + (tracking if idx + 1 < len(text) else 0.0)

    return round_svg_path(pen.getCommands())


def path_el(
    text: str,
    x: float,
    y: float,
    font_key: str,
    size: float,
    fill: str = TEXT,
    tracking: float = 0.0,
    align: str = "left",
    max_right: float = None,
    extra: str = "",
) -> str:
    d = text_to_path_d(text, x, y, font_key, size, tracking, align, max_right=max_right)
    if not d:
        return ""
    ext = f" {extra}" if extra else ""
    return f'<path d="{d}" fill="{fill}"{ext}/>'


def wrap_lines(text: str, font_key: str, size: float, max_width: float, tracking: float = 0.0):
    words = text.split(" ")
    lines = []
    cur = ""
    for word in words:
        cand = word if not cur else f"{cur} {word}"
        if measure_text(cand, font_key, size, tracking) <= max_width:
            cur = cand
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def chamfer_rect(x, y, w, h, cut=12, fill=PANEL, stroke=LINE, sw=1.2, extra=""):
    pts = f"{x+cut},{y} {x+w},{y} {x+w},{y+h-cut} {x+w-cut},{y+h} {x},{y+h} {x},{y+cut}"
    ext = f" {extra}" if extra else ""
    return f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{ext}/>'


def draw_chip_row(chips, start_x, y, accent_color=CYAN, max_x=856):
    out = []
    cx = start_x
    cy = y
    h = 22
    for label in chips:
        tw = measure_text(label, "mono_semi", 10.0, 0.2)
        cw = round(tw + 18, 1)
        if cx + cw > max_x:
            cx = start_x
            cy += 27
        pts = f"{cx+5},{cy} {cx+cw},{cy} {cx+cw},{cy+h-5} {cx+cw-5},{cy+h} {cx},{cy+h} {cx},{cy+5}"
        out.append(
            f'<polygon points="{pts}" fill="#080a13" stroke="{accent_color}" stroke-opacity="0.48" stroke-width="1"/>'
        )
        out.append(path_el(label, cx + cw / 2, cy + 14.6, "mono_semi", 10.0, TEXT, 0.2, "center"))
        cx += cw + 6.5
    return "\n".join(out), cy + h


def xml_esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def save_svg(filename: str, content: str):
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content.strip() + "\n")
    print(f"OK {filename:22s} ({len(content):>7,} bytes)")


# ============================================================================
# 1. HERO BANNER (banner.svg — 880 x 336)
# ============================================================================
def build_banner():
    w, h = 880, 336
    g_d = text_to_path_d("GUILHERME", 46, 126, "display_bold", 68, -0.5, max_right=556)
    d_d = text_to_path_d("DAMASCENO", 46, 196, "display_bold", 68, -0.5, max_right=556)

    term_text = "java-17 · spring-boot · c# · .net · python · langgraph"
    term_w = round(measure_text(term_text, "mono_semi", 10.8, 0.1) + 12, 1)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Guilherme Damasceno — Desenvolvedor Full Stack, Back-end Resiliente e Agentes de IA">',
        "<title>Guilherme Damasceno — Desenvolvedor Full Stack, Back-end Resiliente e Agentes de IA</title>",
        "<defs>",
        '  <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="#111528" stroke-width="1"/></pattern>',
        '  <pattern id="hz" width="16" height="16" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><rect width="8" height="16" fill="#fcee0a"/><rect x="8" width="8" height="16" fill="#06060b"/></pattern>',
        '  <radialGradient id="g1" cx="78%" cy="28%" r="55%"><stop offset="0" stop-color="#00f0ff" stop-opacity="0.14"/><stop offset="1" stop-color="#00f0ff" stop-opacity="0"/></radialGradient>',
        '  <radialGradient id="g2" cx="14%" cy="88%" r="50%"><stop offset="0" stop-color="#ff2a6d" stop-opacity="0.12"/><stop offset="1" stop-color="#ff2a6d" stop-opacity="0"/></radialGradient>',
        '  <linearGradient id="beam" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#00f0ff" stop-opacity="0"/><stop offset="0.5" stop-color="#00f0ff" stop-opacity="0.08"/><stop offset="1" stop-color="#00f0ff" stop-opacity="0"/></linearGradient>',
        '  <clipPath id="tclip"><rect x="46" y="266" width="500" height="34"/></clipPath>',
        "</defs>",
        "<style>",
        "  .blink{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}",
        "  .pulse{animation:pulse 2.2s ease-in-out infinite}@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}",
        "  .ga{animation:ga 6.5s infinite}.gb{animation:gb 6.5s infinite}",
        "  @keyframes ga{0%,90%,100%{transform:translate(0,0);opacity:0}92%{transform:translate(3px,-1px);opacity:.72}94%{transform:translate(-3px,1px);opacity:.72}96%{transform:translate(0,0);opacity:0}}",
        "  @keyframes gb{0%,90%,100%{transform:translate(0,0);opacity:0}92%{transform:translate(-3px,1px);opacity:.72}94%{transform:translate(3px,-1px);opacity:.72}96%{transform:translate(0,0);opacity:0}}",
        "  .beam{animation:beam 6.5s linear infinite}@keyframes beam{from{transform:translateY(-70px)}to{transform:translateY(340px)}}",
        f"  .tp{{animation:tp 9s steps(44,end) infinite}}@keyframes tp{{0%{{transform:translateX(0)}}46%,100%{{transform:translateX({term_w}px)}}}}",
        "  @media (prefers-reduced-motion: reduce){.tp{display:none}*{animation:none!important}}",
        "</style>",
        f'<rect width="{w}" height="{h}" fill="{NIGHT}"/>',
        f'<rect width="{w}" height="{h}" fill="url(#grid)"/>',
        f'<rect width="{w}" height="{h}" fill="url(#g1)"/>',
        f'<rect width="{w}" height="{h}" fill="url(#g2)"/>',
        '<rect class="beam" x="0" y="0" width="880" height="64" fill="url(#beam)"/>',
        f'<rect x="0" y="0" width="10" height="{h-14}" fill="{YELLOW}"/>',
        f'<path d="M26 16H42M26 16V32M864 16H848M864 16V32" stroke="{CYAN}" stroke-width="1.5" fill="none" opacity="0.65"/>',
        f'<rect class="pulse" x="48" y="34" width="7" height="7" fill="{YELLOW}"/>',
        path_el("SYS.ID // GD-01 · PERFIL ATIVO · DESENVOLVEDOR FULL STACK", 64, 41.5, "mono_bold", 10.2, CYAN, 0.9, max_right=556),
        path_el("SOROCABA / SP · BRT", 854, 27, "mono_semi", 9.5, DIM, 0.8, "right"),
        f'<path class="ga" d="{g_d}" fill="{MAGENTA}"/>',
        f'<path class="gb" d="{g_d}" fill="{CYAN}"/>',
        f'<path d="{g_d}" fill="{YELLOW}"/>',
        f'<path class="ga" d="{d_d}" fill="{CYAN}"/>',
        f'<path class="gb" d="{d_d}" fill="{MAGENTA}"/>',
        f'<path d="{d_d}" fill="{TEXT}"/>',
        f'<rect x="48" y="214" width="290" height="2.5" fill="{CYAN}" opacity="0.7"/>',
        f'<rect x="48" y="214" width="68" height="2.5" fill="{YELLOW}"/>',
        path_el("BACK-END RESILIENTE · INTEGRAÇÕES · AGENTES DE IA EM PRODUÇÃO", 48, 243, "display_semi", 13.2, MUTED, 0.5, max_right=556),
        # Terminal Line Box
        chamfer_rect(46, 266, 502, 34, cut=8, fill="#090b14", stroke=LINE, sw=1.2),
        f'<rect x="46" y="266" width="3.5" height="34" fill="{CYAN}"/>',
        path_el("root@gd:~$", 58, 287, "mono_bold", 10.8, CYAN, 0.1),
        path_el(term_text, 132, 287, "mono_semi", 10.8, YELLOW, 0.1, max_right=540),
        f'<g clip-path="url(#tclip)"><g class="tp"><rect x="131" y="270" width="{term_w+24}" height="26" fill="#090b14"/><rect class="blink" x="132" y="275" width="7" height="15" fill="{YELLOW}"/></g></g>',
        # Right Holographic ID Card
        chamfer_rect(574, 38, 282, 262, cut=14, fill=PANEL, stroke=CYAN, sw=1.4),
        '<polygon points="574,52 588,38 856,38 856,64 574,64" fill="#fcee0a"/>',
        path_el("IDENTITY RECORD // GD-01", 590, 55, "mono_bold", 10.2, NIGHT, 0.6),
        f'<rect class="blink" x="834" y="46" width="9" height="9" fill="{MAGENTA}"/>',
        chamfer_rect(590, 78, 56, 56, cut=9, fill="#080a12", stroke=YELLOW, sw=1.5),
        path_el("GD", 618, 115, "display_bold", 26, YELLOW, 0.5, "center"),
        path_el("OPERADOR // LVL-04", 658, 92, "mono_bold", 9.5, CYAN, 0.7),
        path_el("G. DAMASCENO", 658, 113, "display_bold", 19, TEXT, 0.3, max_right=846),
        path_el("FULL STACK ENGINEER", 658, 130, "mono_semi", 9.8, YELLOW, 0.5, max_right=846),
        f'<line x1="590" y1="146" x2="840" y2="146" stroke="{LINE}" stroke-width="1"/>',
        path_el("VÍNCULO", 590, 166, "mono_semi", 9.2, DIM, 0.5),
        path_el("DEVELCODE", 666, 166, "mono_bold", 10.2, TEXT, 0.4, max_right=846),
        path_el("SQUADS", 590, 188, "mono_semi", 9.2, DIM, 0.5),
        path_el("RD SAÚDE · LEROY MERLIN", 666, 188, "mono_bold", 10.0, CYAN, 0.2, max_right=846),
        path_el("CORE", 590, 210, "mono_semi", 9.2, DIM, 0.5),
        path_el("JAVA / SPRING · C# / .NET", 666, 210, "mono_bold", 10.0, TEXT, 0.2, max_right=846),
        path_el("IA & OPS", 590, 232, "mono_semi", 9.2, DIM, 0.5),
        path_el("FASTAPI · LANGGRAPH · AWS", 666, 232, "mono_bold", 10.0, YELLOW, 0.1, max_right=846),
        f'<line x1="590" y1="248" x2="840" y2="248" stroke="{LINE}" stroke-width="1"/>',
        f'<circle class="pulse" cx="596" cy="264" r="3.8" fill="{EMERALD}"/>',
        path_el("ACCESS // AUTHORIZED", 606, 267.5, "mono_bold", 9.5, EMERALD, 0.6),
        '<g fill="#00f0ff" opacity="0.65">'
        + "".join(
            f'<rect x="{bx}" y="278" width="{bw}" height="11"/>'
            for bx, bw in [
                (590, 3), (596, 1.5), (601, 4), (608, 2), (613, 1.5), (618, 5), (626, 2),
                (631, 3), (637, 1.5), (642, 4), (649, 2), (654, 3), (660, 1.5), (665, 5),
                (673, 2), (678, 3), (684, 1.5), (689, 4), (696, 2), (701, 3.5), (708, 1.5),
                (713, 4), (720, 2), (725, 3), (731, 1.5), (736, 5), (744, 2), (749, 3),
                (755, 1.5), (760, 4), (767, 2), (772, 3), (778, 1.5), (783, 4), (790, 2),
                (795, 3.5), (802, 1.5), (807, 4), (814, 2), (819, 3), (825, 1.5), (830, 5), (838, 2),
            ]
        )
        + "</g>",
        f'<rect x="0" y="{h-12}" width="{w}" height="12" fill="url(#hz)"/>',
        f'<line x1="0" y1="{h-13}" x2="{w}" y2="{h-13}" stroke="{YELLOW}" stroke-opacity="0.5" stroke-width="1"/>',
        "</svg>",
    ]
    save_svg("banner.svg", "\n".join(parts))


# ============================================================================
# 2. CLICKABLE BUTTONS (btn-*.svg — height 40)
# ============================================================================
def build_button(filename: str, label: str, accent: str, primary: bool = False):
    text_str = f"{label}  ↗"
    tw = measure_text(text_str, "mono_bold", 11.2, 0.6)
    w = int(round(tw + 38))
    h = 40
    bg = accent if primary else "#0a0c16"
    fg = NIGHT if primary else accent
    bottom_bar = "" if primary else f'<rect x="2" y="{h-4}" width="{w-12}" height="2" fill="{accent}" opacity="0.55"/>'
    svg = "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{xml_esc(label)}">',
            f"<title>{xml_esc(label)}</title>",
            chamfer_rect(1, 1, w - 2, h - 2, cut=9, fill=bg, stroke=accent, sw=1.5),
            bottom_bar,
            path_el(text_str, w / 2, 24.2, "mono_bold", 11.2, fg, 0.6, "center"),
            "</svg>",
        ]
    )
    save_svg(filename, svg)


# ============================================================================
# 3. SECTION HEADERS (sec-0X-*.svg — 880 x 62)
# ============================================================================
def build_section_header(filename: str, num: str, title: str, right_code: str, accent: str):
    w, h = 880, 62
    title_end = 88 + measure_text(title, "display_bold", 28, 0.6) + 18
    svg = "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{xml_esc(f"{num} // {title} — {right_code}")}">',
            f"<title>{xml_esc(f'{num} // {title} — {right_code}')}</title>",
            "<defs>",
            f'  <pattern id="hz-{num}" width="14" height="14" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><rect width="7" height="14" fill="{accent}"/><rect x="7" width="7" height="14" fill="{NIGHT}"/></pattern>',
            "</defs>",
            f'<polygon points="0,16 10,6 70,6 70,44 60,54 0,54" fill="{accent}"/>',
            path_el(num, 35, 38, "display_bold", 25, NIGHT, 0.5, "center"),
            path_el(title, 88, 40, "display_bold", 28, TEXT, 0.6),
            f'<line x1="{title_end:.1f}" y1="42" x2="880" y2="42" stroke="{LINE}" stroke-width="1.5"/>',
            f'<rect x="786" y="41" width="94" height="3" fill="{accent}"/>',
            path_el(right_code, 878, 30, "mono_bold", 10.2, accent, 0.7, "right"),
            f'<rect x="808" y="48" width="72" height="6" fill="url(#hz-{num})"/>',
            f'<line x1="0" y1="60" x2="880" y2="60" stroke="{LINE}" stroke-width="1"/>',
            f'<rect x="0" y="59" width="70" height="2" fill="{accent}"/>',
            "</svg>",
        ]
    )
    save_svg(filename, svg)


# ============================================================================
# 4. DOSSIER CONFIG + EDUCATION PANEL (dossie.svg — 880 x 278)
# ============================================================================
def build_dossie():
    w, h = 880, 278
    code_rows = [
        ("1", "const ", "operador", " = {", None),
        ("2", "  nome:", None, '       "Guilherme Damasceno",', YELLOW),
        ("3", "  funcao:", None, '     "Desenvolvedor Full Stack",', YELLOW),
        ("4", "  empresa:", None, '    "Develcode",', YELLOW),
        ("5", "  squads:", None, '     ["RD Saúde", "Leroy Merlin"],', CYAN),
        ("6", "  core:", None, '       ["Java 17 / Spring Boot", "C# / .NET"],', YELLOW),
        ("7", "  iaAgentes:", None, '  ["Python", "FastAPI", "LangGraph", "Bedrock"],', CYAN),
        ("8", "  foco:", None, '       ["Resiliência", "Integrações", "Automação"],', YELLOW),
        ("9", "};", None, "", None),
    ]

    code_svg = []
    y0 = 64
    for idx, (ln, k1, k2, val, vcol) in enumerate(code_rows):
        delay = f"{idx * 0.08:.2f}s"
        row_parts = [f'<g class="ln" style="animation-delay:{delay}">']
        row_parts.append(path_el(ln, 28, y0, "mono_reg", 11.0, "#464b70", 0.0, "right"))
        if k2:
            row_parts.append(path_el(k1, 44, y0, "mono_bold", 11.2, MAGENTA))
            x2 = 44 + measure_text(k1, "mono_bold", 11.2)
            row_parts.append(path_el(k2, x2, y0, "mono_bold", 11.2, CYAN))
            x3 = x2 + measure_text(k2, "mono_bold", 11.2)
            row_parts.append(path_el(val, x3, y0, "mono_reg", 11.2, MUTED, max_right=542))
        else:
            kcol = MUTED if ln == "9" else "#c8ccf0"
            row_parts.append(path_el(k1, 44, y0, "mono_semi", 11.2, kcol))
            if val:
                xv = 44 + measure_text(k1, "mono_semi", 11.2)
                row_parts.append(path_el(val, xv, y0, "mono_semi", 11.0, vcol, max_right=542))
        row_parts.append("</g>")
        code_svg.append("".join(row_parts))
        y0 += 23.5

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Dossiê de Guilherme Damasceno: Develcode, squads RD Saúde e Leroy Merlin, ADS UNISO e Engenharia de Software Estácio">',
        "<title>Dossiê — Guilherme Damasceno</title>",
        "<style>",
        "  .ln{animation:ln .45s ease-out both}@keyframes ln{from{opacity:0;transform:translateX(-6px)}to{opacity:1;transform:none}}",
        "  @media (prefers-reduced-motion: reduce){*{animation:none!important}}",
        "</style>",
        chamfer_rect(1, 1, 552, h - 2, cut=14, fill="#090b14", stroke=CYAN, sw=1.2),
        '<polygon points="1,15 15,1 553,1 553,36 1,36" fill="#111528"/>',
        f'<rect x="18" y="14" width="9" height="9" fill="{YELLOW}"/>',
        f'<rect x="33" y="14" width="9" height="9" fill="{CYAN}"/>',
        f'<rect x="48" y="14" width="9" height="9" fill="{MAGENTA}"/>',
        path_el("dossie.config.ts", 72, 22.5, "mono_semi", 11.0, DIM, 0.3),
        path_el("SEC_01 // VERIFIED", 538, 22.5, "mono_bold", 10.0, CYAN, 0.6, "right"),
        "\n".join(code_svg),
        # Right Education & Credentials Window
        chamfer_rect(570, 1, 309, h - 2, cut=14, fill=PANEL, stroke=MAGENTA, sw=1.2),
        '<polygon points="570,1 865,1 879,15 879,36 570,36" fill="#ff2a6d"/>',
        path_el("TREINAMENTO // FORMAÇÃO", 586, 23, "mono_bold", 10.5, NIGHT, 0.7),
        f'<rect x="586" y="54" width="7" height="7" fill="{YELLOW}"/>',
        path_el("2023 — 2025 · CONCLUÍDO", 601, 61.5, "mono_bold", 9.6, YELLOW, 0.5, max_right=866),
        path_el("ANÁLISE E DESENV. DE SISTEMAS", 601, 80, "display_bold", 14.5, TEXT, 0.2, max_right=866),
        path_el("Universidade de Sorocaba (UNISO)", 601, 96, "mono_reg", 10.0, MUTED, 0.0, max_right=866),
        f'<line x1="586" y1="110" x2="862" y2="110" stroke="{LINE}" stroke-width="1"/>',
        f'<rect x="586" y="122" width="7" height="7" fill="{CYAN}"/>',
        path_el("2025 — ATUAL · CURSANDO", 601, 129.5, "mono_bold", 9.6, CYAN, 0.5, max_right=866),
        path_el("ENGENHARIA DE SOFTWARE", 601, 148, "display_bold", 14.5, TEXT, 0.2, max_right=866),
        path_el("Estácio", 601, 164, "mono_reg", 10.0, MUTED, 0.0, max_right=866),
        f'<line x1="586" y1="178" x2="862" y2="178" stroke="{LINE}" stroke-width="1"/>',
        path_el("TREINAMENTO COMPLEMENTAR", 586, 196, "mono_bold", 9.2, DIM, 0.5, max_right=866),
        path_el("T-Academy (AMS & SAP) · n8n (Rocketseat)", 586, 213, "mono_reg", 9.5, MUTED, 0.0, max_right=866),
        path_el("TI (Bradesco) · TIC (SENAI) · Web (Ventures)", 586, 229, "mono_reg", 9.5, MUTED, 0.0, max_right=866),
        path_el("IDIOMA // INGLÊS INTERMEDIÁRIO", 586, 256, "mono_bold", 10.0, EMERALD, 0.5, max_right=866),
        "</svg>",
    ]
    save_svg("dossie.svg", "\n".join(parts))


# ============================================================================
# 5. MISSIONS BOARD (mission-01-rd.svg & missions-02-03.svg)
# ============================================================================
def build_mission_01():
    w = 880
    bullets = [
        "Validação obrigatória em Java 17 & Spring Boot com explicação estruturada de falhas, bloqueio preventivo de cards e feature flag fail-closed.",
        "Integração Python (FastAPI, LangChain/LangGraph) ao AWS Bedrock com correlation ID, timeouts configuráveis, Langfuse e mascaramento de dados.",
        "Resiliência do agente com retries para throttling, schemas tolerantes e validação 1:1 dos itens — eliminando perda de critérios de aceite.",
        "Ampliação de testes (Jest/RTL), correção de vulnerabilidades SCA/SAST, mitigação de XSS/Log Injection e CI/CD (Docker, K8s, ArgoCD, Datadog).",
    ]

    stages = [
        (24, "01 // GUARDRAILS", "CORE API", "Java 17 · Spring · Fail-Closed", YELLOW),
        (236, "02 // ORCHESTRATOR", "AGENTE DE IA", "FastAPI · LangGraph · 1:1 Schema", CYAN),
        (448, "03 // LLM GATEWAY", "BEDROCK & TRACE", "AWS Bedrock · Retries · Langfuse", CYAN),
        (660, "04 // DEVSECOPS", "CLOUD & SEC", "K8s · ArgoCD · Datadog · SAST", MAGENTA),
    ]

    stage_svg = []
    for sx, s_step, s_title, s_sub, scol in stages:
        stage_svg.append(chamfer_rect(sx, 76, 196, 66, cut=8, fill="#090b14", stroke=scol, sw=1.2))
        stage_svg.append(path_el(s_step, sx + 12, 93, "mono_bold", 8.8, scol, 0.5, max_right=sx + 188))
        stage_svg.append(path_el(s_title, sx + 12, 114, "display_bold", 15.0, TEXT, 0.3, max_right=sx + 188))
        stage_svg.append(path_el(s_sub, sx + 12, 131, "mono_reg", 8.6, MUTED, 0.0, max_right=sx + 188))

    bullet_svg = []
    by = 172
    for b in bullets:
        wrapped = wrap_lines(b, "mono_reg", 10.2, 808)
        bullet_svg.append(path_el("↳", 24, by, "mono_bold", 11.5, CYAN))
        for li, line_str in enumerate(wrapped):
            bullet_svg.append(path_el(line_str, 44, by, "mono_reg", 10.2, MUTED, 0.0, max_right=858))
            by += 17 if li + 1 < len(wrapped) else 23

    chips = [
        "Java 17", "Spring Boot", "Python", "FastAPI", "LangChain", "LangGraph",
        "AWS Bedrock", "Langfuse", "Next.js", "Jest / RTL", "SCA / SAST",
        "Docker", "Kubernetes", "ArgoCD", "Datadog APM",
    ]
    chips_svg, chips_bottom = draw_chip_row(chips, 24, by + 4, YELLOW, 858)
    h = int(chips_bottom + 20)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Mission 01 — RD Saúde e Develcode: Agentes de IA Resilientes">',
        "<title>MISSION_01 — RD Saúde · Develcode: Agentes de IA Resilientes</title>",
        "<style>",
        "  .flow{stroke-dasharray:5 15;animation:dash 2.2s linear infinite}@keyframes dash{to{stroke-dashoffset:-40}}",
        "  .pulse{animation:pulse 2.2s ease-in-out infinite}@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}",
        "  @media (prefers-reduced-motion: reduce){*{animation:none!important}}",
        "</style>",
        chamfer_rect(1, 1, w - 2, h - 2, cut=16, fill=PANEL, stroke=YELLOW, sw=1.4),
        '<polygon points="1,17 17,1 96,1 96,60 1,60" fill="#fcee0a"/>',
        path_el("MISSION", 48, 25, "mono_bold", 9.5, NIGHT, 0.7, "center"),
        path_el("01", 48, 47, "display_bold", 22, NIGHT, 0.5, "center"),
        path_el("RD SAÚDE · DEVELCODE  //  ENTERPRISE AI & BACK-END", 114, 24, "mono_bold", 10.2, CYAN, 0.8, max_right=715),
        path_el("AGENTES DE IA RESILIENTES & ARQUITETURA FAIL-CLOSED", 114, 48, "display_bold", 20.5, TEXT, 0.3, max_right=715),
        chamfer_rect(726, 15, 134, 28, cut=6, fill="#090d16", stroke=EMERALD, sw=1.1),
        f'<circle class="pulse" cx="742" cy="29" r="4" fill="{EMERALD}"/>',
        path_el("SQUAD ATIVA", 754, 33, "mono_bold", 10.0, EMERALD, 0.6),
        f'<line x1="1" y1="60" x2="879" y2="60" stroke="{LINE}" stroke-width="1.2"/>',
        f'<line x1="220" y1="109" x2="236" y2="109" stroke="{LINE}" stroke-width="2"/>',
        f'<line class="flow" x1="220" y1="109" x2="236" y2="109" stroke="{YELLOW}" stroke-width="2"/>',
        f'<line x1="432" y1="109" x2="448" y2="109" stroke="{LINE}" stroke-width="2"/>',
        f'<line class="flow" x1="432" y1="109" x2="448" y2="109" stroke="{CYAN}" stroke-width="2"/>',
        f'<line x1="644" y1="109" x2="660" y2="109" stroke="{LINE}" stroke-width="2"/>',
        f'<line class="flow" x1="644" y1="109" x2="660" y2="109" stroke="{MAGENTA}" stroke-width="2"/>',
        "\n".join(stage_svg),
        f'<line x1="24" y1="152" x2="856" y2="152" stroke="{LINE}" stroke-width="1"/>',
        "\n".join(bullet_svg),
        chips_svg,
        "</svg>",
    ]
    save_svg("mission-01-rd.svg", "\n".join(parts))


def build_missions_02_03():
    w, h = 880, 224

    def sub_card(ox, num, squad, title, accent, lines, chips):
        c_w = 432
        out = [
            chamfer_rect(ox, 1, c_w, h - 2, cut=14, fill=PANEL, stroke=accent, sw=1.3),
            f'<polygon points="{ox},15 {ox+14},1 {ox+74},1 {ox+74},56 {ox},56" fill="{accent}"/>',
            path_el("MISSION", ox + 37, 23, "mono_bold", 9.0, NIGHT, 0.6, "center"),
            path_el(num, ox + 37, 44, "display_bold", 20, NIGHT, 0.4, "center"),
            path_el(squad, ox + 90, 23, "mono_bold", 9.8, accent, 0.7, max_right=ox + c_w - 14),
            path_el(title, ox + 90, 45, "display_bold", 18.0, TEXT, 0.2, max_right=ox + c_w - 14),
            f'<line x1="{ox}" y1="56" x2="{ox+c_w}" y2="56" stroke="{LINE}" stroke-width="1"/>',
        ]
        ly = 80
        for ln in lines:
            out.append(path_el(ln, ox + 18, ly, "mono_reg", 10.0, MUTED, 0.0, max_right=ox + c_w - 16))
            ly += 18.5
        chips_svg, _ = draw_chip_row(chips, ox + 18, 178, accent, ox + c_w - 14)
        out.append(chips_svg)
        return "\n".join(out)

    m2_lines = wrap_lines(
        "Refatoração de sistemas corporativos legados com C# e .NET, aplicação de padrões de projeto, modelagem de persistência com ActiveRecord/NHibernate e PostgreSQL e diagnóstico de integridade de dados e regras de negócio.",
        "mono_reg",
        10.0,
        394,
    )
    m3_lines = wrap_lines(
        "Desenvolvimento de fluxos automatizados e integrações entre serviços com n8n, Python, JavaScript e recursos de IA assistiva — reduzindo rotinas operacionais manuais e acelerando entregas entre squads.",
        "mono_reg",
        10.0,
        394,
    )

    svg = "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Mission 02 Leroy Merlin e Mission 03 Automação">',
            "<title>MISSION_02 Leroy Merlin &amp; MISSION_03 Automação</title>",
            sub_card(
                1,
                "02",
                "LEROY MERLIN · DEVELCODE",
                "MODERNIZAÇÃO DE SISTEMAS",
                CYAN,
                m2_lines,
                ["C#", ".NET", "ActiveRecord", "NHibernate", "PostgreSQL"],
            ),
            sub_card(
                447,
                "03",
                "TRANSVERSAL · WORKFLOW OPS",
                "AUTOMAÇÃO & FLUXOS DE IA",
                MAGENTA,
                m3_lines,
                ["n8n", "Python", "JavaScript", "IA Assistiva", "Webhooks"],
            ),
            "</svg>",
        ]
    )
    save_svg("missions-02-03.svg", svg)


# ============================================================================
# 6. SELF-CONTAINED CONTRACT CARDS (c1..c6.svg — 432 x 168)
# ============================================================================
def build_contract_card(filename, cid, status, is_live, category, title, desc, chips, cta, accent):
    w, h = 432, 168
    desc_lines = wrap_lines(desc, "mono_reg", 10.0, 394)[:2]
    status_col = EMERALD if is_live else DIM
    status_w = measure_text(status, "mono_bold", 9.0, 0.5)
    live_dot = f'<circle cx="{w - 18 - status_w - 9:.1f}" cy="21.5" r="3.5" fill="{EMERALD}"/>' if is_live else ""

    chips_svg, _ = draw_chip_row(chips, 18, 108, accent, w - 16)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{xml_esc(f"{cid} — {title}")}">',
        f"<title>{xml_esc(f'{cid} — {title}')}</title>",
        chamfer_rect(1, 1, w - 2, h - 2, cut=13, fill=PANEL, stroke=accent if is_live else LINE, sw=1.3),
        f'<rect x="1" y="14" width="3.5" height="36" fill="{accent}"/>',
        path_el(f"{cid} // {category}", 18, 25, "mono_bold", 9.2, accent, 0.5, max_right=300),
        live_dot,
        path_el(status, w - 18, 25, "mono_bold", 9.0, status_col, 0.5, "right"),
        path_el(title.upper(), 18, 50, "display_bold", 20.5, TEXT, 0.3, max_right=412),
    ]
    dy = 72
    for ln in desc_lines:
        parts.append(path_el(ln, 18, dy, "mono_reg", 10.0, MUTED, max_right=414))
        dy += 18

    parts.extend(
        [
            chips_svg,
            f'<line x1="18" y1="140" x2="{w-18}" y2="140" stroke="{LINE}" stroke-width="1"/>',
            path_el(cta, 18, 156, "mono_bold", 10.0, YELLOW if is_live else CYAN, 0.6),
            path_el("↗", w - 18, 156, "mono_bold", 11.5, YELLOW if is_live else CYAN, 0.0, "right"),
            "</svg>",
        ]
    )
    save_svg(filename, "\n".join(parts))


# ============================================================================
# 7. LOADOUT MATRIX (loadout.svg — 880 x 404)
# ============================================================================
def build_loadout():
    w, h = 880, 404
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Loadout Técnico — Java, Spring Boot, C#, .NET, Python, FastAPI, LangGraph, AWS Bedrock, Cloud e Dados">',
        "<title>Loadout Técnico — Guilherme Damasceno</title>",
        chamfer_rect(1, 1, w - 2, 124, cut=14, fill=PANEL, stroke=YELLOW, sw=1.4),
        f'<rect x="1" y="1" width="4" height="32" fill="{YELLOW}"/>',
        path_el("PRIMARY // 01", 18, 22, "mono_bold", 10.0, YELLOW, 0.7),
        path_el("NÚCLEO DE ENGENHARIA  —  STACK PRINCIPAL EM PRODUÇÃO", 132, 22, "mono_semi", 10.0, TEXT, 0.5, max_right=860),
        f'<line x1="16" y1="34" x2="864" y2="34" stroke="{LINE}" stroke-width="1"/>',
    ]

    primaries = [
        (16, "01", "JAVA", "SPRING BOOT · JAVA 17 · REST", YELLOW),
        (303, "02", "C# / .NET", "ARQUITETURA · NHIBERNATE · ORM", YELLOW),
        (590, "03", "PYTHON & IA", "FASTAPI · LANGGRAPH · BEDROCK", CYAN),
    ]
    for px, pnum, ptitle, psub, pcol in primaries:
        parts.append(chamfer_rect(px, 46, 274, 66, cut=10, fill="#090b14", stroke=pcol, sw=1.3))
        parts.append(path_el(pnum, px + 260, 62, "mono_bold", 9.5, pcol, 0.4, "right"))
        parts.append(path_el(ptitle, px + 16, 78, "display_bold", 24, pcol, 0.4, max_right=px + 250))
        parts.append(path_el(psub, px + 16, 99, "mono_semi", 9.4, TEXT, 0.3, max_right=px + 262))

    slots = [
        (
            1, 142, "SPECIAL // 02", "IA, AGENTES & OBSERVABILIDADE", CYAN,
            ["LangChain", "LangGraph", "AWS Bedrock", "Langfuse", "FastAPI", "Data Masking", "Schemas 1:1"],
        ),
        (
            447, 142, "ARCH // 03", "RESILIÊNCIA & INTEGRAÇÃO", MAGENTA,
            ["Fail-Closed Flags", "Retry / Backoff", "Circuit Breaker", "Correlation ID", "APIs RESTful", "n8n", "Webhooks"],
        ),
        (
            1, 280, "CLOUD // 04", "DEVOPS, APM & SEGURANÇA", YELLOW,
            ["Docker", "Kubernetes", "ArgoCD", "Datadog APM", "GitLab CI", "SCA / SAST", "SonarQube", "Jest / RTL"],
        ),
        (
            447, 280, "DATA // 05", "PERSISTÊNCIA, WEB & MOBILE", CYAN,
            ["PostgreSQL", "MongoDB", "MySQL", "ActiveRecord", "React / Next.js", "TypeScript", "Flutter"],
        ),
    ]

    for sx, sy, scode, stitle, scol, schips in slots:
        parts.append(chamfer_rect(sx, sy, 432, 122, cut=12, fill=PANEL, stroke=LINE, sw=1.2))
        parts.append(f'<rect x="{sx}" y="{sy+1}" width="3.5" height="28" fill="{scol}"/>')
        parts.append(path_el(scode, sx + 16, sy + 20, "mono_bold", 9.5, scol, 0.5))
        code_end = sx + 16 + measure_text(scode, "mono_bold", 9.5, 0.5) + 14
        parts.append(path_el(stitle, code_end, sy + 20, "mono_semi", 9.6, TEXT, 0.3, max_right=sx + 418))
        parts.append(f'<line x1="{sx+16}" y1="{sy+31}" x2="{sx+416}" y2="{sy+31}" stroke="{LINE}" stroke-width="1"/>')
        c_svg, _ = draw_chip_row(schips, sx + 16, sy + 44, scol, sx + 418)
        parts.append(c_svg)

    parts.append("</svg>")
    save_svg("loadout.svg", "\n".join(parts))


# ============================================================================
# 8. SYNTHWAVE EQUALIZER FOOTER (footer.svg — 880 x 78)
# ============================================================================
def build_footer():
    w, h = 880, 78
    bars = []
    heights = [
        30, 18, 24, 34, 28, 26, 14, 28, 20, 32, 16, 22, 18, 26, 30, 20, 25, 31, 16, 33, 20, 15,
        22, 28, 21, 19, 27, 20, 16, 19, 32, 30, 26, 18, 20, 14, 16, 22, 21, 19, 20, 24, 25, 21,
    ]
    for i, bh in enumerate(heights):
        bx = 6 + i * 20
        by = 40 - bh
        col = CYAN if i % 7 == 2 else (MAGENTA if i % 11 == 5 else YELLOW)
        dur = f"{1.1 + (i % 5) * 0.35:.2f}s"
        delay = f"-{(i * 0.19) % 2.4:.2f}s"
        op = f"{0.55 + (i % 4) * 0.11:.2f}"
        bars.append(
            f'<rect class="b" x="{bx}" y="{by}" width="10" height="{bh}" fill="{col}" opacity="{op}" style="animation-duration:{dur};animation-delay:{delay}"/>'
        )

    svg = "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Fim do arquivo — Guilherme Damasceno">',
            "<title>Fim do arquivo — Guilherme Damasceno</title>",
            "<defs>",
            f'  <pattern id="hz-ft" width="16" height="16" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><rect width="8" height="16" fill="{YELLOW}"/><rect x="8" width="8" height="16" fill="{NIGHT}"/></pattern>',
            "</defs>",
            "<style>",
            "  @keyframes eq{0%,100%{transform:scaleY(.3)}50%{transform:scaleY(1)}}",
            "  .b{transform-box:fill-box;transform-origin:bottom;animation:eq 1.6s ease-in-out infinite}",
            "  @media (prefers-reduced-motion: reduce){*{animation:none!important}}",
            "</style>",
            "".join(bars),
            f'<line x1="0" y1="42" x2="{w}" y2="42" stroke="{LINE}" stroke-width="1"/>',
            path_el(
                "EOF // GUILHERME DAMASCENO · DEVELCODE · BACK-END, INTEGRAÇÕES & AGENTES DE IA",
                440,
                58,
                "mono_semi",
                9.8,
                DIM,
                0.7,
                "center",
                max_right=870,
            ),
            f'<rect x="0" y="67" width="{w}" height="11" fill="url(#hz-ft)"/>',
            "</svg>",
        ]
    )
    save_svg("footer.svg", svg)


def main():
    build_banner()
    build_button("btn-portfolio.svg", "PORTFÓLIO INTERATIVO", YELLOW, primary=True)
    build_button("btn-english.svg", "ENGLISH READING APP", CYAN, primary=False)
    build_button("btn-source.svg", "CÓDIGO DO PORTFÓLIO", MAGENTA, primary=False)
    build_button("btn-linkedin.svg", "LINKEDIN", CYAN, primary=False)
    build_button("btn-email.svg", "ENVIAR E-MAIL", YELLOW, primary=False)
    build_button("btn-github.svg", "REPOSITÓRIOS", MUTED, primary=False)

    build_section_header("sec-01-dossie.svg", "01", "DOSSIÊ", "// PERFIL & FORMAÇÃO", YELLOW)
    build_section_header("sec-02-missoes.svg", "02", "LOG DE MISSÕES", "// DEVELCODE · RD SAÚDE · LEROY MERLIN", CYAN)
    build_section_header("sec-03-contratos.svg", "03", "CONTRATOS", "// PROJETOS EM DESTAQUE (CLIQUE NO CARD)", MAGENTA)
    build_section_header("sec-04-loadout.svg", "04", "LOADOUT", "// ARQUITETURA, IA & FERRAMENTAS", YELLOW)
    build_section_header("sec-05-canal.svg", "05", "CANAL ABERTO", "// COMUNICAÇÃO DIRETA", CYAN)

    build_dossie()
    build_mission_01()
    build_missions_02_03()

    build_contract_card(
        "c1-english.svg",
        "CTR_01",
        "ONLINE // LIVE",
        True,
        "WEB APP · IDIOMAS",
        "English Reading App",
        "Leitura em inglês com histórias graduadas, filtros por categoria e nível CEFR e exercícios de lacunas.",
        ["TypeScript", "JavaScript", "CSS", "HTML"],
        "ABRIR APLICAÇÃO LIVE",
        EMERALD,
    )
    build_contract_card(
        "c2-dmstech2.svg",
        "CTR_02",
        "REPO // PUBLIC",
        False,
        "E-COMMERCE · FULL STACK",
        "DMSTECH 2.0",
        "Loja de tecnologia com catálogo, busca, ofertas e carrinho conectada a API REST e banco de dados.",
        ["React", "FastAPI", "Python", "MongoDB"],
        "INSPECIONAR REPOSITÓRIO",
        MAGENTA,
    )
    build_contract_card(
        "c3-dmsbooks.svg",
        "CTR_03",
        "REPO // PUBLIC",
        False,
        "CRUD · FULL STACK",
        "DMSBooks",
        "Sistema completo para gerenciamento de livros e usuários com cadastro, consulta, edição e remoção.",
        ["React", "Node.js", "Express", "MySQL"],
        "INSPECIONAR REPOSITÓRIO",
        CYAN,
    )
    build_contract_card(
        "c4-piburger.svg",
        "CTR_04",
        "REPO // PUBLIC",
        False,
        "MOBILE · DELIVERY",
        "DMS PiBurger",
        "Aplicativo mobile multiplataforma de delivery com autenticação, categorias, carrinho e modo escuro.",
        ["Flutter", "Dart", "Mobile UI"],
        "INSPECIONAR REPOSITÓRIO",
        YELLOW,
    )
    build_contract_card(
        "c5-termo.svg",
        "CTR_05",
        "REPO // PUBLIC",
        False,
        "JOGO WEB · BROWSER",
        "Termo",
        "Jogo diário de palavras direto no navegador com suporte aos modos Termo, Dueto e Quarteto.",
        ["JavaScript", "HTML5", "CSS3"],
        "INSPECIONAR REPOSITÓRIO",
        CYAN,
    )
    build_contract_card(
        "c6-banco.svg",
        "CTR_06",
        "REPO // PUBLIC",
        False,
        "REGRAS DE DOMÍNIO",
        "Sistema Bancário",
        "Implementação de clientes, agências e contas com consulta de saldo, extrato e movimentações.",
        ["Python", "Regras de Negócio"],
        "INSPECIONAR REPOSITÓRIO",
        YELLOW,
    )

    build_loadout()
    build_footer()


if __name__ == "__main__":
    main()

