"""
Global pytest configuration for Alexa Morning Briefing Skill tests.

This file provides fixtures and configuration that apply to all tests,
including automatic environment variable setup for unit tests.
"""

import os
import pytest
from unittest.mock import patch


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Automatically set up test environment variables for all unit tests."""
    
    # Define test environment variables
    test_env = {
        'OWM_API_KEY': 'test_openweathermap_api_key_for_unit_tests',
        'GROQ_API_KEY': 'test_groq_api_key_for_unit_tests',
        'GEMINI_API_KEY': 'test_gemini_api_key_for_unit_tests',
        'USER_CITY': 'TestCity,CA',
        'HAS_SCHOOL_KIDS': 'false'
    }
    
    # Only set environment variables if they're not already set
    # This allows for override in specific tests or CI environments
    original_env = {}
    for key, value in test_env.items():
        if key not in os.environ:
            original_env[key] = os.environ.get(key)
            os.environ[key] = value
    
    yield
    
    # Clean up - restore original environment
    for key in test_env.keys():
        if key in original_env:
            if original_env[key] is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_env[key]


@pytest.fixture
def mock_env_minimal():
    """Fixture for tests that need minimal environment (only weather API)."""
    env_vars = {
        'OWM_API_KEY': 'test_weather_key',
        'GROQ_API_KEY': 'test_groq_key',  # At least one LLM key
        'USER_CITY': 'TestCity,CA',
        'HAS_SCHOOL_KIDS': 'false'
    }
    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture  
def mock_env_full():
    """Fixture for tests that need all API keys."""
    env_vars = {
        'OWM_API_KEY': 'test_weather_key',
        'GROQ_API_KEY': 'test_groq_key',
        'GEMINI_API_KEY': 'test_gemini_key',
        'USER_CITY': 'TestCity,CA',
        'HAS_SCHOOL_KIDS': 'true'
    }
    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def mock_env_empty():
    """Fixture for tests that need to test missing environment variables."""
    # Clear all relevant env vars for testing missing config scenarios
    env_vars_to_clear = [
        'OWM_API_KEY', 'GROQ_API_KEY', 'GEMINI_API_KEY', 
        'USER_CITY', 'HAS_SCHOOL_KIDS'
    ]
    with patch.dict(os.environ, {}, clear=False):
        # Remove the specific variables
        for var in env_vars_to_clear:
            os.environ.pop(var, None)
        yield


@pytest.fixture
def sample_weather_data():
    """Sample normalized weather data for testing."""
    return {
        "temp_min": 15.0,
        "temp_max": 22.0,
        "description": "partly cloudy",
        "max_precipitation_prob": 0.3,
        "wind_speed": 5.2,
        "humidity": 65,
        "location": "Vancouver, CA"
    }


@pytest.fixture
def sample_context_data():
    """Sample context data for testing."""
    return {
        "day_type": "weekday",
        "day_name": "Monday",
        "occasion": "work day",
        "season": "spring",
        "location": "Vancouver, BC",
        "has_school_kids": False,
        "date_str": "Monday, April 15, 2024"
    }


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test requiring real APIs"
    )
    config.addinivalue_line(
        "markers", "weather_api: mark test as requiring OpenWeatherMap API"
    )
    config.addinivalue_line(
        "markers", "groq_api: mark test as requiring Groq API"
    )
    config.addinivalue_line(
        "markers", "gemini_api: mark test as requiring Gemini API"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )