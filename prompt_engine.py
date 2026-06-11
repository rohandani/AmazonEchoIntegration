"""
Prompt Engine module for assembling LLM instruction prompts.

This module creates optimized prompts for generating natural language weather briefings
that are constrained to 50-70 words for voice interaction and include contextual 
information based on weather data and user preferences.
"""

import re
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class PromptEngine:
    """
    Assembles LLM prompts with weather data and contextual information.
    
    Creates voice-optimized prompts that instruct LLMs to generate natural,
    conversational weather briefings within word limits suitable for Alexa.
    """
    
    # Word count constraints per requirements 2.1
    MIN_WORDS = 50
    MAX_WORDS = 70
    
    def __init__(self):
        """Initialize the PromptEngine."""
        pass
    
    def build_prompt(self, weather_data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Build a complete LLM prompt string with weather data and context.
        
        Creates a prompt that instructs the LLM to generate a natural, conversational
        weather briefing within the 50-70 word limit, incorporating weather conditions,
        precipitation probability, clothing recommendations, and context-aware language
        for school/work days vs weekends.
        
        Args:
            weather_data: Normalized weather data dictionary containing:
                - temp_min: float (Celsius)
                - temp_max: float (Celsius)
                - description: str (weather condition description)
                - max_precipitation_prob: float (0.0 to 1.0)
                - wind_speed: float (m/s)
                - humidity: int (percentage)
                - location: str (city, country)
            context: Context dictionary containing:
                - day_type: str ("weekday" or "weekend")
                - day_name: str (e.g., "Monday")
                - occasion: str ("school day", "work day", or "weekend")
                - season: str ("spring", "summer", "fall", "winter")
                - location: str (user's location)
                - has_school_kids: bool
                - date_str: str (formatted date)
        
        Returns:
            Complete prompt string ready for LLM API call
            
        Raises:
            ValueError: If required data is missing from weather_data or context
        """
        # Validate required input data
        self._validate_weather_data(weather_data)
        self._validate_context_data(context)
        
        # Extract key data points
        temp_min = weather_data["temp_min"]
        temp_max = weather_data["temp_max"]
        description = weather_data["description"]
        precipitation_prob = weather_data["max_precipitation_prob"]
        location = weather_data["location"]
        
        day_name = context["day_name"]
        occasion = context["occasion"]
        season = context["season"]
        
        # Build the system prompt with constraints and instructions
        system_prompt = self._build_system_prompt()
        
        # Build the weather data section
        weather_section = self._build_weather_section(
            temp_min, temp_max, description, precipitation_prob, location
        )
        
        # Build the context section
        context_section = self._build_context_section(day_name, occasion, season)
        
        # Combine all sections into final prompt
        full_prompt = f"{system_prompt}\n\n{weather_section}\n\n{context_section}"
        
        logger.debug(f"Generated prompt for {location} on {day_name}")
        return full_prompt
    
    def _build_system_prompt(self) -> str:
        """
        Build the system instruction section of the prompt.
        
        Creates the core instructions that constrain the LLM to generate
        voice-optimized, natural language weather briefings.
        
        Returns:
            System prompt string with core constraints and instructions
        """
        return f"""You are a friendly morning weather assistant. Generate a natural, conversational weather briefing for voice interaction.

CONSTRAINTS:
- Keep response between {self.MIN_WORDS}-{self.MAX_WORDS} words exactly
- Use natural, conversational language (not robotic or data-heavy)
- Include clear rain probability statement (yes/no/maybe with percentage if helpful)
- Suggest specific clothing appropriate for temperature and conditions
- Mention specific preparations when needed (umbrella, sunscreen, etc.)
- Sound warm and personal, like talking to a family member

OUTPUT REQUIREMENTS:
- No special formatting, markdown, or symbols
- Plain text only, suitable for voice synthesis
- End with encouraging sentiment for the day ahead"""
    
    def _build_weather_section(self, temp_min: float, temp_max: float, 
                             description: str, precipitation_prob: float, 
                             location: str) -> str:
        """
        Build the weather data section of the prompt.
        
        Formats weather data in a way that's easy for the LLM to process
        and incorporate into natural language output.
        
        Args:
            temp_min: Minimum temperature in Celsius
            temp_max: Maximum temperature in Celsius  
            description: Weather condition description
            precipitation_prob: Precipitation probability (0.0 to 1.0)
            location: Location string
            
        Returns:
            Formatted weather data section
        """
        # Convert precipitation probability to percentage
        precipitation_pct = int(precipitation_prob * 100)
        
        # Format temperature range
        if abs(temp_max - temp_min) <= 2:
            temp_info = f"around {int(round(temp_max))}°C"
        else:
            temp_info = f"{int(round(temp_min))}-{int(round(temp_max))}°C"
        
        return f"""WEATHER DATA:
Location: {location}
Temperature: {temp_info}
Conditions: {description}
Rain probability: {precipitation_pct}%"""
    
    def _build_context_section(self, day_name: str, occasion: str, season: str) -> str:
        """
        Build the contextual information section of the prompt.
        
        Provides context that helps the LLM tailor language and recommendations
        appropriately for the user's situation and time of year.
        
        Args:
            day_name: Name of the day (e.g., "Monday")
            occasion: Type of day ("school day", "work day", "weekend")
            season: Current season ("spring", "summer", "fall", "winter")
            
        Returns:
            Formatted context section
        """
        # Generate context-aware instructions
        if occasion == "school day":
            occasion_note = "This is a school day, so consider mentioning school-related activities and appropriate clothing for kids."
        elif occasion == "work day":
            occasion_note = "This is a work day, so consider mentioning commuting conditions and professional attire."
        else:  # weekend
            occasion_note = "This is a weekend, so consider mentioning leisure activities and casual comfort."
        
        # Season-specific considerations
        season_considerations = {
            "spring": "Spring weather can be variable - mention layering if appropriate.",
            "summer": "Summer weather - consider sun protection and heat comfort.",
            "fall": "Fall weather - mention seasonal clothing and potential weather changes.",
            "winter": "Winter weather - emphasize warmth and weather protection."
        }
        
        season_note = season_considerations.get(season, "Consider seasonal appropriateness of recommendations.")
        
        return f"""CONTEXT:
Day: {day_name}
Occasion: {occasion_note}
Season: {season_note}

Generate your weather briefing now, incorporating all weather data and context naturally."""
    
    def _validate_weather_data(self, weather_data: Dict[str, Any]) -> None:
        """
        Validate that weather_data contains all required fields.
        
        Args:
            weather_data: Dictionary to validate
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        required_fields = [
            "temp_min", "temp_max", "description", 
            "max_precipitation_prob", "location"
        ]
        
        if not isinstance(weather_data, dict):
            raise ValueError("weather_data must be a dictionary")
        
        for field in required_fields:
            if field not in weather_data:
                raise ValueError(f"Missing required weather field: {field}")
        
        # Validate specific field types
        if not isinstance(weather_data["temp_min"], (int, float)):
            raise ValueError("temp_min must be a number")
        
        if not isinstance(weather_data["temp_max"], (int, float)):
            raise ValueError("temp_max must be a number")
        
        if not isinstance(weather_data["description"], str) or not weather_data["description"].strip():
            raise ValueError("description must be a non-empty string")
        
        if not isinstance(weather_data["max_precipitation_prob"], (int, float)):
            raise ValueError("max_precipitation_prob must be a number")
        
        if not (0.0 <= weather_data["max_precipitation_prob"] <= 1.0):
            raise ValueError("max_precipitation_prob must be between 0.0 and 1.0")
        
        if not isinstance(weather_data["location"], str) or not weather_data["location"].strip():
            raise ValueError("location must be a non-empty string")
    
    def _validate_context_data(self, context: Dict[str, Any]) -> None:
        """
        Validate that context contains all required fields.
        
        Args:
            context: Dictionary to validate
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        required_fields = ["day_name", "occasion", "season"]
        
        if not isinstance(context, dict):
            raise ValueError("context must be a dictionary")
        
        for field in required_fields:
            if field not in context:
                raise ValueError(f"Missing required context field: {field}")
        
        # Validate specific field values
        if not isinstance(context["day_name"], str) or not context["day_name"].strip():
            raise ValueError("day_name must be a non-empty string")
        
        valid_occasions = ["school day", "work day", "weekend"]
        if context["occasion"] not in valid_occasions:
            raise ValueError(f"occasion must be one of: {valid_occasions}")
        
        valid_seasons = ["spring", "summer", "fall", "winter"]
        if context["season"] not in valid_seasons:
            raise ValueError(f"season must be one of: {valid_seasons}")
    
    def sanitize_output(self, llm_output: str) -> str:
        """
        Sanitize LLM output for Alexa SSML compatibility and voice output.
        
        Removes HTML/Markdown formatting, filters special characters that could
        cause SSML parsing errors, validates length constraints, and ensures
        the output is safe for text-to-speech synthesis.
        
        Args:
            llm_output: Raw output string from LLM
            
        Returns:
            Sanitized string ready for Alexa voice output
            
        Raises:
            ValueError: If output is empty or None
        """
        if not llm_output or not isinstance(llm_output, str):
            raise ValueError("llm_output must be a non-empty string")
        
        # Start with the raw output
        sanitized = llm_output.strip()
        
        # Remove common HTML tags (case insensitive)
        html_patterns = [
            r'<[^>]+>',  # Any HTML tag
            r'&[a-zA-Z0-9#]+;',  # HTML entities like &amp; &lt; &#123;
        ]
        
        for pattern in html_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        # Remove Markdown formatting
        markdown_patterns = [
            (r'\*\*(.*?)\*\*', r'\1'),  # **bold** -> content
            (r'\*(.*?)\*', r'\1'),      # *italic* -> content  
            (r'__(.*?)__', r'\1'),      # __bold__ -> content
            (r'_(.*?)_', r'\1'),        # _italic_ -> content
            (r'`(.*?)`', r'\1'),        # `code` -> content
            (r'```.*?```', ''),         # ```code blocks``` -> empty
            (r'#{1,6}\s*', ''),         # # headers -> remove hashes
            (r'\[([^\]]+)\]\([^\)]+\)', r'\1'),  # [text](url) -> text
        ]
        
        for pattern, replacement in markdown_patterns:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.DOTALL)
        
        # Remove characters that can cause SSML parsing issues
        ssml_unsafe_chars = [
            '<', '>',  # SSML tag delimiters
            '&',       # Entity reference start
            '"',       # Attribute quote (replace with apostrophe)
        ]
        
        for char in ssml_unsafe_chars:
            if char == '"':
                sanitized = sanitized.replace(char, "'")
            else:
                sanitized = sanitized.replace(char, '')
        
        # Clean up whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized)  # Multiple spaces -> single space
        sanitized = sanitized.strip()
        
        # Validate length for voice output (reasonable limits)
        if len(sanitized) > 500:  # Reasonable upper limit for voice
            logger.warning(f"Sanitized output is long ({len(sanitized)} chars), may be too verbose for voice")
        
        if not sanitized:
            raise ValueError("Sanitized output is empty after cleaning")
        
        logger.debug(f"Sanitized output: {len(sanitized)} characters")
        return sanitized