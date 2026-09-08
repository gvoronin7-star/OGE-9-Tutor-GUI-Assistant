# -*- coding: utf-8 -*-
"""
Тесты для gui_debugger/components/admin/rag_manager.py.

Покрывают только чистые функции проверки структуры новой базы -
_missing_vector_db_files/_vector_db_chunk_count. Раньше эта панель
проверяла структуру chunks/metadata/indices, которую реальный
загрузчик (api/vector_store_existing.py::ExistingVectorStore) не
читает вообще - валидная по чек-листу панели папка не подошла бы
загрузчику, а реальная база (vector_db/dataset.json и т.д.) считалась
"невалидной". Найдено зональным аудитом хаба 2026-09-08 (К-7).

_upload_base_thread сама не тестируется здесь - она завязана на
Tkinter-виджеты через self.after(), нужен запущенный mainloop; ручная
проверка на копии базы описана в decisions/decision-log.md.
"""

import json
from pathlib import Path

from gui_debugger.components.admin.rag_manager import (
    _missing_vector_db_files,
    _vector_db_chunk_count,
)


def _write_valid_vector_db(base: Path, chunks: int = 3) -> None:
    vector_db = base / "vector_db"
    vector_db.mkdir(parents=True)
    (vector_db / "dataset.json").write_text(
        json.dumps([{"text": f"chunk {i}"} for i in range(chunks)]),
        encoding="utf-8",
    )
    (vector_db / "index.faiss").write_bytes(b"\x00")
    (vector_db / "metadata.json").write_text("{}", encoding="utf-8")


class TestMissingVectorDbFiles:
    def test_no_missing_files_for_valid_base(self, tmp_path):
        _write_valid_vector_db(tmp_path)
        assert _missing_vector_db_files(tmp_path) == []

    def test_reports_all_three_when_vector_db_absent(self, tmp_path):
        missing = _missing_vector_db_files(tmp_path)
        assert set(missing) == {"dataset.json", "index.faiss", "metadata.json"}

    def test_reports_only_the_missing_file(self, tmp_path):
        _write_valid_vector_db(tmp_path)
        (tmp_path / "vector_db" / "index.faiss").unlink()
        assert _missing_vector_db_files(tmp_path) == ["index.faiss"]

    def test_old_chunks_metadata_indices_layout_is_rejected(self, tmp_path):
        # Старая структура, которую панель раньше считала валидной -
        # реальный загрузчик её не читает, поэтому она должна остаться
        # "невалидной" и по новой проверке.
        (tmp_path / "chunks").mkdir()
        (tmp_path / "metadata").mkdir()
        (tmp_path / "indices").mkdir()
        assert len(_missing_vector_db_files(tmp_path)) == 3


class TestVectorDbChunkCount:
    def test_counts_chunks_in_dataset_json(self, tmp_path):
        _write_valid_vector_db(tmp_path, chunks=157)
        assert _vector_db_chunk_count(tmp_path) == 157

    def test_none_when_dataset_missing(self, tmp_path):
        assert _vector_db_chunk_count(tmp_path) is None

    def test_none_when_dataset_is_not_valid_json(self, tmp_path):
        vector_db = tmp_path / "vector_db"
        vector_db.mkdir()
        (vector_db / "dataset.json").write_text("not json", encoding="utf-8")
        assert _vector_db_chunk_count(tmp_path) is None
