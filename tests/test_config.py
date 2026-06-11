"""
Unit tests for configuration management module.

Tests the SkillConfig class for proper environment variable loading,
validation, and error handling scenarios.
"""

import os
import pytest
from unittest.mock import patch

from config import SkillConfig, ConfigurationError, load_config


class TestSkillConfig:
    """Test cases for SkillConfig class."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Clear any existing environment variables
        env_vars = [
            'OWM_API_KEY', 'GROQ_API_KEY', 'GEMINI_API_KEY', 
            'USER_CITY', 'HAS_SCHOOL_KIDS'
        ]
        for var in env_vars:
            if var in os.environ:
                del os.environ[var]
    
    def test_from_environment_success(self):
        """Test successful configuration loading from environment variables."""
        # Set up valid environment variables
        test_env = {
            'OWM_API_KEY': 'test_owm_key_1234567890',
            'GROQ_API_KEY': 'test_groq_key_1234567890',
            'GEMINI_API_KEY': 'test_gemini_key_1234567890',
            'USER_CITY': 'Vancouver,CA',
            'HAS_SCHOOL_KIDS': 'true'
        }
        
        with patch.dict(os.environ, test_env):
            config = SkillConfig.from_environment()
            
            assert config.owm_api_key == 'test_owm_key_1234567890'
            assert config.groq_api_key == 'test_groq_key_1234567890'
            assert config.gemini_api_key == 'test_gemini_key_1234567890'
            assert config.user_city == 'Vancouver,CA'
            assert config.has_school_kids is True
    
    def test_from_environment_has_school_kids_false(self):
        """Test HAS_SCHOOL_KIDS parsing for false values."""
        test_env = {
            'OWM_API_KEY': 'test_owm_key_1234567890',
            'GROQ_API_KEY': 'test_groq_key_1234567890',
            'GEMINI_API_KEY': 'test_gemini_key_1234567890',
            'USER_CITY': 'Toronto,CA',
            'HAS_SCHOOL_KIDS': 'false'
        }
        
        with patch.dict(os.environ, test_env):
            config = SkillConfig.from_environment()
            assert config.has_school_kids is False
    
    def test_from_environment_has_school_kids_default(self):
        """Test HAS_SCHOOL_KIDS defaults to false when not set."""
        test_env = {
            'OWM_API_KEY': 'test_owm_key_1234567890',
            'GROQ_API_KEY': 'test_groq_key_1234567890',
            'GEMINI_API_KEY': 'test_gemini_key_1234567890',
            'USER_CITY': 'Seattle,US'
        }
        
        with patch.dict(os.environ, test_env):
            config = SkillConfig.from_environment()
            assert config.has_school_kids is False
    
    def test_from_environment_has_school_kids_variations(self):
        """Test different true/false variations for HAS_SCHOOL_KIDS."""
        true_values = ['true', 'TRUE', '1', 'yes', 'YES', 'on', 'ON']
        false_values = ['false', 'FALSE', '0', 'no', 'NO', 'off', 'OFF', 'random']
        
        base_env = {
            'OWM_API_KEY': 'test_owm_key_1234567890',
            'GROQ_API_KEY': 'test_groq_key_1234567890',
            'GEMINI_API_KEY': 'test_gemini_key_1234567890',
            'USER_CITY': 'Portland,US'
        }
        
        # Test true values
        for value in true_values:
            test_env = {**base_env, 'HAS_SCHOOL_KIDS': value}
            with patch.dict(os.environ, test_env):
                config = SkillConfig.from_environment()
                assert config.has_school_kids is True, f"Value '{value}' should be True"
        
        # Test false values
        for value in false_values:
            test_env = {**base_env, 'HAS_SCHOOL_KIDS': value}
            with patch.dict(os.environ, test_env):
                config = SkillConfig.from_environment()
                assert config.has_school_kids is False, f"Value '{value}' should be False"
    
    def test_from_environment_missing_owm_api_key(self):
        """Test error when OWM_API_KEY is missing."""
        test_env = {
            'GROQ_API_KEY': 'test_groq_key_1234567890',
            'GEMINI_API_KEY': 'test_gemini_key_1234567890',
            'USER_CITY': 'Vancouver,CA'
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                SkillConfig.from_environment()
            assert 'OWM_API_KEY' in str(exc_info.value)
    
    def test_from_environment_missing_multiple_keys(self):
        """Test error when multiple API keys are missing."""
        test_env = {
            'USER_CITY': 'Vancouver,CA'
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                SkillConfig.from_environment()
            error_message = str(exc_info.value)
            assert 'OWM_API_KEY' in error_message
            assert 'At least one of GROQ_API_KEY or GEMINI_API_KEY' in error_message
    
    def test_from_environment_only_groq_key(self):
        """Test successful loading with only Groq API key."""
        test_env = {
            'OWM_API_KEY': 'test_owm_key_1234567890',
            'GROQ_API_KEY': 'test_groq_key_1234567890',
            'USER_CITY': 'Vancouver,CA'
        }
        
        with patch.dict(os.environ, test_env):
            config = SkillConfig.from_environment()
            assert config.groq_api_key == 'test_groq_key_1234567890'
            assert config.gemini_api_key == ''
    
    def test_from_environment_only_gemini_key(self):
        """Test successful loading with only Gemini API key."""
        test_env = {
            'OWM_API_KEY': 'test_owm_key_1234567890',
            'GEMINI_API_KEY': 'test_gemini_key_1234567890',
            'USER_CITY': 'Vancouver,CA'
        }
        
        with patch.dict(os.environ, test_env):
            config = SkillConfig.from_environment()
            assert config.groq_api_key == ''
            assert config.gemini_api_key == 'test_gemini_key_1234567890'
    
    def test_from_environment_missing_user_city(self):
        """Test error when USER_CITY is missing."""
        test_env = {
            'OWM_API_KEY': 'test_owm_key_1234567890',
            'GROQ_API_KEY': 'test_groq_key_1234567890',
            'GEMINI_API_KEY': 'test_gemini_key_1234567890'
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                SkillConfig.from_environment()
            assert 'USER_CITY' in str(exc_info.value)
    
    def test_from_environment_short_api_keys(self):
        """Test validation of API key lengths."""
        # Test short weather API key
        test_env = {
            'OWM_API_KEY': 'short',
            'GROQ_API_KEY': 'test_groq_key_1234567890',
            'USER_CITY': 'Vancouver,CA'
        }
        
        with patch.dict(os.environ, test_env):
            with pytest.raises(ValueError) as exc_info:
                SkillConfig.from_environment()
            assert 'OWM_API_KEY' in str(exc_info.value)
            assert 'invalid' in str(exc_info.value).lower()
        
        # Test short Groq API key when present
        test_env = {
            'OWM_API_KEY': 'test_owm_key_1234567890',
            'GROQ_API_KEY': 'tiny',
            'USER_CITY': 'Vancouver,CA'
        }
        
        with patch.dict(os.environ, test_env):
            with pytest.raises(ValueError) as exc_info:
                SkillConfig.from_environment()
            assert 'GROQ_API_KEY' in str(exc_info.value)
            assert 'invalid' in str(exc_info.value).lower()
        
        # Test short Gemini API key when present
        test_env = {
            'OWM_API_KEY': 'test_owm_key_1234567890',
            'GEMINI_API_KEY': '123',
            'USER_CITY': 'Vancouver,CA'
        }
        
        with patch.dict(os.environ, test_env):
            with pytest.raises(ValueError) as exc_info:
                SkillConfig.from_environment()
            assert 'GEMINI_API_KEY' in str(exc_info.value)
            assert 'invalid' in str(exc_info.value).lower()
    
    def test_from_environment_invalid_city_format(self):
        """Test validation of USER_CITY format."""
        invalid_cities = [
            'Vancouver',  # No comma
            'Vancouver,',  # No country code
            ',CA',  # No city
            'Vancouver,CA,Extra'  # Too many parts
        ]
        
        base_env = {
            'OWM_API_KEY': 'test_owm_key_1234567890',
            'GROQ_API_KEY': 'test_groq_key_1234567890',
            'GEMINI_API_KEY': 'test_gemini_key_1234567890'
        }
        
        for invalid_city in invalid_cities:
            test_env = {**base_env, 'USER_CITY': invalid_city}
            with patch.dict(os.environ, test_env):
                with pytest.raises(ValueError) as exc_info:
                    SkillConfig.from_environment()
                assert 'USER_CITY' in str(exc_info.value)
    
    def test_from_environment_strips_whitespace(self):
        """Test that whitespace is stripped from environment variables."""
        test_env = {
            'OWM_API_KEY': '  test_owm_key_1234567890  ',
            'GROQ_API_KEY': '\ttest_groq_key_1234567890\t',
            'GEMINI_API_KEY': '\ntest_gemini_key_1234567890\n',
            'USER_CITY': '  Vancouver,CA  '
        }
        
        with patch.dict(os.environ, test_env):
            config = SkillConfig.from_environment()
            
            assert config.owm_api_key == 'test_owm_key_1234567890'
            assert config.groq_api_key == 'test_groq_key_1234567890'
            assert config.gemini_api_key == 'test_gemini_key_1234567890'
            assert config.user_city == 'Vancouver,CA'


class TestSkillConfigValidation:
    """Test cases for SkillConfig validation methods."""
    
    def test_validate_success(self):
        """Test successful validation with valid configuration."""
        config = SkillConfig(
            owm_api_key='valid_owm_api_key_123',
            groq_api_key='valid_groq_api_key_123',
            gemini_api_key='valid_gemini_api_key_123',
            user_city='Vancouver,CA',
            has_school_kids=True
        )
        
        # Should not raise any exception
        config.validate()
    
    def test_validate_placeholder_api_keys(self):
        """Test validation fails for placeholder API key values."""
        placeholder_patterns = [
            'your_api_key_here',
            'replace_with_key',
            'enter_your_key',
            'add_api_key',
            'insert_key_here'
        ]
        
        for pattern in placeholder_patterns:
            # Test weather API key with placeholder (always required)
            config = SkillConfig(
                owm_api_key=pattern,
                groq_api_key='valid_groq_key_123',
                gemini_api_key='',
                user_city='Vancouver,CA',
                has_school_kids=False
            )
            with pytest.raises(ValueError) as exc_info:
                config.validate()
            assert 'placeholder' in str(exc_info.value).lower()
            
            # Test Groq API key with placeholder (when present)
            config = SkillConfig(
                owm_api_key='valid_owm_key_123',
                groq_api_key=pattern,
                gemini_api_key='',
                user_city='Vancouver,CA',
                has_school_kids=False
            )
            with pytest.raises(ValueError) as exc_info:
                config.validate()
            assert 'placeholder' in str(exc_info.value).lower()
            
            # Test Gemini API key with placeholder (when present)
            config = SkillConfig(
                owm_api_key='valid_owm_key_123',
                groq_api_key='',
                gemini_api_key=pattern,
                user_city='Vancouver,CA',
                has_school_kids=False
            )
            with pytest.raises(ValueError) as exc_info:
                config.validate()
            assert 'placeholder' in str(exc_info.value).lower()
    
    def test_validate_no_llm_keys(self):
        """Test validation fails when no LLM API keys are provided."""
        config = SkillConfig(
            owm_api_key='valid_owm_key_123',
            groq_api_key='',
            gemini_api_key='',
            user_city='Vancouver,CA',
            has_school_kids=False
        )
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert 'At least one LLM API key' in str(exc_info.value)
    
    def test_validate_invalid_city_formats(self):
        """Test validation of various invalid city formats."""
        invalid_cities = [
            'NoComma',
            'Multiple,Commas,Here',
            ',OnlyCountry',
            'OnlyCity,',
            ' ,CA',  # Empty city name
            'Vancouver, ',  # Empty country code
            'Vancouver,ABC'  # Country code too long
        ]
        
        base_config = {
            'owm_api_key': 'valid_owm_key_123',
            'groq_api_key': 'valid_groq_key_123',
            'gemini_api_key': 'valid_gemini_key_123',
            'has_school_kids': False
        }
        
        for invalid_city in invalid_cities:
            config = SkillConfig(**base_config, user_city=invalid_city)
            with pytest.raises(ValueError) as exc_info:
                config.validate()
            error_message = str(exc_info.value)
            assert any(word in error_message for word in ['comma', 'city', 'country', 'characters'])


class TestLoadConfig:
    """Test cases for the convenience load_config function."""
    
    def test_load_config_success(self):
        """Test successful configuration loading and validation."""
        test_env = {
            'OWM_API_KEY': 'test_owm_key_1234567890',
            'GROQ_API_KEY': 'test_groq_key_1234567890',
            'GEMINI_API_KEY': 'test_gemini_key_1234567890',
            'USER_CITY': 'Vancouver,CA',
            'HAS_SCHOOL_KIDS': 'true'
        }
        
        with patch.dict(os.environ, test_env):
            config = load_config()
            
            assert isinstance(config, SkillConfig)
            assert config.owm_api_key == 'test_owm_key_1234567890'
            assert config.user_city == 'Vancouver,CA'
            assert config.has_school_kids is True
    
    def test_load_config_missing_env_var(self):
        """Test load_config error handling for missing environment variables."""
        test_env = {
            'GROQ_API_KEY': 'test_groq_key_1234567890',
            'GEMINI_API_KEY': 'test_gemini_key_1234567890',
            'USER_CITY': 'Vancouver,CA'
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                load_config()
            assert 'Configuration loading failed' in str(exc_info.value)
            assert 'OWM_API_KEY' in str(exc_info.value)
    
    def test_load_config_validation_error(self):
        """Test load_config error handling for validation failures."""
        test_env = {
            'OWM_API_KEY': 'your_api_key_here',  # Placeholder value
            'GROQ_API_KEY': 'test_groq_key_1234567890',
            'GEMINI_API_KEY': 'test_gemini_key_1234567890',
            'USER_CITY': 'Vancouver,CA'
        }
        
        with patch.dict(os.environ, test_env):
            with pytest.raises(ConfigurationError) as exc_info:
                load_config()
            assert 'Configuration loading failed' in str(exc_info.value)
            assert 'placeholder' in str(exc_info.value).lower()