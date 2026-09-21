"""Intent classification using hybrid Machine Learning and rule-based heuristics."""

import os
import re
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

from .intent_types import IntentType, RiskLevel, INTENT_RISK_MAP, IntentResult
from .training_corpus import TRAINING_DATA
from .entity_extractor import EntityExtractor
from ..config import MODEL_CACHE_FILE


class IntentClassifier:
    """Hybrid intent classifier combining scikit-learn TF-IDF with rule heuristics."""

    def __init__(self, force_retrain: bool = False):
        self.pipeline: Optional[Pipeline] = None
        self._load_or_train(force_retrain)

    def _load_or_train(self, force_retrain: bool = False) -> None:
        """Loads cached model or trains a new one from TRAINING_DATA."""
        if not force_retrain and MODEL_CACHE_FILE.exists():
            try:
                self.pipeline = joblib.load(MODEL_CACHE_FILE)
                return
            except Exception:
                pass

        self._train()

    def _train(self) -> None:
        """Trains TF-IDF + Multinomial Naive Bayes model."""
        texts = [item[0] for item in TRAINING_DATA]
        labels = [item[1].value for item in TRAINING_DATA]

        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 3), lowercase=True, max_features=1500)),
            ("clf", MultinomialNB(alpha=0.1))
        ])
        self.pipeline.fit(texts, labels)

        # Cache the trained pipeline
        try:
            MODEL_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(self.pipeline, MODEL_CACHE_FILE)
        except Exception:
            pass

    def classify(self, text: str) -> IntentResult:
        """Classifies the natural language text into an IntentResult."""
        raw_text = text.strip()
        lower_text = raw_text.lower()

        if not lower_text:
            return IntentResult(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                entities={},
                raw_text=raw_text,
                risk_level=RiskLevel.READ_ONLY
            )

        # Step 1: High-precision rule / keyword pre-checks
        rule_intent = self._rule_based_check(lower_text)
        entities = EntityExtractor.extract(raw_text)

        if rule_intent:
            risk = INTENT_RISK_MAP.get(rule_intent, RiskLevel.READ_ONLY)
            return IntentResult(
                intent=rule_intent,
                confidence=1.0,
                entities=entities,
                raw_text=raw_text,
                risk_level=risk
            )

        # Step 2: Machine Learning Classification
        predicted_intent_str = IntentType.UNKNOWN.value
        confidence = 0.0

        if self.pipeline:
            try:
                probs = self.pipeline.predict_proba([lower_text])[0]
                classes = self.pipeline.classes_
                best_idx = probs.argmax()
                confidence = float(probs[best_idx])
                predicted_intent_str = classes[best_idx]
            except Exception:
                pass

        # If confidence is below threshold, fallback to heuristic or unknown
        if confidence < 0.25:
            fallback = self._fuzzy_fallback(lower_text)
            if fallback:
                predicted_intent_str = fallback.value
                confidence = 0.5
            else:
                predicted_intent_str = IntentType.UNKNOWN.value

        try:
            intent = IntentType(predicted_intent_str)
        except ValueError:
            intent = IntentType.UNKNOWN

        risk = INTENT_RISK_MAP.get(intent, RiskLevel.READ_ONLY)

        return IntentResult(
            intent=intent,
            confidence=round(confidence, 3),
            entities=entities,
            raw_text=raw_text,
            risk_level=risk
        )

    def _rule_based_check(self, text: str) -> Optional[IntentType]:
        """Fast-path deterministic rule triggers."""
        if text in {"exit", "quit", "bye", "q", ":q"}:
            return IntentType.EXIT
        if text in {"help", "commands", "?", "man", "info"}:
            return IntentType.HELP
        if "lock" in text and ("screen" in text or "workstation" in text or "pc" in text or "computer" in text):
            return IntentType.LOCK_WORKSTATION
        if "screenshot" in text or "snapshot" in text or ("capture" in text and "screen" in text):
            return IntentType.TAKE_SCREENSHOT
        if "clipboard" in text:
            if any(w in text for w in ["copy", "set", "write", "store"]):
                return IntentType.CLIPBOARD_SET
            return IntentType.CLIPBOARD_GET
        if "public ip" in text or "my ip" in text or "ping test" in text:
            return IntentType.NETWORK_DIAGNOSTICS
        if ("temp" in text or "temporary" in text) and any(w in text for w in ["clean", "clear", "purge", "delete", "empty"]):
            return IntentType.CLEANUP_TEMP
        if any(w in text for w in ["remind", "timer", "alarm"]) and any(w in text for w in ["min", "sec", "hour"]):
            return IntentType.SET_REMINDER
        if ("convert" in text or "exchange rate" in text) and any(c in text.upper() for c in ["USD", "INR", "EUR", "GBP"]):
            return IntentType.CURRENCY_CONVERT
        return None

    def _fuzzy_fallback(self, text: str) -> Optional[IntentType]:
        """Secondary keyword fallback for borderline low-confidence phrases."""
        if any(w in text for w in ["organize", "tidy", "sort", "categorize"]):
            return IntentType.ORGANIZE_FILES
        if any(w in text for w in ["find", "search", "locate", "where"]):
            return IntentType.SEARCH_FILES
        if any(w in text for w in ["rename", "bulk rename"]):
            return IntentType.BATCH_RENAME
        if any(w in text for w in ["cpu", "ram", "memory", "performance", "specs", "stats", "battery", "hardware"]):
            return IntentType.SYSTEM_STATS
        if any(w in text for w in ["processes", "process list", "task list", "running apps"]):
            return IntentType.LIST_PROCESSES
        if any(w in text for w in ["kill", "terminate", "force close", "end task"]):
            return IntentType.KILL_PROCESS
        if any(w in text for w in ["weather", "temperature", "forecast", "rain"]):
            return IntentType.WEATHER_QUERY
        if any(w in text for w in ["wiki", "wikipedia", "who is", "what is", "summarize"]):
            return IntentType.WIKI_SUMMARY
        if any(w in text for w in ["open", "launch", "start", "run"]):
            if any(w in text for w in ["http", "www", ".com", ".org", "site", "web"]):
                return IntentType.OPEN_URL
            return IntentType.LAUNCH_APP
        if any(w in text for w in ["routine", "workflow", "macro"]):
            if any(w in text for w in ["list", "show", "all"]):
                return IntentType.LIST_ROUTINES
            if any(w in text for w in ["create", "new", "make"]):
                return IntentType.CREATE_ROUTINE
            return IntentType.RUN_ROUTINE
        return None
