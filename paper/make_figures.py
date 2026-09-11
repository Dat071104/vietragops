"""Generate the three paper figures from the frozen Gate 10 evidence ledger."""

from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "figures"
OUT.mkdir(parents=True, exist_ok=True)

NAVY = "#17324D"
BLUE = "#2878B5"
PALE_BLUE = "#DCECF7"
RED = "#C94C4C"
PALE_RED = "#F7DEDE"
GOLD = "#D9A441"
PALE_GOLD = "#FAF0D5"
GRAY = "#667085"
LIGHT = "#F6F8FA"
WHITE = "#FFFFFF"
BLACK = "#1F2933"


def font(size: int, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()


F16 = font(16)
F18 = font(18)
F20 = font(20)
F22 = font(22, True)
F26 = font(26, True)
F30 = font(30, True)
F36 = font(36, True)


def centered(draw, box, text, fnt, fill=BLACK):
    x0, y0, x1, y1 = box
    left, top, right, bottom = draw.textbbox((0, 0), text, font=fnt)
    draw.text(
        ((x0 + x1 - (right - left)) / 2, (y0 + y1 - (bottom - top)) / 2 - top),
        text,
        font=fnt,
        fill=fill,
    )


def wrapped(draw, xy, text, width, fnt, fill=BLACK, line_gap=8):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textbbox((0, 0), trial, font=fnt)[2] <= width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + line_gap
    return y


def arrow(draw, start, end, fill=NAVY, width=5):
    draw.line([start, end], fill=fill, width=width)
    x0, y0 = start
    x1, y1 = end
    if x1 >= x0:
        points = [(x1, y1), (x1 - 18, y1 - 12), (x1 - 18, y1 + 12)]
    else:
        points = [(x1, y1), (x1 + 18, y1 - 12), (x1 + 18, y1 + 12)]
    draw.polygon(points, fill=fill)


def save(im, name):
    im.save(OUT / name, format="PNG", dpi=(300, 300), optimize=True)


def figure1():
    im = Image.new("RGB", (2100, 1050), WHITE)
    d = ImageDraw.Draw(im)
    d.text((80, 55), "The benchmark failure: a target outside the declared rights", font=F36, fill=NAVY)
    d.text((80, 115), "The agent may be asked to construct a value that cannot be derived before the first call.", font=F20, fill=GRAY)

    boxes = [
        (90, 300, 450, 610, PALE_BLUE, "OLD CONTRACT", "course_code = CRS-021\nterm_id = TERM-01"),
        (570, 300, 930, 610, PALE_BLUE, "VERIFIED OLD TRACE", "successful call\nwith the old tool"),
        (1050, 250, 1410, 660, PALE_BLUE, "NEW CONTRACT", "section_ref\n(required)\n\nNo separator\nconvention shown"),
        (1530, 300, 2010, 610, PALE_RED, "GROUND-TRUTH TARGET", "section_ref =\nCRS-021::TERM-01\n\nUNREACHABLE ORACLE"),
    ]
    for x0, y0, x1, y1, fill, heading, body in boxes:
        d.rounded_rectangle((x0, y0, x1, y1), radius=24, fill=fill, outline=NAVY, width=4)
        centered(d, (x0 + 20, y0 + 22, x1 - 20, y0 + 70), heading, F22, NAVY)
        lines = body.split("\n")
        yy = y0 + 105
        for line in lines:
            centered(d, (x0 + 20, yy, x1 - 20, yy + 42), line, F20, BLACK if fill != PALE_RED else RED)
            yy += 44
    arrow(d, (460, 455), (555, 455))
    arrow(d, (940, 455), (1035, 455))
    arrow(d, (1420, 455), (1515, 455), fill=RED)

    d.rounded_rectangle((540, 785, 1560, 930), radius=22, fill=PALE_GOLD, outline=GOLD, width=4)
    centered(d, (570, 805, 1530, 850), "Oracle reachability under declared information rights", F22, NAVY)
    centered(d, (570, 855, 1530, 910), "REACHABLE iff the target and every construction step are derivable from the granted information.", F18, BLACK)
    arrow(d, (1050, 665), (1050, 770), fill=GOLD)
    save(im, "figure1_problem.png")


def figure2():
    im = Image.new("RGB", (2500, 1460), WHITE)
    d = ImageDraw.Draw(im)
    d.text((70, 45), "Information rights define what an oracle may require", font=F36, fill=NAVY)
    d.text((70, 105), "The audit asks whether the ground truth is derivable from the method's declared view.", font=F20, fill=GRAY)

    x0, y0 = 70, 190
    widths = [470, 310, 310, 310, 360, 520]
    headers = ["Method", "Old schema", "Old trace", "New schema", "Migration map", "Probe new API before first call"]
    rows = [
        ["Static", "yes", "no", "yes", "no", "no"],
        ["Direct LLM", "yes", "optional", "yes", "no", "no"],
        ["ToolEVO", "stale", "--", "via interaction", "no", "yes"],
        ["IEEE normalization", "--", "controller memory", "yes", "known manifest", "at execution"],
        ["Ours", "yes", "yes", "yes", "no", "no, before first call"],
        ["Oracle", "yes", "yes", "yes", "yes", "no"],
    ]
    x_positions = [x0]
    for width in widths:
        x_positions.append(x_positions[-1] + width)
    row_h = 145
    for c, header in enumerate(headers):
        cell = (x_positions[c], y0, x_positions[c + 1], y0 + row_h)
        d.rectangle(cell, fill=NAVY, outline=WHITE, width=3)
        wrapped(d, (cell[0] + 18, cell[1] + 22), header, widths[c] - 36, F20, WHITE, line_gap=5)
    for r, row in enumerate(rows):
        yy = y0 + row_h * (r + 1)
        for c, value in enumerate(row):
            fill = PALE_GOLD if row[0] == "Ours" else (LIGHT if r % 2 == 0 else WHITE)
            cell = (x_positions[c], yy, x_positions[c + 1], yy + row_h)
            d.rectangle(cell, fill=fill, outline="#D8DEE6", width=2)
            wrapped(d, (cell[0] + 18, cell[1] + 32), value, widths[c] - 36, F20, NAVY if c == 0 else BLACK, line_gap=5)
    d.rounded_rectangle((70, 1240, 2430, 1385), radius=20, fill=PALE_BLUE, outline=BLUE, width=3)
    wrapped(d, (100, 1275), "The benchmark oracle is not allowed to demand information that the method cannot observe. The Oracle row is an audit reference, not an agent condition.", 2280, F20, BLACK, line_gap=6)
    save(im, "figure2_information_rights.png")


def figure3():
    im = Image.new("RGB", (2550, 1700), WHITE)
    d = ImageDraw.Draw(im)
    d.text((70, 45), "Oracle reachability across synthetic drift families", font=F36, fill=NAVY)
    d.text((70, 105), "Blue = derivable pair items; red = unreachable pair items. The real-pair control is shown separately.", font=F20, fill=GRAY)

    data = [
        ("added_required_field", 40, 0, "40/40"),
        ("argument_merge", 0, 30, "0/30"),
        ("argument_rename", 20, 0, "20/20"),
        ("argument_split", 40, 0, "40/40"),
        ("multiple_old_to_one_new", 30, 0, "30/30"),
        ("multiple_simultaneous_renames", 40, 0, "40/40"),
        ("no_equivalent", None, None, "N/A"),
        ("one_old_to_multiple_new", 30, 0, "30/30"),
        ("output_restructure", 15, 0, "15/15"),
        ("semantic_near_collision", 15, 0, "15/15"),
        ("tool_rename", 15, 0, "15/15"),
        ("tool_replacement", 15, 20, "15/35"),
    ]
    left = 90
    label_w = 560
    bar_left = left + label_w
    bar_w = 800
    count_x = bar_left + bar_w + 30
    top = 210
    row_h = 98
    max_total = 40
    d.text((bar_left, 160), "pair items (maximum width = 40)", font=F18, fill=GRAY)
    for i, (label, reachable, unreachable, value) in enumerate(data):
        yy = top + i * row_h
        d.text((left, yy + 30), label, font=F18, fill=BLACK)
        if reachable is None:
            d.rounded_rectangle((bar_left, yy + 20, bar_left + bar_w, yy + 67), radius=10, fill="#E7EAEE")
            d.text((bar_left + 20, yy + 28), "not an argument-pair family", font=F18, fill=GRAY)
        else:
            rw = int(bar_w * reachable / max_total)
            uw = int(bar_w * unreachable / max_total)
            if rw:
                d.rectangle((bar_left, yy + 20, bar_left + rw, yy + 67), fill=BLUE)
            if uw:
                d.rectangle((bar_left + rw, yy + 20, bar_left + rw + uw, yy + 67), fill=RED)
        d.text((count_x, yy + 25), value, font=F20, fill=NAVY)

    legend_y = top + len(data) * row_h + 30
    d.rectangle((left, legend_y, left + 30, legend_y + 30), fill=BLUE)
    d.text((left + 45, legend_y + 2), "reachable", font=F18, fill=BLACK)
    d.rectangle((left + 210, legend_y, left + 240, legend_y + 30), fill=RED)
    d.text((left + 255, legend_y + 2), "unreachable", font=F18, fill=BLACK)
    d.rectangle((left + 475, legend_y, left + 505, legend_y + 30), fill="#E7EAEE")
    d.text((left + 520, legend_y + 2), "not applicable", font=F18, fill=BLACK)

    panel_x0, panel_y0, panel_x1, panel_y1 = 1550, 280, 2440, 950
    d.rounded_rectangle((panel_x0, panel_y0, panel_x1, panel_y1), radius=24, fill=PALE_BLUE, outline=BLUE, width=4)
    centered(d, (panel_x0 + 35, panel_y0 + 35, panel_x1 - 35, panel_y0 + 95), "REAL MCP/API VERSION-PAIR CONTROL", F22, NAVY)
    centered(d, (panel_x0 + 60, panel_y0 + 170, panel_x1 - 60, panel_y0 + 270), "0 / 20", F36, BLUE)
    centered(d, (panel_x0 + 60, panel_y0 + 280, panel_x1 - 60, panel_y0 + 335), "unreachable", F22, BLACK)
    centered(d, (panel_x0 + 60, panel_y0 + 390, panel_x1 - 60, panel_y0 + 480), "20 / 20", F36, NAVY)
    centered(d, (panel_x0 + 60, panel_y0 + 490, panel_x1 - 60, panel_y0 + 545), "reachable", F22, BLACK)
    wrapped(d, (panel_x0 + 70, panel_y0 + 610), "Negative control, not an external prevalence estimate.", panel_x1 - panel_x0 - 140, F18, GRAY, line_gap=6)

    d.rounded_rectangle((70, 1510, 2440, 1640), radius=20, fill=PALE_GOLD, outline=GOLD, width=3)
    wrapped(d, (105, 1540), "Across the synthetic pair surface: 260 reachable and 50 unreachable. The local finding is not validated as a field prevalence claim by the 20-pair control.", 2260, F20, BLACK, line_gap=6)
    save(im, "figure3_reachability.png")


if __name__ == "__main__":
    figure1()
    figure2()
    figure3()
    print(f"wrote {OUT / 'figure1_problem.png'}")
    print(f"wrote {OUT / 'figure2_information_rights.png'}")
    print(f"wrote {OUT / 'figure3_reachability.png'}")
