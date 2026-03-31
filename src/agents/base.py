"""
BaseLLMProvider — shared API setup and model initialization.

All agents inherit from this class. Centralizes the API key loading,
genai.configure() call, and model instantiation so each agent
only needs to declare which model name/temperature it uses.
"""
import os
import google.generativeai as genai
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from src.services.data_manager import DataManager

load_dotenv()


class BaseLLMProvider:
    """Parent class for all LLM Agents. Handles API setup only."""

    def __init__(
        self,
        settings: Optional[Dict[str, Any]] = None,
        arbiter_model: str = "gemini-2.5-flash-lite",
        narrator_model: str = "gemini-2.5-flash-lite",
        arbiter_temp: float = 0.3,
        narrator_temp: float = 0.7,
    ):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env")

        # 1. Fetch settings from disk if not provided by caller
        if not settings:
            settings = DataManager.load_settings()

        # 2. Extract values with overrides
        llm_cfg = settings.get("llm", {})
        arbiter_model = llm_cfg.get("arbiter_model", arbiter_model)
        narrator_model = llm_cfg.get("narrator_model", narrator_model)
        arbiter_temp = llm_cfg.get("arbiter_temperature", arbiter_temp)
        narrator_temp = llm_cfg.get("narrator_temperature", narrator_temp)

        genai.configure(api_key=api_key)

        # Two model instances: low-temp Arbiter and high-temp Narrator
        self.model = genai.GenerativeModel(
            model_name=arbiter_model,
            generation_config={"temperature": arbiter_temp, "response_mime_type": "text/plain"},
        )
        self.narrator_model = genai.GenerativeModel(
            model_name=narrator_model,
            generation_config={"temperature": narrator_temp},
        )
