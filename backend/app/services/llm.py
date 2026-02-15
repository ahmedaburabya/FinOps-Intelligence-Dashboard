"""
LLM Integration service for generating FinOps insights using Google Generative AI (Gemini Model).
This module integrates with Google Generative AI for generating automated spend summaries,
detecting anomalies, and providing cost-optimization recommendations, authenticated via an API Key.
Initialization failures will raise exceptions.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import asyncio  # Import asyncio for running blocking calls in a thread pool

# Google Generative AI imports
import google.generativeai as genai

from app import schemas

logger = logging.getLogger(__name__)

# --- Configuration for LLM ---
# These are loaded once at module level.
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")  # Used by genai.Client
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")  # Used by genai.Client
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gemini-2.5-flash")  # The model to use

# Max character limit for LLM input to avoid exceeding context window.
# This is a rough estimate and should be tuned based on the specific model's token limits.
MAX_LLM_INPUT_CHARS = 8000


class LLMService:
    """
    A service class to interact with Google Generative AI (Gemini Model).
    Strictly provides methods for generating various FinOps insights.
    Initialization failures will halt the application startup.
    """

    _instance = None  # Singleton instance

    def __new__(cls):
        """
        Implements a singleton pattern to ensure only one LLM client instance is created.
        """
        if cls._instance is None:
            cls._instance = super(LLMService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Initializes the Google Generative AI client.
        Raises an exception if initialization fails due to configuration or connection issues.
        """
        self.llm_model = None  # Will store the actual GenerativeModel

        # --- Strict Validation for Google Generative AI API Key ---
        if not GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY environment variable is not set. "
                "Cannot initialize Google Generative AI LLM client without an API Key."
            )
        # GCP_PROJECT_ID check is less critical here as it's not directly passed to GenerativeModel
        # but is still good for context/future-proofing if needed for other APIs.

        try:
            # Configure the API key globally for genai
            genai.configure(api_key=GOOGLE_API_KEY)

            # Directly initialize GenerativeModel
            self.llm_model = genai.GenerativeModel(model_name=LLM_MODEL_NAME)

            logger.info(
                f"Google Generative AI client initialized successfully with model: {LLM_MODEL_NAME}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Google Generative AI client: {e}")
            raise RuntimeError(
                f"Critical: Failed to initialize Google Generative AI client. Error: {e}"
            )

    async def _generate_with_gemini(self, prompt: str) -> str:
        """
        Generates text using the Google Generative AI model.
        Raises an exception if generation fails.
        """
        if not self.llm_model:
            raise RuntimeError("Google Generative AI LLM model is not initialized.")

        try:
            generation_config = genai.GenerationConfig(
                temperature=0.2,  # Lower temperature for more focused output
                top_p=0.8,
                top_k=40,
                max_output_tokens=1024,
            )
            # LLM calls can be blocking, so run in a thread pool to avoid blocking the event loop
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,  # Use the default thread pool executor
                lambda: self.llm_model.generate_content(
                    contents=prompt, generation_config=generation_config
                ),
            )

            # Ensure a response candidate exists
            if not response.candidates:
                raise ValueError(
                    "Google Generative AI returned no response candidates."
                )
            return response.text
        except Exception as e:
            logger.error(f"Error generating content with Google Generative AI: {e}")
            raise

    async def generate_spend_summary(
        self, aggregated_data: List[schemas.AggregatedCostData]
    ) -> str:
        """
        Generates a natural language summary of cloud spend based on aggregated data using Google Generative AI.
        """
        prompt = self._format_data_for_llm(
            aggregated_data, "summarize the cloud spend trends and key cost drivers"
        )
        return await self._generate_with_gemini(prompt)

    async def detect_anomalies(
        self, aggregated_data: List[schemas.AggregatedCostData]
    ) -> str:
        """
        Analyzes aggregated data for unusual spending patterns or anomalies using Google Generative AI.
        """
        prompt = self._format_data_for_llm(
            aggregated_data,
            "identify any unusual spending patterns or anomalies and explain them",
        )
        return await self._generate_with_gemini(prompt)

    async def generate_cost_optimization_recommendations(
        self, aggregated_data: List[schemas.AggregatedCostData]
    ) -> str:
        """
        Provides recommendations for optimizing cloud costs based on aggregated data using Google Generative AI.
        """
        prompt = self._format_data_for_llm(
            aggregated_data,
            "provide specific and actionable cost optimization recommendations",
        )
        return await self._generate_with_gemini(prompt)

    def _format_data_for_llm(
        self, aggregated_data: List[schemas.AggregatedCostData], context: str
    ) -> str:
        """
        Helper method to format aggregated data into a string suitable for LLM input.
        If the data exceeds MAX_LLM_INPUT_CHARS, it will be truncated with a warning.
        """
        if not aggregated_data:
            return f"No data available to {context}."

        data_lines = []
        for item in aggregated_data:
            data_lines.append(
                f"- Service: {item.service}, Project: {item.project}, SKU: {item.sku}, "
                f"Time: {item.time_period.strftime('%Y-%m-%d')}, Cost: {item.cost:.2f} {item.currency}, "
                f"Usage: {item.usage_amount if item.usage_amount is not None else 'N/A'} {item.usage_unit if item.usage_unit else ''}"
            )

        full_formatted_data = "\n".join(data_lines)

        # Check for length and truncate if necessary
        if len(full_formatted_data) > MAX_LLM_INPUT_CHARS:
            truncated_formatted_data = full_formatted_data[:MAX_LLM_INPUT_CHARS]
            # Try to truncate at a line break to avoid cutting off mid-data point
            last_newline = truncated_formatted_data.rfind("\n")
            if last_newline != -1:
                truncated_formatted_data = (
                    truncated_formatted_data[:last_newline] + "\n..."
                )
            else:
                truncated_formatted_data += (
                    "..."  # Just append ellipsis if no newline found
                )

            logger.warning(
                f"LLM input data truncated from {len(full_formatted_data)} to {len(truncated_formatted_data)} characters. "
                "The LLM will process partial data. Consider refining filters for more targeted analysis."
            )
            formatted_data_for_llm = truncated_formatted_data
        else:
            formatted_data_for_llm = full_formatted_data

        return (
            f"Analyze the following cloud spend data:\n\n"
            f"{formatted_data_for_llm}\n\n"
            f"Based on this data, please {context}. "
            f"Be concise, clear, and actionable. Focus on key insights."
        )


# Instantiate the LLMService as a singleton
llm_service = LLMService()
