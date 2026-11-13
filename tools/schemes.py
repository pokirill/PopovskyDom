#!/usr/bin/env python3
"""Генератор схем «было / стало» для проекта перестройки дома.

Все координаты — в метрах. Начало — юго-западный угол участка (у проезда, слева),
ось X — на восток (к уч. 27), ось Y — на север (в глубину участка).
Для поэтажных планов начало — юго-западный наружный угол дома (лит. А).

Размеры существующего дома взяты из техпаспорта МОБТИ от 11.03.2016.
Положение дома на участке и все новые объекты — СХЕМАТИЧНО, по эскизам владельца.
Точные привязки даст топосъёмка и проект.

Запуск: python3 tools/schemes.py  → перезаписывает файлы в schemes/
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "schemes"
OUT.mkdir(exist_ok=True)

C = {
    "exist": "#8a8f98",      # существующие конструкции
    "exist_fill": "#eef0f3",
    "demo": "#c0392b",       # демонтаж
    "new": "#d35400",        # новое строительство
    "new_fill": "#fdebd0",
    "later": "#2e86c1",      # позже / вне регистрации
    "later_fill": "#d6eaf8",
    "green": "#27ae60",
    "green_fill": "#d5f5e3",
    "water": "#5dade2",
    "water_fill": "#d6eaf8",
    "path": "#d4ac0d",
    "path_fill": "#fcf3cf",
    "text": "#1c2833",
    "dim": "#566573",
}
FONT = "DejaVu Sans, Arial, sans-serif"


class Svg:
    def __init__(self, w_m, h_m, scale, margin=60, title="", extra_h=0):
        self.s = scale
        self.m = margin
        self.w = w_m * scale + 2 * margin
        self.h = h_m * scale + 2 * margin + extra_h
        self.h_m = h_m
        self.items = []
        self.extra_h = extra_h
        for i, t in enumerate(title.split("\n") if title else []):
            self.items.append(
                f'<text x="{self.m}" y="{28 + i * 22}" font-family="{FONT}" font-size="{18 if i == 0 else 14}" '
                f'font-weight="{"bold" if i == 0 else "normal"}" fill="{C["text"]}">{t}</text>'
            )

    # координаты: метры → пиксели (Y вверх)
    def X(self, x):
        return self.m + x * self.s

    def Y(self, y):
        return self.m + (self.h_m - y) * self.s

    def poly(self, pts, stroke, fill="none", sw=2, dash=None, opacity=1):
        d = " ".join(f"{self.X(x):.1f},{self.Y(y):.1f}" for x, y in pts)
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.items.append(
            f'<polygon points="{d}" stroke="{stroke}" fill="{fill}" stroke-width="{sw}"{da} fill-opacity="{opacity}"/>'
        )

    def rect(self, x0, y0, x1, y1, stroke, fill="none", sw=2, dash=None, opacity=1):
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], stroke, fill, sw, dash, opacity)

    def line(self, x0, y0, x1, y1, stroke, sw=2, dash=None):
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.items.append(
            f'<line x1="{self.X(x0):.1f}" y1="{self.Y(y0):.1f}" x2="{self.X(x1):.1f}" '
            f'y2="{self.Y(y1):.1f}" stroke="{stroke}" stroke-width="{sw}"{da}/>'
        )

    def ellipse(self, cx, cy, rx, ry, stroke, fill="none", sw=2, dash=None):
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.items.append(
            f'<ellipse cx="{self.X(cx):.1f}" cy="{self.Y(cy):.1f}" rx="{rx*self.s:.1f}" '
            f'ry="{ry*self.s:.1f}" stroke="{stroke}" fill="{fill}" stroke-width="{sw}"{da}/>'
        )

    def text(self, x, y, s, size=12, color=None, anchor="middle", bold=False, rotate=0):
        color = color or C["text"]
        fw = ' font-weight="bold"' if bold else ""
        lines = s.split("\n")
        px, py = self.X(x), self.Y(y)
        tr = f' transform="rotate({rotate} {px:.1f} {py:.1f})"' if rotate else ""
        start = py - (len(lines) - 1) * size * 0.6
        tspans = "".join(
            f'<tspan x="{px:.1f}" y="{start + i * size * 1.2:.1f}">{ln}</tspan>' for i, ln in enumerate(lines)
        )
        self.items.append(
            f'<text font-family="{FONT}" font-size="{size}" fill="{color}" text-anchor="{anchor}" '
            f'dominant-baseline="middle"{fw}{tr}>{tspans}</text>'
        )

    def raw_text(self, px, py, s, size=12, color=None, anchor="start", bold=False):
        color = color or C["text"]
        fw = ' font-weight="bold"' if bold else ""
        self.items.append(
            f'<text x="{px}" y="{py}" font-family="{FONT}" font-size="{size}" fill="{color}" '
            f'text-anchor="{anchor}"{fw}>{s}</text>'
        )

    def dim(self, x0, y0, x1, y1, label, off=0.6, size=11):
        """Размерная линия со смещением off (м) влево/вниз."""
        if abs(y0 - y1) < 1e-6:  # горизонтальная
            yy = y0 - off
            self.line(x0, yy, x1, yy, C["dim"], 1)
            self.line(x0, yy - 0.15, x0, yy + 0.15, C["dim"], 1)
            self.line(x1, yy - 0.15, x1, yy + 0.15, C["dim"], 1)
            self.text((x0 + x1) / 2, yy - 0.3, label, size, C["dim"])
        else:
            xx = x0 - off
            self.line(xx, y0, xx, y1, C["dim"], 1)
            self.line(xx - 0.15, y0, xx + 0.15, y0, C["dim"], 1)
            self.line(xx - 0.15, y1, xx + 0.15, y1, C["dim"], 1)
            self.text(xx - 0.35, (y0 + y1) / 2, label, size, C["dim"], rotate=-90)

    def legend(self, entries, top=None):
        y = top if top is not None else self.h - self.extra_h - 10
        x = self.m
        for color, fill, dash, label in entries:
            da = f' stroke-dasharray="{dash}"' if dash else ""
            self.items.append(
                f'<rect x="{x}" y="{y}" width="22" height="14" stroke="{color}" fill="{fill}" stroke-width="2"{da}/>'
            )
            self.raw_text(x + 30, y + 12, label, 12)
            y += 22

    def save(self, name):
        body = "\n".join(self.items)
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w:.0f}" height="{self.h:.0f}" '
            f'viewBox="0 0 {self.w:.0f} {self.h:.0f}">\n'
            f'<rect width="100%" height="100%" fill="white"/>\n{body}\n</svg>\n'
        )
        (OUT / name).write_text(svg, encoding="utf-8")
        print("wrote", OUT / name)


# ---------------------------------------------------------------- участок
PLOT = [(0, 0), (16.5, 0), (18.3, 35.95), (2.2, 38.05)]  # схематично по ситуационному плану
HOUSE_X0, HOUSE_Y0 = 5.2, 5.8                          # SW угол дома на участке (схематично)
HW, HD = 8.70, 6.45                                    # дом: ширина (В-З) × глубина (С-Ю)
AW = 6.67                                              # лит. А, без веранды
EXT_D = 5.0                                            # пристройка, глубина


def genplan(stage):
    """stage: 'bylo' или 'stalo'."""
    title = ("Генплан участка — БЫЛО\nпо техпаспорту МОБТИ 2016" if stage == "bylo"
             else "Генплан участка — СТАЛО\nконцепция, схематично")
    g = Svg(19.5, 39, 20, margin=70, title=title, extra_h=230)
    g.poly(PLOT, C["text"], "white", 2)
    # подписи границ
    g.text(8.25, -1.2, "проезд · 16,50", 12, C["dim"])
    g.text(10.3, 38.3, "16,50", 11, C["dim"])
    g.text(-1.2, 19, "уч. 25 · 38,09", 12, C["dim"], rotate=-90)
    g.text(19.6, 18, "уч. 27 · 36,00", 12, C["dim"], rotate=90)
    g.text(0.6, 0.7, "въезд", 10, C["dim"], anchor="start")

    x0, y0 = HOUSE_X0, HOUSE_Y0
    house = [(x0, y0), (x0 + AW, y0), (x0 + AW, y0 + 1.19), (x0 + HW, y0 + 1.19),
             (x0 + HW, y0 + HD), (x0, y0 + HD)]
    if stage == "bylo":
        g.poly(house, C["exist"], C["exist_fill"], 2)
        g.text(x0 + AW / 2, y0 + HD / 2, "Лит. А\n(цоколь А1,\nмансарда А2)", 11)
        g.text(x0 + AW + 1.0, y0 + 3.8, "а", 12, bold=True)
        g.dim(x0, y0 + HD, x0 + HW, y0 + HD, "8,70", off=-0.6)
        g.dim(x0, y0, x0, y0 + HD, "6,45", off=0.5)
        g.dim(x0 + 4, 0, x0 + 4, y0, "≈5,8", off=0)
        g.text(9, 25, "Участок без построек.\nВерхний слой снят при выравнивании,\nстоит вода (нужен дренаж).", 12, C["dim"])
        g.text(8.25, 1.4, "забор: металл на мет. столбах (по фасаду — ворота, калитка)", 10, C["dim"])
        g.legend([(C["exist"], C["exist_fill"], None, "существующий дом, 2002 г. (по техпаспорту)"),
                  (C["text"], "white", None, "граница участка (схематично, уточнить топосъёмкой)")],
                 top=g.h - g.extra_h + 40)
        g.save("genplan-bylo.svg")
        return

    # --- СТАЛО
    # фронтярд
    g.rect(0.6, 0.4, 5.0, 5.4, C["green"], C["green_fill"], 1.5)
    g.text(2.8, 2.9, "деревья,\nкусты", 10)
    g.rect(5.3, 0.6, 11.0, 5.3, C["path"], C["path_fill"], 1.5)
    g.text(8.15, 3.0, "Плитка:\nзаезд, дорожка\nк дому", 11)
    g.rect(11.1, 0.6, 15.8, 5.4, C["green"], "none", 2, "6,4")
    g.text(13.45, 3.0, "Навес /\nпарковка", 11)
    # проезд машин слева
    g.poly([(0.3, 5.6), (2.9, 5.6), (3.4, 30.5), (1.9, 30.5)], C["path"], C["path_fill"], 1, "4,4", 0.6)
    g.text(1.8, 14.5, "проезд машин вглубь участка (≈3 м)", 10, rotate=-88)
    # навес слева от дома
    g.rect(3.0, 9.1, 5.1, 13.1, C["green"], "none", 2, "6,4")
    g.text(4.05, 11.1, "навес", 10, rotate=-90)
    # дом существующий + пристройка
    g.poly(house, C["exist"], C["exist_fill"], 2)
    g.text(x0 + AW / 2, y0 + HD / 2, "ДОМ\n(существующий,\nреконструкция)", 11, bold=True)
    g.rect(x0, y0 + HD, x0 + HW, y0 + HD + EXT_D, C["new"], C["new_fill"], 2.5)
    g.text(x0 + HW / 2, y0 + HD + EXT_D / 2, "ПРИСТРОЙКА 5 м\nкухня-гостиная,\nвторой свет", 11, C["new"], bold=True)
    # терраса
    g.rect(x0, y0 + HD + EXT_D, x0 + HW, y0 + HD + EXT_D + 2.2, C["green"], C["green_fill"], 1.5)
    g.text(x0 + HW / 2, y0 + HD + EXT_D + 1.1, "открытая терраса", 11)
    # восточная сторона: навес + тамбур
    g.rect(x0 + HW, y0 - 0.2, x0 + HW + 2.0, y0 + HD + EXT_D, C["green"], "none", 2, "6,4")
    g.rect(x0 + HW, y0 + 3.2, x0 + HW + 2.0, y0 + 7.2, C["later"], C["later_fill"], 2, "5,3")
    g.text(x0 + HW + 1.0, y0 + 5.2, "тамбур-\nприхожая\n(позже)", 9, C["later"])
    g.text(x0 + HW + 1.0, y0 + 9.5, "навес\n2 м", 9)
    # дорожка
    g.poly([(8.6, 19.9), (9.8, 19.9), (10.4, 25.0), (9.9, 30.6), (8.9, 30.6), (9.2, 25.0)],
           C["path"], C["path_fill"], 1.5)
    # газон, теплица, грядки, хвойные
    g.poly([(3.6, 19.9), (8.4, 19.9), (8.8, 25.0), (5.0, 25.0), (3.8, 23.5)], C["green"], C["green_fill"], 1.5)
    g.text(6.4, 22.0, "газон\nдо 150 м²", 10)
    g.rect(2.4, 21.0, 3.7, 25.0, C["later"], "none", 2)
    g.text(3.05, 23.0, "теплица", 9, rotate=-90)
    g.rect(2.5, 25.4, 3.7, 27.6, C["later"], "none", 1.5)
    g.text(3.1, 26.5, "грядки", 8, rotate=-90)
    g.poly([(2.6, 28.0), (4.6, 28.0), (4.8, 30.4), (2.8, 30.4)], C["green"], C["green_fill"], 1.5)
    g.text(3.7, 29.2, "ели,\nможж.", 8)
    # пруд
    g.ellipse(6.9, 27.8, 2.2, 2.6, C["water"], C["water_fill"], 2)
    g.text(6.9, 27.8, "пруд\n≈100 м²?\n(на эскизе\n≈20–35)", 9)
    # костровая
    g.ellipse(13.0, 28.6, 2.1, 1.7, C["path"], C["path_fill"], 2)
    g.text(13.0, 28.6, "костровая\nзона", 10)
    # туи
    g.rect(10.6, 25.4, 16.6, 26.3, C["green"], C["green_fill"], 1.5)
    g.text(13.6, 25.85, "туи", 9)
    # кусты/клевер
    g.poly([(10.6, 20.4), (16.9, 20.4), (16.9, 25.0), (11.2, 25.0)], C["green"], C["green_fill"], 1.2, None, 0.6)
    g.text(13.8, 22.7, "кусты, деревья,\nклевер", 10)
    # дровник / хозблок
    g.rect(16.1, 26.8, 17.6, 30.3, C["later"], C["later_fill"], 2)
    g.text(16.85, 28.55, "дровник / хозблок", 8, rotate=-90)
    # гостевой домик
    gy0, gy1 = 30.8, 35.2
    g.rect(3.0, gy0, 11.3, gy1, C["new"], C["new_fill"], 2.5)
    g.text(7.15, (gy0 + gy1) / 2, "ГОСТЕВОЙ ДОМИК\nспальня, кухня-гостиная,\nс/у (круглогодичный)", 10, C["new"], bold=True)
    g.rect(11.3, gy0, 17.1, gy1, C["new"], "none", 2, "6,4")
    g.text(14.2, (gy0 + gy1) / 2, "крытая\nмангальная зона", 10, C["new"])
    # отступы
    g.text(9.6, 39.6, "домик: ≈1 м до границ (по желанию; норматив для жилого дома — 3 м)", 10, C["demo"])
    # сети
    g.line(8.25, 0, x0 + 3.0, y0, C["water"], 1.5, "3,3")
    g.text(7.2, 4.6, "", 8)
    g.legend([
        (C["exist"], C["exist_fill"], None, "существующий дом (реконструкция)"),
        (C["new"], C["new_fill"], None, "новое строительство (капитальное)"),
        (C["new"], "none", "6,4", "навесы (без стен)"),
        (C["later"], C["later_fill"], "5,3", "позже / без регистрации / лёгкие постройки"),
        (C["green"], C["green_fill"], None, "озеленение, терраса"),
        (C["path"], C["path_fill"], None, "мощение, дорожки, проезд"),
        (C["water"], C["water_fill"], None, "пруд"),
    ], top=g.h - g.extra_h + 25)
    g.save("genplan-stalo.svg")


# ---------------------------------------------------------------- поэтажные планы
def house_outline(g, stroke, fill, sw=3):
    g.poly([(0, 0), (AW, 0), (AW, 1.19), (HW, 1.19), (HW, HD), (0, HD)], stroke, fill, sw)


def plan_bylo(level):
    names = {1: "цоколь (лит. А1), h=2,00", 2: "1 этаж (лит. А и веранда а), h=2,80",
             3: "мансарда (лит. А2), h=2,52"}
    nums = {1: "Уровень 1", 2: "Уровень 2", 3: "Уровень 3"}
    g = Svg(10, 12.5, 45, margin=70, title=f"{nums[level]} — БЫЛО\n{names[level]}", extra_h=60)
    if level == 1:
        house_outline(g, C["exist"], C["exist_fill"])
        g.text(HW / 2, -0.9, "стены — бетонные блоки (ФБС), наружная высота 2,30", 11, C["dim"])
        g.rect(0.4, 0.4, 3.94, 5.99, C["exist"])
        g.text(2.17, 3.2, "6\nподсобная\n19,8 м²\n3,54×5,59", 11)
        g.rect(4.1, 3.4, 6.03, 6.02, C["exist"])
        g.text(5.06, 4.7, "8\n4,9 м²\n1,93×2,62", 10)
        g.rect(4.1, 0.4, 6.27, 3.03, C["exist"])
        g.text(5.18, 1.7, "7\n5,7 м²\n2,17×2,63", 10)
        g.rect(6.8, 1.55, 8.35, 6.0, C["exist"])
        g.text(7.57, 3.8, "9\n6,9 м²\n1,55×4,45", 10)
        g.text(HW / 2, -1.8, "Итого цоколь: 37,3 м²\nплощадь застройки 53,7 м²", 12)
    elif level == 2:
        house_outline(g, C["exist"], C["exist_fill"])
        g.text(HW / 2, -0.9, "стены — кирпич; веранда «а» — кирпич, холодная", 11, C["dim"])
        g.rect(0.38, 0.38, 3.89, 5.94, C["exist"])
        g.text(2.13, 3.2, "1\nкомната\n19,5 м²", 12)
        g.rect(4.02, 0.38, 6.19, 4.16, C["exist"])
        g.text(5.1, 2.4, "2\nкухня\n7,6 м²", 11)
        g.rect(4.3, 0.6, 4.7, 2.1, C["demo"], "none", 1.5)
        g.text(4.5, 1.35, "печь", 8, C["demo"], rotate=-90)
        g.rect(4.02, 4.26, 6.09, 6.0, C["exist"])
        g.text(5.05, 5.13, "3 · 3,6 м²", 10)
        g.rect(6.79, 1.31, 8.70 - 0.12, 6.31, C["exist"])
        g.text(7.68, 2.6, "4\nверанда\n9,6 м²\n(без отоп.)", 10)
        for i in range(6):
            g.line(6.85, 3.9 + i * 0.35, 8.5, 3.9 + i * 0.35, C["exist"], 1)
        g.text(7.68, 6.0, "лестница", 9)
        g.text(7.7, 0.55, "вход", 10, C["dim"])
        g.dim(0, HD, HW, HD, "8,70", off=-0.7)
        g.dim(0, 0, 0, HD, "6,45", off=0.6)
        g.text(HW / 2, -1.8, "Итого этаж: 40,3 м² (А: 30,7 + веранда 9,6)", 12)
    else:
        g.poly([(0, 0), (AW, 0), (AW, HD), (0, HD)], C["exist"], "none", 1.5, "6,4")
        g.rect(0.5, 0.2, 5.1, 6.4, C["exist"], C["exist_fill"], 3)
        g.text(2.8, 3.3, "5\nмансарда\n25,7 м²\n4,32×5,99\nh=2,52", 12)
        g.text(HW / 2, -0.9, "стены — каркасно-обшивные (под снос)", 11, C["dim"])
        g.text(HW / 2, -1.8, "Итого: 25,7 м². Общая площадь дома по техпаспорту — 103,3 м²", 12)
    g.save(f"etazh-{level}-bylo.svg")


def plan_stalo(level):
    names = {1: "бывший цоколь + пристройка (чистовая высота 2,5–2,6)",
             2: "бывший 1 этаж + второй свет",
             3: "мансарда — спальный этаж"}
    g = Svg(11.5, 13.5, 45, margin=70, title=f"Уровень {level} — СТАЛО\n{names[level]}", extra_h=150)
    ey = HD  # начало пристройки
    if level in (1, 2):
        house_outline(g, C["exist"], C["exist_fill"])
    if level == 1:
        g.rect(0, ey, HW, ey + EXT_D, C["new"], C["new_fill"], 3)
        # существующая часть
        g.rect(0.4, 3.2, 3.94, 5.99, C["exist"])
        g.text(2.17, 4.6, "хранение\nкрупное", 11)
        g.rect(0.4, 0.4, 3.94, 3.1, C["exist"])
        g.text(2.17, 1.75, "мастерская /\nhobby house", 11, bold=True)
        g.rect(4.1, 3.4, 6.03, 6.02, C["exist"])
        g.text(5.06, 4.7, "хранение\nмелкое", 10)
        g.rect(4.1, 0.4, 6.27, 3.03, C["exist"])
        g.text(5.18, 1.7, "кладовая /\nчасть\nмастерской?", 9)
        g.rect(6.8, 1.55, 8.35, 6.0, C["exist"])
        g.text(7.57, 4.6, "тех-\nпомещ.\nгаз,\nвода,\nэлектро", 9)
        g.rect(6.8, 1.55, 8.35, 2.9, C["new"], "none", 2)
        g.text(7.57, 2.2, "WC", 10, C["new"], bold=True)
        # проёмы из пристройки
        g.line(4.4, ey, 5.6, ey, "white", 6)
        g.line(4.4, ey, 5.6, ey, C["new"], 2, "3,3")
        g.text(5.0, ey - 0.35, "проём", 9, C["new"])
        # пристройка
        g.rect(0.25, ey + 0.25, 1.8, ey + EXT_D - 0.25, C["new"], "none", 1.5)
        g.text(1.0, ey + 2.5, "кухня (рабочая линия)", 10, C["new"], rotate=-90)
        g.ellipse(3.6, ey + 2.8, 1.2, 1.6, C["path"], C["path_fill"], 1.5)
        g.text(3.6, ey + 2.8, "обеденная\nзона", 10)
        g.ellipse(6.6, ey + 3.0, 1.6, 1.4, C["path"], C["path_fill"], 1.5)
        g.text(6.6, ey + 3.0, "гостиная,\nдиваны", 10)
        g.rect(7.6, ey + EXT_D - 0.9, 8.5, ey + EXT_D - 0.2, C["demo"], "#fadbd8", 2)
        g.text(8.05, ey + EXT_D + 0.35, "камин (мечта)", 9, C["demo"])
        for i in range(5):
            g.line(2.4 + i * 0.25, ey + 0.2, 2.4 + i * 0.25, ey + 1.3, C["new"], 1)
        g.text(3.0, ey + 1.55, "лестница ↑", 9, C["new"])
        g.text(HW / 2, ey + EXT_D + 0.6, "выход на открытую террасу", 10, C["green"])
        g.text(HW / 2, -0.9, "пол опустить: чистовая высота 2,5–2,6 м (нужно ≈2,7 в черновой)", 11, C["demo"])
        g.dim(0, ey, 0, ey + EXT_D, "5,00", off=0.6)
    elif level == 2:
        # второй свет над пристройкой
        g.rect(0, ey, HW, ey + EXT_D, C["new"], "#fef5e7", 3, "8,4")
        g.rect(0, ey, 1.8, ey + EXT_D, C["new"], C["new_fill"], 2)
        g.text(0.9, ey + 2.5, "библиотека / место для чтения\n(над кухней)", 9, C["new"], rotate=-90)
        g.text(5.2, ey + 2.7, "ВТОРОЙ СВЕТ\n(потолок ≈5–6 м\nот пола кухни)", 12, C["new"], bold=True)
        g.line(1.8, ey, 1.8, ey + EXT_D, C["new"], 3)
        g.text(2.15, ey + 4.0, "ограждение", 8, C["new"], rotate=-90)
        g.rect(0.38, 0.38, 3.89, 5.94, C["exist"])
        g.text(2.13, 3.2, "КАБИНЕТ /\nгостевая\n(жилая комната)\n≈19,5 м²", 11, bold=True)
        g.rect(4.02, 0.38, 6.19, 3.6, C["exist"])
        g.text(5.1, 2.0, "холл /\nприхожая", 10)
        g.rect(4.02, 3.7, 6.19, 6.0, C["exist"])
        for i in range(6):
            g.line(4.1, 3.9 + i * 0.35, 6.1, 3.9 + i * 0.35, C["new"], 1)
        g.text(5.1, 5.85, "лестница ↕", 9, C["new"])
        g.rect(6.79, 3.6, 8.58, 6.31, C["new"], "none", 2)
        g.text(7.68, 4.95, "ПАРНАЯ", 10, C["new"], bold=True)
        g.rect(6.79, 0.12, 8.58, 3.5, C["new"], "none", 2)
        g.text(7.68, 1.8, "душ +\nWC", 10, C["new"], bold=True)
        g.line(HW, 0.6, HW, 1.6, "white", 6)
        g.text(9.6, 1.1, "выход\nпод навес →", 9, C["later"])
        g.rect(HW, -0.2, HW + 2.0, ey + EXT_D, C["green"], "none", 2, "6,4")
        g.rect(HW, 3.2, HW + 2.0, 7.2, C["later"], C["later_fill"], 2, "5,3")
        g.text(HW + 1.0, 5.2, "тамбур-\nприхожая\n(позже)", 9, C["later"])
        g.text(HW + 1.0, 9.0, "навес", 9)
        g.text(HW / 2, -0.9, "печь демонтировать; веранда «а» → тёплая (душ+WC, парная)", 11, C["demo"])
    else:
        g.rect(0, 0, HW, ey + EXT_D, C["new"], C["new_fill"], 3)
        g.line(HW / 2, 0, HW / 2, ey + EXT_D, C["new"], 1, "10,5")
        g.text(HW / 2 + 0.25, ey + EXT_D - 0.6, "конёк", 9, C["new"], anchor="start")
        g.rect(0.3, 0.3, 4.2, 4.3, C["new"], "none", 1.5)
        g.text(2.25, 2.3, "спальня 1\n(родители)\n+ гардероб", 10)
        g.rect(4.5, 0.3, 8.4, 4.3, C["new"], "none", 1.5)
        g.text(6.45, 2.3, "спальня 2\n+ гардероб", 10)
        g.rect(4.1, 4.5, 6.2, 6.3, C["new"], "none", 1.5)
        g.text(5.15, 5.4, "лестница", 9)
        g.rect(0.3, 4.5, 3.9, 7.3, C["new"], "none", 1.5)
        g.text(2.1, 5.9, "с/у 1", 10)
        g.rect(6.4, 4.5, 8.4, 7.3, C["new"], "none", 1.5)
        g.text(7.4, 5.9, "с/у 2", 10)
        g.rect(0.3, 7.5, 3.9, 11.15, C["new"], "none", 1.5)
        g.text(2.1, 9.3, "гардеробная-\nпостирочная\n(общая)", 10)
        g.rect(4.1, 7.5, 8.4, 11.15, C["new"], "none", 1.5)
        g.text(6.25, 9.3, "спальня 3\n(сестра с мужем)\n+ гардероб", 10)
        g.poly([(0, 0), (AW, 0), (AW, 1.19), (HW, 1.19), (HW, HD), (0, HD)], C["exist"], "none", 1.5, "4,4")
        g.text(HW / 2, -0.9, "мансарда над домом и пристройкой; колено 1,2–1,5 м — уточнит архитектор", 11, C["dim"])
        g.dim(0, 0, 0, ey + EXT_D, "≈11,45", off=0.6)
    g.legend([
        (C["exist"], C["exist_fill"], None, "существующие стены (оставляем)"),
        (C["new"], C["new_fill"], None, "новое / перепланировка"),
        (C["later"], C["later_fill"], "5,3", "позже, после регистрации"),
        (C["demo"], "#fadbd8", None, "демонтаж / требует проверки"),
    ], top=g.h - g.extra_h + 20)
    g.save(f"etazh-{level}-stalo.svg")


def razrez():
    g = Svg(19, 11, 45, margin=110, title="Схематичный разрез Ю—С\nотметки ориентировочные, уточнит проект", extra_h=110)
    gl = 1.0  # земля: сейчас пол цоколя на 0,3 ниже земли; после понижения на 0,7 — на 1,0
    # уровни
    L1, L2, L3 = 0.0, 3.0, 6.1
    g.line(-0.5, gl, 18.5, gl, C["green"], 2, "8,4")
    g.text(17.2, gl + 0.35, "земля ≈ +1,0", 10, C["green"], anchor="start")
    # дом (юг слева) 6,45 / пристройка 5,0 / терраса 2,2
    hx0, hx1, ex1, tx1 = 1.0, 1.0 + HD, 1.0 + HD + EXT_D, 1.0 + HD + EXT_D + 2.2
    g.rect(hx0, L1, hx1, L2, C["exist"], C["exist_fill"], 2)
    g.text((hx0 + hx1) / 2, 1.5, "Уровень 1 (цоколь)\nh≈2,7 черн. / 2,5–2,6 чист.\nпол −0,7 м → ниже земли ≈1,0", 10)
    g.rect(hx0, L2, hx1, L3, C["exist"], C["exist_fill"], 2)
    g.text((hx0 + hx1) / 2, 4.55, "Уровень 2\n(кирпич, h=2,80)", 10)
    g.rect(hx1, L1, ex1, L3, C["new"], C["new_fill"], 2)
    g.text((hx1 + ex1) / 2, 4.5, "второй свет\n≈5,5–6 м", 10, C["new"], bold=True)
    g.rect(hx1, L2, hx1 + 1.8, L2 + 0.25, C["new"], C["new"], 1)
    g.text(hx1 + 0.9, L2 + 0.6, "библиотека", 8, C["new"])
    g.text((hx1 + ex1) / 2, 1.3, "пристройка: кухня-гостиная", 10, C["new"])
    # мансарда / кровля
    ridge = L3 + 3.6
    g.poly([(hx0 - 0.5, L3), (ex1 + 0.5, L3), ((hx0 + ex1) / 2, ridge)], C["new"], C["new_fill"], 2)
    g.text((hx0 + ex1) / 2, L3 + 1.3, "Уровень 3 — мансарда (спальни)", 10, C["new"], bold=True)
    g.rect(ex1, gl - 0.15, tx1, gl, C["green"], C["green_fill"], 1.5)
    g.text(tx1 + 0.2, gl - 0.1, "терраса", 9, anchor="start")
    # фундамент
    g.rect(hx0, -0.7, hx1, L1, C["demo"], "#fadbd8", 1.5, "4,3")
    g.text((hx0 + hx1) / 2, -0.35, "подводка/усиление фундамента ФБС?", 9, C["demo"])
    g.rect(hx1, -0.6, ex1, L1, C["new"], "none", 1.5, "4,3")
    g.text((hx1 + ex1) / 2, -0.3, "новый фундамент + гидроизоляция", 9, C["new"])
    for lvl, nm in ((L1, "±0,00"), (L2, "+3,00"), (L3, "+6,10"), (ridge, "≈+9,7 конёк")):
        g.line(-0.4, lvl, hx0, lvl, C["dim"], 1)
        g.text(-0.5, lvl, nm, 10, C["dim"], anchor="end")
    g.text(hx0, -1.3, "ЮГ (проезд)", 10, C["dim"])
    g.text(tx1, -1.3, "СЕВЕР (сад)", 10, C["dim"])
    g.raw_text(g.m, g.h - 80, "Сейчас пол цоколя ниже земли на 0,3 м. После понижения на 0,7 м — ниже на ≈1,0 м. Выход из пристройки в сад «в уровень»", 12)
    g.raw_text(g.m, g.h - 60, "требует понизить террасу/сад у дома на ≈1 м (подпорные стенки, дренаж) или пол пристройки выше пола цоколя (ступени).", 12)
    g.raw_text(g.m, g.h - 40, "Высота до конька по ПЗЗ ограничена (для ИЖС обычно ≤20 м и ≤3 надземных этажа) — запас есть.", 12)
    g.save("razrez.svg")


if __name__ == "__main__":
    genplan("bylo")
    genplan("stalo")
    for lv in (1, 2, 3):
        plan_bylo(lv)
        plan_stalo(lv)
    razrez()
