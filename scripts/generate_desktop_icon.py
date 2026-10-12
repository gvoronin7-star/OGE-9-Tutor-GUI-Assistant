# -*- coding: utf-8 -*-
"""
Генерация значка окна/таскбара для десктопного GUI (фаза 3 доработки
дизайна десктопа, см. decisions/decision-log.md, 2026-10-12).

Повторно использует `draw_icon()` из generate_app_icon.py — та же
академическая шапочка на индиго-квадрате, что уже служит иконкой
мобильного приложения. Не бренд заказчика (владелец решил не ждать
бренда для этого шага) — просто то, что уже есть и узнаваемо между
обоими клиентами.

Запуск:
    python scripts/generate_desktop_icon.py
"""

from pathlib import Path

from generate_app_icon import draw_icon
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "gui_debugger" / "assets" / "icon"

# tk.PhotoImage читает PNG нативно (Tcl/Tk 8.6+) — отдельный .ico не нужен,
# iconphoto() сам подбирает подходящий размер из переданного набора.
SIZES = (16, 32, 48, 64, 128, 256)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    full = draw_icon(background=True)

    for size in SIZES:
        resized = full.resize((size, size), resample=Image.Resampling.BICUBIC)
        path = OUTPUT_DIR / f"app_icon_{size}.png"
        resized.save(path)
        print(f"{size}x{size} -> {path}")


if __name__ == "__main__":
    main()
