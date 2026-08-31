# -*- coding: utf-8 -*-
"""
Панель управления пользователями.

Список, статистика, блокировка.
"""

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional


class UsersPanel(ttk.Frame):
    """Панель пользователей."""

    def __init__(self, parent: tk.Widget) -> None:
        """
        Инициализация панели пользователей.

        Args:
            parent: Родительский виджет
        """
        super().__init__(parent)

        self.users_data = self._get_demo_users()
        self.selected_user: Optional[Dict[str, Any]] = None

        self._create_widgets()
        self._populate_users()

    def _get_demo_users(self) -> List[Dict[str, Any]]:
        """Демо-данные пользователей."""
        return [
            {
                "user_id": "12345",
                "active": True,
                "tests": 15,
                "accuracy": 85,
                "last_seen": "09.04 14:30",
            },
            {
                "user_id": "67890",
                "active": True,
                "tests": 8,
                "accuracy": 72,
                "last_seen": "09.04 13:15",
            },
            {
                "user_id": "11111",
                "active": False,
                "tests": 25,
                "accuracy": 91,
                "last_seen": "08.04 18:45",
            },
            {
                "user_id": "22222",
                "active": True,
                "tests": 3,
                "accuracy": 60,
                "last_seen": "09.04 12:00",
            },
            {
                "user_id": "33333",
                "active": True,
                "tests": 42,
                "accuracy": 88,
                "last_seen": "09.04 14:25",
            },
        ]

    def _create_widgets(self) -> None:
        """Создание виджетов."""
        # Заголовок
        header = ttk.Label(self, text="👥 ПОЛЬЗОВАТЕЛИ", font=("Segoe UI", 14, "bold"))
        header.pack(pady=10)

        # Фильтры
        filters_frame = ttk.Frame(self)
        filters_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(filters_frame, text="Поиск:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filters_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<KeyRelease>", lambda e: self._filter_users())

        self.show_active_var = tk.BooleanVar(value=True)
        active_check = ttk.Checkbutton(
            filters_frame,
            text="Только активные",
            variable=self.show_active_var,
            command=self._filter_users,
        )
        active_check.pack(side=tk.LEFT, padx=10)

        # Таблица пользователей
        table_frame = ttk.LabelFrame(self, text="Список пользователей", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        columns = ("user_id", "status", "tests", "accuracy", "last_seen")
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings", height=15
        )

        # Настройка колонок
        self.tree.heading("user_id", text="ID")
        self.tree.heading("status", text="Статус")
        self.tree.heading("tests", text="Тесты")
        self.tree.heading("accuracy", text="Точность")
        self.tree.heading("last_seen", text="Последний вход")

        self.tree.column("user_id", width=100)
        self.tree.column("status", width=80)
        self.tree.column("tests", width=80)
        self.tree.column("accuracy", width=80)
        self.tree.column("last_seen", width=150)

        # Scrollbars
        v_scroll = ttk.Scrollbar(
            table_frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=v_scroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Привязка выбора
        self.tree.bind("<<TreeviewSelect>>", self._on_user_select)

        # Детали пользователя
        details_frame = ttk.LabelFrame(self, text="Детали пользователя", padding=10)
        details_frame.pack(fill=tk.X, padx=20, pady=10)

        self.user_info_text = tk.Text(
            details_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 10),
            bg="#1e1e1e",
            fg="#ffffff",
            height=8,
        )
        self.user_info_text.pack(fill=tk.BOTH, expand=True)

        # Кнопки действий
        actions_frame = ttk.Frame(self)
        actions_frame.pack(fill=tk.X, padx=20, pady=10)

        details_btn = ttk.Button(
            actions_frame, text="📊 Детали", command=self._show_details
        )
        details_btn.pack(side=tk.LEFT, padx=5)

        block_btn = ttk.Button(
            actions_frame, text="🚫 Блокировать", command=self._block_user
        )
        block_btn.pack(side=tk.LEFT, padx=5)

        message_btn = ttk.Button(
            actions_frame, text="✉️ Сообщение", command=self._send_message
        )
        message_btn.pack(side=tk.LEFT, padx=5)

        export_btn = ttk.Button(
            actions_frame, text="📤 Экспорт", command=self._export_users
        )
        export_btn.pack(side=tk.RIGHT, padx=5)

        refresh_btn = ttk.Button(
            actions_frame, text="🔄 Обновить", command=self._refresh_users
        )
        refresh_btn.pack(side=tk.RIGHT, padx=5)

    def _populate_users(self) -> None:
        """Заполнение списка пользователей."""
        # Очистка
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Добавление
        for user in self.users_data:
            status = "✅" if user["active"] else "❌"
            self.tree.insert(
                "",
                tk.END,
                values=[
                    user["user_id"],
                    status,
                    user["tests"],
                    f"{user['accuracy']}%",
                    user["last_seen"],
                ],
            )

    def _filter_users(self) -> None:
        """Фильтрация пользователей."""
        search_term = self.search_var.get().lower()
        show_active = self.show_active_var.get()

        # Очистка
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Фильтрация
        for user in self.users_data:
            # Фильтр по активности
            if show_active and not user["active"]:
                continue

            # Поиск по ID
            if search_term and search_term not in user["user_id"]:
                continue

            status = "✅" if user["active"] else "❌"
            self.tree.insert(
                "",
                tk.END,
                values=[
                    user["user_id"],
                    status,
                    user["tests"],
                    f"{user['accuracy']}%",
                    user["last_seen"],
                ],
            )

    def _on_user_select(self, event: tk.Event) -> None:
        """Выбор пользователя."""
        selection = self.tree.selection()

        if not selection:
            return

        item = self.tree.item(selection[0])
        user_id = item["values"][0]

        # Поиск пользователя
        for user in self.users_data:
            if user["user_id"] == str(user_id):
                self.selected_user = user
                break

        # Отображение информации
        if self.selected_user:
            info = (
                f"ID пользователя: {self.selected_user['user_id']}\n"
                f"Статус: {'Активен' if self.selected_user['active'] else 'Заблокирован'}\n"
                f"Пройдено тестов: {self.selected_user['tests']}\n"
                f"Точность: {self.selected_user['accuracy']}%\n"
                f"Последний вход: {self.selected_user['last_seen']}\n"
            )
            self.user_info_text.delete(1.0, tk.END)
            self.user_info_text.insert(tk.END, info)

    def _show_details(self) -> None:
        """Показ деталей."""
        if not self.selected_user:
            messagebox.showwarning("Предупреждение", "Выберите пользователя из списка")
            return

        # В реальной версии — загрузка полной статистики
        messagebox.showinfo(
            "Детали",
            f"Пользователь {self.selected_user['user_id']}\n\n"
            f"Тестов: {self.selected_user['tests']}\n"
            f"Точность: {self.selected_user['accuracy']}%\n"
            f"Статус: {'Активен' if self.selected_user['active'] else 'Заблокирован'}",
        )

    def _block_user(self) -> None:
        """Блокировка пользователя."""
        if not self.selected_user:
            messagebox.showwarning("Предупреждение", "Выберите пользователя из списка")
            return

        action = "заблокировать" if self.selected_user["active"] else "разблокировать"

        if messagebox.askyesno(
            "Подтверждение",
            f"Вы уверены, что хотите {action} пользователя {self.selected_user['user_id']}?",
        ):
            self.selected_user["active"] = not self.selected_user["active"]
            self._populate_users()
            self._filter_users()

            messagebox.showinfo("Успешно", f"Пользователь {action}ён")

    def _send_message(self) -> None:
        """Отправка сообщения."""
        if not self.selected_user:
            messagebox.showwarning("Предупреждение", "Выберите пользователя из списка")
            return

        dialog = tk.Toplevel(self)
        dialog.title(f"Сообщение пользователю {self.selected_user['user_id']}")
        dialog.geometry("400x200")

        ttk.Label(dialog, text="Текст сообщения:").pack(pady=10)

        message_text = tk.Text(dialog, height=5, width=50)
        message_text.pack(pady=10)

        def send():
            message = message_text.get("1.0", tk.END).strip()
            if message:
                messagebox.showinfo(
                    "Отправлено",
                    f"Сообщение отправлено пользователю {self.selected_user['user_id']}",
                )
                dialog.destroy()
            else:
                messagebox.showwarning("Предупреждение", "Введите текст сообщения")

        ttk.Button(dialog, text="Отправить", command=send).pack(pady=10)

    def _export_users(self) -> None:
        """Экспорт пользователей."""
        import csv
        from datetime import datetime
        from tkinter import filedialog

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )

        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["user_id", "active", "tests", "accuracy", "last_seen"],
                )
                writer.writeheader()
                writer.writerows(self.users_data)

            messagebox.showinfo(
                "Экспорт", f"Экспортировано {len(self.users_data)} пользователей"
            )

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка экспорта: {str(e)}")

    def _refresh_users(self) -> None:
        """Обновление списка."""
        self._populate_users()
        self._filter_users()
