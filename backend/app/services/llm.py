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
from datetime import datetime, date # Added datetime import, also date for stricter type hinting

# Google Generative AI imports
import google.generativeai as genai
# 
# 


from app import schemas, crud # Import crud to potentially use in tools


logger = logging.getLogger(__name__)

# --- Configuration for LLM ---
# These are loaded once at module level.
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")  # Used by genai.Client
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")  # Used by genai.Client
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gemini-2.5-flash")  # The model to use

# Max character limit for LLM input to avoid exceeding context window.
# This is a rough estimate and should be tuned based on the specific model's token limits.
MAX_LLM_INPUT_CHARS = 200000 # Adjusted to be more conservative for token limits


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
            generation_config = genai.GenerationConfig( # Use genai.GenerationConfig
                temperature=0.2,  # Lower temperature for more focused output
                top_p=0.8,
                top_k=40,
                max_output_tokens=8192, # Increased token limit for more detailed responses
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
            # Access text from the first candidate
            return response.text
        except Exception as e:
            logger.error(f"Error generating content with Google Generative AI: {e}")
            raise

    async def generate_spend_summary(
        self,
        aggregated_data: List[schemas.AggregatedCostData],
        project: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> str:
        """
        Generates a natural language summary of cloud spend based on aggregated data using Google Generative AI.
        """
        # This method will now leverage the more generic get_ai_insight
        return await self.get_ai_insight(
            insight_type="summary",
            query="Generate a detailed summary of cloud spend trends and key cost drivers.",
            aggregated_data=aggregated_data,
            project=project,
            start_date=start_date,
            end_date=end_date,
        )

    async def detect_anomalies(
        self,
        aggregated_data: List[schemas.AggregatedCostData],
        project: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> str:
        """
        Analyzes aggregated data for unusual spending patterns or anomalies using Google Generative AI.
        """
        return await self.get_ai_insight(
            insight_type="anomaly",
            query="Identify any unusual spending patterns or anomalies and explain them.",
            aggregated_data=aggregated_data,
            project=project,
            start_date=start_date,
            end_date=end_date,
        )

    async def generate_cost_optimization_recommendations(
        self,
        aggregated_data: List[schemas.AggregatedCostData],
        project: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> str:
        """
        Provides recommendations for optimizing cloud costs based on aggregated data using Google Generative AI.
        """
        return await self.get_ai_insight(
            insight_type="recommendation",
            query="Provide specific and actionable cost optimization recommendations.",
            aggregated_data=aggregated_data,
            project=project,
            start_date=start_date,
            end_date=end_date,
        )

    async def get_ai_insight(
        self,
        insight_type: str,
        query: str,
        aggregated_data: List[schemas.AggregatedCostData],
        project: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> str:
        """
        Generates an AI-driven insight based on the specified type and query.
        This is the central method for interactive AI.
        """
        prompt = self._generate_insight_prompt(
            insight_type=insight_type,
            query=query,
            aggregated_data=aggregated_data,
            project=project,
            start_date=start_date,
            end_date=end_date,
        )
        return await self._generate_with_gemini(prompt)

    def _generate_insight_prompt(
        self,
        insight_type: str,
        query: str,
        aggregated_data: List[schemas.AggregatedCostData],
        project: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> str:
        """
        Helper method to craft detailed prompts for the LLM based on insight type and data.
        """
        data_header_parts = ["The following aggregated cloud spend data is available:"]
        if project:
            data_header_parts.append(f"For Project ID: {project}")
        if start_date and end_date:
            data_header_parts.append(f"From {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        elif start_date:
            data_header_parts.append(f"From {start_date.strftime('%Y-%m-%d')}")
        elif end_date:
            data_header_parts.append(f"Up to {end_date.strftime('%Y-%m-%d')}")
        
        data_header = "\n".join(data_header_parts) + "\n\n"

        formatted_data_for_llm = self._format_data_for_llm_content(aggregated_data)

        base_prompt = (
            f"You are an expert FinOps analyst. Your task is to analyze cloud spend data "
            f"and provide insights. Always respond in clear, concise, plain English."
        )

        if insight_type == "summary":
            instruction = (
                "Based on the provided data, generate a detailed summary of cloud spend trends and key cost drivers. "
                "Include potential anomalies or areas for optimization. Structure your response with clear headings or bullet points for readability."
            )
        elif insight_type == "anomaly":
            instruction = (
                "Based on the provided data, identify any unusual spending patterns or anomalies. "
                "Explain what makes them anomalous and suggest potential reasons or root causes. "
                "Provide specific examples from the data if possible."
            )
        elif insight_type == "root_cause":
            instruction = (
                "Analyze the provided cloud spend data to determine the root cause for any significant changes or anomalies. "
                "Focus on identifying specific services, projects, or SKUs that drove the change. "
                "If the query provides a specific change to investigate, focus on that."
            )
        elif insight_type == "prediction":
            instruction = (
                "Analyze the historical trends in the provided cloud spend data. "
                "Based on these trends, predict future costs for the next month or quarter. "
                "Highlight key assumptions made and potential factors that could influence the prediction."
                "Provide numerical estimates if possible."
            )
        elif insight_type == "recommendation":
            instruction = (
                "Based on the provided cloud spend data, generate specific and actionable cost optimization recommendations. "
                "Categorize recommendations by service or area (e.g., 'Compute Optimization', 'Storage Optimization'). "
                "Quantify potential savings where feasible."
            )
        elif insight_type == "natural_query":
            instruction = f"Answer the following question based on the provided cloud spend data: '{query}'."
            instruction += " If the data is insufficient to answer, state that."
        else:
            instruction = f"Process the following request using the cloud spend data: '{query}'."


        full_prompt = (
            f"{base_prompt}\n\n"
            f"{data_header}"
            f"```json\n{formatted_data_for_llm}\n```\n\n"
            f"{instruction}"
        )
        return full_prompt

    def _format_data_for_llm_content(
        self,
        aggregated_data: List[schemas.AggregatedCostData],
    ) -> str:
        """
        Helper method to format aggregated data into a JSON string suitable for LLM input.
        If the data exceeds MAX_LLM_INPUT_CHARS, it will be truncated with a warning.
        """
        if not aggregated_data:
            return "[]" # Return empty JSON array if no data

        # Convert aggregated_data SQLAlchemy model objects to Pydantic schema objects for JSON serialization
        data_as_dicts = [schemas.AggregatedCostData.model_validate(item).model_dump_json(exclude_unset=True) for item in aggregated_data]
        full_json_data = f"[{', '.join(data_as_dicts)}]"
        
        # Simple truncation if it's too long
        if len(full_json_data) > MAX_LLM_INPUT_CHARS:
            truncated_json_data = full_json_data[:MAX_LLM_INPUT_CHARS]
            last_bracket = truncated_json_data.rfind('}')
            if last_bracket != -1:
                truncated_json_data = truncated_json_data[:last_bracket + 1] + "...]"
            else:
                truncated_json_data += "..."
            
            logger.warning(
                f"LLM input data (JSON) truncated from {len(full_json_data)} to {len(truncated_json_data)} characters. "
                "The LLM will process partial data. Consider refining filters for more targeted analysis."
            )
            return truncated_json_data
        else:
            return full_json_data


# Instantiate the LLMService as a singleton
llm_service = LLMService()
