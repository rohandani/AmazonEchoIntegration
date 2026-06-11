"""
Integration tests for Alexa request/response cycle in lambda_function.py

Tests the end-to-end flow of Alexa requests through the skill handlers
with mocked external dependencies.
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from ask_sdk_model import RequestEnvelope
from ask_sdk_model.launch_request import LaunchRequest
from ask_sdk_model.intent_request import IntentRequest
from ask_sdk_model.session_ended_request import SessionEndedRequest
from ask_sdk_model.intent import Intent
from ask_sdk_model.session import Session
from ask_sdk_model.context import Context

# Import the lambda handler and components
from lambda_function import lambda_handler
from weather_client import WeatherClientError


class TestLambdaIntegration:
    """Integration tests for Lambda function handlers."""
    
    def _extract_speech_text(self, response_data: dict) -> str:
        """
        Helper function to extract speech text from ASK SDK response.
        Handles both PlainText and SSML output formats.
        """
        output_speech = response_data.get("outputSpeech", {})
        if output_speech.get("type") == "SSML":
            # Extract text from SSML tags
            ssml = output_speech.get("ssml", "")
            # Remove <speak> tags
            import re
            text = re.sub(r'<[^>]+>', '', ssml)
            return text
        else:
            return output_speech.get("text", "")
    
    @pytest.fixture
    def mock_environment(self):
        """Mock environment variables for testing."""
        env_vars = {
            'OWM_API_KEY': 'test_owm_key',
            'GROQ_API_KEY': 'test_groq_key',
            'GEMINI_API_KEY': 'test_gemini_key',
            'USER_CITY': 'Vancouver,CA',
            'HAS_SCHOOL_KIDS': 'true'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            yield env_vars
    
    @pytest.fixture
    def sample_weather_data(self):
        """Sample normalized weather data for testing."""
        return {
            "temp_min": 8.5,
            "temp_max": 15.2,
            "description": "light rain",
            "max_precipitation_prob": 0.8,
            "wind_speed": 3.2,
            "humidity": 85,
            "location": "Vancouver, CA"
        }
    
    @pytest.fixture
    def sample_context_data(self):
        """Sample context data for testing."""
        return {
            "day_type": "weekday",
            "day_name": "Monday", 
            "occasion": "school day",
            "season": "fall",
            "location": "Vancouver, CA",
            "has_school_kids": True,
            "date_str": "Monday, October 06, 2026"
        }
    
    def create_alexa_request(self, request_type: str, intent_name: str = None) -> dict:
        """
        Create a mock Alexa request event for testing.
        
        Args:
            request_type: Type of request ("LaunchRequest", "IntentRequest", etc.)
            intent_name: Name of intent for IntentRequest types
            
        Returns:
            Dictionary representing Alexa request event
        """
        request_data = {
            "type": request_type,
            "requestId": "amzn1.echo-api.request.test-request-id",
            "timestamp": "2026-10-06T14:00:00Z",
            "locale": "en-US"
        }
        
        if request_type == "IntentRequest" and intent_name:
            request_data["intent"] = {
                "name": intent_name,
                "confirmationStatus": "NONE"
            }
        elif request_type == "SessionEndedRequest":
            request_data["reason"] = "USER_INITIATED"
        
        return {
            "version": "1.0",
            "session": {
                "new": True,
                "sessionId": "amzn1.echo-api.session.test-session-id",
                "application": {
                    "applicationId": "amzn1.ask.skill.test-skill-id"
                },
                "user": {
                    "userId": "amzn1.ask.account.test-user-id"
                }
            },
            "context": {
                "System": {
                    "application": {
                        "applicationId": "amzn1.ask.skill.test-skill-id"
                    },
                    "user": {
                        "userId": "amzn1.ask.account.test-user-id"
                    },
                    "device": {
                        "deviceId": "amzn1.ask.device.test-device-id",
                        "supportedInterfaces": {}
                    }
                }
            },
            "request": request_data
        }
    
    @patch('lambda_function.create_llm_client_from_environment')
    @patch('lambda_function.PromptEngine')
    @patch('lambda_function.ContextBuilder')
    @patch('lambda_function.WeatherClient')
    def test_launch_request_success(self, mock_weather_client, mock_context_builder,
                                  mock_prompt_engine, mock_llm_client, 
                                  mock_environment, sample_weather_data, sample_context_data):
        """Test successful LaunchRequest handling with full briefing generation."""
        
        # Setup mocks
        mock_weather_instance = Mock()
        mock_weather_instance.get_forecast.return_value = sample_weather_data
        mock_weather_client.return_value = mock_weather_instance
        
        mock_context_instance = Mock()
        mock_context_instance.build_context.return_value = sample_context_data
        mock_context_builder.return_value = mock_context_instance
        
        mock_prompt_instance = Mock()
        mock_prompt_instance.build_prompt.return_value = "Generated prompt"
        mock_prompt_instance.sanitize_output.return_value = "Today in Vancouver: 15 degrees with light rain expected. Bring an umbrella and dress warmly for school. The kids should wear waterproof jackets. Have a wonderful Monday!"
        mock_prompt_engine.return_value = mock_prompt_instance
        
        mock_llm_instance = Mock()
        mock_llm_instance.generate_briefing.return_value = "Raw LLM response"
        mock_llm_client.return_value = mock_llm_instance
        
        # Create launch request
        event = self.create_alexa_request("LaunchRequest")
        context = {}
        
        # Execute lambda handler
        response = lambda_handler(event, context)
        
        # Validate response structure
        assert response is not None
        assert "version" in response
        assert "response" in response
        
        response_data = response["response"]
        assert "outputSpeech" in response_data
        
        speech_text = self._extract_speech_text(response_data)
        assert "Today in Vancouver" in speech_text
        assert response_data["shouldEndSession"] is True
        
        # Validate card is present
        assert "card" in response_data
        assert response_data["card"]["type"] == "Simple"
        assert response_data["card"]["title"] == "Morning Weather Briefing"
        
        # Verify all components were called
        mock_weather_client.assert_called_once()
        mock_context_builder.assert_called_once()
        mock_prompt_engine.assert_called_once()
        mock_llm_client.assert_called_once()
    
    @patch('lambda_function.WeatherClient')
    def test_launch_request_weather_api_failure(self, mock_weather_client, mock_environment):
        """Test LaunchRequest handling when weather API fails."""
        
        # Setup weather client to fail
        mock_weather_instance = Mock()
        mock_weather_instance.get_forecast.side_effect = WeatherClientError("API failed")
        mock_weather_client.return_value = mock_weather_instance
        
        # Create launch request
        event = self.create_alexa_request("LaunchRequest")
        context = {}
        
        # Execute lambda handler
        response = lambda_handler(event, context)
        
        # Validate error response
        assert response is not None
        response_data = response["response"]
        
        speech_text = self._extract_speech_text(response_data)
        assert "couldn't get today's weather" in speech_text.lower()
        assert "have a great day" in speech_text.lower()
        assert response_data["shouldEndSession"] is True
    
    def test_missing_environment_variables(self):
        """Test lambda handler with missing required environment variables."""
        
        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            event = self.create_alexa_request("LaunchRequest")
            context = {}
            
            # Execute lambda handler
            response = lambda_handler(event, context)
            
            # Should get error response
            assert response is not None
            response_data = response["response"]
            
            speech_text = self._extract_speech_text(response_data)
            assert "couldn't get your weather briefing" in speech_text.lower()
            assert response_data["shouldEndSession"] is True
    
    def test_morning_briefing_intent_request(self, mock_environment):
        """Test MorningBriefingIntent request handling."""
        
        with patch('lambda_function.LaunchRequestHandler.handle') as mock_launch_handle:
            mock_launch_handle.return_value = Mock(response={"test": "response"})
            
            # Create intent request
            event = self.create_alexa_request("IntentRequest", "MorningBriefingIntent")
            context = {}
            
            # Execute lambda handler
            response = lambda_handler(event, context)
            
            # Should delegate to launch handler
            assert response is not None
    
    def test_help_intent_request(self, mock_environment):
        """Test AMAZON.HelpIntent request handling."""
        
        # Create help intent request
        event = self.create_alexa_request("IntentRequest", "AMAZON.HelpIntent")
        context = {}
        
        # Execute lambda handler
        response = lambda_handler(event, context)
        
        # Validate help response
        assert response is not None
        response_data = response["response"]
        
        speech_text = self._extract_speech_text(response_data)
        assert "morning briefing provides daily weather" in speech_text.lower()
        assert "what should i wear today" in speech_text.lower()
        
        # Should not end session (allows follow-up)
        assert response_data.get("shouldEndSession", False) is False
        
        # Should have reprompt
        assert "reprompt" in response_data
    
    def test_cancel_intent_request(self, mock_environment):
        """Test AMAZON.CancelIntent request handling."""
        
        # Create cancel intent request
        event = self.create_alexa_request("IntentRequest", "AMAZON.CancelIntent")
        context = {}
        
        # Execute lambda handler
        response = lambda_handler(event, context)
        
        # Validate cancel response
        assert response is not None
        response_data = response["response"]
        
        speech_text = self._extract_speech_text(response_data)
        assert "have a great day" in speech_text.lower()
        assert response_data["shouldEndSession"] is True
    
    def test_stop_intent_request(self, mock_environment):
        """Test AMAZON.StopIntent request handling."""
        
        # Create stop intent request
        event = self.create_alexa_request("IntentRequest", "AMAZON.StopIntent")
        context = {}
        
        # Execute lambda handler
        response = lambda_handler(event, context)
        
        # Validate stop response
        assert response is not None
        response_data = response["response"]
        
        speech_text = self._extract_speech_text(response_data)
        assert "have a great day" in speech_text.lower()
        assert response_data["shouldEndSession"] is True
    
    def test_session_ended_request(self, mock_environment):
        """Test SessionEndedRequest handling."""
        
        # Create session ended request
        event = self.create_alexa_request("SessionEndedRequest")
        context = {}
        
        # Execute lambda handler
        response = lambda_handler(event, context)
        
        # Validate session end response (should be minimal)
        assert response is not None
        response_data = response["response"]
        
        # Session end responses typically don't have speech output
        assert "outputSpeech" not in response_data or not response_data.get("outputSpeech")
    
    def test_unhandled_exception_recovery(self, mock_environment):
        """Test that unhandled exceptions are caught and return friendly error."""
        
        with patch('lambda_function.LaunchRequestHandler._get_morning_briefing') as mock_briefing:
            # Force an unhandled exception
            mock_briefing.side_effect = Exception("Unexpected error")
            
            # Create launch request
            event = self.create_alexa_request("LaunchRequest")
            context = {}
            
            # Execute lambda handler
            response = lambda_handler(event, context)
            
            # Should get friendly error response
            assert response is not None
            response_data = response["response"]
            
            speech_text = self._extract_speech_text(response_data)
            assert "having trouble right now" in speech_text.lower()
            assert response_data["shouldEndSession"] is True
    
    def test_request_logging_interceptor(self, mock_environment):
        """Test that request logging interceptor logs correctly."""
        
        with patch('lambda_function.logger') as mock_logger:
            # Create launch request
            event = self.create_alexa_request("LaunchRequest") 
            context = {}
            
            # Execute lambda handler (will fail due to missing mocks, but logging should work)
            try:
                lambda_handler(event, context)
            except:
                pass  # Ignore other errors, we're testing logging
            
            # Verify logging occurred
            mock_logger.info.assert_any_call("Incoming request: LaunchRequest")