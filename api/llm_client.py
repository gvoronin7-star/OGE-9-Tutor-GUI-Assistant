# -*- coding: utf-8 -*-
"""
Клиент для работы с LLM через ProxyAPI.

Интеграция с GigaChat-Max и Yandex GPT Lite.

Автор: KODA
Дата: Март 2026
"""

import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

import aiohttp

from utils.advanced_logger import detailed_logger, logger_llm
from utils.cache import CacheManager

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Клиент для работы с LLM через ProxyAPI.

    Поддерживает основную модель GigaChat-Max и резервную Yandex GPT Lite.

    Attributes:
        cache_manager: Менеджер кэширования
        api_url: URL ProxyAPI
        api_key: API-ключ
        primary_model: Основная модель
        fallback_model: Резервная модель
    """

    def __init__(self, cache_manager: CacheManager) -> None:
        """
        Инициализация LLM-клиента.

        Args:
            cache_manager: Менеджер кэширования
        """
        self.cache_manager = cache_manager
        self.api_url = os.getenv("PROXY_API_URL", "https://api.proxyapi.ru/openai/v1")
        self.api_key = os.getenv("PROXY_API_KEY", "")
        self.primary_model = "gpt-4o-mini"
        self.fallback_model = "gpt-4o-mini"

        self.session: Optional[aiohttp.ClientSession] = None
        self.initialized = False

    async def initialize(self) -> None:
        """
        Инициализация ( теперь создаём сессию при каждом запросе).
        """
        # Сессия создаётся при каждом запросе, поэтому здесь ничего не делаем
        self.initialized = True
        logger.info("LLM-клиент инициализирован (GPT-4o-mini через ProxyAPI)")

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
        query: Optional[str] = None,
    ) -> str:
        """
        Генерация текста через LLM.

        Args:
            prompt: Промпт для модели (обычно включает системную
                инструкцию и контекст из базы знаний, не только сам
                вопрос)
            model: Название модели (если None - используется основная)
            max_tokens: Максимальное количество токенов
            temperature: Температура генерации
            query: Собственно вопрос/тема пользователя, без системной
                инструкции и контекста — используется демо-фолбэком
                для подбора ответа по ключевым словам. Если не задан,
                фолбэк ищет ключевые слова во всём `prompt`, включая
                системную инструкцию и контекст, что может привести
                к ложному совпадению (см. decisions/
                2026-09-01_content-quality-review.md, находка 2).

        Returns:
            str: Сгенерированный текст
        """
        request_start = time.time()

        if not self.api_key:
            logger_llm.warning("PROXY_API_KEY не установлен. Возвращаю демо-ответ.")
            return self._generate_fallback(query or prompt)

        current_model = model or self.primary_model

        try:
            logger_llm.info(f"Запрос к {current_model}, prompt length={len(prompt)}")

            result = await self._call_api(
                model=current_model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            duration = (time.time() - request_start) * 1000
            logger_llm.info(
                f"Ответ получен, длина={len(result)}, время={duration:.2f}ms"
            )

            # Логирование успешного запроса
            detailed_logger.log_request(
                component="llm",
                action="generate",
                input_data={
                    "model": current_model,
                    "prompt_length": len(prompt),
                    "max_tokens": max_tokens,
                },
                output_data={
                    "response_length": len(result),
                    "truncated_response": result[:100],
                },
                duration_ms=duration,
                status="success",
            )

            return result

        except Exception as e:
            duration = (time.time() - request_start) * 1000
            logger_llm.warning(f"Ошибка генерации через {current_model}: {e}")

            # Логирование ошибки
            detailed_logger.log_request(
                component="llm",
                action="generate",
                input_data={"model": current_model, "prompt_length": len(prompt)},
                output_data=None,
                duration_ms=duration,
                status="error",
                error_message=str(e),
            )

            # Попытка использовать резервную модель
            if current_model != self.fallback_model:
                try:
                    logger_llm.info(f"Попытка резервной модели {self.fallback_model}")
                    result = await self._call_api(
                        model=self.fallback_model,
                        prompt=prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                    logger_llm.info(f"Резервная модель ответила")
                    return result
                except Exception as e2:
                    logger_llm.error(f"Ошибка резервной модели: {e2}")

            # Возврат к демо-ответу
            return self._generate_fallback(query or prompt)

    async def _call_api(
        self, model: str, prompt: str, max_tokens: int, temperature: float
    ) -> str:
        """
        Вызов API для генерации текста.

        Args:
            model: Название модели
            prompt: Промпт
            max_tokens: Максимальное количество токенов
            temperature: Температура генерации

        Returns:
            str: Сгенерированный текст
        """
        request_start = time.time()

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        logger_llm.debug(f"Запрос к {model}: {prompt[:100]}...")

        # Создаём новую сессию для каждого запроса
        async with aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        ) as session:
            try:
                async with session.post(
                    f"{self.api_url}/chat/completions",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    duration = (time.time() - request_start) * 1000

                    if response.status != 200:
                        error_msg = f"API вернул статус {response.status}"
                        logger_llm.error(error_msg)

                        detailed_logger.log_request(
                            component="llm",
                            action="api_call",
                            input_data={"model": model, "prompt_len": len(prompt)},
                            output_data=None,
                            duration_ms=duration,
                            status="error",
                            error_message=error_msg,
                        )

                        raise Exception(error_msg)

                    data = await response.json()

                    # Парсинг ответа (формат может отличаться)
                    content = ""
                    if "choices" in data and len(data["choices"]) > 0:
                        content = data["choices"][0]["message"]["content"]
                    elif "result" in data:
                        content = data["result"]
                    else:
                        error_msg = "Неизвестный формат ответа API"
                        logger_llm.error(error_msg)
                        raise Exception(error_msg)

                    # Очистка от markdown блоков ```json ... ```
                    content = content.strip()
                    if content.startswith("```json"):
                        content = content[7:]
                    if content.startswith("```"):
                        content = content[3:]
                    if content.endswith("```"):
                        content = content[:-3]

                    content = content.strip()

                    logger_llm.info(
                        f"Ответ от {model} за {duration:.2f}ms, длина={len(content)}"
                    )

                    # Успешное логирование
                    detailed_logger.log_request(
                        component="llm",
                        action="api_call",
                        input_data={"model": model, "prompt_len": len(prompt)},
                        output_data={"response_len": len(content)},
                        duration_ms=duration,
                        status="success",
                    )

                    return content

            except aiohttp.ClientError as e:
                duration = (time.time() - request_start) * 1000
                error_msg = f"Network error: {e}"
                logger_llm.error(error_msg)

                detailed_logger.log_request(
                    component="llm",
                    action="api_call",
                    input_data={"model": model},
                    output_data=None,
                    duration_ms=duration,
                    status="error",
                    error_message=str(e),
                )

                raise Exception(error_msg)

    async def generate_questions(
        self, topic: str, difficulty: str, num_questions: int, context: str
    ) -> Dict[str, Any]:
        """
        Генерация вопросов для теста.

        Args:
            topic: Тема теста
            difficulty: Сложность
            num_questions: Количество вопросов
            context: Контекст из базы знаний

        Returns:
            Dict[str, Any]: Словарь вопросов
        """
        request_start = time.time()
        logger_llm.info(
            f"Генерация вопросов: тема={topic}, сложность={difficulty}, количество={num_questions}"
        )

        # Формирование промпта для генерации вопросов
        prompt = f"""На основе следующего материала составь {num_questions} вопросов для ОГЭ по обществознанию на тему "{topic}".

Уровень сложности: {difficulty}
- easy: простые вопросы на знание фактов (определения, названия)
- medium: вопросы на понимание и применение (классификации, сравнения)
- hard: вопросы на анализ и оценку (причинно-следственные связи, прогнозы)

Контекст:
{context}

Формат ответа (JSON):
{{
    "questions": [
        {{
            "question": "Текст вопроса",
            "answers": ["Вариант А", "Вариант Б", "Вариант В", "Вариант Г"],
            "correct_answer": 0,
            "explanation": "Краткое пояснение",
            "difficulty": "{difficulty}"
        }}
    ]
}}

Ответь только JSON, без дополнительного текста:"""

        try:
            # Генерация через LLM
            response = await self.generate(
                prompt=prompt, max_tokens=2000, temperature=0.5, query=topic
            )

            duration = (time.time() - request_start) * 1000

            if not response or not response.strip():
                logger_llm.warning("LLM вернул пустой ответ")
                detailed_logger.log_request(
                    component="llm",
                    action="generate_questions",
                    input_data={"topic": topic, "num_questions": num_questions},
                    output_data=None,
                    duration_ms=duration,
                    status="error",
                    error_message="Пустой ответ от LLM",
                )
                return {}

            # Парсинг JSON
            try:
                questions_data = json.loads(response)
            except json.JSONDecodeError as e:
                logger_llm.warning(
                    f"Не удалось распарсить JSON: {e}, ответ: {response[:200]}"
                )
                detailed_logger.log_request(
                    component="llm",
                    action="generate_questions",
                    input_data={"topic": topic, "num_questions": num_questions},
                    output_data={"raw_response": response[:200]},
                    duration_ms=duration,
                    status="error",
                    error_message=f"JSON parse error: {e}",
                )
                return {}

            questions = questions_data.get("questions", [])

            # Добавляем difficulty в каждый вопрос
            for q in questions:
                q["difficulty"] = difficulty

            # Форматирование в словарь
            questions_dict = {}
            for i, q in enumerate(questions):
                questions_dict[f"q_{i}"] = q

            logger_llm.info(
                f"Сгенерировано {len(questions)} вопросов за {duration:.2f}ms"
            )

            # Логирование успешной генерации
            detailed_logger.log_request(
                component="llm",
                action="generate_questions",
                input_data={"topic": topic, "num_questions": num_questions},
                output_data={"questions_count": len(questions)},
                duration_ms=duration,
                status="success",
            )

            return questions_dict

        except Exception as e:
            duration = (time.time() - request_start) * 1000
            logger_llm.error(f"Ошибка генерации вопросов: {e}")

            detailed_logger.log_request(
                component="llm",
                action="generate_questions",
                input_data={"topic": topic, "num_questions": num_questions},
                output_data=None,
                duration_ms=duration,
                status="error",
                error_message=str(e),
            )

            # Возврат пустого словаря - будет использован демо-контент
            return {}

    def _generate_fallback(self, text: str) -> str:
        """
        Генерация демо-ответа без API.

        Args:
            text: Вопрос/тема пользователя, по которой подбирается
                демо-ответ через поиск ключевых слов — не весь промпт
                целиком (иначе системная инструкция и контекст могут
                дать ложное совпадение раньше настоящей темы вопроса)

        Returns:
            str: Демо-ответ
        """
        # Простой демо-ответ на основе ключевых слов
        prompt_lower = text.lower()

        if "экономика" in prompt_lower or "деньги" in prompt_lower:
            return (
                "Я нашёл информацию по этому вопросу в базе знаний. "
                "Экономика изучает производство, распределение и потребление товаров и услуг. "
                "Деньги выполняют функции: меры стоимости, средства платежа и средства накопления. "
                "Для более подробного ответа мне нужно подключить LLM."
            )
        elif "право" in prompt_lower or "закон" in prompt_lower:
            return (
                "Право — это система обязательных правил поведения, установленных государством. "
                "Основные источники права в России: Конституция, законы, подзаконные акты. "
                "Конституция РФ — главный закон страны, принятый в 1993 году. "
                "Для более подробного ответа мне нужно подключить LLM."
            )
        elif (
            "политик" in prompt_lower
            or "власт" in prompt_lower
            or "парти" in prompt_lower
        ):
            return (
                "Политика — это деятельность, связанная с управлением государством и "
                "обществом, борьбой за власть и её осуществлением. Государство — основной "
                "институт политической системы, обладающий суверенитетом. Политический "
                "режим может быть демократическим, авторитарным или тоталитарным. "
                "Политические партии объединяют людей со схожими взглядами для участия "
                "в выборах и влияния на власть. Для более подробного ответа мне нужно "
                "подключить LLM."
            )
        elif "социальн" in prompt_lower or "мобильност" in prompt_lower:
            return (
                "Социальная сфера изучает общественные отношения между разными группами "
                "людей — социальные слои, классы, этносы. Социальный статус — положение "
                "человека в обществе, а социальная роль — ожидаемое поведение, связанное "
                "с этим статусом. Социальная мобильность — переход человека из одной "
                "социальной группы в другую. Семья — важнейший социальный институт, "
                "выполняющий репродуктивную, воспитательную и хозяйственную функции. "
                "Для более подробного ответа мне нужно подключить LLM."
            )
        elif (
            "культур" in prompt_lower
            or "искусств" in prompt_lower
            or "религи" in prompt_lower
            or "мораль" in prompt_lower
            or "наук" in prompt_lower
        ):
            return (
                "Духовная культура — это область человеческой деятельности, связанная с "
                "созданием и освоением духовных ценностей: наука, образование, искусство, "
                "религия, мораль. Наука стремится к объективному познанию мира, искусство "
                "отражает действительность через художественные образы. Мораль регулирует "
                "поведение людей через понятия добра и зла, а религия основана на вере в "
                "сверхъестественное. Образование обеспечивает передачу знаний и культурных "
                "ценностей между поколениями. Для более подробного ответа мне нужно "
                "подключить LLM."
            )
        elif "общество" in prompt_lower or "человек" in prompt_lower:
            return (
                "Общество — это совокупность людей, объединённых общими интересами, "
                "культурой и социальными связями. Человек — часть природы, но общество "
                "представляет собой результат социальной эволюции. Социальные институты — "
                "это устойчивые формы организации общественной жизни (семья, образование, государство). "
                "Для более подробного ответа мне нужно подключить LLM."
            )
        else:
            return (
                "Я нашёл релевантную информацию в базе знаний. "
                "Попробую ответить на основе имеющихся данных. "
                "Если нужна более подробная информация, уточни свой вопрос. "
                "Для полного ответа мне нужно подключить LLM."
            )

    async def close(self) -> None:
        """Закрытие ( теперь нечего закрывать)."""
        # Сессии создаются и закрываются при каждом запросе
        logger.info("LLM-клиент закрыт")
