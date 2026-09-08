# -*- coding: utf-8 -*-
"""
Панель управления RAG базой данных.

Позволяет пользователю:
- Выбрать новую папку с базой RAG
- Загрузить и заменить текущую базу
- Проверить статус базы
- Просмотреть статистику
"""

import json
import logging
import os
import shutil
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Callable, Optional, cast

from gui_debugger.utils.gui_logger import log_action, log_error

logger = logging.getLogger(__name__)

# Реальный загрузчик (api/vector_store_existing.py::ExistingVectorStore)
# читает RAG_data_base/vector_db/{dataset.json,index.faiss,metadata.json} -
# эта панель раньше проверяла и показывала совсем другую, никогда не
# читаемую структуру (chunks/*.md, metadata/*.json, indices/*), из-за
# чего реальная база на 157 чанков показывалась как "Статус: Пустая", а
# "валидная" по чек-листу панели папка всё равно не подошла бы
# загрузчику. Найдено зональным аудитом хаба 2026-09-08 (К-7).
REQUIRED_VECTOR_DB_FILES = ("dataset.json", "index.faiss", "metadata.json")


def _vector_db_chunk_count(base_path: Path) -> Optional[int]:
    """Число чанков в base_path/vector_db/dataset.json, None если не читается."""
    dataset_file = base_path / "vector_db" / "dataset.json"
    try:
        with open(dataset_file, "r", encoding="utf-8") as f:
            return len(json.load(f))
    except (OSError, json.JSONDecodeError, TypeError):
        return None


def _missing_vector_db_files(base_path: Path) -> list[str]:
    """Список отсутствующих файлов vector_db/ внутри base_path."""
    vector_db = base_path / "vector_db"
    return [
        name for name in REQUIRED_VECTOR_DB_FILES if not (vector_db / name).exists()
    ]


class RAGManager(ttk.Frame):
    """Панель управления RAG базой данных."""

    def __init__(
        self,
        parent: tk.Widget,
        rag_pipeline: Optional[Any] = None,
        on_back: Optional[Callable[[], Any]] = None,
    ) -> None:
        """
        Инициализация панели управления RAG.

        Args:
            parent: Родительский виджет
            rag_pipeline: RAG-пайплайн
            on_back: Callback для кнопки "Назад"
        """
        super().__init__(parent)
        self.rag_pipeline = rag_pipeline
        self.on_back = on_back

        self.new_base_path: Optional[Path] = None

        self._create_widgets()
        self._update_status()

    def _create_widgets(self) -> None:
        """Создание виджетов."""
        # Заголовок
        header = ttk.Frame(self)
        header.pack(fill=tk.X, pady=10)

        back_btn = ttk.Button(
            header,
            text="🔙 Назад",
            command=cast(Callable[[], Any], self.on_back),
            width=15,
        )
        back_btn.pack(side=tk.LEFT, padx=10)

        title = ttk.Label(
            header,
            text="🗄️ УПРАВЛЕНИЕ RAG БАЗОЙ",
            font=("Segoe UI", 14, "bold"),
            foreground="#0078d4",
        )
        title.pack()

        # Разделитель
        ttk.Separator(header, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=20, pady=10)

        # Текущая база
        current_frame = ttk.LabelFrame(self, text="Текущая база данных", padding=10)
        current_frame.pack(fill=tk.X, padx=20, pady=10)

        self.current_path_label = ttk.Label(
            current_frame,
            text="Не определена",
            font=("Segoe UI", 10),
            foreground="#808080",
            wraplength=600,
        )
        self.current_path_label.pack(anchor=tk.W)

        self.current_status_label = ttk.Label(
            current_frame,
            text="Статус: Неизвестно",
            font=("Segoe UI", 9),
            foreground="#808080",
        )
        self.current_status_label.pack(anchor=tk.W, pady=(5, 0))

        self.current_stats_label = ttk.Label(
            current_frame,
            text="Статистика: --",
            font=("Segoe UI", 9),
            foreground="#808080",
        )
        self.current_stats_label.pack(anchor=tk.W, pady=(5, 0))

        # Разделитель
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=20, pady=10)

        # Загрузка новой базы
        upload_frame = ttk.LabelFrame(self, text="Загрузка новой базы", padding=10)
        upload_frame.pack(fill=tk.X, padx=20, pady=10)

        # Выбор папки
        path_frame = ttk.Frame(upload_frame)
        path_frame.pack(fill=tk.X, pady=5)

        ttk.Label(path_frame, text="Папка с базой:", font=("Segoe UI", 10)).pack(
            side=tk.LEFT, padx=5
        )

        self.path_var = tk.StringVar(value="")
        path_entry = ttk.Entry(path_frame, textvariable=self.path_var, width=60)
        path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        browse_btn = ttk.Button(
            path_frame, text="📁 Обзор...", command=self._browse_folder, width=15
        )
        browse_btn.pack(side=tk.LEFT, padx=5)

        # Информация о новой базе
        self.new_base_info_label = ttk.Label(
            upload_frame,
            text="Папка не выбрана",
            font=("Segoe UI", 9),
            foreground="#808080",
        )
        self.new_base_info_label.pack(anchor=tk.W, pady=(5, 0))

        # Кнопки управления
        btn_frame = ttk.Frame(upload_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        validate_btn = ttk.Button(
            btn_frame, text="✓ Проверить базу", command=self._validate_base, width=20
        )
        validate_btn.pack(side=tk.LEFT, padx=5)

        self.upload_btn = ttk.Button(
            btn_frame,
            text="🔄 Заменить базу",
            command=self._upload_base,
            state=tk.DISABLED,
            style="Accent.TButton",
            width=20,
        )
        self.upload_btn.pack(side=tk.LEFT, padx=5)

        # Статус операции
        self.operation_status_label = ttk.Label(
            upload_frame, text="", font=("Segoe UI", 9), wraplength=600
        )
        self.operation_status_label.pack(anchor=tk.W, pady=(5, 0))

        # Разделитель
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=20, pady=10)

        # Инструкция
        info_frame = ttk.LabelFrame(self, text="Инструкция", padding=10)
        info_frame.pack(fill=tk.X, padx=20, pady=10)

        info_text = tk.Text(
            info_frame, height=8, wrap=tk.WORD, font=("Segoe UI", 9), state=tk.DISABLED
        )
        info_text.pack(fill=tk.X)

        info_text.config(state=tk.NORMAL)
        info_text.insert(
            tk.END,
            """Операция замены базы данных:

1. Нажмите "📁 Обзор..." и выберите папку с новой базой RAG - она
   должна содержать подпапку vector_db/ с файлами dataset.json,
   index.faiss и metadata.json (формат, который реально использует
   бэкенд)
2. Нажмите "✓ Проверить базу" для валидации
3. Нажмите "🔄 Заменить базу" для замены
4. Дождитесь завершения операции

ВНИМАНИЕ:
- Новая база сначала копируется и проверяется во временном каталоге;
  текущая база не удаляется, а переименовывается в RAG_data_base_backup/
  и остаётся на диске
- Замена вступит в силу только при USE_EXISTING_INDEX=true в .env
- Операция может занять несколько минут
- Во время загрузки не закрывайте приложение
""",
        )
        info_text.config(state=tk.DISABLED)

        # Статус бар
        self.status_bar = ttk.Label(
            self, text="Готов", font=("Segoe UI", 9), foreground="#808080"
        )
        self.status_bar.pack(pady=5)

    def _browse_folder(self) -> None:
        """Открытие диалога выбора папки."""
        folder = filedialog.askdirectory(
            title="Выберите папку с RAG базой данных", initialdir=Path.home()
        )

        if folder:
            self.path_var.set(folder)
            self.new_base_path = Path(folder)
            self._check_new_base()

    def _check_new_base(self) -> None:
        """Проверка новой базы данных."""
        if not self.new_base_path or not self.new_base_path.exists():
            self.new_base_info_label.configure(
                text="Папка не выбрана", foreground="#808080"
            )
            return

        # Проверка структуры - vector_db/{dataset.json,index.faiss,metadata.json},
        # ровно то, что реально читает ExistingVectorStore.load().
        missing = _missing_vector_db_files(self.new_base_path)

        if missing:
            self.new_base_info_label.configure(
                text=f"❌ В vector_db/ отсутствуют файлы: {', '.join(missing)}",
                foreground="#e81123",
            )
            self.upload_btn.configure(state=tk.DISABLED)
        else:
            chunks_count = _vector_db_chunk_count(self.new_base_path)
            if chunks_count is None:
                self.new_base_info_label.configure(
                    text="❌ dataset.json повреждён или не читается",
                    foreground="#e81123",
                )
                self.upload_btn.configure(state=tk.DISABLED)
            else:
                self.new_base_info_label.configure(
                    text=f"✅ База готова: {chunks_count} чанков", foreground="#107c10"
                )
                self.upload_btn.configure(state=tk.NORMAL)

    def _validate_base(self) -> None:
        """Валидация новой базы данных."""
        self.status_bar.configure(text="Проверка базы...", foreground="#0078d4")
        self.operation_status_label.configure(text="", foreground="#808080")

        if not self.new_base_path or not self.new_base_path.exists():
            self.operation_status_label.configure(
                text="❌ Папка не выбрана", foreground="#e81123"
            )
            self.status_bar.configure(text="Ошибка", foreground="#e81123")
            return

        try:
            # Проверка структуры - см. REQUIRED_VECTOR_DB_FILES выше.
            missing = _missing_vector_db_files(self.new_base_path)

            if missing:
                self.operation_status_label.configure(
                    text=f"❌ В vector_db/ отсутствуют файлы: {', '.join(missing)}",
                    foreground="#e81123",
                )
                self.status_bar.configure(text="Ошибка", foreground="#e81123")
                return

            chunks_count = _vector_db_chunk_count(self.new_base_path)
            if chunks_count is None:
                self.operation_status_label.configure(
                    text="❌ dataset.json повреждён или не читается",
                    foreground="#e81123",
                )
                self.status_bar.configure(text="Ошибка", foreground="#e81123")
                return

            self.operation_status_label.configure(
                text=f"✅ База валидна: {chunks_count} чанков в vector_db/",
                foreground="#107c10",
            )

            self.status_bar.configure(text="Готово", foreground="#107c10")

            # Логирование
            log_action(
                "rag_validation",
                {"path": str(self.new_base_path), "chunks": chunks_count},
            )

            use_existing_index = os.getenv("USE_EXISTING_INDEX", "false").lower()
            index_warning = (
                ""
                if use_existing_index == "true"
                else "\n\n⚠️ USE_EXISTING_INDEX не включён - после замены "
                "бэкенд продолжит использовать пустой локальный индекс, "
                "новая база не вступит в силу."
            )
            messagebox.showinfo(
                "Валидация успешна",
                f"База данных валидна!\n\nЧанков: {chunks_count}\n\n"
                f"Можно загружать.{index_warning}",
            )

        except Exception as e:
            self.operation_status_label.configure(
                text=f"❌ Ошибка: {str(e)}", foreground="#e81123"
            )
            self.status_bar.configure(text="Ошибка", foreground="#e81123")

            log_error("rag_validation", str(e))
            messagebox.showerror("Ошибка валидации", str(e))

    def _upload_base(self) -> None:
        """Загрузка новой базы данных."""
        # Подтверждение
        confirm = messagebox.askyesno(
            "Подтверждение замены базы",
            "ВНИМАНИЕ!\n\n"
            "Вы собираетесь заменить текущую базу данных RAG.\n"
            "Старая база будет переименована в RAG_data_base_backup/ "
            "(предыдущий бэкап, если был, будет удалён).\n\n"
            "Продолжить?",
            icon=messagebox.WARNING,
        )

        if not confirm:
            return

        # Блокировка кнопок
        self.upload_btn.configure(state=tk.DISABLED)
        self.status_bar.configure(text="Загрузка базы...", foreground="#0078d4")
        self.operation_status_label.configure(
            text="Начинаю загрузку...", foreground="#0078d4"
        )

        # Запуск в отдельном потоке
        thread = threading.Thread(target=self._upload_base_thread, daemon=True)
        thread.start()

    def _upload_base_thread(self) -> None:
        """
        Загрузка базы в отдельном потоке.

        Раньше `rmtree` текущей базы выполнялся ДО того, как новая база
        была на месте - любая ошибка между шагами оставляла проект без
        рабочей базы вообще (спасала только резервная копия рядом, если
        её кто-то вручную восстановил). Теперь новая база сначала
        копируется во временный каталог и заново проверяется там же, и
        только после этого текущая база переименовывается в бэкап, а
        временная - на её место: `Path.rename()` на одной файловой
        системе - переименование записи в каталоге, не копирование, и
        либо происходит целиком, либо не происходит вовсе. Найдено
        зональным аудитом хаба 2026-09-08 (К-7).
        """
        current_base = Path("RAG_data_base")
        backup_base = Path("RAG_data_base_backup")
        temp_base = Path("RAG_data_base_incoming_tmp")

        try:
            if not self.rag_pipeline:
                self._upload_error("RAG-пайплайн не инициализирован")
                return

            assert self.new_base_path is not None, "Новая база не выбрана"

            # Шаг 1: скопировать новую базу во временный каталог и
            # проверить именно эту копию (а не источник, который мог
            # измениться после выбора папки).
            self._set_operation_status("Копирование новой базы во временный каталог...")

            if temp_base.exists():
                shutil.rmtree(temp_base)
            shutil.copytree(self.new_base_path, temp_base)

            self._set_operation_status("Повторная проверка скопированной базы...")
            missing = _missing_vector_db_files(temp_base)
            if missing:
                shutil.rmtree(temp_base)
                self._upload_error(
                    f"В скопированной базе отсутствуют файлы vector_db/: "
                    f"{', '.join(missing)} - текущая база не тронута."
                )
                return
            if _vector_db_chunk_count(temp_base) is None:
                shutil.rmtree(temp_base)
                self._upload_error(
                    "dataset.json скопированной базы повреждён или не "
                    "читается - текущая база не тронута."
                )
                return

            # Шаг 2: старая база -> бэкап, новая (временная) -> на место
            # старой. Обе операции - rename на одной файловой системе,
            # не copytree+rmtree - окно, в котором проекта нет ни в
            # каком виде, исчезающе мало по сравнению со старой версией.
            self._set_operation_status("Замена текущей базы...")

            if current_base.exists():
                if backup_base.exists():
                    shutil.rmtree(backup_base)
                current_base.rename(backup_base)

            temp_base.rename(current_base)

            # Шаг 3: переиндексировать
            self._set_operation_status("Переиндексация базы...")

            import asyncio

            from gui_debugger.utils.async_helper import async_helper

            async def reindex():
                await self.rag_pipeline.initialize()
                return True

            success = async_helper.run_async(reindex())

            if success:
                self._upload_success()
            else:
                self._upload_error("Ошибка переиндексации")

        except Exception as e:
            self._upload_error(str(e))

    def _set_operation_status(self, message: str) -> None:
        """
        Обновление статуса операции.

        Вызывается из фонового потока (`_upload_base_thread`) — маршалит
        обращение к виджетам на главный поток через `after()`, поскольку
        Tkinter не потокобезопасен.
        """

        def _do() -> None:
            self.operation_status_label.configure(text=message, foreground="#0078d4")
            self.update()

        self.after(0, _do)

    def _upload_success(self) -> None:
        """
        Успешная загрузка базы.

        Вызывается из фонового потока — маршалит на главный поток через
        `after()`, поскольку Tkinter/`messagebox` не потокобезопасны.
        """

        def _do() -> None:
            self.operation_status_label.configure(
                text="✅ База успешно заменена!", foreground="#107c10"
            )
            self.status_bar.configure(text="Готово", foreground="#107c10")
            self.upload_btn.configure(state=tk.NORMAL)

            # Обновить статус текущей базы
            self._update_status()

            # Логирование
            log_action(
                "rag_base_replaced",
                {"new_path": str(self.new_base_path), "success": True},
            )

            messagebox.showinfo(
                "Успех",
                "База данных успешно заменена!\n\n"
                "Старая база сохранена в RAG_data_base_backup/\n\n"
                "Рекомендуется проверить работу системы.",
            )

            self.new_base_path = None
            self.path_var.set("")
            self.new_base_info_label.configure(
                text="Папка не выбрана", foreground="#808080"
            )

        self.after(0, _do)

    def _upload_error(self, error_message: str) -> None:
        """
        Ошибка загрузки базы.

        Вызывается из фонового потока — маршалит на главный поток через
        `after()`, поскольку Tkinter/`messagebox` не потокобезопасны.
        """

        def _do() -> None:
            self.operation_status_label.configure(
                text=f"❌ Ошибка: {error_message}", foreground="#e81123"
            )
            self.status_bar.configure(text="Ошибка", foreground="#e81123")
            self.upload_btn.configure(state=tk.NORMAL)

            # Логирование
            log_error("rag_base_replaced", error_message)

            messagebox.showerror("Ошибка замены базы", error_message)

        self.after(0, _do)

    def _update_status(self) -> None:
        """Обновление статуса текущей базы."""
        current_base = Path("RAG_data_base")

        if not current_base.exists():
            self.current_path_label.configure(
                text="Не определена", foreground="#808080"
            )
            self.current_status_label.configure(
                text="Статус: База не найдена", foreground="#e81123"
            )
            self.current_stats_label.configure(
                text="Статистика: --", foreground="#808080"
            )
            return

        # Путь
        self.current_path_label.configure(
            text=f"Путь: {current_base.absolute()}", foreground="#303030"
        )

        # Статистика - vector_db/dataset.json, то же, что реально читает
        # ExistingVectorStore.load(). Раньше здесь проверялась
        # chunks/*.md - структура, которую загрузчик не читает вообще,
        # из-за чего реальная база на 157 чанков показывалась как
        # "Статус: Пустая". Найдено зональным аудитом хаба 2026-09-08 (К-7).
        try:
            chunks_count = _vector_db_chunk_count(current_base)

            if chunks_count is None:
                self.current_stats_label.configure(
                    text="Статистика: vector_db/dataset.json не найден или повреждён",
                    foreground="#303030",
                )
                self.current_status_label.configure(
                    text="Статус: Пустая", foreground="#ffb900"
                )
            else:
                self.current_stats_label.configure(
                    text=f"Статистика: {chunks_count} чанков в vector_db/",
                    foreground="#303030",
                )
                self.current_status_label.configure(
                    text="Статус: Активна", foreground="#107c10"
                )

        except Exception as e:
            self.current_stats_label.configure(
                text=f"Статистика: Ошибка ({str(e)})", foreground="#e81123"
            )
