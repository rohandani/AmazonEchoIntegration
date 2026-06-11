"""
Context Builder module for generating contextual metadata for personalized briefings.

This module provides day/season awareness and contextual information based on
user preferences like school schedules and location.
"""

from datetime import datetime
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class BriefingContext:
    """Data model for briefing context information."""
    day_type: str
    day_name: str
    occasion: str
    season: str
    location: str
    has_school_kids: bool
    date_str: str


class ContextBuilder:
    """
    Generates contextual metadata for personalized morning briefings.
    
    Provides day type detection (weekday vs weekend), season calculation,
    and school day context when configured for families with school-age children.
    """
    
    def __init__(self):
        """Initialize the ContextBuilder."""
        pass
    
    def build_context(self, user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build context dictionary with day/season/occasion information.
        
        Args:
            user_preferences: Dictionary containing user configuration including:
                - location: str - User's city/location
                - has_school_kids: bool - Whether household has school-age children
                - current_date: datetime (optional) - For testing, defaults to now
        
        Returns:
            Dict containing context information with keys:
                - day_type: "weekday" | "weekend"
                - day_name: "Monday", "Tuesday", etc.
                - occasion: "school day" | "work day" | "weekend"
                - season: "spring", "summer", "fall", "winter"
                - location: User's location string
                - has_school_kids: Boolean from user preferences
                - date_str: Formatted date string
        """
        # Get current date/time, allow override for testing
        current_date = user_preferences.get('current_date', datetime.now())
        
        # Extract user preferences
        location = user_preferences.get('location', 'your area')
        if not location or not location.strip():
            location = 'your area'
        has_school_kids = user_preferences.get('has_school_kids', False)
        
        # Determine day type and name
        day_type = self._get_day_type(current_date)
        day_name = self._get_day_name(current_date)
        
        # Determine occasion based on day type and school kids
        occasion = self._get_occasion(day_type, has_school_kids)
        
        # Calculate season
        season = self._get_season(current_date)
        
        # Format date string
        date_str = current_date.strftime("%A, %B %d, %Y")
        
        return {
            "day_type": day_type,
            "day_name": day_name,
            "occasion": occasion,
            "season": season,
            "location": location,
            "has_school_kids": has_school_kids,
            "date_str": date_str
        }
    
    def _get_day_type(self, date: datetime) -> str:
        """
        Determine if the given date is a weekday or weekend.
        
        Args:
            date: The date to check
            
        Returns:
            "weekday" for Monday-Friday, "weekend" for Saturday-Sunday
        """
        # weekday() returns 0-6, where 0=Monday, 6=Sunday
        if date.weekday() < 5:  # Monday-Friday (0-4)
            return "weekday"
        else:  # Saturday-Sunday (5-6)
            return "weekend"
    
    def _get_day_name(self, date: datetime) -> str:
        """
        Get the name of the day for the given date.
        
        Args:
            date: The date to get the day name for
            
        Returns:
            Full day name (e.g., "Monday", "Tuesday")
        """
        return date.strftime("%A")
    
    def _get_occasion(self, day_type: str, has_school_kids: bool) -> str:
        """
        Determine the occasion type based on day and family situation.
        
        Args:
            day_type: "weekday" or "weekend"
            has_school_kids: Whether the household has school-age children
            
        Returns:
            "school day" for weekdays with school kids,
            "work day" for weekdays without school kids,
            "weekend" for weekend days
        """
        if day_type == "weekend":
            return "weekend"
        elif has_school_kids:
            return "school day"
        else:
            return "work day"
    
    def _get_season(self, date: datetime) -> str:
        """
        Calculate the season based on the given date.
        
        Uses meteorological seasons:
        - Spring: March, April, May
        - Summer: June, July, August  
        - Fall: September, October, November
        - Winter: December, January, February
        
        Args:
            date: The date to determine the season for
            
        Returns:
            Season name: "spring", "summer", "fall", or "winter"
        """
        month = date.month
        
        if month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        elif month in [9, 10, 11]:
            return "fall"
        else:  # month in [12, 1, 2]
            return "winter"