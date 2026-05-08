# -*- coding: utf-8 -*-
import json
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

class RAGPipelineLite:
    def __init__(self, cache_manager=None):
        self.cache_manager = cache_manager
        self.metrics = {"total_requests": 0}
        self.chunks = []
        self.keywords_index = {}
    
    async def initialize(self):
        db_path = Path("data/indices/dataset.json")
        if db_path.exists():
            with open(db_path, 'r', encoding='utf-8') as f:
                self.chunks = json.load(f)
            self._build_index()
            logger.info(f"RAG Lite loaded: {len(self.chunks)} chunks")
        else:
            logger.warning("Database not found")
            self._load_demo()
    
    def _build_index(self):
        for i, chunk in enumerate(self.chunks):
            keywords = chunk.get('metadata', {}).get('keywords', [])
            for kw in keywords:
                kw_lower = kw.lower()
                if kw_lower not in self.keywords_index:
                    self.keywords_index[kw_lower] = []
                self.keywords_index[kw_lower].append(i)
    
    def _load_demo(self):
        self.chunks = [
            {"text": "Экономика", "type": "heading"},
            {"text": "Экономика изучает производство", "type": "paragraph"},
        ]
    
    async def get_answer(self, query, user_id):
        start_time = time.time()
        self.metrics["total_requests"] += 1
        
        query_lower = query.lower()
        query_words = query_lower.split()
        
        scores = {}
        for word in query_words:
            if word in self.keywords_index:
                for idx in self.keywords_index[word]:
                    scores[idx] = scores.get(idx, 0) + 1
        
        if not scores:
            return {
                "answer": "Информация не найдена",
                "sources": [],
                "is_cached": False,
                "response_time": time.time() - start_time
            }
        
        top_indices = sorted(scores.items(), key=lambda x: -x[1])[:3]
        results = [self.chunks[idx] for idx, _ in top_indices]
        
        answer_parts = []
        sources = []
        for r in results:
            text = r.get('text', '')
            if text and len(text) > 5:
                answer_parts.append(text)
                sources.append(r.get('metadata', {}).get('source', 'unknown'))
        
        answer = "## Найденная информация:\n\n" + "\n\n".join(answer_parts[:3]) if answer_parts else "Информация не найдена"
        
        return {"answer": answer, "sources": list(set(sources)), "is_cached": False, "response_time": time.time() - start_time}
    
    async def generate_test(self, topic, difficulty="medium", num_questions=5):
        questions = {
            "q_0": {
                "question": "Что такое общество?",
                "answers": ["Совокупность людей", "Группа животных", "Компьютерная сеть", "Государство"],
                "correct_answer": 0,
                "explanation": "Общество - совокупность людей с общими интересами."
            }
        }
        return {"topic": topic, "questions": questions, "total_questions": 1, "current_question": 0}
    
    def get_metrics(self):
        return self.metrics
    
    async def close(self):
        pass
