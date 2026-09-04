# -*- coding: utf-8 -*-
"""
Генерация базовой иконки приложения (Фаза 4).

Рисует академическую шапочку (mortarboard) на закруглённом
индиго-квадрате - тот же seed-цвет, что Material 3 тема приложения
(Colors.indigo, mobile/lib/core/theme.dart). Только базовый файл для
flutter_launcher_icons/flutter_native_splash - масштабирование под
конкретные размеры платформ делают сами эти пакеты.

Запуск:
    python scripts/generate_app_icon.py
"""

from pathlib import Path

from PIL import Image, ImageDraw

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "mobile" / "assets" / "icon"

SIZE = 1024
INDIGO = (63, 81, 181, 255)  # Material Colors.indigo
WHITE = (255, 255, 255, 255)


def draw_icon(background: bool) -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if background:
        draw.rounded_rectangle([(0, 0), (SIZE, SIZE)], radius=SIZE // 5, fill=INDIGO)

    cx, cy = SIZE // 2, SIZE // 2 - SIZE // 30

    # Плоский верх шапочки (ромб)
    half_w, half_h = SIZE * 0.34, SIZE * 0.14
    board = [
        (cx, cy - half_h),
        (cx + half_w, cy),
        (cx, cy + half_h),
        (cx - half_w, cy),
    ]
    draw.polygon(board, fill=WHITE)

    # Основание (купол) под ромбом
    base_w, base_h = SIZE * 0.20, SIZE * 0.14
    draw.rounded_rectangle(
        [
            (cx - base_w / 2, cy + half_h * 0.15),
            (cx + base_w / 2, cy + half_h * 0.15 + base_h),
        ],
        radius=int(base_w * 0.25),
        fill=WHITE,
    )

    # Кисточка (тассель): линия от центра ромба к кружку сбоку
    tassel_start = (cx, cy)
    tassel_mid = (cx + half_w * 0.55, cy + half_h * 1.6)
    tassel_end = (cx + half_w * 0.55, cy + half_h * 2.4)
    draw.line([tassel_start, tassel_mid], fill=WHITE, width=SIZE // 60)
    draw.line([tassel_mid, tassel_end], fill=WHITE, width=SIZE // 60)
    tassel_r = SIZE * 0.035
    draw.ellipse(
        [
            (tassel_end[0] - tassel_r, tassel_end[1] - tassel_r),
            (tassel_end[0] + tassel_r, tassel_end[1] + tassel_r),
        ],
        fill=WHITE,
    )

    return img


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    full = draw_icon(background=True)
    full_path = OUTPUT_DIR / "icon.png"
    full.save(full_path)
    print(f"Иконка (с фоном) -> {full_path}")

    # Foreground-only версия для Android adaptive icons (фон задаётся
    # отдельно как сплошной цвет через flutter_launcher_icons).
    foreground = draw_icon(background=False)
    foreground_path = OUTPUT_DIR / "icon_foreground.png"
    foreground.save(foreground_path)
    print(f"Иконка (foreground) -> {foreground_path}")


if __name__ == "__main__":
    main()
