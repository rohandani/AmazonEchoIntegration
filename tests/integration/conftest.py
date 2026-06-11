"""
Configuration for integration tests.

This file provides pytest configuration and fixtures for integration tests
that require real API keys and network access.
"""

import os
import pytest
import logging

def pytest_configure(config):
    """Configure pytest for integration tests."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def pytest_collection_modifyitems(config, items):
    """Add markers to tests based on API key requirements."""
    for item in items:
        # Mark tests that require API keys
        if 'OWM_API_KEY' in item.name or 'owm' in item.name.lower():
            item.add_marker(pytest.mark.weather_api)
        if 'GROQ_API_KEY' in item.name or 'groq' in item.name.lower():
            item.add_marker(pytest.mark.groq_api)
        if 'GEMINI_API_KEY' in item.name or 'gemini' in item.name.lower():
            item.add_marker(pytest.mark.gemini_api)

def pytest_runtest_setup(item):
    """Setup for each test run."""
    # Add any per-test setup here
    pass

@pytest.fixture
def api_keys():
    """Fixture providing available API keys for tests."""
    return {
        'owm': os.environ.get('OWM_API_KEY'),
        'groq': os.environ.get('GROQ_API_KEY'),
        'gemini': os.environ.get('GEMINI_API_KEY')
    }

@pytest.fixture  
def test_cities():
    """Fixture providing test cities for weather API tests."""
    return [
        "Vancouver,CA",
        "London,UK",
        "Tokyo,JP",
        "Sydney,AU",
        "New York,US"
    ]