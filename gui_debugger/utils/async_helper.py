# -*- coding: utf-8 -*-
"""
Помощник для работы с asyncio в GUI.

Позволяет запускать асинхронные функции без блокировки GUI.
"""

import asyncio
from typing import Any


class AsyncHelper:
    """Помощник для запуска asyncio функций в GUI."""
    
    def __init__(self) -> None:
        """Инициализация помощника."""
        pass
    
    def run_async(self, coro: Any) -> Any:
        """
        Запуск асинхронной функции.
        
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
    
    def run_async_callback(self, func: Any, *args: Any, **kwargs: Any) -> None:
        """
        Запуск асинхронной функции с callback (fire and forget).
        
        Args:
            func: Асинхронная функция для вызова
            args: Позиционные аргументы
            kwargs: Именованные аргументы
        """
        import threading
        
        def run():
            try:
                asyncio.run(func(*args, **kwargs))
            except Exception as e:
                print(f"Async callback error: {e}")
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
    
    def stop(self) -> None:
        """Остановка (nop для нового подхода)."""
        pass


# Глобальный экземпляр
async_helper = AsyncHelper()
