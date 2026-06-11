"""
Unit tests for LLM Client module
Tests Groq integration, fallback logic, and error handling
"""

import os
import pytest
import responses
import json
from unittest.mock import patch, MagicMock
from llm_client import LLMClient, LLMConfig, create_llm_client_from_environment


@pytest.fixture
def llm_config():
    """Create test LLM configuration"""
    return LLMConfig(
        groq_api_key="test-groq-key",
        gemini_api_key="test-gemini-key",
        timeout=5.0
    )


@pytest.fixture
def llm_client(llm_config):
    """Create LLM client for testing"""
    return LLMClient(llm_config)


@pytest.fixture
def sample_weather_data():
    """Sample weather data for testing"""
    return {
        'location': 'Vancouver, CA',
        'temp_max': 22.5,
        'temp_min': 18.0,
        'description': 'light rain',
        'max_precipitation_prob': 0.8,
        'wind_speed': 3.2,
        'humidity': 75
    }


class TestLLMClient:
    """Test cases for LLMClient class"""

    def test_init_with_valid_config(self, llm_config):
        """Test LLMClient initialization with valid config"""
        client = LLMClient(llm_config)
        assert client.config == llm_config
        assert client.groq_base_url == "https://api.groq.com/openai/v1/chat/completions"

    @responses.activate
    def test_call_groq_success(self, llm_client):
        """Test successful Groq API call"""
        # Mock successful Groq response
        responses.add(
            responses.POST,
            "https://api.groq.com/openai/v1/chat/completions",
            json={
                "choices": [
                    {
                        "message": {
                            "content": "Good morning! Today will be partly cloudy with temperatures reaching 22 degrees. Light rain expected this afternoon, so grab an umbrella. Perfect weather for staying cozy indoors!"
                        }
                    }
                ]
            },
            status=200
        )

        prompt = "Generate a weather briefing for light rain, 22 degrees"
        result = llm_client._call_groq(prompt)
        
        assert result is not None
        assert "22 degrees" in result
        assert "rain" in result.lower()
        assert len(result.split()) >= 10  # Should be substantial response

    @responses.activate
    def test_call_groq_http_error(self, llm_client):
        """Test Groq API HTTP error handling"""
        responses.add(
            responses.POST,
            "https://api.groq.com/openai/v1/chat/completions",
            status=500
        )

        prompt = "Generate a weather briefing"
        
        with pytest.raises(Exception):
            llm_client._call_groq(prompt)

    @responses.activate
    def test_call_groq_invalid_response_no_choices(self, llm_client):
        """Test Groq API with invalid response structure"""
        responses.add(
            responses.POST,
            "https://api.groq.com/openai/v1/chat/completions",
            json={"error": "Invalid request"},
            status=200
        )

        prompt = "Generate a weather briefing"
        
        with pytest.raises(ValueError, match="no choices"):
            llm_client._call_groq(prompt)

    @responses.activate
    def test_call_groq_empty_content(self, llm_client):
        """Test Groq API with empty content response"""
        responses.add(
            responses.POST,
            "https://api.groq.com/openai/v1/chat/completions",
            json={
                "choices": [
                    {
                        "message": {
                            "content": ""
                        }
                    }
                ]
            },
            status=200
        )

        prompt = "Generate a weather briefing"
        
        with pytest.raises(ValueError, match="Empty response from Groq API"):
            llm_client._call_groq(prompt)

    def test_call_groq_no_api_key(self):
        """Test Groq API call without API key"""
        config = LLMConfig(groq_api_key="", gemini_api_key="test-key")
        client = LLMClient(config)
        
        with pytest.raises(ValueError, match="Groq API key not configured"):
            client._call_groq("test prompt")

    @responses.activate
    def test_call_groq_timeout(self, llm_client):
        """Test Groq API timeout handling"""
        responses.add(
            responses.POST,
            "https://api.groq.com/openai/v1/chat/completions",
            body=responses.ConnectionError("Timeout")
        )

        prompt = "Generate a weather briefing"
        
        with pytest.raises(Exception):
            llm_client._call_groq(prompt)

    @responses.activate
    def test_call_groq_request_format(self, llm_client):
        """Test Groq API request format and headers"""
        def request_callback(request):
            # Verify headers
            assert request.headers['Authorization'] == 'Bearer test-groq-key'
            assert request.headers['Content-Type'] == 'application/json'
            
            # Verify request payload
            payload = json.loads(request.body)
            assert payload['model'] == 'llama-3.3-70b-versatile'
            assert payload['messages'][0]['role'] == 'user'
            assert payload['messages'][0]['content'] == 'test prompt'
            assert payload['max_tokens'] == 150
            assert payload['temperature'] == 0.7
            assert payload['stream'] is False
            
            return (200, {}, json.dumps({
                "choices": [{"message": {"content": "Test response"}}]
            }))

        responses.add_callback(
            responses.POST,
            "https://api.groq.com/openai/v1/chat/completions",
            callback=request_callback
        )

        result = llm_client._call_groq("test prompt")
        assert result == "Test response"

    def test_generate_template_fallback_complete_data(self, llm_client, sample_weather_data):
        """Test template fallback with complete weather data"""
        result = llm_client._generate_template_fallback(sample_weather_data)
        
        assert "I'm unable to generate a personalized briefing today" in result
        assert "Vancouver, CA" in result
        assert "22 degrees" in result
        assert "18" in result  # min temp
        assert "light rain" in result
        assert "umbrella" in result  # high precipitation probability
        assert "Have a great day!" in result

    def test_generate_template_fallback_minimal_data(self, llm_client):
        """Test template fallback with minimal weather data"""
        minimal_data = {'description': 'sunny'}
        
        result = llm_client._generate_template_fallback(minimal_data)
        
        assert "I'm unable to generate a personalized briefing today" in result
        assert "your area" in result  # default location
        assert "temperatures unavailable" in result
        assert "sunny" in result
        assert "Have a great day!" in result

    def test_generate_template_fallback_empty_data(self, llm_client):
        """Test template fallback with empty weather data"""
        result = llm_client._generate_template_fallback({})
        
        assert "I'm unable to generate a personalized briefing today" in result
        assert "your area" in result
        assert "conditions unavailable" in result
        assert "Have a great day!" in result

    def test_generate_template_fallback_precipitation_levels(self, llm_client):
        """Test template fallback precipitation probability responses"""
        # High probability (> 0.7)
        high_rain_data = {'max_precipitation_prob': 0.8, 'temp_max': 20}
        result = llm_client._generate_template_fallback(high_rain_data)
        assert "umbrella" in result
        
        # Medium probability (0.3 - 0.7)
        medium_rain_data = {'max_precipitation_prob': 0.5, 'temp_max': 20}
        result = llm_client._generate_template_fallback(medium_rain_data)
        assert "possible" in result
        
        # Low probability (< 0.3)
        low_rain_data = {'max_precipitation_prob': 0.1, 'temp_max': 20}
        result = llm_client._generate_template_fallback(low_rain_data)
        assert "umbrella" not in result
        assert "possible" not in result


class TestGeminiFallback:
    """Test cases for Gemini fallback functionality"""
    
    @pytest.fixture
    def llm_client_with_gemini(self):
        """Create LLM client configured for Gemini testing"""
        config = LLMConfig(
            groq_api_key="",  # No Groq key to force fallback
            gemini_api_key="test-gemini-key",
            timeout=5.0
        )
        return LLMClient(config)
    
    def test_call_gemini_no_api_key(self):
        """Test Gemini API call without API key"""
        config = LLMConfig(groq_api_key="test-key", gemini_api_key="")
        client = LLMClient(config)
        
        with pytest.raises(ValueError, match="Gemini API key not configured"):
            client._call_gemini("test prompt")
    
    @patch('google.genai.Client')
    def test_call_gemini_success(self, mock_client_class, llm_client_with_gemini):
        """Test successful Gemini API call"""
        # Mock the client and response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Good morning! It's going to be 22 degrees with light rain today. Perfect weather for staying cozy inside with a warm cup of coffee!"
        
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        # Set up the client mock for the instance
        llm_client_with_gemini.gemini_client = mock_client
        
        prompt = "Generate a weather briefing for light rain, 22 degrees"
        result = llm_client_with_gemini._call_gemini(prompt)
        
        assert result is not None
        assert "22 degrees" in result
        assert "rain" in result
        assert len(result.split()) >= 10  # Should be substantial response
        
        # Verify the model was called correctly
        mock_client.models.generate_content.assert_called_once()
    
    @patch('google.genai.Client')
    def test_call_gemini_empty_response(self, mock_client_class, llm_client_with_gemini):
        """Test Gemini API with empty response"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = ""
        
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client
        llm_client_with_gemini.gemini_client = mock_client
        
        with pytest.raises(ValueError, match="Empty response from Gemini API"):
            llm_client_with_gemini._call_gemini("test prompt")
    
    @patch('google.genai.Client')
    def test_call_gemini_api_error(self, mock_client_class, llm_client_with_gemini):
        """Test Gemini API error handling"""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API Error")
        mock_client_class.return_value = mock_client
        llm_client_with_gemini.gemini_client = mock_client
        
        with pytest.raises(Exception, match="API Error"):
            llm_client_with_gemini._call_gemini("test prompt")
    
    @patch('google.genai.Client')
    def test_call_gemini_generation_config(self, mock_client_class, llm_client_with_gemini):
        """Test Gemini API generation configuration"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Test response"
        
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client
        llm_client_with_gemini.gemini_client = mock_client
        
        llm_client_with_gemini._call_gemini("test prompt")
        
        # Verify generation config was passed
        call_args = mock_client.models.generate_content.call_args
        assert call_args[1]['model'] == "gemini-2.0-flash-exp"
        assert call_args[1]['contents'] == "test prompt"
        
        # Check config parameter
        config = call_args[1]['config']
        assert config.max_output_tokens == 150
        assert config.temperature == 0.7


class TestFallbackLogic:
    """Test cases for automatic fallback logic execution"""
    
    @responses.activate
    @patch('google.genai.Client')
    def test_generate_briefing_groq_to_gemini_fallback(self, mock_client_class, sample_weather_data):
        """Test automatic fallback from Groq to Gemini when Groq fails"""
        # Configure Groq to fail
        responses.add(
            responses.POST,
            "https://api.groq.com/openai/v1/chat/completions",
            status=500
        )
        
        # Mock successful Gemini response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Good morning from Gemini! Today will be 22 degrees with light rain. Perfect for staying cozy indoors!"
        
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        config = LLMConfig(
            groq_api_key="test-groq-key",
            gemini_api_key="test-gemini-key"
        )
        client = LLMClient(config)
        
        result = client.generate_briefing("Test prompt", sample_weather_data)
        
        assert result is not None
        assert "Gemini" in result
        assert "22 degrees" in result
        mock_client.models.generate_content.assert_called_once()
    
    @responses.activate
    @patch('google.genai.Client')  
    def test_generate_briefing_both_apis_fail_to_template(self, mock_client_class, sample_weather_data):
        """Test fallback to template when both Groq and Gemini fail"""
        # Configure Groq to fail
        responses.add(
            responses.POST,
            "https://api.groq.com/openai/v1/chat/completions",
            status=500
        )
        
        # Configure Gemini to fail
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("Gemini API Error")
        mock_client_class.return_value = mock_client
        
        config = LLMConfig(
            groq_api_key="test-groq-key",
            gemini_api_key="test-gemini-key"
        )
        client = LLMClient(config)
        
        result = client.generate_briefing("Test prompt", sample_weather_data)
        
        assert result is not None
        assert "I'm unable to generate a personalized briefing today" in result
        assert "Vancouver, CA" in result
        assert "22 degrees" in result
        assert "Have a great day!" in result
    
    @responses.activate
    def test_generate_briefing_successful_groq_no_fallback(self, sample_weather_data):
        """Test successful Groq call with no fallback needed"""
        # Mock successful Groq response
        responses.add(
            responses.POST,
            "https://api.groq.com/openai/v1/chat/completions",
            json={
                "choices": [
                    {
                        "message": {
                            "content": "Good morning! Today in Vancouver: 22 degrees with light rain. Grab an umbrella and enjoy the cozy weather!"
                        }
                    }
                ]
            },
            status=200
        )
        
        config = LLMConfig(
            groq_api_key="test-groq-key",
            gemini_api_key="test-gemini-key"
        )
        client = LLMClient(config)
        
        with patch.object(client, '_call_gemini') as mock_gemini:
            result = client.generate_briefing("Test prompt", sample_weather_data)
            
            assert result is not None
            assert "Vancouver" in result
            assert "22 degrees" in result
            assert "umbrella" in result
            
            # Verify Gemini was never called
            mock_gemini.assert_not_called()
    
    def test_generate_briefing_no_weather_data_fallback(self):
        """Test template fallback with no weather data provided"""
        config = LLMConfig(
            groq_api_key="",  # No keys to force template fallback
            gemini_api_key=""
        )
        client = LLMClient(config)
        
        result = client.generate_briefing("Test prompt")
        
        assert result is not None
        assert "I'm unable to generate a personalized briefing today" in result
        assert "your area" in result
        assert "Have a great day!" in result


class TestLLMClientFromEnvironment:
    """Test cases for environment-based configuration"""

    def test_create_client_from_environment_both_keys(self):
        """Test creating client with both API keys in environment"""
        with patch.dict(os.environ, {
            'GROQ_API_KEY': 'env-groq-key',
            'GEMINI_API_KEY': 'env-gemini-key'
        }):
            client = create_llm_client_from_environment()
            assert client.config.groq_api_key == 'env-groq-key'
            assert client.config.gemini_api_key == 'env-gemini-key'

    def test_create_client_from_environment_groq_only(self):
        """Test creating client with only Groq API key"""
        with patch.dict(os.environ, {
            'GROQ_API_KEY': 'env-groq-key'
        }, clear=True):
            client = create_llm_client_from_environment()
            assert client.config.groq_api_key == 'env-groq-key'
            assert client.config.gemini_api_key == ''

    def test_create_client_from_environment_gemini_only(self):
        """Test creating client with only Gemini API key"""
        with patch.dict(os.environ, {
            'GEMINI_API_KEY': 'env-gemini-key'
        }, clear=True):
            client = create_llm_client_from_environment()
            assert client.config.groq_api_key == ''
            assert client.config.gemini_api_key == 'env-gemini-key'

    def test_create_client_from_environment_no_keys(self):
        """Test creating client with no API keys raises error"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="At least one of GROQ_API_KEY or GEMINI_API_KEY must be set"):
                create_llm_client_from_environment()


class TestTemplateSystemComprehensive:
    """Comprehensive test cases for hardcoded template fallback system"""
    
    def test_template_always_returns_valid_alexa_response(self, llm_client):
        """Test template fallback always returns valid Alexa-compatible response"""
        # Test with various weather data scenarios
        test_cases = [
            {},  # Empty data
            {'temp_max': None, 'temp_min': None},  # No temperature data
            {'location': '', 'description': ''},  # Empty strings
            {'temp_max': -10, 'temp_min': -15, 'description': 'heavy snow'},  # Extreme cold
            {'temp_max': 40, 'temp_min': 35, 'description': 'extreme heat'},  # Extreme heat
        ]
        
        for weather_data in test_cases:
            result = llm_client._generate_template_fallback(weather_data)
            
            # Verify basic structure
            assert result is not None
            assert isinstance(result, str)
            assert len(result) > 0
            
            # Verify required components
            assert "I'm unable to generate a personalized briefing today" in result
            assert "Have a great day!" in result
            
            # Verify no dangerous characters for SSML
            assert "<" not in result
            assert ">" not in result
            assert "&" not in result or "&" in ["&amp;", "&lt;", "&gt;"]
    
    def test_template_acknowledgment_message(self, llm_client, sample_weather_data):
        """Test template includes proper acknowledgment of LLM service unavailability"""
        result = llm_client._generate_template_fallback(sample_weather_data)
        
        # Verify acknowledgment is present and properly formatted
        assert result.startswith("I'm unable to generate a personalized briefing today.")
        assert "personalized briefing" in result
        assert not result.startswith("Error") or result.startswith("Failed")
        
        # Should still provide weather information
        assert "Vancouver, CA" in result
        assert "light rain" in result
    
    def test_template_handles_missing_critical_data(self, llm_client):
        """Test template gracefully handles missing critical weather data"""
        incomplete_data = {
            'location': 'Test City',
            # Missing temp_max, temp_min, description, precipitation_prob
        }
        
        result = llm_client._generate_template_fallback(incomplete_data)
        
        assert "Test City" in result
        assert "temperatures unavailable" in result
        assert "conditions unavailable" in result
        assert "Have a great day!" in result
    
    def test_template_response_length_reasonable(self, llm_client, sample_weather_data):
        """Test template response is reasonable length for voice output"""
        result = llm_client._generate_template_fallback(sample_weather_data)
        
        words = result.split()
        # Should be concise but informative (roughly 20-40 words)
        assert 15 <= len(words) <= 60
        
        # Should not be too verbose
        sentences = result.split('.')
        assert len(sentences) <= 5  # Keep it concise
    
    def test_double_failure_scenario_comprehensive(self, llm_client, sample_weather_data):
        """Test comprehensive double-failure scenario with various configurations"""
        # Test different API key configurations
        configurations = [
            LLMConfig(groq_api_key="", gemini_api_key=""),  # No keys
            LLMConfig(groq_api_key="invalid", gemini_api_key=""),  # Invalid Groq only
            LLMConfig(groq_api_key="", gemini_api_key="invalid"),  # Invalid Gemini only
            LLMConfig(groq_api_key="invalid", gemini_api_key="invalid"),  # Both invalid
        ]
        
        for config in configurations:
            client = LLMClient(config)
            result = client.generate_briefing("Test prompt", sample_weather_data)
            
            # Should always fall back to template
            assert "I'm unable to generate a personalized briefing today" in result
            assert "Vancouver, CA" in result
            assert "Have a great day!" in result
    
    @responses.activate
    @patch('google.genai.Client')
    def test_timeout_double_failure(self, mock_client_class, sample_weather_data):
        """Test double failure due to timeouts on both services"""
        # Mock Groq timeout
        responses.add(
            responses.POST,
            "https://api.groq.com/openai/v1/chat/completions",
            body=responses.ConnectionError("Connection timeout")
        )
        
        # Mock Gemini timeout
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("Request timeout")
        mock_client_class.return_value = mock_client
        
        config = LLMConfig(
            groq_api_key="test-groq-key",
            gemini_api_key="test-gemini-key",
            timeout=1.0  # Short timeout for testing
        )
        client = LLMClient(config)
        
        result = client.generate_briefing("Test prompt", sample_weather_data)
        
        assert "I'm unable to generate a personalized briefing today" in result
        assert "Vancouver, CA" in result
        assert "22 degrees" in result
        assert "Have a great day!" in result
    
    def test_template_weather_context_integration(self, llm_client):
        """Test template properly integrates all available weather context"""
        rich_weather_data = {
            'location': 'Toronto, CA',
            'temp_max': 15.5,
            'temp_min': 8.2,
            'description': 'partly cloudy',
            'max_precipitation_prob': 0.4,  # Medium chance
            'wind_speed': 12.5,
            'humidity': 65
        }
        
        result = llm_client._generate_template_fallback(rich_weather_data)
        
        # Verify all key weather information is included
        assert "Toronto, CA" in result
        assert "15 degrees" in result  # Rounded max temp
        assert "8" in result  # Min temp  
        assert "partly cloudy" in result
        assert "possible" in result  # Medium precipitation probability
        
        # Should still maintain professional tone
        assert "I'm unable to generate a personalized briefing today" in result
        assert "Have a great day!" in result


class TestLLMClientWithFixtures:
    """Additional comprehensive tests using fixture data and extensive mocking."""
    
    @responses.activate
    def test_groq_api_with_fixture_response(self):
        """Test Groq API call using fixture response data."""
        import json
        import os
        
        # Load fixture data
        fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'groq_response.json')
        with open(fixture_path, 'r') as f:
            fixture_data = json.load(f)
        
        responses.add(
            responses.POST,
            "https://api.groq.com/openai/v1/chat/completions",
            json=fixture_data,
            status=200
        )
        
        config = LLMConfig(groq_api_key="test-key", gemini_api_key="")
        client = LLMClient(config)
        
        result = client._call_groq("Generate weather briefing for sunny day")
        
        expected = fixture_data["choices"][0]["message"]["content"]
        assert result == expected
        assert "Vancouver" in result
        assert "27 degrees" in result
        assert "sunny" in result
        assert len(result.split()) >= 20  # Should be substantial
    
    @patch('google.genai.Client')
    def test_gemini_api_with_fixture_style_response(self, mock_client_class):
        """Test Gemini API call with fixture-style response."""
        # Mock Gemini client with realistic response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Good morning! It's looking like a lovely day in Vancouver with clear skies and temperatures around 24 degrees. Perfect for a morning walk or bike ride! You'll be comfortable in light layers. No rain in sight, so no need for an umbrella today. Enjoy your beautiful day!"
        
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        config = LLMConfig(groq_api_key="", gemini_api_key="test-key")
        client = LLMClient(config)
        
        result = client._call_gemini("Generate weather briefing")
        
        assert "Vancouver" in result
        assert "24 degrees" in result
        assert "clear skies" in result
        assert "morning walk" in result
        assert len(result.split()) >= 25  # Comprehensive response
    
    @responses.activate
    @patch('google.genai.Client')
    def test_comprehensive_fallback_chain_with_different_weather(self, mock_client_class):
        """Test complete fallback chain with various weather scenarios."""
        weather_scenarios = [
            {
                'location': 'Calgary, CA',
                'temp_max': -5.0,
                'temp_min': -12.0,
                'description': 'heavy snow',
                'max_precipitation_prob': 0.9
            },
            {
                'location': 'Miami, FL',
                'temp_max': 35.0,
                'temp_min': 28.0,
                'description': 'scorching heat',
                'max_precipitation_prob': 0.1
            },
            {
                'location': 'London, UK', 
                'temp_max': 18.0,
                'temp_min': 12.0,
                'description': 'light drizzle',
                'max_precipitation_prob': 0.6
            }
        ]
        
        # Configure both APIs to fail
        responses.add(
            responses.POST,
            "https://api.groq.com/openai/v1/chat/completions",
            status=500
        )
        
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("Gemini failed")
        mock_client_class.return_value = mock_client
        
        config = LLMConfig(groq_api_key="test-key", gemini_api_key="test-key")
        client = LLMClient(config)
        
        for weather_data in weather_scenarios:
            result = client.generate_briefing("test prompt", weather_data)
            
            # Should fall back to template
            assert "I'm unable to generate a personalized briefing today" in result
            assert weather_data['location'] in result
            assert str(int(weather_data['temp_max'])) in result
            assert weather_data['description'] in result
            assert "Have a great day!" in result
    
    @responses.activate
    def test_api_authentication_failures(self):
        """Test various API authentication failure scenarios."""
        auth_error_responses = [
            (401, {"error": "Invalid API key"}),
            (403, {"error": "Forbidden - insufficient permissions"}),
            (401, {"error": "API key expired"})
        ]
        
        config = LLMConfig(groq_api_key="invalid-key", gemini_api_key="")
        client = LLMClient(config)
        
        for status_code, response_data in auth_error_responses:
            responses.reset()
            responses.add(
                responses.POST,
                "https://api.groq.com/openai/v1/chat/completions",
                json=response_data,
                status=status_code
            )
            
            with pytest.raises(Exception):
                client._call_groq("test prompt")
    
    @responses.activate
    def test_api_response_malformation_scenarios(self):
        """Test handling of malformed API responses."""
        malformed_responses = [
            {"choices": []},  # Empty choices
            {"choices": [{"message": {}}]},  # Missing content
            {"choices": [{"message": {"content": ""}}]},  # Empty content
            {"error": "Model overloaded"},  # Error response
            "not json",  # Invalid JSON
        ]
        
        config = LLMConfig(groq_api_key="test-key", gemini_api_key="")
        client = LLMClient(config)
        
        for i, response_data in enumerate(malformed_responses):
            responses.reset()
            if response_data == "not json":
                responses.add(
                    responses.POST,
                    "https://api.groq.com/openai/v1/chat/completions",
                    body=response_data,
                    status=200
                )
            else:
                responses.add(
                    responses.POST,
                    "https://api.groq.com/openai/v1/chat/completions",
                    json=response_data,
                    status=200
                )
            
            with pytest.raises(Exception):
                client._call_groq("test prompt")
    
    def test_llm_config_validation(self):
        """Test LLM configuration validation and edge cases."""
        # Test with various config combinations
        valid_configs = [
            LLMConfig("groq-key", ""),  # Groq only
            LLMConfig("", "gemini-key"),  # Gemini only  
            LLMConfig("groq-key", "gemini-key"),  # Both
            LLMConfig("groq-key", "gemini-key", timeout=10.0),  # Custom timeout
        ]
        
        for config in valid_configs:
            client = LLMClient(config)
            assert client.config == config
    
    @patch('google.genai.Client')
    def test_gemini_generation_config_variations(self, mock_client_class):
        """Test Gemini API with different generation configurations."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Test response"
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        # Test with different model configurations
        configs = [
            LLMConfig("", "test-key", gemini_model="gemini-2.0-flash-exp"),
            LLMConfig("", "test-key", gemini_model="gemini-1.5-pro", timeout=8.0),
        ]
        
        for config in configs:
            client = LLMClient(config)
            result = client._call_gemini("test prompt")
            
            assert result == "Test response"
            
            # Verify correct model was used in call
            call_kwargs = mock_client.models.generate_content.call_args[1]
            assert call_kwargs['model'] == config.gemini_model
    
    def test_template_fallback_comprehensive_scenarios(self):
        """Test template fallback with comprehensive weather scenarios."""
        config = LLMConfig("", "")  # No API keys to force template
        client = LLMClient(config)
        
        comprehensive_scenarios = [
            # Extreme cold
            {
                'location': 'Iqaluit, CA',
                'temp_max': -25.0,
                'temp_min': -35.0,
                'description': 'blizzard',
                'max_precipitation_prob': 0.95
            },
            # Extreme heat
            {
                'location': 'Phoenix, AZ', 
                'temp_max': 48.0,
                'temp_min': 35.0,
                'description': 'scorching sun',
                'max_precipitation_prob': 0.0
            },
            # Perfect weather
            {
                'location': 'San Diego, CA',
                'temp_max': 24.0,
                'temp_min': 18.0, 
                'description': 'partly cloudy',
                'max_precipitation_prob': 0.2
            },
            # Unpredictable weather
            {
                'location': 'London, UK',
                'temp_max': 15.0,
                'temp_min': 8.0,
                'description': 'changeable conditions', 
                'max_precipitation_prob': 0.5
            }
        ]
        
        for weather_data in comprehensive_scenarios:
            result = client._generate_template_fallback(weather_data)
            
            # Basic template structure
            assert "I'm unable to generate a personalized briefing today" in result
            assert weather_data['location'] in result
            assert "Have a great day!" in result
            
            # Weather-specific content
            assert str(int(weather_data['temp_max'])) in result
            assert weather_data['description'] in result
            
            # Precipitation-appropriate messaging
            if weather_data['max_precipitation_prob'] > 0.7:
                assert "umbrella" in result.lower()
            elif weather_data['max_precipitation_prob'] > 0.3:
                assert "possible" in result.lower()
    
    @responses.activate
    @patch('google.genai.Client')
    def test_performance_and_timeout_scenarios(self, mock_client_class):
        """Test performance characteristics and timeout handling."""
        # Test Groq timeout
        def slow_groq_response(request):
            time.sleep(7)  # Longer than timeout
            return (200, {}, json.dumps({"choices": [{"message": {"content": "Late response"}}]}))
        
        responses.add_callback(
            responses.POST,
            "https://api.groq.com/openai/v1/chat/completions", 
            callback=slow_groq_response
        )
        
        # Mock Gemini to succeed quickly
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Gemini fallback response"
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        config = LLMConfig("test-key", "test-key", timeout=3.0)  # Short timeout
        client = LLMClient(config)
        
        weather_data = {'location': 'Vancouver, CA', 'temp_max': 20, 'description': 'cloudy'}
        
        # Should fallback to Gemini due to Groq timeout
        result = client.generate_briefing("test prompt", weather_data)
        assert result == "Gemini fallback response"


if __name__ == "__main__":
    pytest.main([__file__])