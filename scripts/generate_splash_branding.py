# -*- coding: utf-8 -*-
"""
Добавляет название приложения под иконкой на заставке (Фаза 4+, находка
из внешнего показа демо владельцу 2026-09-03).

Правит только "лёгаси"-путь заставки (`android/app/src/main/res/
drawable*/splash.png`, используется через `launch_background.xml` на
Android <12 - подтверждено на Redmi Note 8T, API 30). Файлы
`android12splash.png` (Android 12+ SplashScreen API) намеренно не
трогаются - эта системная API сама масштабирует изображение в свою
рамку иконки и не рассчитана на произвольный контент вроде текста под
иконкой; правка без реального устройства с Android 12+ для проверки
слишком рискованна.

Источник глифа - `assets/icon/icon_foreground.png` (тот же файл, из
которого изначально сгенерирована сама заставка через
flutter_native_splash, см. scripts/generate_app_icon.py) - не
перерисовывается заново, чтобы не разойтись с иконкой по деталям.

Запуск (из корня mobile/):
    python ../scripts/generate_splash_branding.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parent.parent
MOBILE_DIR = REPO_ROOT / "mobile"
RES_DIR = MOBILE_DIR / "android" / "app" / "src" / "main" / "res"
GLYPH_PATH = MOBILE_DIR / "assets" / "icon" / "icon_foreground.png"

CANVAS_SIZE = 1024
APP_NAME = "ОГЭ-Тьютор"
FONT_PATH = "C:/Windows/Fonts/segoeuib.ttf"
FONT_SIZE = 76
TEXT_BAND_TOP = 868  # ниже этой Y начинается прозрачная полоса под глифом
TEXT_BAND_HEIGHT = CANVAS_SIZE - TEXT_BAND_TOP

DENSITIES = {
    "mdpi": 256,
    "hdpi": 384,
    "xhdpi": 512,
    "xxhdpi": 768,
    "xxxhdpi": 1024,
}


def build_master() -> Image.Image:
    glyph = Image.open(GLYPH_PATH).convert("RGBA")
    assert glyph.size == (CANVAS_SIZE, CANVAS_SIZE), glyph.size

    canvas = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    canvas.alpha_composite(glyph)

    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    bbox = draw.textbbox((0, 0), APP_NAME, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (CANVAS_SIZE - w) / 2 - bbox[0]
    y = TEXT_BAND_TOP + (TEXT_BAND_HEIGHT - h) / 2 - bbox[1]
    draw.text((x, y), APP_NAME, font=font, fill=(255, 255, 255, 255))

    return canvas


def main() -> None:
    master = build_master()
    for density, size in DENSITIES.items():
        resized = master.resize((size, size), Image.LANCZOS)
        for prefix in (f"drawable-{density}", f"drawable-night-{density}"):
            path = RES_DIR / prefix / "splash.png"
            resized.save(path)
            print(f"-> {path}")


if __name__ == "__main__":
    main()
