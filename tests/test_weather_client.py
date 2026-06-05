"""
Unit tests for WeatherClient module.

Tests weather data parsing with mocked OpenWeatherMap API responses
as required by task 2.1.
"""

import pytest
import responses
import requests
import json
from unittest.mock import patch, Mock
from weather_client import WeatherClient


class TestWeatherClient:
    """Test suite for WeatherClient class."""
    
    def test_init_valid_params(self):
        """Test WeatherClient initialization with valid parameters."""
        client = WeatherClient("test_api_key", "Vancouver,CA")
        assert client.api_key == "test_api_key"
        assert client.city == "Vancouver,CA"
    
    def test_init_empty_api_key(self):
        """Test WeatherClient initialization with empty API key."""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            WeatherClient("", "Vancouver,CA")
    
    def test_init_whitespace_api_key(self):
        """Test WeatherClient initialization with whitespace API key."""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            WeatherClient("   ", "Vancouver,CA")
    
    def test_init_empty_city(self):
        """Test WeatherClient initialization with empty city."""
        with pytest.raises(ValueError, match="City cannot be empty"):
            WeatherClient("test_key", "")
    
    def test_init_whitespace_city(self):
        """Test WeatherClient initialization with whitespace city."""
        with pytest.raises(ValueError, match="City cannot be empty"):
            WeatherClient("test_key", "   ")
    
    def test_init_strips_whitespace(self):
        """Test WeatherClient strips whitespace from inputs."""
        client = WeatherClient("  test_key  ", "  Vancouver,CA  ")
        assert client.api_key == "test_key"
        assert client.city == "Vancouver,CA"
    
    @responses.activate
    def test_get_forecast_sunny_day(self):
        """Test weather data parsing for sunny day conditions."""
        # Mock OpenWeatherMap API response for sunny day
        mock_response = {
            "cod": "200",
            "message": 0,
            "cnt": 4,
            "list": [
                {
                    "dt": 1609459200,
                    "main": {
                        "temp": 22.5,
                        "feels_like": 21.8,
                        "temp_min": 20.1,
                        "temp_max": 24.3,
                        "pressure": 1013,
                        "humidity": 45
                    },
                    "weather": [
                        {
                            "id": 800,
                            "main": "Clear",
                            "description": "clear sky",
                            "icon": "01d"
                        }
                    ],
                    "wind": {
                        "speed": 2.1,
                        "deg": 180
                    },
                    "pop": 0.0
                },
                {
                    "dt": 1609470000,
                    "main": {
                        "temp": 24.8,
                        "feels_like": 24.2,
                        "temp_min": 22.5,
                        "temp_max": 26.1,
                        "pressure": 1012,
                        "humidity": 42
                    },
                    "weather": [
                        {
                            "id": 800,
                            "main": "Clear",
                            "description": "clear sky",
                            "icon": "01d"
                        }
                    ],
                    "wind": {
                        "speed": 1.8,
                        "deg": 200
                    },
                    "pop": 0.0
                }
            ],
            "city": {
                "id": 6173331,
                "name": "Vancouver",
                "coord": {
                    "lat": 49.2497,
                    "lon": -123.1193
                },
                "country": "CA",
                "population": 0,
                "timezone": -28800
            }
        }
        
        responses.add(
            responses.GET,
            "http://api.openweathermap.org/data/2.5/forecast",
            json=mock_response,
            status=200
        )
        
        client = WeatherClient("test_api_key", "Vancouver,CA")
        result = client.get_forecast()
        
        expected = {
            "temp_min": 22.5,
            "temp_max": 24.8,
            "description": "clear sky",
            "max_precipitation_prob": 0.0,
            "wind_speed": 2.0,  # Average of 2.1 and 1.8, rounded to 1 decimal
            "humidity": 43,      # Average of 45 and 42
            "location": "Vancouver, CA"
        }
        
        assert result == expected
    
    @responses.activate
    def test_get_forecast_rainy_day(self):
        """Test weather data parsing for rainy day conditions."""
        # Mock OpenWeatherMap API response for rainy day
        mock_response = {
            "cod": "200",
            "message": 0,
            "cnt": 4,
            "list": [
                {
                    "dt": 1609459200,
                    "main": {
                        "temp": 15.2,
                        "feels_like": 14.1,
                        "temp_min": 13.8,
                        "temp_max": 16.5,
                        "pressure": 1008,
                        "humidity": 78
                    },
                    "weather": [
                        {
                            "id": 500,
                            "main": "Rain",
                            "description": "light rain",
                            "icon": "10d"
                        }
                    ],
                    "wind": {
                        "speed": 5.2,
                        "deg": 240
                    },
                    "pop": 0.65
                },
                {
                    "dt": 1609470000,
                    "main": {
                        "temp": 14.1,
                        "feels_like": 13.2,
                        "temp_min": 12.9,
                        "temp_max": 15.3,
                        "pressure": 1006,
                        "humidity": 82
                    },
                    "weather": [
                        {
                            "id": 501,
                            "main": "Rain",
                            "description": "moderate rain",
                            "icon": "10d"
                        }
                    ],
                    "wind": {
                        "speed": 6.1,
                        "deg": 260
                    },
                    "pop": 0.85
                }
            ],
            "city": {
                "id": 6173331,
                "name": "Vancouver",
                "coord": {
                    "lat": 49.2497,
                    "lon": -123.1193
                },
                "country": "CA",
                "population": 0,
                "timezone": -28800
            }
        }
        
        responses.add(
            responses.GET,
            "http://api.openweathermap.org/data/2.5/forecast",
            json=mock_response,
            status=200
        )
        
        client = WeatherClient("test_api_key", "Vancouver,CA")
        result = client.get_forecast()
        
        expected = {
            "temp_min": 14.1,
            "temp_max": 15.2,
            "description": "light rain",
            "max_precipitation_prob": 0.85,  # Maximum of 0.65 and 0.85
            "wind_speed": 5.7,  # Average of 5.2 and 6.1, rounded to 1 decimal
            "humidity": 80,      # Average of 78 and 82
            "location": "Vancouver, CA"
        }
        
        assert result == expected
    
    @responses.activate
    def test_get_forecast_missing_optional_data(self):
        """Test weather data parsing when optional fields are missing."""
        # Mock response with missing wind and pop data
        mock_response = {
            "cod": "200",
            "message": 0,
            "cnt": 2,
            "list": [
                {
                    "dt": 1609459200,
                    "main": {
                        "temp": 18.0,
                        "humidity": 60
                    },
                    "weather": [
                        {
                            "description": "partly cloudy"
                        }
                    ]
                    # Missing wind and pop fields
                }
            ],
            "city": {
                "name": "TestCity",
                "country": "TC"
            }
        }
        
        responses.add(
            responses.GET,
            "http://api.openweathermap.org/data/2.5/forecast",
            json=mock_response,
            status=200
        )
        
        client = WeatherClient("test_api_key", "TestCity,TC")
        result = client.get_forecast()
        
        assert result["temp_min"] == 18.0
        assert result["temp_max"] == 18.0
        assert result["description"] == "partly cloudy"
        assert result["max_precipitation_prob"] == 0.0  # Default when missing
        assert result["wind_speed"] == 0.0  # Default when missing
        assert result["humidity"] == 60
        assert result["location"] == "TestCity, TC"
    
    @responses.activate
    def test_get_forecast_http_error(self):
        """Test handling of HTTP errors from API."""
        responses.add(
            responses.GET,
            "http://api.openweathermap.org/data/2.5/forecast",
            status=401,
            json={"cod": 401, "message": "Invalid API key"}
        )
        
        client = WeatherClient("invalid_key", "Vancouver,CA")
        
        from weather_client import WeatherAPIError
        with pytest.raises(WeatherAPIError):
            client.get_forecast()
    
    @responses.activate
    def test_get_forecast_timeout(self):
        """Test timeout handling as per requirement 8.1."""
        # Mock a timeout by not adding any responses
        # The request will timeout after 5 seconds
        
        client = WeatherClient("test_key", "Vancouver,CA")
        
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
            
            from weather_client import WeatherAPIError
            with pytest.raises(WeatherAPIError):
                client.get_forecast()
    
    @responses.activate
    def test_get_forecast_invalid_json(self):
        """Test handling of invalid JSON response."""
        responses.add(
            responses.GET,
            "http://api.openweathermap.org/data/2.5/forecast",
            body="Invalid JSON",
            status=200
        )
        
        client = WeatherClient("test_key", "Vancouver,CA")
        
        from weather_client import WeatherDataError
        with pytest.raises(WeatherDataError):
            client.get_forecast()
    
    @responses.activate
    def test_get_forecast_missing_list(self):
        """Test handling of API response missing forecast list."""
        mock_response = {
            "cod": "200",
            "city": {"name": "Vancouver", "country": "CA"}
            # Missing "list" field
        }
        
        responses.add(
            responses.GET,
            "http://api.openweathermap.org/data/2.5/forecast",
            json=mock_response,
            status=200
        )
        
        client = WeatherClient("test_key", "Vancouver,CA")
        
        from weather_client import WeatherDataError
        with pytest.raises(WeatherDataError, match="Invalid API response: missing 'list' field"):
            client.get_forecast()
    
    @responses.activate
    def test_get_forecast_empty_list(self):
        """Test handling of API response with empty forecast list."""
        mock_response = {
            "cod": "200",
            "list": [],  # Empty forecast list
            "city": {"name": "Vancouver", "country": "CA"}
        }
        
        responses.add(
            responses.GET,
            "http://api.openweathermap.org/data/2.5/forecast",
            json=mock_response,
            status=200
        )
        
        client = WeatherClient("test_key", "Vancouver,CA")
        
        from weather_client import WeatherDataError
        with pytest.raises(WeatherDataError, match="Invalid API response: forecast list is empty"):
            client.get_forecast()
    
    @responses.activate
    def test_get_forecast_missing_city(self):
        """Test handling of API response missing city data."""
        mock_response = {
            "cod": "200",
            "list": [
                {
                    "main": {"temp": 20.0, "humidity": 50},
                    "weather": [{"description": "clear"}]
                }
            ]
            # Missing "city" field
        }
        
        responses.add(
            responses.GET,
            "http://api.openweathermap.org/data/2.5/forecast",
            json=mock_response,
            status=200
        )
        
        client = WeatherClient("test_key", "Vancouver,CA")
        
        from weather_client import WeatherDataError
        with pytest.raises(WeatherDataError, match="Invalid API response: missing 'city' field"):
            client.get_forecast()
    
    def test_repr(self):
        """Test string representation of WeatherClient."""
        client = WeatherClient("secret_key", "Vancouver,CA")
        repr_str = repr(client)
        
        assert "WeatherClient" in repr_str
        assert "Vancouver,CA" in repr_str
        assert "secret_key" not in repr_str  # API key should be masked
        assert "***" in repr_str


if __name__ == "__main__":
    pytest.main([__file__])


# Additional tests for error handling and validation (Task 2.2)

class TestWeatherClientErrorHandling:
    """Test suite for WeatherClient error handling and validation."""
    
    @responses.activate
    def test_retry_logic_server_error(self):
        """Test retry logic for server errors (5xx)."""
        # First two requests return server errors, third succeeds
        responses.add(
            responses.GET,
            "http://api.openweathermap.org/data/2.5/forecast",
            status=500
        )
        responses.add(
            responses.GET,
            "http://api.openweathermap.org/data/2.5/forecast",
            status=502
        )
        responses.add(
            responses.GET,
            "http://api.openweathermap.org/data/2.5/forecast",
            json={
                "list": [{"main": {"temp": 20.0, "humidity": 50}, "weather": [{"description": "clear"}]}],
                "city": {"name": "Vancouver", "country": "CA"}
            },
            status=200
        )
        
        client = WeatherClient("test_key", "Vancouver,CA")
        
        # Should succeed on the third attempt
        result = client.get_forecast()
        assert result["location"] == "Vancouver, CA"
        
        # Verify all three requests were made
        assert len(responses.calls) == 3
    
    @responses.activate
    def test_retry_exhaustion(self):
        """Test that retries are exhausted and exception is raised."""
        # All requests return server errors
        for _ in range(4):  # More than MAX_RETRIES + 1
            responses.add(
                responses.GET,
                "http://api.openweathermap.org/data/2.5/forecast",
                status=500
            )
        
        client = WeatherClient("test_key", "Vancouver,CA")
        
        from weather_client import WeatherAPIError
        with pytest.raises(WeatherAPIError, match="API request failed after 3 attempts"):
            client.get_forecast()
        
        # Should only make MAX_RETRIES + 1 = 3 attempts
        assert len(responses.calls) == 3
    
    @responses.activate
    def test_no_retry_for_client_errors(self):
        """Test that client errors (4xx) are not retried."""
        responses.add(
            responses.GET,
            "http://api.openweathermap.org/data/2.5/forecast",
            status=401,
            json={"cod": 401, "message": "Invalid API key"}
        )
        
        client = WeatherClient("test_key", "Vancouver,CA")
        
        from weather_client import WeatherAPIError
        with pytest.raises(WeatherAPIError, match="Invalid API key"):
            client.get_forecast()
        
        # Should only make 1 attempt (no retries for 4xx)
        assert len(responses.calls) == 1
    
    @responses.activate
    def test_api_error_404_city_not_found(self):
        """Test handling of 404 city not found error."""
        responses.add(
            responses.GET,
            "http://api.openweathermap.org/data/2.5/forecast",
            status=404,
            json={"cod": "404", "message": "city not found"}
        )
        
        client = WeatherClient("test_key", "InvalidCity")
        
        from weather_client import WeatherAPIError
        with pytest.raises(WeatherAPIError, match="City 'InvalidCity' not found"):
            client.get_forecast()
    
    @responses.activate
    def test_api_error_429_rate_limit(self):
        """Test handling of 429 rate limit error."""
        responses.add(
            responses.GET,
            "http://api.openweathermap.org/data/2.5/forecast",
            status=429,
            json={"cod": 429, "message": "API calls limit exceeded"}
        )
        
        client = WeatherClient("test_key", "Vancouver,CA")
        
        from weather_client import WeatherAPIError
        with pytest.raises(WeatherAPIError, match="API rate limit exceeded"):
            client.get_forecast()
    
    @responses.activate
    def test_timeout_retry(self):
        """Test retry logic for timeout errors."""
        with patch('time.sleep'):  # Mock sleep to speed up test
            with patch('requests.get') as mock_get:
                # First two calls timeout, third succeeds
                success_response = Mock()
                success_response.status_code = 200
                success_response.json.return_value = {
                    "list": [{"main": {"temp": 20.0, "humidity": 50}, "weather": [{"description": "clear"}]}],
                    "city": {"name": "Vancouver", "country": "CA"}
                }
                success_response.raise_for_status.return_value = None
                
                mock_get.side_effect = [
                    requests.exceptions.Timeout("Timed out"),
                    requests.exceptions.Timeout("Timed out"),
                    success_response
                ]
                
                client = WeatherClient("test_key", "Vancouver,CA")
                result = client.get_forecast()
                
                assert result["location"] == "Vancouver, CA"
                assert mock_get.call_count == 3
    
    @responses.activate
    def test_connection_error_retry(self):
        """Test retry logic for connection errors."""
        with patch('time.sleep'):  # Mock sleep to speed up test
            with patch('requests.get') as mock_get:
                # All calls fail with connection error
                mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
                
                client = WeatherClient("test_key", "Vancouver,CA")
                
                from weather_client import WeatherAPIError
                with pytest.raises(WeatherAPIError, match="Connection failed after 3 attempts"):
                    client.get_forecast()
                
                assert mock_get.call_count == 3
    
    def test_data_validation_non_dict_response(self):
        """Test validation error when API response is not a dictionary."""
        client = WeatherClient("test_key", "Vancouver,CA")
        
        from weather_client import WeatherDataError
        with pytest.raises(WeatherDataError, match="API response is not a valid dictionary"):
            client._validate_api_response("not a dict")
    
    def test_data_validation_missing_list_field(self):
        """Test validation error when API response missing list field."""
        client = WeatherClient("test_key", "Vancouver,CA")
        
        invalid_response = {"city": {"name": "Vancouver", "country": "CA"}}
        
        from weather_client import WeatherDataError
        with pytest.raises(WeatherDataError, match="missing 'list' field"):
            client._validate_api_response(invalid_response)
    
    def test_data_validation_empty_forecast_list(self):
        """Test validation error when forecast list is empty."""
        client = WeatherClient("test_key", "Vancouver,CA")
        
        invalid_response = {
            "list": [],
            "city": {"name": "Vancouver", "country": "CA"}
        }
        
        from weather_client import WeatherDataError
        with pytest.raises(WeatherDataError, match="forecast list is empty"):
            client._validate_api_response(invalid_response)
    
    def test_data_validation_missing_city_field(self):
        """Test validation error when city field is missing."""
        client = WeatherClient("test_key", "Vancouver,CA")
        
        invalid_response = {
            "list": [{"main": {"temp": 20.0, "humidity": 50}, "weather": [{"description": "clear"}]}]
        }
        
        from weather_client import WeatherDataError
        with pytest.raises(WeatherDataError, match="missing 'city' field"):
            client._validate_api_response(invalid_response)
    
    def test_data_validation_invalid_forecast_item(self):
        """Test validation error for invalid forecast items."""
        client = WeatherClient("test_key", "Vancouver,CA")
        
        invalid_response = {
            "list": ["not a dict"],  # Invalid forecast item
            "city": {"name": "Vancouver", "country": "CA"}
        }
        
        from weather_client import WeatherDataError
        with pytest.raises(WeatherDataError, match="Invalid forecast item 0: not a dictionary"):
            client._validate_api_response(invalid_response)
    
    def test_data_validation_missing_main_data(self):
        """Test validation error when main weather data is missing."""
        client = WeatherClient("test_key", "Vancouver,CA")
        
        invalid_response = {
            "list": [{"weather": [{"description": "clear"}]}],  # Missing main data
            "city": {"name": "Vancouver", "country": "CA"}
        }
        
        from weather_client import WeatherDataError
        with pytest.raises(WeatherDataError, match="missing or invalid 'main' data"):
            client._validate_api_response(invalid_response)
    
    def test_data_validation_missing_temperature(self):
        """Test validation error when temperature data is missing."""
        client = WeatherClient("test_key", "Vancouver,CA")
        
        invalid_response = {
            "list": [{"main": {"humidity": 50}, "weather": [{"description": "clear"}]}],  # Missing temp
            "city": {"name": "Vancouver", "country": "CA"}
        }
        
        from weather_client import WeatherDataError
        with pytest.raises(WeatherDataError, match="missing 'temp' in main data"):
            client._validate_api_response(invalid_response)
    
    def test_data_validation_invalid_temperature_type(self):
        """Test validation error for non-numeric temperature."""
        client = WeatherClient("test_key", "Vancouver,CA")
        
        invalid_response = {
            "list": [{"main": {"temp": "not a number", "humidity": 50}, "weather": [{"description": "clear"}]}],
            "city": {"name": "Vancouver", "country": "CA"}
        }
        
        from weather_client import WeatherDataError
        with pytest.raises(WeatherDataError, match="'temp' is not a number"):
            client._validate_api_response(invalid_response)
    
    def test_normalization_invalid_humidity(self):
        """Test handling of invalid humidity values during normalization."""
        client = WeatherClient("test_key", "Vancouver,CA")
        
        invalid_response = {
            "list": [{"main": {"temp": 20.0, "humidity": 150}, "weather": [{"description": "clear"}]}],  # Invalid humidity > 100
            "city": {"name": "Vancouver", "country": "CA"}
        }
        
        from weather_client import WeatherDataError
        with pytest.raises(WeatherDataError, match="Invalid humidity value: 150"):
            client._normalize_forecast_data(invalid_response)
    
    def test_normalization_handles_invalid_wind_speed(self):
        """Test that invalid wind speeds are handled gracefully."""
        client = WeatherClient("test_key", "Vancouver,CA")
        
        response_data = {
            "list": [{"main": {"temp": 20.0, "humidity": 50}, "weather": [{"description": "clear"}], "wind": {"speed": -5.0}}],  # Negative wind speed
            "city": {"name": "Vancouver", "country": "CA"}
        }
        
        # Should not raise exception, but log warning and use 0.0
        result = client._normalize_forecast_data(response_data)
        assert result["wind_speed"] == 0.0
    
    def test_normalization_handles_invalid_precipitation(self):
        """Test that invalid precipitation probabilities are handled gracefully."""
        client = WeatherClient("test_key", "Vancouver,CA")
        
        response_data = {
            "list": [{"main": {"temp": 20.0, "humidity": 50}, "weather": [{"description": "clear"}], "pop": 1.5}],  # Invalid > 1.0
            "city": {"name": "Vancouver", "country": "CA"}
        }
        
        # Should not raise exception, but log warning and use 0.0
        result = client._normalize_forecast_data(response_data)
        assert result["max_precipitation_prob"] == 0.0
    
    def test_normalization_handles_missing_weather_description(self):
        """Test handling when weather description is missing."""
        client = WeatherClient("test_key", "Vancouver,CA")
        
        response_data = {
            "list": [{"main": {"temp": 20.0, "humidity": 50}}],  # Missing weather field
            "city": {"name": "Vancouver", "country": "CA"}
        }
        
        result = client._normalize_forecast_data(response_data)
        assert result["description"] == "unknown"
    
    def test_normalization_empty_temperatures_list(self):
        """Test error when no valid temperature data is found."""
        client = WeatherClient("test_key", "Vancouver,CA")
        
        response_data = {
            "list": [],  # Empty list
            "city": {"name": "Vancouver", "country": "CA"}
        }
        
        from weather_client import WeatherDataError
        with pytest.raises(WeatherDataError, match="No valid temperature data found"):
            client._normalize_forecast_data(response_data)


class TestWeatherClientCustomExceptions:
    """Test custom exception classes."""
    
    def test_weather_client_error_inheritance(self):
        """Test that custom exceptions inherit properly."""
        from weather_client import WeatherClientError, WeatherAPIError, WeatherDataError
        
        api_error = WeatherAPIError("API failed")
        data_error = WeatherDataError("Data invalid")
        
        assert isinstance(api_error, WeatherClientError)
        assert isinstance(data_error, WeatherClientError)
        assert isinstance(api_error, Exception)
        assert isinstance(data_error, Exception)