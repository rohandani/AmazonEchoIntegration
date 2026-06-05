"""
Weather client module for OpenWeatherMap API integration.

This module provides the WeatherClient class for fetching and normalizing
weather forecast data from OpenWeatherMap API.
"""

import requests
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class WeatherClientError(Exception):
    """Base exception for WeatherClient errors."""
    pass


class WeatherAPIError(WeatherClientError):
    """Exception raised when the weather API returns an error."""
    pass


class WeatherDataError(WeatherClientError):
    """Exception raised when weather data is invalid or cannot be parsed."""
    pass


class WeatherClient:
    """
    Client for OpenWeatherMap API integration.
    
    Fetches weather forecast data and normalizes it for use by the briefing system.
    Supports timeout configuration, retry logic, and comprehensive error handling 
    as per requirements 4.4, 8.1, and 8.2.
    """
    
    BASE_URL = "http://api.openweathermap.org/data/2.5"
    TIMEOUT = 5.0  # seconds, as per requirement 8.1
    MAX_RETRIES = 2  # Retry transient failures twice
    RETRY_DELAY = 1.0  # seconds between retries
    
    def __init__(self, api_key: str, city: str):
        """
        Initialize WeatherClient with API credentials.
        
        Args:
            api_key: OpenWeatherMap API key
            city: City name for weather data (e.g., "Vancouver,CA")
            
        Raises:
            ValueError: If api_key or city are empty or invalid
        """
        if not api_key or not api_key.strip():
            raise ValueError("API key cannot be empty")
        if not city or not city.strip():
            raise ValueError("City cannot be empty")
            
        self.api_key = api_key.strip()
        self.city = city.strip()
        
    def get_forecast(self) -> Dict[str, Any]:
        """
        Fetch weather forecast for the next 12 hours and normalize data.
        
        Implements retry logic for transient failures as per requirement 4.4.
        Returns normalized weather data including temperature, precipitation,
        wind, and humidity information as required by requirements 2.1 and 2.2.
        
        Returns:
            Dict containing normalized weather data:
            {
                "temp_min": float,           # Celsius
                "temp_max": float,           # Celsius  
                "description": str,          # "light rain", "clear sky"
                "max_precipitation_prob": float,  # 0.0 to 1.0
                "wind_speed": float,         # m/s
                "humidity": int,             # percentage
                "location": str              # "Vancouver, CA"
            }
            
        Raises:
            WeatherAPIError: For API-related errors (4xx, 5xx responses)
            WeatherDataError: For invalid API responses or data parsing errors
            requests.RequestException: For network-related errors after retries
        """
        last_exception = None
        
        for attempt in range(self.MAX_RETRIES + 1):  # +1 for initial attempt
            try:
                # Fetch forecast data
                forecast_url = f"{self.BASE_URL}/forecast"
                params = {
                    "q": self.city,
                    "appid": self.api_key,
                    "units": "metric",  # Celsius
                    "cnt": 4  # Next 12 hours (4 x 3-hour intervals)
                }
                
                logger.info(f"Fetching weather forecast for {self.city} (attempt {attempt + 1})")
                response = requests.get(
                    forecast_url, 
                    params=params, 
                    timeout=self.TIMEOUT
                )
                
                # Handle HTTP errors
                if response.status_code == 401:
                    raise WeatherAPIError("Invalid API key")
                elif response.status_code == 404:
                    raise WeatherAPIError(f"City '{self.city}' not found")
                elif response.status_code == 429:
                    raise WeatherAPIError("API rate limit exceeded")
                elif 400 <= response.status_code < 500:
                    raise WeatherAPIError(f"Client error: {response.status_code}")
                elif 500 <= response.status_code < 600:
                    # Server errors are retryable
                    raise requests.exceptions.HTTPError(f"Server error: {response.status_code}")
                
                response.raise_for_status()
                
                # Parse JSON response
                try:
                    data = response.json()
                except ValueError as e:
                    raise WeatherDataError(f"Invalid JSON response: {e}")
                
                # Validate response structure
                self._validate_api_response(data)
                
                # Normalize the forecast data
                return self._normalize_forecast_data(data)
                
            except (requests.exceptions.Timeout, 
                    requests.exceptions.ConnectionError,
                    requests.exceptions.HTTPError) as e:
                
                last_exception = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
                # Don't retry on the last attempt
                if attempt < self.MAX_RETRIES:
                    logger.info(f"Retrying in {self.RETRY_DELAY} seconds...")
                    time.sleep(self.RETRY_DELAY)
                    continue
                else:
                    # All retries exhausted
                    logger.error(f"All {self.MAX_RETRIES + 1} attempts failed for {self.city}")
                    break
                    
            except (WeatherAPIError, WeatherDataError):
                # Don't retry client errors or data parsing errors
                raise
            except Exception as e:
                # Unexpected errors
                logger.error(f"Unexpected error fetching weather data: {e}")
                raise WeatherDataError(f"Unexpected error: {e}")
        
        # If we get here, all retries failed
        if isinstance(last_exception, requests.exceptions.Timeout):
            raise WeatherAPIError(f"Request timed out after {self.MAX_RETRIES + 1} attempts")
        elif isinstance(last_exception, requests.exceptions.ConnectionError):
            raise WeatherAPIError(f"Connection failed after {self.MAX_RETRIES + 1} attempts")
        else:
            raise WeatherAPIError(f"API request failed after {self.MAX_RETRIES + 1} attempts: {last_exception}")
    
    def _validate_api_response(self, data: Dict[str, Any]) -> None:
        """
        Validate OpenWeatherMap API response structure.
        
        Ensures the response contains all required fields before processing.
        
        Args:
            data: Raw API response dictionary
            
        Raises:
            WeatherDataError: If response is missing required fields
        """
        if not isinstance(data, dict):
            raise WeatherDataError("API response is not a valid dictionary")
        
        if "list" not in data:
            raise WeatherDataError("Invalid API response: missing 'list' field")
        
        if not data["list"] or not isinstance(data["list"], list):
            raise WeatherDataError("Invalid API response: forecast list is empty or invalid")
        
        if "city" not in data:
            raise WeatherDataError("Invalid API response: missing 'city' field")
        
        if not isinstance(data["city"], dict):
            raise WeatherDataError("Invalid API response: city data is not valid")
        
        city_data = data["city"]
        if "name" not in city_data or "country" not in city_data:
            raise WeatherDataError("Invalid API response: missing city name or country")
        
        # Validate each forecast item has required fields
        for i, forecast in enumerate(data["list"]):
            if not isinstance(forecast, dict):
                raise WeatherDataError(f"Invalid forecast item {i}: not a dictionary")
            
            if "main" not in forecast or not isinstance(forecast["main"], dict):
                raise WeatherDataError(f"Invalid forecast item {i}: missing or invalid 'main' data")
            
            main_data = forecast["main"]
            required_main_fields = ["temp", "humidity"]
            for field in required_main_fields:
                if field not in main_data:
                    raise WeatherDataError(f"Invalid forecast item {i}: missing '{field}' in main data")
                if not isinstance(main_data[field], (int, float)):
                    raise WeatherDataError(f"Invalid forecast item {i}: '{field}' is not a number")
            
            if "weather" not in forecast or not isinstance(forecast["weather"], list) or not forecast["weather"]:
                raise WeatherDataError(f"Invalid forecast item {i}: missing or empty 'weather' data")
    
    def _normalize_forecast_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize raw OpenWeatherMap API response into standardized format.
        
        Extracts temperature, precipitation, wind, and humidity data from
        the next 12 hours of forecast data as required.
        
        Args:
            raw_data: Raw API response from OpenWeatherMap
            
        Returns:
            Normalized weather data dictionary
            
        Raises:
            WeatherDataError: If data cannot be normalized
        """
        try:
            forecasts = raw_data["list"]
            city_info = raw_data["city"]
            
            # Extract data from all forecast periods (next 12 hours)
            temps = []
            precipitation_probs = []
            descriptions = []
            wind_speeds = []
            humidities = []
            
            for forecast in forecasts:
                # Temperature data (required)
                temp = forecast["main"]["temp"]
                if not isinstance(temp, (int, float)):
                    raise WeatherDataError(f"Invalid temperature value: {temp}")
                temps.append(float(temp))
                
                # Precipitation probability (optional, default 0.0)
                precip_prob = forecast.get("pop", 0.0)
                if not isinstance(precip_prob, (int, float)) or precip_prob < 0 or precip_prob > 1:
                    logger.warning(f"Invalid precipitation probability: {precip_prob}, using 0.0")
                    precip_prob = 0.0
                precipitation_probs.append(float(precip_prob))
                
                # Weather description (required)
                weather_list = forecast.get("weather", [])
                if weather_list and isinstance(weather_list, list) and len(weather_list) > 0:
                    description = weather_list[0].get("description", "unknown")
                    if isinstance(description, str):
                        descriptions.append(description.strip().lower())
                    else:
                        descriptions.append("unknown")
                else:
                    descriptions.append("unknown")
                
                # Wind speed (optional, default 0.0)
                wind_data = forecast.get("wind", {})
                wind_speed = wind_data.get("speed", 0.0) if isinstance(wind_data, dict) else 0.0
                if not isinstance(wind_speed, (int, float)) or wind_speed < 0:
                    logger.warning(f"Invalid wind speed: {wind_speed}, using 0.0")
                    wind_speed = 0.0
                wind_speeds.append(float(wind_speed))
                
                # Humidity (required)
                humidity = forecast["main"]["humidity"]
                if not isinstance(humidity, (int, float)) or humidity < 0 or humidity > 100:
                    raise WeatherDataError(f"Invalid humidity value: {humidity}")
                humidities.append(int(humidity))
            
            # Validate we have data
            if not temps:
                raise WeatherDataError("No valid temperature data found")
            
            # Calculate aggregated values
            temp_min = min(temps)
            temp_max = max(temps)
            max_precipitation_prob = max(precipitation_probs) if precipitation_probs else 0.0
            
            # Use the most recent description
            primary_description = descriptions[0] if descriptions else "unknown"
            
            # Average wind speed and humidity
            avg_wind_speed = sum(wind_speeds) / len(wind_speeds) if wind_speeds else 0.0
            avg_humidity = int(sum(humidities) / len(humidities)) if humidities else 0
            
            # Format location string
            city_name = str(city_info.get("name", "Unknown"))
            country_code = str(city_info.get("country", "??"))
            location = f"{city_name}, {country_code}"
            
            normalized_data = {
                "temp_min": round(temp_min, 1),
                "temp_max": round(temp_max, 1),
                "description": primary_description,
                "max_precipitation_prob": round(max_precipitation_prob, 2),
                "wind_speed": round(avg_wind_speed, 1),
                "humidity": avg_humidity,
                "location": location
            }
            
            logger.info(f"Normalized weather data for {location}: {normalized_data}")
            return normalized_data
            
        except (KeyError, TypeError, ZeroDivisionError, ValueError) as e:
            raise WeatherDataError(f"Error normalizing weather data: {e}")
    
    def __repr__(self):
        """String representation for debugging."""
        return f"WeatherClient(city='{self.city}', api_key='***')"