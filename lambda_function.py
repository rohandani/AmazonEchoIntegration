"""
Main Lambda function entry point for Alexa Morning Briefing Skill.

This module implements the ASK SDK request handlers for the Alexa Morning Briefing Skill,
including launch requests, morning briefing intent handling, help functionality, and
session management.
"""

import logging
import os
import traceback
from typing import Optional, Dict, Any

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractExceptionHandler, AbstractRequestInterceptor
)
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard

# Import our custom modules
from weather_client import WeatherClient, WeatherClientError
from context_builder import ContextBuilder
from llm_client import create_llm_client_from_environment
from prompt_engine import PromptEngine

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Alexa skill launch requests - 'Alexa, open Morning Briefing'."""
    
    def can_handle(self, handler_input: HandlerInput) -> bool:
        """Check if this handler can handle the request."""
        return is_request_type("LaunchRequest")(handler_input)
    
    def handle(self, handler_input: HandlerInput) -> Response:
        """Handle the launch request by providing morning briefing."""
        logger.info("LaunchRequest received - executing morning briefing")
        
        try:
            # Get the morning briefing using core orchestration logic
            briefing_text = self._get_morning_briefing()
            
            speech_text = briefing_text
            card_title = "Morning Weather Briefing"
            card_content = briefing_text
            
            return (handler_input.response_builder
                    .speak(speech_text)
                    .set_card(SimpleCard(card_title, card_content))
                    .set_should_end_session(True)  # End session after briefing
                    .response)
                    
        except Exception as e:
            logger.error(f"Error in LaunchRequestHandler: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Provide friendly error response
            error_text = ("I'm sorry, I couldn't get your weather briefing right now. "
                         "Please try again later. Have a great day!")
            
            return (handler_input.response_builder
                    .speak(error_text)
                    .set_card(SimpleCard("Morning Briefing - Error", error_text))
                    .set_should_end_session(True)
                    .response)
    
    def _get_morning_briefing(self) -> str:
        """
        Core orchestration logic for generating morning briefing.
        
        Integrates weather data, context building, prompt engineering, and LLM generation
        with proper error handling and fallback mechanisms as per requirements.
        
        Returns:
            Generated briefing text ready for voice output
            
        Raises:
            Exception: For various system errors (handled by caller)
        """
        # Load configuration from environment
        config = self._load_configuration()
        
        # Initialize components
        weather_client = WeatherClient(config['owm_api_key'], config['user_city'])
        context_builder = ContextBuilder()
        prompt_engine = PromptEngine()
        llm_client = create_llm_client_from_environment()
        
        # Fetch weather data
        try:
            weather_data = weather_client.get_forecast()
            logger.info(f"Weather data fetched for {weather_data['location']}")
        except WeatherClientError as e:
            logger.error(f"Weather API failed: {str(e)}")
            # Return friendly error message as per requirement 4.4
            return "I couldn't get today's weather. Have a great day!"
        
        # Build context
        user_preferences = {
            'location': config['user_city'],
            'has_school_kids': config['has_school_kids']
        }
        context_data = context_builder.build_context(user_preferences)
        logger.info(f"Context built for {context_data['occasion']} on {context_data['day_name']}")
        
        # Generate prompt
        prompt = prompt_engine.build_prompt(weather_data, context_data)
        logger.debug("Prompt generated for LLM")
        
        # Generate briefing using LLM with fallback chain
        raw_briefing = llm_client.generate_briefing(prompt, weather_data)
        
        # Sanitize output for Alexa SSML compatibility
        sanitized_briefing = prompt_engine.sanitize_output(raw_briefing)
        
        logger.info(f"Morning briefing generated successfully ({len(sanitized_briefing)} chars)")
        return sanitized_briefing
    
    def _load_configuration(self) -> Dict[str, Any]:
        """
        Load configuration from Lambda environment variables.
        
        Returns:
            Dictionary containing all required configuration values
            
        Raises:
            ValueError: If required environment variables are missing
        """
        config = {}
        
        # Required API keys
        config['owm_api_key'] = os.environ.get('OWM_API_KEY')
        if not config['owm_api_key']:
            raise ValueError("OWM_API_KEY environment variable is required")
        
        # At least one LLM API key must be present (validated in llm_client)
        groq_key = os.environ.get('GROQ_API_KEY')
        gemini_key = os.environ.get('GEMINI_API_KEY')
        if not groq_key and not gemini_key:
            raise ValueError("At least one of GROQ_API_KEY or GEMINI_API_KEY is required")
        
        # User configuration
        config['user_city'] = os.environ.get('USER_CITY')
        if not config['user_city']:
            raise ValueError("USER_CITY environment variable is required")
        
        # Optional configuration with defaults
        config['has_school_kids'] = os.environ.get('HAS_SCHOOL_KIDS', 'false').lower() == 'true'
        
        return config


class MorningBriefingIntentHandler(AbstractRequestHandler):
    """Handler for explicit MorningBriefingIntent requests."""
    
    def can_handle(self, handler_input: HandlerInput) -> bool:
        """Check if this handler can handle the request."""
        return is_intent_name("MorningBriefingIntent")(handler_input)
    
    def handle(self, handler_input: HandlerInput) -> Response:
        """Handle the MorningBriefingIntent by delegating to launch logic."""
        logger.info("MorningBriefingIntent received")
        
        # Reuse the launch request handler logic for consistency
        launch_handler = LaunchRequestHandler()
        return launch_handler.handle(handler_input)


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for AMAZON.HelpIntent - provides usage instructions."""
    
    def can_handle(self, handler_input: HandlerInput) -> bool:
        """Check if this handler can handle the request."""
        return is_intent_name("AMAZON.HelpIntent")(handler_input)
    
    def handle(self, handler_input: HandlerInput) -> Response:
        """Handle help requests by providing usage guidance."""
        logger.info("HelpIntent received")
        
        speech_text = ("Morning Briefing provides daily weather updates. "
                      "Say 'Alexa, open Morning Briefing' to get today's weather, "
                      "or ask 'what should I wear today' for clothing recommendations. "
                      "You can also set up a daily routine at 7 AM. "
                      "What would you like to know?")
        
        reprompt_text = "How can I help you with your morning briefing?"
        
        return (handler_input.response_builder
                .speak(speech_text)
                .ask(reprompt_text)
                .set_card(SimpleCard("Morning Briefing Help", speech_text))
                .response)


class CancelAndStopIntentHandler(AbstractRequestHandler):
    """Handler for AMAZON.CancelIntent and AMAZON.StopIntent - session termination."""
    
    def can_handle(self, handler_input: HandlerInput) -> bool:
        """Check if this handler can handle the request."""
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))
    
    def handle(self, handler_input: HandlerInput) -> Response:
        """Handle cancel/stop requests by ending the session cleanly."""
        intent_name = handler_input.request_envelope.request.intent.name
        logger.info(f"{intent_name} received")
        
        speech_text = "Have a great day!"
        
        return (handler_input.response_builder
                .speak(speech_text)
                .set_should_end_session(True)
                .response)


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for SessionEndedRequest - cleanup operations."""
    
    def can_handle(self, handler_input: HandlerInput) -> bool:
        """Check if this handler can handle the request."""
        return is_request_type("SessionEndedRequest")(handler_input)
    
    def handle(self, handler_input: HandlerInput) -> Response:
        """Handle session end requests with cleanup logging."""
        reason = handler_input.request_envelope.request.reason
        logger.info(f"Session ended with reason: {reason}")
        
        # No speech output needed for session end
        return handler_input.response_builder.response


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Catch all exception handler to prevent skill crashes."""
    
    def can_handle(self, handler_input: HandlerInput, exception: Exception) -> bool:
        """This handler can handle all exceptions."""
        return True
    
    def handle(self, handler_input: HandlerInput, exception: Exception) -> Response:
        """Handle all unhandled exceptions gracefully."""
        logger.error(f"Unhandled exception: {str(exception)}")
        logger.error(traceback.format_exc())
        
        speech_text = ("Sorry, I'm having trouble right now. "
                      "Please try your morning briefing again later.")
        
        return (handler_input.response_builder
                .speak(speech_text)
                .set_card(SimpleCard("Morning Briefing - Error", speech_text))
                .set_should_end_session(True)
                .response)


class RequestLoggingInterceptor(AbstractRequestInterceptor):
    """Log all incoming requests for debugging."""
    
    def process(self, handler_input: HandlerInput) -> None:
        """Log request details."""
        request_type = handler_input.request_envelope.request.object_type
        logger.info(f"Incoming request: {request_type}")
        
        # Log intent name for intent requests
        if hasattr(handler_input.request_envelope.request, 'intent'):
            intent_name = handler_input.request_envelope.request.intent.name
            logger.info(f"Intent: {intent_name}")


# Initialize skill builder and register handlers
sb = SkillBuilder()

# Register request handlers
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(MorningBriefingIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelAndStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

# Register exception handlers
sb.add_exception_handler(CatchAllExceptionHandler())

# Register request interceptors
sb.add_global_request_interceptor(RequestLoggingInterceptor())

# Lambda handler entry point
lambda_handler = sb.lambda_handler()