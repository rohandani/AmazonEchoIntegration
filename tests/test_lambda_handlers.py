"""
Unit tests for individual Alexa request handlers in lambda_function.py

Tests each handler class individually with mocked dependencies.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import RequestEnvelope
from ask_sdk_model.launch_request import LaunchRequest
from ask_sdk_model.intent_request import IntentRequest
from ask_sdk_model.session_ended_request import SessionEndedRequest
from ask_sdk_model.intent import Intent
from ask_sdk_model.session import Session
from ask_sdk_model.context import Context

# Import handlers to test
from lambda_function import (
    LaunchRequestHandler, 
    MorningBriefingIntentHandler,
    HelpIntentHandler,
    CancelAndStopIntentHandler,
    SessionEndedRequestHandler,
    CatchAllExceptionHandler,
    RequestLoggingInterceptor
)
from weather_client import WeatherClientError


class TestLaunchRequestHandler:
    """Test LaunchRequestHandler class."""
    
    @pytest.fixture
    def handler(self):
        """Create LaunchRequestHandler instance."""
        return LaunchRequestHandler()
    
    @pytest.fixture
    def mock_handler_input(self):
        """Create mock HandlerInput for LaunchRequest."""
        mock_input = Mock(spec=HandlerInput)
        mock_input.request_envelope = Mock(spec=RequestEnvelope)
        mock_input.request_envelope.request = Mock(spec=LaunchRequest)
        mock_input.request_envelope.request.object_type = "LaunchRequest"
        
        # Mock response builder
        mock_response_builder = Mock()
        mock_response_builder.speak.return_value = mock_response_builder
        mock_response_builder.set_card.return_value = mock_response_builder
        mock_response_builder.set_should_end_session.return_value = mock_response_builder
        mock_response_builder.response = {"test": "response"}
        mock_input.response_builder = mock_response_builder
        
        return mock_input
    
    def test_can_handle_launch_request(self, handler, mock_handler_input):
        """Test that handler can handle LaunchRequest."""
        assert handler.can_handle(mock_handler_input) is True
    
    def test_can_handle_non_launch_request(self, handler):
        """Test that handler rejects non-LaunchRequest."""
        mock_input = Mock(spec=HandlerInput)
        mock_input.request_envelope = Mock(spec=RequestEnvelope)
        mock_input.request_envelope.request = Mock(spec=IntentRequest)
        mock_input.request_envelope.request.object_type = "IntentRequest"
        
        assert handler.can_handle(mock_input) is False
    
    @patch.dict(os.environ, {
        'OWM_API_KEY': 'test_key',
        'GROQ_API_KEY': 'test_groq',
        'USER_CITY': 'TestCity,CA',
        'HAS_SCHOOL_KIDS': 'false'
    })
    @patch('lambda_function.create_llm_client_from_environment')
    @patch('lambda_function.PromptEngine')
    @patch('lambda_function.ContextBuilder')
    @patch('lambda_function.WeatherClient')
    def test_handle_success(self, mock_weather_client, mock_context_builder,
                           mock_prompt_engine, mock_llm_client,
                           handler, mock_handler_input):
        """Test successful handling of LaunchRequest."""
        
        # Setup mocks
        weather_data = {"temp_max": 20, "location": "TestCity, CA", "description": "sunny"}
        context_data = {"day_name": "Monday", "occasion": "work day", "season": "summer"}
        
        mock_weather_instance = Mock()
        mock_weather_instance.get_forecast.return_value = weather_data
        mock_weather_client.return_value = mock_weather_instance
        
        mock_context_instance = Mock()
        mock_context_instance.build_context.return_value = context_data
        mock_context_builder.return_value = mock_context_instance
        
        mock_prompt_instance = Mock()
        mock_prompt_instance.build_prompt.return_value = "test prompt"
        mock_prompt_instance.sanitize_output.return_value = "Clean briefing text"
        mock_prompt_engine.return_value = mock_prompt_instance
        
        mock_llm_instance = Mock()
        mock_llm_instance.generate_briefing.return_value = "Raw briefing"
        mock_llm_client.return_value = mock_llm_instance
        
        # Execute handler
        response = handler.handle(mock_handler_input)
        
        # Verify response builder was called correctly
        mock_handler_input.response_builder.speak.assert_called_once_with("Clean briefing text")
        mock_handler_input.response_builder.set_should_end_session.assert_called_once_with(True)
        
        # Verify components were initialized and called
        mock_weather_client.assert_called_once_with('test_key', 'TestCity,CA')
        mock_weather_instance.get_forecast.assert_called_once()
        mock_context_instance.build_context.assert_called_once()
        mock_llm_instance.generate_briefing.assert_called_once()
    
    @patch.dict(os.environ, {
        'OWM_API_KEY': 'test_key',
        'USER_CITY': 'TestCity,CA'
    })
    @patch('lambda_function.WeatherClient')
    def test_handle_weather_error(self, mock_weather_client, handler, mock_handler_input):
        """Test handling when weather API fails."""
        
        # Setup weather client to fail
        mock_weather_instance = Mock()
        mock_weather_instance.get_forecast.side_effect = WeatherClientError("API failed")
        mock_weather_client.return_value = mock_weather_instance
        
        # Execute handler
        response = handler.handle(mock_handler_input)
        
        # Should get weather error message
        call_args = mock_handler_input.response_builder.speak.call_args[0]
        assert "couldn't get today's weather" in call_args[0].lower()
    
    def test_handle_missing_env_vars(self, handler, mock_handler_input):
        """Test handling when environment variables are missing."""
        
        # Clear environment
        with patch.dict(os.environ, {}, clear=True):
            response = handler.handle(mock_handler_input)
            
            # Should get error response
            call_args = mock_handler_input.response_builder.speak.call_args[0]
            assert "couldn't get your weather briefing" in call_args[0].lower()


class TestMorningBriefingIntentHandler:
    """Test MorningBriefingIntentHandler class."""
    
    @pytest.fixture
    def handler(self):
        """Create MorningBriefingIntentHandler instance."""
        return MorningBriefingIntentHandler()
    
    def test_can_handle_morning_briefing_intent(self, handler):
        """Test that handler can handle MorningBriefingIntent."""
        mock_input = Mock(spec=HandlerInput)
        mock_input.request_envelope = Mock(spec=RequestEnvelope)
        mock_input.request_envelope.request = Mock(spec=IntentRequest)
        mock_input.request_envelope.request.intent = Mock(spec=Intent)
        mock_input.request_envelope.request.intent.name = "MorningBriefingIntent"
        
        assert handler.can_handle(mock_input) is True
    
    def test_can_handle_other_intent(self, handler):
        """Test that handler rejects other intents."""
        mock_input = Mock(spec=HandlerInput)
        mock_input.request_envelope = Mock(spec=RequestEnvelope)
        mock_input.request_envelope.request = Mock(spec=IntentRequest)
        mock_input.request_envelope.request.intent = Mock(spec=Intent)
        mock_input.request_envelope.request.intent.name = "AMAZON.HelpIntent"
        
        assert handler.can_handle(mock_input) is False
    
    @patch('lambda_function.LaunchRequestHandler.handle')
    def test_handle_delegates_to_launch(self, mock_launch_handle, handler):
        """Test that MorningBriefingIntent delegates to LaunchRequestHandler."""
        mock_input = Mock()
        expected_response = {"test": "response"}
        mock_launch_handle.return_value = expected_response
        
        result = handler.handle(mock_input)
        
        assert result == expected_response
        mock_launch_handle.assert_called_once_with(mock_input)


class TestHelpIntentHandler:
    """Test HelpIntentHandler class."""
    
    @pytest.fixture
    def handler(self):
        """Create HelpIntentHandler instance."""
        return HelpIntentHandler()
    
    @pytest.fixture
    def mock_handler_input(self):
        """Create mock HandlerInput for HelpIntent."""
        mock_input = Mock(spec=HandlerInput)
        mock_input.request_envelope = Mock(spec=RequestEnvelope)
        mock_input.request_envelope.request = Mock(spec=IntentRequest)
        mock_input.request_envelope.request.intent = Mock(spec=Intent)
        mock_input.request_envelope.request.intent.name = "AMAZON.HelpIntent"
        
        # Mock response builder
        mock_response_builder = Mock()
        mock_response_builder.speak.return_value = mock_response_builder
        mock_response_builder.ask.return_value = mock_response_builder
        mock_response_builder.set_card.return_value = mock_response_builder
        mock_response_builder.response = {"test": "response"}
        mock_input.response_builder = mock_response_builder
        
        return mock_input
    
    def test_can_handle_help_intent(self, handler, mock_handler_input):
        """Test that handler can handle AMAZON.HelpIntent."""
        assert handler.can_handle(mock_handler_input) is True
    
    def test_handle_provides_help_text(self, handler, mock_handler_input):
        """Test that help handler provides usage instructions."""
        response = handler.handle(mock_handler_input)
        
        # Check that speak was called with help text
        speak_call_args = mock_handler_input.response_builder.speak.call_args[0][0]
        assert "morning briefing provides daily weather" in speak_call_args.lower()
        assert "what should i wear today" in speak_call_args.lower()
        assert "7 am" in speak_call_args.lower()
        
        # Check that reprompt was set
        mock_handler_input.response_builder.ask.assert_called_once()
        
        # Check card was set
        mock_handler_input.response_builder.set_card.assert_called_once()


class TestCancelAndStopIntentHandler:
    """Test CancelAndStopIntentHandler class."""
    
    @pytest.fixture
    def handler(self):
        """Create CancelAndStopIntentHandler instance."""
        return CancelAndStopIntentHandler()
    
    @pytest.fixture
    def mock_handler_input(self):
        """Create mock HandlerInput."""
        mock_input = Mock(spec=HandlerInput)
        mock_input.request_envelope = Mock(spec=RequestEnvelope)
        mock_input.request_envelope.request = Mock(spec=IntentRequest)
        mock_input.request_envelope.request.intent = Mock(spec=Intent)
        
        # Mock response builder
        mock_response_builder = Mock()
        mock_response_builder.speak.return_value = mock_response_builder
        mock_response_builder.set_should_end_session.return_value = mock_response_builder
        mock_response_builder.response = {"test": "response"}
        mock_input.response_builder = mock_response_builder
        
        return mock_input
    
    def test_can_handle_cancel_intent(self, handler, mock_handler_input):
        """Test that handler can handle AMAZON.CancelIntent."""
        mock_handler_input.request_envelope.request.intent.name = "AMAZON.CancelIntent"
        assert handler.can_handle(mock_handler_input) is True
    
    def test_can_handle_stop_intent(self, handler, mock_handler_input):
        """Test that handler can handle AMAZON.StopIntent."""
        mock_handler_input.request_envelope.request.intent.name = "AMAZON.StopIntent"
        assert handler.can_handle(mock_handler_input) is True
    
    def test_can_handle_other_intent(self, handler, mock_handler_input):
        """Test that handler rejects other intents."""
        mock_handler_input.request_envelope.request.intent.name = "AMAZON.HelpIntent"
        assert handler.can_handle(mock_handler_input) is False
    
    def test_handle_ends_session(self, handler, mock_handler_input):
        """Test that cancel/stop handler ends the session."""
        mock_handler_input.request_envelope.request.intent.name = "AMAZON.CancelIntent"
        
        response = handler.handle(mock_handler_input)
        
        # Should speak goodbye message
        speak_call_args = mock_handler_input.response_builder.speak.call_args[0][0]
        assert "have a great day" in speak_call_args.lower()
        
        # Should end session
        mock_handler_input.response_builder.set_should_end_session.assert_called_once_with(True)


class TestSessionEndedRequestHandler:
    """Test SessionEndedRequestHandler class."""
    
    @pytest.fixture
    def handler(self):
        """Create SessionEndedRequestHandler instance."""
        return SessionEndedRequestHandler()
    
    @pytest.fixture
    def mock_handler_input(self):
        """Create mock HandlerInput for SessionEndedRequest."""
        mock_input = Mock(spec=HandlerInput)
        mock_input.request_envelope = Mock(spec=RequestEnvelope)
        mock_input.request_envelope.request = Mock(spec=SessionEndedRequest)
        mock_input.request_envelope.request.object_type = "SessionEndedRequest"
        mock_input.request_envelope.request.reason = "USER_INITIATED"
        
        # Mock response builder
        mock_response_builder = Mock()
        mock_response_builder.response = {"test": "response"}
        mock_input.response_builder = mock_response_builder
        
        return mock_input
    
    def test_can_handle_session_ended_request(self, handler, mock_handler_input):
        """Test that handler can handle SessionEndedRequest."""
        assert handler.can_handle(mock_handler_input) is True
    
    def test_can_handle_other_request(self, handler):
        """Test that handler rejects other request types."""
        mock_input = Mock(spec=HandlerInput)
        mock_input.request_envelope = Mock(spec=RequestEnvelope)
        mock_input.request_envelope.request = Mock(spec=LaunchRequest)
        mock_input.request_envelope.request.object_type = "LaunchRequest"
        
        assert handler.can_handle(mock_input) is False
    
    def test_handle_logs_session_end(self, handler, mock_handler_input):
        """Test that session end handler logs the reason."""
        with patch('lambda_function.logger') as mock_logger:
            response = handler.handle(mock_handler_input)
            
            # Should log the session end reason
            mock_logger.info.assert_called_with("Session ended with reason: USER_INITIATED")


class TestCatchAllExceptionHandler:
    """Test CatchAllExceptionHandler class."""
    
    @pytest.fixture
    def handler(self):
        """Create CatchAllExceptionHandler instance."""
        return CatchAllExceptionHandler()
    
    @pytest.fixture
    def mock_handler_input(self):
        """Create mock HandlerInput."""
        mock_input = Mock(spec=HandlerInput)
        
        # Mock response builder
        mock_response_builder = Mock()
        mock_response_builder.speak.return_value = mock_response_builder
        mock_response_builder.set_card.return_value = mock_response_builder
        mock_response_builder.set_should_end_session.return_value = mock_response_builder
        mock_response_builder.response = {"test": "response"}
        mock_input.response_builder = mock_response_builder
        
        return mock_input
    
    def test_can_handle_any_exception(self, handler, mock_handler_input):
        """Test that handler can handle any exception."""
        test_exception = Exception("Test error")
        assert handler.can_handle(mock_handler_input, test_exception) is True
        
        # Test with different exception types
        assert handler.can_handle(mock_handler_input, ValueError("Test")) is True
        assert handler.can_handle(mock_handler_input, KeyError("Test")) is True
    
    def test_handle_provides_friendly_error(self, handler, mock_handler_input):
        """Test that exception handler provides friendly error message."""
        test_exception = Exception("Something went wrong")
        
        with patch('lambda_function.logger') as mock_logger:
            response = handler.handle(mock_handler_input, test_exception)
            
            # Should log the error
            mock_logger.error.assert_called()
            
            # Should speak friendly error message
            speak_call_args = mock_handler_input.response_builder.speak.call_args[0][0]
            assert "having trouble right now" in speak_call_args.lower()
            assert "try your morning briefing again" in speak_call_args.lower()
            
            # Should end session
            mock_handler_input.response_builder.set_should_end_session.assert_called_once_with(True)


class TestRequestLoggingInterceptor:
    """Test RequestLoggingInterceptor class."""
    
    @pytest.fixture
    def interceptor(self):
        """Create RequestLoggingInterceptor instance."""
        return RequestLoggingInterceptor()
    
    def test_logs_launch_request(self, interceptor):
        """Test that interceptor logs LaunchRequest."""
        mock_input = Mock(spec=HandlerInput)
        mock_input.request_envelope = Mock(spec=RequestEnvelope)
        mock_input.request_envelope.request = Mock(spec=LaunchRequest)
        mock_input.request_envelope.request.object_type = "LaunchRequest"
        
        with patch('lambda_function.logger') as mock_logger:
            interceptor.process(mock_input)
            
            mock_logger.info.assert_called_with("Incoming request: LaunchRequest")
    
    def test_logs_intent_request_with_intent_name(self, interceptor):
        """Test that interceptor logs IntentRequest with intent name."""
        mock_input = Mock(spec=HandlerInput)
        mock_input.request_envelope = Mock(spec=RequestEnvelope)
        mock_input.request_envelope.request = Mock(spec=IntentRequest)
        mock_input.request_envelope.request.object_type = "IntentRequest"
        mock_input.request_envelope.request.intent = Mock(spec=Intent)
        mock_input.request_envelope.request.intent.name = "AMAZON.HelpIntent"
        
        with patch('lambda_function.logger') as mock_logger:
            interceptor.process(mock_input)
            
            # Should log both request type and intent name
            mock_logger.info.assert_any_call("Incoming request: IntentRequest")
            mock_logger.info.assert_any_call("Intent: AMAZON.HelpIntent")