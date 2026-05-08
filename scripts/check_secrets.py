#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт проверки репозитория на утечки секретов.

Использование:
    python scripts/check_secrets.py

Находит:
- API ключи (sk-...)
- Telegram токены
- Пароли в коде
- Приватные ключи
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple


# Паттерны для поиска секретов
SECRET_PATTERNS = [
    {
        "name": "OpenAI/ProxyAPI API Key",
        "pattern": r"sk-[a-zA-Z0-9]{20,}",
        "severity": "CRITICAL"
    },
    {
        "name": "Telegram Bot Token",
        "pattern": r"[0-9]{8,}:[A-Za-z0-9_-]{30,}",
        "severity": "CRITICAL"
    },
    {
        "name": "Generic API Key",
        "pattern": r"(?i)(api[_-]?key|apikey)\s*[=:]\s*['\"][^'\"]{16,}['\"]",
        "severity": "HIGH"
    },
    {
        "name": "Password in Code",
        "pattern": r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"][^'\"]{8,}['\"]",
        "severity": "HIGH"
    },
    {
        "name": "Private Key",
        "pattern": r"-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----",
        "severity": "CRITICAL"
    },
    {
        "name": "AWS Access Key",
        "pattern": r"AKIA[0-9A-Z]{16}",
        "severity": "CRITICAL"
    },
    {
        "name": "GitHub Token",
        "pattern": r"gh[pousr]_[A-Za-z0-9_]{36,}",
        "severity": "CRITICAL"
    }
]

# Файлы и директории для исключения
EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "htmlcov"
}

EXCLUDE_FILES = {
    ".env",  # .env в gitignore, не проверяем
    ".env.local",
    "check_secrets.py",  # Этот скрипт
}


def is_excluded(path: Path) -> bool:
    """Проверка на исключение."""
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
    
    if path.name in EXCLUDE_FILES:
        return True
    
    return False


def scan_file(filepath: Path) -> List[Tuple[str, str, str]]:
    """
    Сканирование файла на наличие секретов.
    
    Returns:
        List[Tuple[str, str, str]]: (pattern_name, line_number, line_content)
    """
    findings = []
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        for line_num, line in enumerate(lines, 1):
            for pattern_info in SECRET_PATTERNS:
                if re.search(pattern_info["pattern"], line):
                    # Пропускаем плейсхолдеры
                    if any(placeholder in line for placeholder in [
                        "<your_", "<ваш_", "your_", "here", "example",
                        "<замените", "<replace", "REPLACE"
                    ]):
                        continue
                    
                    findings.append((
                        pattern_info["name"],
                        f"{filepath}:{line_num}",
                        line.strip()[:80]
                    ))
    
    except Exception as e:
        print(f"  [SKIP] {filepath}: {e}")
    
    return findings


def scan_directory(root_dir: Path) -> List[Tuple[Path, str, str, str]]:
    """
    Сканирование директории.
    
    Returns:
        List[Tuple[Path, str, str, str]]: (filepath, pattern_name, location, content)
    """
    all_findings = []
    
    # Поиск файлов
    for ext in ["*.py", "*.md", "*.txt", "*.yml", "*.yaml", "*.json", "*.js", "*.ts"]:
        for filepath in root_dir.rglob(ext):
            if is_excluded(filepath):
                continue
            
            findings = scan_file(filepath)
            
            for finding in findings:
                all_findings.append((filepath, *finding))
    
    return all_findings


def print_report(findings: List[Tuple[Path, str, str, str]]) -> None:
    """Вывод отчёта."""
    print("=" * 70)
    print("ОТЧЁТ ПРОВЕРКИ НА УТЕЧКИ СЕКРЕТОВ")
    print("=" * 70)
    print()
    
    if not findings:
        print("[OK] Утечки секретов не найдены!")
        print()
        return
    
    # Группировка по критичности
    critical = [f for f in findings if "CRITICAL" in str(f)]
    high = [f for f in findings if "HIGH" in str(f) and f not in critical]
    other = [f for f in findings if f not in critical and f not in high]
    
    print(f"Найдено утечек: {len(findings)}")
    print(f"  - CRITICAL: {len(critical)}")
    print(f"  - HIGH: {len(high)}")
    print(f"  - OTHER: {len(other)}")
    print()
    
    if critical:
        print("-" * 70)
        print("CRITICAL УТЕЧКИ (требуют немедленного устранения):")
        print("-" * 70)
        for filepath, name, location, content in critical:
            print(f"\n[{name}]")
            print(f"  Файл: {location}")
            print(f"  Содержимое: {content}")
    
    if high:
        print("\n" + "-" * 70)
        print("HIGH УТЕЧКИ (рекомендуется устранить):")
        print("-" * 70)
        for filepath, name, location, content in high:
            print(f"\n[{name}]")
            print(f"  Файл: {location}")
            print(f"  Содержимое: {content}")
    
    if other:
        print("\n" + "-" * 70)
        print("OTHER (проверить вручную):")
        print("-" * 70)
        for filepath, name, location, content in other:
            print(f"\n[{name}]")
            print(f"  Файл: {location}")
            print(f"  Содержимое: {content}")
    
    print()
    print("=" * 70)
    print("РЕКОМЕНДАЦИИ:")
    print("=" * 70)
    print("1. Немедленно смените скомпрометированные токены")
    print("2. Удалите секреты из файлов")
    print("3. Используйте .env для хранения секретов")
    print("4. Добавьте .env в .gitignore")
    print("5. Настройте pre-commit hooks для проверки")
    print()


def main() -> int:
    """Главная функция."""
    root_dir = Path(__file__).parent.parent
    
    print(f"Сканирование: {root_dir}")
    print()
    
    findings = scan_directory(root_dir)
    print_report(findings)
    
    # Возвращаем код ошибки если найдены CRITICAL
    critical_count = sum(1 for f in findings if "CRITICAL" in str(f))
    
    if critical_count > 0:
        print(f"[FAIL] Найдено {critical_count} CRITICAL утечек!")
        return 1
    else:
        print("[PASS] Проверка пройдена")
        return 0


if __name__ == "__main__":
    sys.exit(main())