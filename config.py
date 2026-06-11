"""
Configuration management for Alexa Morning Briefing Skill.

This module handles loading and validating environment variables required
for the skill operation, including API keys and user preferences.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class SkillConfig:
    """Configuration class for the Alexa Morning Briefing Skill.
    
    Loads and validates all required environment variables including API keys
    and user preferences. Provides a centralized configuration management
    system for the skill.
    
    Attributes:
        owm_api_key: OpenWeatherMap API key for weather data
        groq_api_key: Groq API key for primary LLM service
        gemini_api_key: Google Gemini API key for fallback LLM service
        user_city: User's city for weather data (e.g., "Vancouver,CA")
        has_school_kids: Whether user has school-age children for context
    """
    
    owm_api_key: str
    groq_api_key: str
    gemini_api_key: str
    user_city: str
    has_school_kids: bool
    
    @classmethod
    def from_environment(cls) -> 'SkillConfig':
        """Load configuration from environment variables.
        
        Returns:
            SkillConfig: Configured instance with all required settings
            
        Raises:
            ConfigurationError: If required environment variables are missing
            ValueError: If environment variable values are invalid
        """
        # Load required API keys
        owm_api_key = os.getenv('OWM_API_KEY')
        groq_api_key = os.getenv('GROQ_API_KEY')
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        user_city = os.getenv('USER_CITY')
        
        # Load optional settings with defaults
        has_school_kids_str = os.getenv('HAS_SCHOOL_KIDS', 'false').lower()
        
        # Validate required environment variables
        missing_vars = []
        if not owm_api_key:
            missing_vars.append('OWM_API_KEY')
        if not groq_api_key:
            missing_vars.append('GROQ_API_KEY')
        if not gemini_api_key:
            missing_vars.append('GEMINI_API_KEY')
        if not user_city:
            missing_vars.append('USER_CITY')
            
        if missing_vars:
            raise ConfigurationError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )
        
        # Validate API key formats (basic validation)
        if len(owm_api_key.strip()) < 10:
            raise ValueError("OWM_API_KEY appears to be invalid (too short)")
        if len(groq_api_key.strip()) < 10:
            raise ValueError("GROQ_API_KEY appears to be invalid (too short)")
        if len(gemini_api_key.strip()) < 10:
            raise ValueError("GEMINI_API_KEY appears to be invalid (too short)")
            
        # Basic validation - check basic format issues early
        if ',' not in user_city:
            raise ValueError(
                "USER_CITY should be in format 'City,CountryCode' (e.g., 'Vancouver,CA')"
            )
        
        # Check for obvious format issues early
        city_parts = user_city.split(',')
        if len(city_parts) != 2:
            raise ValueError(
                "USER_CITY must have exactly one comma separating city and country code"
            )
        
        # Check for empty parts early
        city_name, country_code = city_parts
        if not city_name.strip():
            raise ValueError("USER_CITY city name cannot be empty")
        if not country_code.strip():
            raise ValueError("USER_CITY country code cannot be empty")
        
        # Parse boolean setting
        has_school_kids = has_school_kids_str in ('true', '1', 'yes', 'on')
        
        return cls(
            owm_api_key=owm_api_key.strip(),
            groq_api_key=groq_api_key.strip(),
            gemini_api_key=gemini_api_key.strip(),
            user_city=user_city.strip(),
            has_school_kids=has_school_kids
        )
    
    def validate(self) -> None:
        """Perform additional validation on configuration values.
        
        Raises:
            ValueError: If any configuration values are invalid
        """
        # Validate API keys are not placeholder values
        placeholder_patterns = [
            'your_',
            'replace_',
            'enter_',
            'add_',
            'insert_'
        ]
        
        for pattern in placeholder_patterns:
            if pattern in self.owm_api_key.lower():
                raise ValueError("OWM_API_KEY appears to be a placeholder value")
            if pattern in self.groq_api_key.lower():
                raise ValueError("GROQ_API_KEY appears to be a placeholder value")
            if pattern in self.gemini_api_key.lower():
                raise ValueError("GEMINI_API_KEY appears to be a placeholder value")
        
        # Validate city format more thoroughly
        city_parts = self.user_city.split(',')
        if len(city_parts) != 2:
            raise ValueError(
                "USER_CITY must have exactly one comma separating city and country code"
            )
        
        city_name, country_code = city_parts
        city_name = city_name.strip()
        country_code = country_code.strip()
        
        if not city_name:
            raise ValueError("USER_CITY city name cannot be empty")
        if not country_code:
            raise ValueError("USER_CITY country code cannot be empty")
        if len(country_code) != 2:
            raise ValueError("USER_CITY country code should be 2 characters (e.g., 'US', 'CA')")


class ConfigurationError(Exception):
    """Exception raised when configuration loading fails."""
    pass


def load_config() -> SkillConfig:
    """Convenience function to load and validate configuration.
    
    Returns:
        SkillConfig: Fully validated configuration instance
        
    Raises:
        ConfigurationError: If configuration cannot be loaded
        ValueError: If configuration values are invalid
    """
    try:
        config = SkillConfig.from_environment()
        config.validate()
        return config
    except (ConfigurationError, ValueError) as e:
        # Re-raise with additional context
        raise ConfigurationError(f"Configuration loading failed: {str(e)}") from e