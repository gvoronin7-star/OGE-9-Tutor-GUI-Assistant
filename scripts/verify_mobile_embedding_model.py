# -*- coding: utf-8 -*-
"""
Проверка экспорта из export_mobile_embedding_model.py.

1. Сверяет эмбеддинги из квантизованного ONNX (CLS-пулинг + L2-норм,
   вручную) с sentence_transformers.encode() на тех же предложениях -
   должны совпадать с точностью до шума от int8-квантизации.
2. Пишет fixture для Dart-тестов (tokenizer + итоговые векторы) -
   mobile/test/fixtures/embedding_reference.json.

Запуск:
    python scripts/verify_mobile_embedding_model.py
"""

import json
from pathlib import Path

import numpy as np
import onnxruntime as ort
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer

MODEL_NAME = "cointegrated/rubert-tiny2"
REPO_ROOT = Path(__file__).resolve().parent.parent
ONNX_PATH = REPO_ROOT / "mobile" / "assets" / "models" / "rubert_tiny2.int8.onnx"
FIXTURE_PATH = REPO_ROOT / "mobile" / "test" / "fixtures" / "embedding_reference.json"

TEST_SENTENCES = [
    "Что такое общество?",
    "Экономика изучает производство и потребление товаров.",
    "Конституция РФ — главный закон страны.",
    "Демократия предполагает свободные выборы.",
]


def cls_pool_and_normalize(last_hidden_state: np.ndarray) -> np.ndarray:
    cls = last_hidden_state[:, 0, :]
    norm = np.linalg.norm(cls, axis=1, keepdims=True)
    return cls / norm


def main() -> None:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    reference_model = SentenceTransformer(MODEL_NAME)
    session = ort.InferenceSession(str(ONNX_PATH))

    fixtures = []
    max_cosine_diff = 0.0

    for sentence in TEST_SENTENCES:
        encoded = tokenizer(sentence, return_tensors="np")

        onnx_output = session.run(
            ["last_hidden_state"],
            {
                "input_ids": encoded["input_ids"].astype(np.int64),
                "attention_mask": encoded["attention_mask"].astype(np.int64),
                "token_type_ids": encoded["token_type_ids"].astype(np.int64),
            },
        )[0]
        onnx_vector = cls_pool_and_normalize(onnx_output)[0]

        reference_vector = reference_model.encode(sentence)

        cosine = float(
            np.dot(onnx_vector, reference_vector)
            / (np.linalg.norm(onnx_vector) * np.linalg.norm(reference_vector))
        )
        max_cosine_diff = max(max_cosine_diff, 1 - cosine)
        print(f"cosine(onnx_int8, sentence_transformers) = {cosine:.5f}  | {sentence!r}")

        fixtures.append(
            {
                "text": sentence,
                "input_ids": encoded["input_ids"][0].tolist(),
                "token_type_ids": encoded["token_type_ids"][0].tolist(),
                "attention_mask": encoded["attention_mask"][0].tolist(),
                "expected_vector": reference_vector.tolist(),
            }
        )

    FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE_PATH.write_text(
        json.dumps(fixtures, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nFixture -> {FIXTURE_PATH}")

    if max_cosine_diff > 0.01:
        raise SystemExit(
            f"Расхождение между ONNX(int8) и sentence_transformers слишком "
            f"большое: 1-cosine={max_cosine_diff:.5f} (порог 0.01)"
        )
    print(f"OK: максимальное расхождение 1-cosine = {max_cosine_diff:.5f}")


if __name__ == "__main__":
    main()
