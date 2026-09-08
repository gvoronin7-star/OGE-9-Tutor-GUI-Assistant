# -*- coding: utf-8 -*-
"""
Генерирует витринные иллюстрации для тем "Право" и "Экономика" -
две из трёх схем, показанных как черновик в артефакте с идеями по
иллюстрациям (2026-09-03/04), решение владельца встроить пришло
2026-09-08. Третья (для темы "Человек и общество",
social_institutions.png) уже в сборке с 2026-09-03 - её собственный
скрипт генерации не сохранился в репозитории (остался только PNG),
поэтому геометрия и палитра здесь измерены заново по самому файлу
(radius/центры кругов через сканирование пикселей, цвета - через
getpixel), чтобы новые схемы визуально совпадали, а не рисовались "на
глаз".

Тот же приём хаб-спицы (тёмный индиго-круг в центре, светлее-индиго
спутники, соединительные линии) на канве 1000x620:
- Экономика: хаб "Экономика", три спутника - Производство /
  Распределение / Потребление, три стадии, которые статья называет
  прямо в первом абзаце ("...для производства, распределения и
  потребления товаров и услуг").
- Право: хаб "Права человека", четыре спутника - Гражданские /
  Политические / Экономические / Социально-культурные - ровно та
  группировка, что в статье третьим абзацем ("Права человека делятся
  на несколько групп: ..."). Не буквально "отрасли права" из
  черновика идеи в артефакте - в актуальном тексте статьи нет
  гражданского/уголовного/административного деления, зато есть эта
  группировка; иллюстрация должна подкреплять то, что реально в
  статье, а не то, что было предложено до чтения текста.

Запуск (из корня репозитория):
    python scripts/generate_topic_illustrations.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "mobile" / "assets" / "images"
FONT_PATH = "C:/Windows/Fonts/segoeuib.ttf"

CANVAS_SIZE = (1000, 620)
HUB_CENTER = (500, 310)
HUB_RADIUS = 105
SAT_RADIUS = 95

HUB_COLOR = (63, 81, 181, 255)
SAT_COLOR = (92, 107, 192, 255)
LINE_COLOR = (121, 134, 203, 200)
LINE_WIDTH = 6
TEXT_COLOR = (255, 255, 255, 255)

# Позиции спутников измерены по assets/images/social_institutions.png
# (сканирование границ кругов по пикселям) - четвёрка используется как
# есть, тройка - тот же canvas, треугольником вокруг хаба.
POSITIONS_4 = [(150, 130), (850, 130), (150, 490), (850, 490)]
POSITIONS_3 = [(500, 110), (170, 490), (830, 490)]


def _fit_font(
    draw: ImageDraw.ImageDraw, lines: list[str], max_width: int, max_size: int
) -> ImageFont.FreeTypeFont:
    size = max_size
    while size > 12:
        font = ImageFont.truetype(FONT_PATH, size)
        widest = max(draw.textbbox((0, 0), line, font=font)[2] for line in lines)
        if widest <= max_width:
            return font
        size -= 2
    return ImageFont.truetype(FONT_PATH, 12)


def _draw_centered_lines(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
    lines: list[str],
    max_width: int,
    max_size: int,
) -> None:
    font = _fit_font(draw, lines, max_width, max_size)
    line_heights = [
        draw.textbbox((0, 0), line, font=font)[3]
        - draw.textbbox((0, 0), line, font=font)[1]
        for line in lines
    ]
    spacing = 6
    total_h = sum(line_heights) + spacing * (len(lines) - 1)
    y = center[1] - total_h / 2
    for line, h in zip(lines, line_heights):
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = center[0] - w / 2 - bbox[0]
        draw.text((x, y - bbox[1]), line, font=font, fill=TEXT_COLOR)
        y += h + spacing


def build_diagram(hub_lines: list[str], satellites: list[list[str]]) -> Image.Image:
    canvas = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    positions = POSITIONS_4 if len(satellites) == 4 else POSITIONS_3

    for pos in positions:
        draw.line([HUB_CENTER, pos], fill=LINE_COLOR, width=LINE_WIDTH)

    for pos in positions:
        draw.ellipse(
            [
                pos[0] - SAT_RADIUS,
                pos[1] - SAT_RADIUS,
                pos[0] + SAT_RADIUS,
                pos[1] + SAT_RADIUS,
            ],
            fill=SAT_COLOR,
        )
    draw.ellipse(
        [
            HUB_CENTER[0] - HUB_RADIUS,
            HUB_CENTER[1] - HUB_RADIUS,
            HUB_CENTER[0] + HUB_RADIUS,
            HUB_CENTER[1] + HUB_RADIUS,
        ],
        fill=HUB_COLOR,
    )

    for pos, lines in zip(positions, satellites):
        _draw_centered_lines(
            draw, pos, lines, max_width=int(SAT_RADIUS * 1.7), max_size=34
        )
    _draw_centered_lines(
        draw, HUB_CENTER, hub_lines, max_width=int(HUB_RADIUS * 1.7), max_size=38
    )

    return canvas


def main() -> None:
    economy = build_diagram(
        hub_lines=["Экономика"],
        satellites=[["Производство"], ["Распределение"], ["Потребление"]],
    )
    economy_path = OUTPUT_DIR / "economic_cycle.png"
    economy.save(economy_path)
    print(f"-> {economy_path}")

    law = build_diagram(
        hub_lines=["Права", "человека"],
        satellites=[
            ["Гражданские"],
            ["Политические"],
            ["Экономические"],
            ["Социально-", "культурные"],
        ],
    )
    law_path = OUTPUT_DIR / "human_rights_groups.png"
    law.save(law_path)
    print(f"-> {law_path}")


if __name__ == "__main__":
    main()
