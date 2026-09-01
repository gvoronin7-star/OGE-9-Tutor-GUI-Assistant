# -*- coding: utf-8 -*-
"""
Экспорт офлайн-поисковой базы (Фаза 2) в mobile/assets/data/chunks.json.

Переэмбеддинг чанков реальной базы ФИПИ через rubert-tiny2 (тот же
эмбеддер, что и офлайн-запрос на устройстве - см.
scripts/export_mobile_embedding_model.py) - векторы из
RAG_data_base/vector_db/ построены OpenAI text-embedding-3-small,
несовместимы по пространству (см. предупреждение в CLAUDE.md уровня
пары проектов).

Не переносит `metadata.source` (локальный путь на диске владельца) и
служебные поля (context/timestamp/chunk_type/char_count/word_count/
intent) - только то, что нужно для отображения и поиска на устройстве.

Требует: pip install sentence-transformers (уже есть в requirements.txt
для десктопной части).

Запуск:
    python scripts/export_mobile_chunks.py
"""

import json
from pathlib import Path

from sentence_transformers import SentenceTransformer

MODEL_NAME = "cointegrated/rubert-tiny2"
REPO_ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = REPO_ROOT / "RAG_data_base" / "vector_db" / "dataset.json"
OUTPUT_PATH = REPO_ROOT / "mobile" / "assets" / "data" / "chunks.json"


def main() -> None:
    chunks = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    model = SentenceTransformer(MODEL_NAME)

    texts = [c["text"] for c in chunks]
    vectors = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

    output = []
    for chunk, vector in zip(chunks, vectors):
        metadata = chunk.get("metadata", {})
        output.append(
            {
                "id": metadata.get("chunk_id"),
                "text": chunk["text"],
                "summary": metadata.get("summary"),
                "keywords": metadata.get("keywords", []),
                "page": metadata.get("page_number"),
                "vector": vector.tolist(),
            }
        )

    OUTPUT_PATH.write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    dim = len(output[0]["vector"]) if output else 0
    size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(
        f"Написано {len(output)} чанков (dim={dim}) -> {OUTPUT_PATH} "
        f"({size_kb:.0f} КБ)"
    )


if __name__ == "__main__":
    main()
