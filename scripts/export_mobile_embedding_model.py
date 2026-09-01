# -*- coding: utf-8 -*-
"""
Экспорт rubert-tiny2 в ONNX для офлайн-инференса на устройстве (Фаза 2).

Одноразовый инструмент, не зависимость приложения - требует пакеты,
которых нет в requirements.txt (не нужны для запуска самого сервиса):

    pip install torch transformers onnx onnxruntime

Пулинг этой модели - **[CLS]-токен**, не усреднение по токенам
(проверено по 1_Pooling/config.json в кэше HuggingFace:
pooling_mode_cls_token=true, pooling_mode_mean_tokens=false) - ONNX
экспортирует полный last_hidden_state, а взятие нулевого токена и
L2-нормализация делаются уже в Dart (mobile/lib/data/embeddings/), а
не внутри графа. Черновое предположение «усреднение, 768 измерений» из более ранней
версии плана было неверным по обоим пунктам - реальная размерность
312, пулинг по CLS-токену.

Запуск:
    python scripts/export_mobile_embedding_model.py
"""

import json
from pathlib import Path

import torch
from onnxruntime.quantization import QuantType, quantize_dynamic
from transformers import AutoModel, AutoTokenizer

MODEL_NAME = "cointegrated/rubert-tiny2"
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "mobile" / "assets" / "models"


class _EncoderOnly(torch.nn.Module):
    """Тонкая обёртка: фиксирует use_cache=False именованным аргументом,
    чтобы обойти конфликт позиционных/именованных аргументов между
    torch.onnx TorchScript-трассировщиком и BertModel.forward() в этой
    версии transformers."""

    def __init__(self, base_model: torch.nn.Module) -> None:
        super().__init__()
        self.base_model = base_model

    def forward(self, input_ids, attention_mask, token_type_ids):
        output = self.base_model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            use_cache=False,
        )
        return output.last_hidden_state


def export_onnx() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = _EncoderOnly(AutoModel.from_pretrained(MODEL_NAME))
    model.eval()

    sample = tokenizer("Пример текста для трассировки графа", return_tensors="pt")

    onnx_path = OUTPUT_DIR / "rubert_tiny2.onnx"
    torch.onnx.export(
        model,
        (sample["input_ids"], sample["attention_mask"], sample["token_type_ids"]),
        str(onnx_path),
        input_names=["input_ids", "attention_mask", "token_type_ids"],
        output_names=["last_hidden_state"],
        dynamic_axes={
            "input_ids": {0: "batch", 1: "sequence"},
            "attention_mask": {0: "batch", 1: "sequence"},
            "token_type_ids": {0: "batch", 1: "sequence"},
            "last_hidden_state": {0: "batch", 1: "sequence"},
        },
        opset_version=14,
        dynamo=False,
    )
    fp32_size = onnx_path.stat().st_size / 1_000_000
    print(f"ONNX-модель (fp32) -> {onnx_path} ({fp32_size:.1f} МБ)")

    # 117 МБ у fp32-версии - это не "лишний вес" экспорта, а сама модель
    # (embedding-таблица 83828 токенов x 312 измерений ~= 105 МБ, при том
    # же размере, что исходный model.safetensors). "~45 МБ" из черновой
    # версии плана было неверной оценкой, не сверенной с реальным файлом.
    # Динамическая int8-квантизация возвращает размер в район исходной
    # оценки без переобучения - веса эмбеддингов и линейных слоёв
    # округляются до int8, активации остаются float.
    quantized_path = OUTPUT_DIR / "rubert_tiny2.int8.onnx"
    quantize_dynamic(
        str(onnx_path),
        str(quantized_path),
        weight_type=QuantType.QInt8,
    )
    quantized_size = quantized_path.stat().st_size / 1_000_000
    print(f"ONNX-модель (int8) -> {quantized_path} ({quantized_size:.1f} МБ)")

    onnx_path.unlink()  # только квантизованная версия идёт в assets

    # vocab.txt (WordPiece) - для собственного BERT-токенизатора на Dart,
    # т.к. общего пакета токенизации HuggingFace-моделей для Flutter нет.
    vocab_src = Path(tokenizer.vocab_file)
    vocab_dst = OUTPUT_DIR / "vocab.txt"
    vocab_dst.write_text(vocab_src.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"vocab.txt -> {vocab_dst} ({len(tokenizer.get_vocab())} токенов)")

    tokenizer_meta = {
        "do_lower_case": tokenizer.do_lower_case,
        "cls_token": tokenizer.cls_token,
        "sep_token": tokenizer.sep_token,
        "pad_token": tokenizer.pad_token,
        "unk_token": tokenizer.unk_token,
        "model_max_length": 256,  # чанки короткие; реальный лимит модели 2048
    }
    meta_path = OUTPUT_DIR / "tokenizer_config.json"
    meta_path.write_text(
        json.dumps(tokenizer_meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"tokenizer_config.json -> {meta_path}")


if __name__ == "__main__":
    export_onnx()
