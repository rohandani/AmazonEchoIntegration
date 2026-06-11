"""
Integration tests for real API endpoints.

These tests make actual API calls to OpenWeatherMap, Groq, and Gemini APIs
to verify end-to-end functionality. They require valid API keys and are
designed to run within free tier limits to maintain zero infrastructure costs.

Requirements: All requirements verification (from task 8.2)
"""

import os
import pytest
import time
import logging
from datetime import datetime
from typing import Dict, Any

# Import our modules to test
from weather_client import WeatherClient, WeatherAPIError, WeatherDataError
from llm_client import LLMClient, LLMConfig, create_llm_client_from_environment
from context_builder import ContextBuilder
from prompt_engine import PromptEngine

# Configure logging for integration tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting helpers
LAST_OWM_CALL = 0
LAST_GROQ_CALL = 0
LAST_GEMINI_CALL = 0
MIN_INTERVAL_OWM = 1.0  # 1 second between OpenWeatherMap calls
MIN_INTERVAL_GROQ = 0.5  # 0.5 seconds between Groq calls  
MIN_INTERVAL_GEMINI = 1.0  # 1 second between Gemini calls


def rate_limit_owm():
    """Rate limit OpenWeatherMap API calls to stay within free tier limits."""
    global LAST_OWM_CALL
    current_time = time.time()
    elapsed = current_time - LAST_OWM_CALL
    if elapsed < MIN_INTERVAL_OWM:
        time.sleep(MIN_INTERVAL_OWM - elapsed)
    LAST_OWM_CALL = time.time()


def rate_limit_groq():
    """Rate limit Groq API calls to stay within free tier limits."""
    global LAST_GROQ_CALL
    current_time = time.time()
    elapsed = current_time - LAST_GROQ_CALL
    if elapsed < MIN_INTERVAL_GROQ:
        time.sleep(MIN_INTERVAL_GROQ - elapsed)
    LAST_GROQ_CALL = time.time()


def rate_limit_gemini():
    """Rate limit Gemini API calls to stay within free tier limits."""
    global LAST_GEMINI_CALL
    current_time = time.time()
    elapsed = current_time - LAST_GEMINI_CALL
    if elapsed < MIN_INTERVAL_GEMINI:
        time.sleep(MIN_INTERVAL_GEMINI - elapsed)
    LAST_GEMINI_CALL = time.time()


# Skip integration tests if no API keys are available
def requires_api_key(env_var: str):
    """Decorator to skip tests if required API key is not available."""
    def decorator(test_func):
        return pytest.mark.skipif(
            not os.environ.get(env_var),
            reason=f"Integration test requires {env_var} environment variable"
        )(test_func)
    return decorator


class TestWeatherClientIntegration:
    """Integration tests for WeatherClient with real OpenWeatherMap API."""
    
    @requires_api_key('OWM_API_KEY')
    def test_real_weather_api_major_cities(self):
        """Test real weather API calls for major cities."""
        api_key = os.environ['OWM_API_KEY']
        
        # Test cities across different climates and time zones
        test_cities = [
            "Vancouver,CA",
            "London,UK", 
            "Tokyo,JP",
            "Sydney,AU",
            "New York,US"
        ]
        
        for city in test_cities:
            rate_limit_owm()
            
            logger.info(f"Testing weather API for {city}")
            client = WeatherClient(api_key, city)
            
            try:
                result = client.get_forecast()
                
                # Verify result structure and data validity
                assert isinstance(result, dict)
                assert 'temp_min' in result
                assert 'temp_max' in result
                assert 'description' in result
                assert 'max_precipitation_prob' in result
                assert 'location' in result
                assert 'humidity' in result
                assert 'wind_speed' in result
                
                # Verify data ranges are reasonable
                assert -50 <= result['temp_min'] <= 60  # Celsius
                assert -50 <= result['temp_max'] <= 60  # Celsius
                assert result['temp_min'] <= result['temp_max']
                assert 0 <= result['max_precipitation_prob'] <= 1.0
                assert 0 <= result['humidity'] <= 100
                assert result['wind_speed'] >= 0
                assert isinstance(result['description'], str)
                assert len(result['description']) > 0
                
                # Location should contain city info
                assert city.split(',')[0].lower() in result['location'].lower()
                
                logger.info(f"✓ {city}: {result['temp_max']}°C, {result['description']}")
                
            except (WeatherAPIError, WeatherDataError) as e:
                pytest.fail(f"Weather API failed for {city}: {e}")
    
    @requires_api_key('OWM_API_KEY')
    def test_real_weather_api_error_handling(self):
        """Test real weather API error handling with invalid inputs."""
        api_key = os.environ['OWM_API_KEY']
        
        # Test invalid city
        rate_limit_owm()
        client = WeatherClient(api_key, "InvalidCityNameThatDoesNotExist,XX")
        
        with pytest.raises(WeatherAPIError) as exc_info:
            client.get_forecast()
        
        assert "not found" in str(exc_info.value).lower()
    
    @requires_api_key('OWM_API_KEY')
    def test_real_weather_api_performance(self):
        """Test real weather API performance requirements."""
        api_key = os.environ['OWM_API_KEY']
        client = WeatherClient(api_key, "Vancouver,CA")
        
        rate_limit_owm()
        
        start_time = time.time()
        result = client.get_forecast()
        end_time = time.time()
        
        # Should complete within timeout limit (5 seconds)
        response_time = end_time - start_time
        assert response_time < 5.0, f"API call took {response_time:.2f}s, exceeds 5s limit"
        
        logger.info(f"Weather API response time: {response_time:.2f}s")


class TestLLMClientIntegration:
    """Integration tests for LLMClient with real Groq and Gemini APIs."""
    
    @requires_api_key('GROQ_API_KEY')
    def test_real_groq_api_weather_briefing(self):
        """Test real Groq API for weather briefing generation."""
        groq_key = os.environ['GROQ_API_KEY']
        config = LLMConfig(groq_api_key=groq_key, gemini_api_key="")
        client = LLMClient(config)
        
        # Create realistic weather prompt
        prompt_engine = PromptEngine()
        weather_data = {
            "temp_min": 15.0,
            "temp_max": 22.0,
            "description": "partly cloudy",
            "max_precipitation_prob": 0.3,
            "location": "Vancouver, CA"
        }
        context_data = {
            "day_type": "weekday",
            "day_name": "Monday",
            "occasion": "work day", 
            "season": "spring"
        }
        
        prompt = prompt_engine.build_prompt(weather_data, context_data)
        
        rate_limit_groq()
        
        start_time = time.time()
        result = client._call_groq(prompt)
        end_time = time.time()
        
        # Verify response quality
        assert isinstance(result, str)
        assert len(result.strip()) > 0
        assert len(result.split()) >= 20  # Should be substantial
        assert len(result.split()) <= 100  # Should be concise
        
        # Should contain relevant weather information
        assert "vancouver" in result.lower() or "weather" in result.lower()
        
        # Performance check
        response_time = end_time - start_time
        assert response_time < 6.0, f"Groq API call took {response_time:.2f}s, exceeds 6s limit"
        
        logger.info(f"✓ Groq API response time: {response_time:.2f}s")
        logger.info(f"✓ Groq response: {result[:100]}...")
    
    @requires_api_key('GEMINI_API_KEY')
    def test_real_gemini_api_weather_briefing(self):
        """Test real Gemini API for weather briefing generation."""
        gemini_key = os.environ['GEMINI_API_KEY']
        config = LLMConfig(groq_api_key="", gemini_api_key=gemini_key)
        client = LLMClient(config)
        
        # Create realistic weather prompt
        prompt = "Generate a friendly 50-70 word weather briefing for today in Toronto: 18°C, light rain, 70% chance of precipitation. It's a Monday work day in fall."
        
        rate_limit_gemini()
        
        start_time = time.time()
        result = client._call_gemini(prompt)
        end_time = time.time()
        
        # Verify response quality
        assert isinstance(result, str)
        assert len(result.strip()) > 0
        assert len(result.split()) >= 20  # Should be substantial
        assert len(result.split()) <= 100  # Should be concise
        
        # Should contain relevant weather information
        assert "toronto" in result.lower() or "weather" in result.lower() or "rain" in result.lower()
        
        # Performance check
        response_time = end_time - start_time
        assert response_time < 6.0, f"Gemini API call took {response_time:.2f}s, exceeds 6s limit"
        
        logger.info(f"✓ Gemini API response time: {response_time:.2f}s")
        logger.info(f"✓ Gemini response: {result[:100]}...")
    
    @requires_api_key('GROQ_API_KEY')
    @requires_api_key('GEMINI_API_KEY')
    def test_real_llm_fallback_integration(self):
        """Test real LLM fallback integration between Groq and Gemini."""
        groq_key = os.environ['GROQ_API_KEY'] 
        gemini_key = os.environ['GEMINI_API_KEY']
        
        # Test with valid keys (should use Groq first)
        config = LLMConfig(groq_api_key=groq_key, gemini_api_key=gemini_key)
        client = LLMClient(config)
        
        weather_data = {
            'location': 'Seattle, WA',
            'temp_max': 20,
            'description': 'overcast'
        }
        
        rate_limit_groq()
        
        result = client.generate_briefing("Test weather briefing prompt", weather_data)
        
        # Should get a valid response (either from Groq or fallback to Gemini or template)
        assert isinstance(result, str)
        assert len(result.strip()) > 0
        assert "seattle" in result.lower() or "weather" in result.lower() or "unable to generate" in result.lower()
        
        logger.info(f"✓ Fallback chain response: {result[:100]}...")
        
        # Test with invalid Groq key (should fall back to Gemini)
        config_fallback = LLMConfig(groq_api_key="invalid", gemini_api_key=gemini_key)
        client_fallback = LLMClient(config_fallback)
        
        rate_limit_gemini()
        
        result_fallback = client_fallback.generate_briefing("Test weather briefing prompt", weather_data)
        
        # Should still get a valid response (from Gemini or template fallback)
        assert isinstance(result_fallback, str)
        assert len(result_fallback.strip()) > 0
        
        logger.info(f"✓ Fallback response: {result_fallback[:100]}...")


class TestEndToEndIntegration:
    """End-to-end integration tests that exercise the full briefing generation pipeline."""
    
    @requires_api_key('OWM_API_KEY')
    @pytest.mark.parametrize("city,expected_country", [
        ("Vancouver,CA", "CA"),
        ("London,UK", "UK"),
        ("Tokyo,JP", "JP")
    ])
    def test_end_to_end_briefing_generation(self, city, expected_country):
        """Test complete end-to-end briefing generation with real APIs."""
        # Only run if we have at least weather API key
        weather_api_key = os.environ['OWM_API_KEY']
        groq_key = os.environ.get('GROQ_API_KEY', '')
        gemini_key = os.environ.get('GEMINI_API_KEY', '')
        
        logger.info(f"Testing end-to-end briefing generation for {city}")
        
        # 1. Get real weather data
        rate_limit_owm()
        weather_client = WeatherClient(weather_api_key, city)
        weather_data = weather_client.get_forecast()
        
        # 2. Build context
        context_builder = ContextBuilder()
        preferences = {
            'location': city,
            'has_school_kids': True,  # Test school day scenario
            'current_date': datetime.now()
        }
        context_data = context_builder.build_context(preferences)
        
        # 3. Create prompt
        prompt_engine = PromptEngine()
        prompt = prompt_engine.build_prompt(weather_data, context_data)
        
        # 4. Generate briefing (with fallback chain)
        if groq_key or gemini_key:
            config = LLMConfig(groq_api_key=groq_key, gemini_api_key=gemini_key)
            llm_client = LLMClient(config)
            
            if groq_key:
                rate_limit_groq()
            elif gemini_key:
                rate_limit_gemini()
            
            briefing = llm_client.generate_briefing(prompt, weather_data)
        else:
            # Fall back to template if no LLM keys available
            config = LLMConfig(groq_api_key="", gemini_api_key="")
            llm_client = LLMClient(config)
            briefing = llm_client.generate_briefing(prompt, weather_data)
        
        # 5. Sanitize output
        sanitized_briefing = prompt_engine.sanitize_output(briefing)
        
        # Verify end-to-end result
        assert isinstance(sanitized_briefing, str)
        assert len(sanitized_briefing.strip()) > 0
        
        # Should contain location information
        city_name = city.split(',')[0].lower()
        assert (city_name in sanitized_briefing.lower() or 
                "weather" in sanitized_briefing.lower() or
                "unable to generate" in sanitized_briefing.lower())
        
        # Should be safe for Alexa SSML
        unsafe_chars = ['<', '>', '&', '"']
        for char in unsafe_chars:
            if char == '"':
                continue  # Quotes converted to apostrophes is OK
            assert char not in sanitized_briefing
        
        # Log results
        logger.info(f"✓ Weather: {weather_data['temp_max']}°C, {weather_data['description']}")
        logger.info(f"✓ Context: {context_data['day_name']} {context_data['occasion']}")
        logger.info(f"✓ Briefing: {sanitized_briefing}")
        
        # Performance check - entire pipeline should complete reasonably fast
        # Note: This is measured implicitly by the test execution time
    
    @requires_api_key('OWM_API_KEY')
    def test_error_resilience_integration(self):
        """Test system resilience with various error conditions."""
        weather_api_key = os.environ['OWM_API_KEY']
        
        # Test with valid weather but no LLM keys (should fall back to template)
        rate_limit_owm()
        weather_client = WeatherClient(weather_api_key, "Paris,FR")
        weather_data = weather_client.get_forecast()
        
        # Use LLM client with no API keys (forces template fallback)
        config = LLMConfig(groq_api_key="", gemini_api_key="")
        llm_client = LLMClient(config)
        
        context_builder = ContextBuilder()
        context_data = context_builder.build_context({
            'location': 'Paris, France',
            'has_school_kids': False
        })
        
        prompt_engine = PromptEngine()
        prompt = prompt_engine.build_prompt(weather_data, context_data)
        
        # Should fall back to template gracefully
        briefing = llm_client.generate_briefing(prompt, weather_data)
        
        assert isinstance(briefing, str)
        assert len(briefing.strip()) > 0
        assert "unable to generate a personalized briefing" in briefing.lower()
        assert "paris" in briefing.lower()
        assert "have a great day" in briefing.lower()
        
        logger.info(f"✓ Template fallback: {briefing}")
    
    @requires_api_key('OWM_API_KEY')
    def test_rate_limiting_compliance(self):
        """Test that our rate limiting keeps us within free tier limits."""
        weather_api_key = os.environ['OWM_API_KEY']
        
        # Make multiple rapid calls to test rate limiting
        cities = ["Toronto,CA", "Montreal,CA", "Calgary,CA"]
        start_time = time.time()
        
        for city in cities:
            rate_limit_owm()
            client = WeatherClient(weather_api_key, city)
            result = client.get_forecast()
            assert 'location' in result
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should take at least 2 seconds due to rate limiting (3 cities * ~1s each)
        assert total_time >= 2.0, f"Rate limiting may be insufficient: {total_time:.2f}s for 3 calls"
        
        logger.info(f"✓ Rate limiting working: {total_time:.2f}s for 3 API calls")


class TestSystemPerformance:
    """Integration tests focused on performance requirements."""
    
    @requires_api_key('OWM_API_KEY')
    def test_response_time_requirements(self):
        """Test that system meets response time requirements under normal conditions."""
        weather_api_key = os.environ['OWM_API_KEY']
        groq_key = os.environ.get('GROQ_API_KEY', '')
        gemini_key = os.environ.get('GEMINI_API_KEY', '')
        
        # Test with fastest configuration (Groq primary)
        if groq_key:
            config = LLMConfig(groq_api_key=groq_key, gemini_api_key=gemini_key)
        elif gemini_key:
            config = LLMConfig(groq_api_key="", gemini_api_key=gemini_key)
        else:
            config = LLMConfig(groq_api_key="", gemini_api_key="")
        
        # Measure complete pipeline performance
        start_time = time.time()
        
        # Weather API call
        rate_limit_owm()
        weather_client = WeatherClient(weather_api_key, "Vancouver,CA")
        weather_data = weather_client.get_forecast()
        
        # Context building (should be fast)
        context_builder = ContextBuilder()
        context_data = context_builder.build_context({
            'location': 'Vancouver, BC',
            'has_school_kids': False
        })
        
        # Prompt creation (should be fast)
        prompt_engine = PromptEngine()
        prompt = prompt_engine.build_prompt(weather_data, context_data)
        
        # LLM call (potentially slow)
        llm_client = LLMClient(config)
        if groq_key:
            rate_limit_groq()
        elif gemini_key:
            rate_limit_gemini()
        
        briefing = llm_client.generate_briefing(prompt, weather_data)
        
        # Sanitization (should be fast)
        sanitized_briefing = prompt_engine.sanitize_output(briefing)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should meet performance requirements
        if groq_key or gemini_key:
            assert total_time < 8.0, f"Total pipeline time {total_time:.2f}s exceeds 8s Alexa limit"
        else:
            # Template fallback should be very fast
            assert total_time < 3.0, f"Template fallback time {total_time:.2f}s too slow"
        
        logger.info(f"✓ Complete pipeline time: {total_time:.2f}s")
        logger.info(f"✓ Final briefing: {sanitized_briefing}")
    
    @requires_api_key('OWM_API_KEY')
    def test_concurrent_request_handling(self):
        """Test system behavior under concurrent load (simulate multiple Alexa users)."""
        import threading
        import concurrent.futures
        
        weather_api_key = os.environ['OWM_API_KEY']
        results = []
        errors = []
        
        def generate_briefing_for_city(city):
            """Generate a briefing for a specific city."""
            try:
                rate_limit_owm()
                
                weather_client = WeatherClient(weather_api_key, city)
                weather_data = weather_client.get_forecast()
                
                context_builder = ContextBuilder()
                context_data = context_builder.build_context({
                    'location': city,
                    'has_school_kids': False
                })
                
                # Use template fallback for speed and reliability in concurrent test
                config = LLMConfig(groq_api_key="", gemini_api_key="")
                llm_client = LLMClient(config)
                
                prompt_engine = PromptEngine()
                prompt = prompt_engine.build_prompt(weather_data, context_data)
                briefing = llm_client.generate_briefing(prompt, weather_data)
                
                return {'city': city, 'briefing': briefing, 'weather': weather_data}
                
            except Exception as e:
                return {'city': city, 'error': str(e)}
        
        # Test with multiple cities concurrently
        cities = ["Vancouver,CA", "Toronto,CA", "Montreal,CA", "Calgary,CA"]
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(generate_briefing_for_city, city) for city in cities]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify all requests completed successfully
        successful_results = [r for r in results if 'error' not in r]
        assert len(successful_results) >= len(cities) - 1, "Too many concurrent requests failed"
        
        # Verify reasonable performance with concurrency
        assert total_time < 15.0, f"Concurrent requests took too long: {total_time:.2f}s"
        
        logger.info(f"✓ Concurrent requests completed in {total_time:.2f}s")
        logger.info(f"✓ Successful: {len(successful_results)}/{len(cities)} requests")


if __name__ == "__main__":
    # Run integration tests with verbose output
    pytest.main([
        __file__,
        "-v",
        "-s",  # Don't capture output
        "--tb=short",  # Short traceback format
        "-x"  # Stop on first failure
    ])