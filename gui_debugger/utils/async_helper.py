# -*- coding: utf-8 -*-
"""
Помощник для работы с asyncio в GUI.

Позволяет запускать асинхронные функции без блокировки GUI.
"""

import asyncio
import threading
import tkinter as tk
from typing import Any, Callable, Optional


class AsyncHelper:
    """Помощник для запуска asyncio функций в GUI."""

    def __init__(self) -> None:
        """Инициализация помощника."""
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None

    def _get_or_create_loop(self) -> asyncio.AbstractEventLoop:
        """
        Получение постоянного event loop, работающего в фоновом потоке.

        Loop создаётся один раз и живёт всё время работы приложения —
        это позволяет отправлять в него корутины без блокировки GUI.
        """
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            self._loop_thread = threading.Thread(
                target=self._loop.run_forever, daemon=True
            )
            self._loop_thread.start()

        return self._loop

    def run_async(self, coro: Any) -> Any:
        """
        Запуск асинхронной функции.

        Блокирует вызывающий поток до получения результата — использовать
        только вне главного потока Tk (например, в отдельном потоке).
        Для запуска из обработчика виджета используйте
        run_async_in_background().

        Args:
            coro: Асинхронная корутина

        Returns:
            Результат выполнения
        """
        try:
            # Создаём новый event loop для каждого вызова
            return asyncio.run(coro)
        except RuntimeError as e:
            if "Event loop is closed" in str(e) or "no running event loop" in str(e):
                # Fallback: создаём новый loop вручную
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(coro)
                finally:
                    loop.close()
            raise

    def run_async_in_background(
        self,
        widget: tk.Misc,
        coro: Any,
        on_success: Callable[[Any], None],
        on_error: Callable[[BaseException], None],
        poll_interval_ms: int = 50,
    ) -> None:
        """
        Запуск корутины в фоновом event loop без блокировки GUI.

        Корутина выполняется в отдельном потоке с постоянным event loop.
        Готовность результата проверяется периодическим опросом через
        `widget.after(...)`, поэтому on_success/on_error вызываются на
        главном потоке Tk — внутри них безопасно обращаться к виджетам.

        Args:
            widget: Виджет, через который планируется опрос (`.after()`)
            coro: Асинхронная корутина для выполнения
            on_success: Вызывается с результатом корутины при успехе
            on_error: Вызывается с исключением при ошибке
            poll_interval_ms: Интервал опроса готовности результата
        """
        loop = self._get_or_create_loop()
        future = asyncio.run_coroutine_threadsafe(coro, loop)

        def _poll() -> None:
            # Виджет мог быть уничтожен (пользователь ушёл с экрана) пока
            # корутина ещё выполнялась — не планируем следующий опрос и не
            # вызываем on_success/on_error, иначе получим
            # _tkinter.TclError: invalid command name на уничтоженных
            # дочерних виджетах.
            if not widget.winfo_exists():
                return

            if not future.done():
                widget.after(poll_interval_ms, _poll)
                return

            try:
                result = future.result()
            except BaseException as e:  # noqa: BLE001 - пробрасываем в on_error
                on_error(e)
            else:
                on_success(result)

        widget.after(poll_interval_ms, _poll)

    def stop(self) -> None:
        """Остановка фонового event loop (если был создан)."""
        if self._loop is not None and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(self._loop.stop)


# Глобальный экземпляр
async_helper = AsyncHelper()
