"""
LLM Client module for Alexa Morning Briefing Skill
Handles LLM integrations with fallback system: Groq -> Gemini -> Template
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
import requests
import google.genai as genai
from google.genai.types import GenerateContentConfig

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Configuration for LLM clients"""
    groq_api_key: str
    gemini_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"
    gemini_model: str = "gemini-2.0-flash-exp"
    timeout: float = 6.0


class LLMClient:
    """
    LLM client with cascading fallback system:
    1. Groq API (primary)
    2. Google Gemini API (fallback)  
    3. Hardcoded template (final fallback)
    """
    
    def __init__(self, config: LLMConfig):
        """Initialize LLM client with configuration"""
        self.config = config
        self.groq_base_url = "https://api.groq.com/openai/v1/chat/completions"
        
        # Configure Gemini client
        self.gemini_client = None
        if config.gemini_api_key:
            self.gemini_client = genai.Client(api_key=config.gemini_api_key)
    
    def generate_briefing(self, prompt: str, weather_data: Optional[Dict] = None) -> str:
        """
        Generate weather briefing using fallback chain
        
        Args:
            prompt: The formatted prompt for the LLM
            weather_data: Weather data for fallback template (optional)
            
        Returns:
            Generated briefing text
        """
        # Try Groq first (primary)
        try:
            result = self._call_groq(prompt)
            if result:
                logger.info("Successfully generated briefing using Groq")
                return result
        except Exception as e:
            logger.warning(f"Groq API failed: {str(e)}")
        
        # Fallback to Gemini
        try:
            result = self._call_gemini(prompt)
            if result:
                logger.info("Successfully generated briefing using Gemini fallback")
                return result
        except Exception as e:
            logger.warning(f"Gemini API failed: {str(e)}")
        
        # Final fallback to template
        logger.info("Using hardcoded template fallback")
        return self._generate_template_fallback(weather_data or {})
    
    def _call_groq(self, prompt: str) -> Optional[str]:
        """
        Call Groq API using OpenAI-compatible interface
        
        Args:
            prompt: The formatted prompt
            
        Returns:
            Generated response or None if failed
            
        Raises:
            requests.exceptions.RequestException: For HTTP errors
            ValueError: For invalid API responses
        """
        if not self.config.groq_api_key:
            raise ValueError("Groq API key not configured")
        
        headers = {
            "Authorization": f"Bearer {self.config.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.config.groq_model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 150,
            "temperature": 0.7,
            "stream": False
        }
        
        response = requests.post(
            self.groq_base_url,
            headers=headers,
            json=payload,
            timeout=self.config.timeout
        )
        
        response.raise_for_status()
        
        result = response.json()
        
        if "choices" not in result or not result["choices"]:
            raise ValueError("Invalid Groq API response: no choices")
        
        content = result["choices"][0].get("message", {}).get("content", "").strip()
        
        if not content:
            raise ValueError("Empty response from Groq API")
        
        return content
    
    def _call_gemini(self, prompt: str) -> Optional[str]:
        """
        Call Google Gemini API as fallback
        
        Args:
            prompt: The formatted prompt
            
        Returns:
            Generated response or None if failed
            
        Raises:
            Exception: For API errors
        """
        if not self.config.gemini_api_key or not self.gemini_client:
            raise ValueError("Gemini API key not configured")
        
        # Create generation config using new API
        config = GenerateContentConfig(
            max_output_tokens=150,
            temperature=0.7,
        )
        
        response = self.gemini_client.models.generate_content(
            model=self.config.gemini_model,
            contents=prompt,
            config=config
        )
        
        if not response.text:
            raise ValueError("Empty response from Gemini API")
        
        return response.text.strip()
    
    def _generate_template_fallback(self, weather_data: Dict[str, Any]) -> str:
        """
        Generate hardcoded template response when both LLMs fail
        
        Args:
            weather_data: Weather information for template
            
        Returns:
            Template-based response
        """
        location = weather_data.get('location', 'your area')
        temp_max = weather_data.get('temp_max')
        temp_min = weather_data.get('temp_min')  
        description = weather_data.get('description', 'conditions unavailable')
        precipitation_prob = weather_data.get('max_precipitation_prob', 0)
        
        # Build temperature string
        temp_str = "temperatures unavailable"
        if temp_max is not None:
            if temp_min is not None:
                temp_str = f"{int(temp_max)} degrees, low of {int(temp_min)}"
            else:
                temp_str = f"{int(temp_max)} degrees"
        
        # Build precipitation string
        rain_str = ""
        if precipitation_prob > 0.7:
            rain_str = " Bring an umbrella."
        elif precipitation_prob > 0.3:
            rain_str = " Rain is possible."
        
        return (f"I'm unable to generate a personalized briefing today. "
               f"Today in {location}: {temp_str}, {description}.{rain_str} "
               f"Have a great day!")


def create_llm_client_from_environment() -> LLMClient:
    """
    Create LLMClient instance from environment variables
    
    Returns:
        Configured LLMClient instance
        
    Raises:
        ValueError: If required environment variables are missing
    """
    groq_key = os.environ.get('GROQ_API_KEY')
    gemini_key = os.environ.get('GEMINI_API_KEY')
    
    if not groq_key and not gemini_key:
        raise ValueError("At least one of GROQ_API_KEY or GEMINI_API_KEY must be set")
    
    config = LLMConfig(
        groq_api_key=groq_key or "",
        gemini_api_key=gemini_key or ""
    )
    
    return LLMClient(config)