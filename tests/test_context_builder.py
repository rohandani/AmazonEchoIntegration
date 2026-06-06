"""
Unit tests for the ContextBuilder module.

Tests day type detection, season calculation, and school day context
for various date scenarios and configurations.
"""

import unittest
from datetime import datetime
from context_builder import ContextBuilder, BriefingContext


class TestContextBuilder(unittest.TestCase):
    """Test cases for the ContextBuilder class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.context_builder = ContextBuilder()
    
    def test_weekday_detection(self):
        """Test detection of weekdays (Monday-Friday)."""
        # Test Monday (2024-01-01 was a Monday)
        monday = datetime(2024, 1, 1)
        preferences = {'current_date': monday, 'location': 'Vancouver', 'has_school_kids': False}
        context = self.context_builder.build_context(preferences)
        
        self.assertEqual(context['day_type'], 'weekday')
        self.assertEqual(context['day_name'], 'Monday')
        
        # Test Friday
        friday = datetime(2024, 1, 5)
        preferences['current_date'] = friday
        context = self.context_builder.build_context(preferences)
        
        self.assertEqual(context['day_type'], 'weekday')
        self.assertEqual(context['day_name'], 'Friday')
    
    def test_weekend_detection(self):
        """Test detection of weekends (Saturday-Sunday)."""
        # Test Saturday
        saturday = datetime(2024, 1, 6)
        preferences = {'current_date': saturday, 'location': 'Vancouver', 'has_school_kids': False}
        context = self.context_builder.build_context(preferences)
        
        self.assertEqual(context['day_type'], 'weekend')
        self.assertEqual(context['day_name'], 'Saturday')
        
        # Test Sunday  
        sunday = datetime(2024, 1, 7)
        preferences['current_date'] = sunday
        context = self.context_builder.build_context(preferences)
        
        self.assertEqual(context['day_type'], 'weekend')
        self.assertEqual(context['day_name'], 'Sunday')
    
    def test_school_day_context_with_kids(self):
        """Test school day context when HAS_SCHOOL_KIDS=true."""
        # Weekday with school kids should be "school day"
        weekday = datetime(2024, 1, 2)  # Tuesday
        preferences = {
            'current_date': weekday,
            'location': 'Vancouver', 
            'has_school_kids': True
        }
        context = self.context_builder.build_context(preferences)
        
        self.assertEqual(context['occasion'], 'school day')
        self.assertEqual(context['has_school_kids'], True)
        
        # Weekend with school kids should still be "weekend"
        weekend = datetime(2024, 1, 6)  # Saturday
        preferences['current_date'] = weekend
        context = self.context_builder.build_context(preferences)
        
        self.assertEqual(context['occasion'], 'weekend')
        self.assertEqual(context['has_school_kids'], True)
    
    def test_work_day_context_without_kids(self):
        """Test work day context when HAS_SCHOOL_KIDS=false."""
        # Weekday without school kids should be "work day"
        weekday = datetime(2024, 1, 3)  # Wednesday
        preferences = {
            'current_date': weekday,
            'location': 'Vancouver',
            'has_school_kids': False
        }
        context = self.context_builder.build_context(preferences)
        
        self.assertEqual(context['occasion'], 'work day')
        self.assertEqual(context['has_school_kids'], False)
    
    def test_spring_season_calculation(self):
        """Test spring season detection (March, April, May)."""
        # Test March
        march_date = datetime(2024, 3, 15)
        preferences = {'current_date': march_date, 'location': 'Vancouver', 'has_school_kids': False}
        context = self.context_builder.build_context(preferences)
        self.assertEqual(context['season'], 'spring')
        
        # Test April
        april_date = datetime(2024, 4, 20)
        preferences['current_date'] = april_date
        context = self.context_builder.build_context(preferences)
        self.assertEqual(context['season'], 'spring')
        
        # Test May
        may_date = datetime(2024, 5, 30)
        preferences['current_date'] = may_date
        context = self.context_builder.build_context(preferences)
        self.assertEqual(context['season'], 'spring')
    
    def test_summer_season_calculation(self):
        """Test summer season detection (June, July, August)."""
        # Test June
        june_date = datetime(2024, 6, 15)
        preferences = {'current_date': june_date, 'location': 'Vancouver', 'has_school_kids': False}
        context = self.context_builder.build_context(preferences)
        self.assertEqual(context['season'], 'summer')
        
        # Test July
        july_date = datetime(2024, 7, 4)
        preferences['current_date'] = july_date
        context = self.context_builder.build_context(preferences)
        self.assertEqual(context['season'], 'summer')
        
        # Test August
        august_date = datetime(2024, 8, 25)
        preferences['current_date'] = august_date
        context = self.context_builder.build_context(preferences)
        self.assertEqual(context['season'], 'summer')
    
    def test_fall_season_calculation(self):
        """Test fall season detection (September, October, November)."""
        # Test September
        sept_date = datetime(2024, 9, 10)
        preferences = {'current_date': sept_date, 'location': 'Vancouver', 'has_school_kids': False}
        context = self.context_builder.build_context(preferences)
        self.assertEqual(context['season'], 'fall')
        
        # Test October
        oct_date = datetime(2024, 10, 31)
        preferences['current_date'] = oct_date
        context = self.context_builder.build_context(preferences)
        self.assertEqual(context['season'], 'fall')
        
        # Test November
        nov_date = datetime(2024, 11, 15)
        preferences['current_date'] = nov_date
        context = self.context_builder.build_context(preferences)
        self.assertEqual(context['season'], 'fall')
    
    def test_winter_season_calculation(self):
        """Test winter season detection (December, January, February)."""
        # Test December
        dec_date = datetime(2024, 12, 20)
        preferences = {'current_date': dec_date, 'location': 'Vancouver', 'has_school_kids': False}
        context = self.context_builder.build_context(preferences)
        self.assertEqual(context['season'], 'winter')
        
        # Test January
        jan_date = datetime(2024, 1, 15)
        preferences['current_date'] = jan_date
        context = self.context_builder.build_context(preferences)
        self.assertEqual(context['season'], 'winter')
        
        # Test February
        feb_date = datetime(2024, 2, 29)  # Leap year
        preferences['current_date'] = feb_date
        context = self.context_builder.build_context(preferences)
        self.assertEqual(context['season'], 'winter')
    
    def test_location_context(self):
        """Test location context is properly included."""
        date = datetime(2024, 6, 15)
        preferences = {
            'current_date': date,
            'location': 'Toronto, ON',
            'has_school_kids': True
        }
        context = self.context_builder.build_context(preferences)
        
        self.assertEqual(context['location'], 'Toronto, ON')
    
    def test_default_location(self):
        """Test default location when not provided."""
        date = datetime(2024, 6, 15)
        preferences = {
            'current_date': date,
            'has_school_kids': False
        }
        context = self.context_builder.build_context(preferences)
        
        self.assertEqual(context['location'], 'your area')
    
    def test_date_string_formatting(self):
        """Test date string is properly formatted."""
        date = datetime(2024, 7, 4)  # Independence Day 2024 (Thursday)
        preferences = {
            'current_date': date,
            'location': 'Boston, MA',
            'has_school_kids': False
        }
        context = self.context_builder.build_context(preferences)
        
        self.assertEqual(context['date_str'], 'Thursday, July 04, 2024')
    
    def test_default_has_school_kids(self):
        """Test default value for has_school_kids when not provided."""
        date = datetime(2024, 6, 15)
        preferences = {
            'current_date': date,
            'location': 'Vancouver'
        }
        context = self.context_builder.build_context(preferences)
        
        self.assertEqual(context['has_school_kids'], False)
        self.assertEqual(context['occasion'], 'weekend')  # Saturday
    
    def test_current_date_defaults_to_now(self):
        """Test that current_date defaults to now when not provided."""
        preferences = {
            'location': 'Vancouver',
            'has_school_kids': False
        }
        context = self.context_builder.build_context(preferences)
        
        # Should have all required keys
        required_keys = ['day_type', 'day_name', 'occasion', 'season', 'location', 'has_school_kids', 'date_str']
        for key in required_keys:
            self.assertIn(key, context)
        
        # day_type should be either 'weekday' or 'weekend'
        self.assertIn(context['day_type'], ['weekday', 'weekend'])
        
        # season should be one of the four seasons
        self.assertIn(context['season'], ['spring', 'summer', 'fall', 'winter'])
    
    def test_edge_case_leap_year(self):
        """Test leap year February 29th handling."""
        leap_day = datetime(2024, 2, 29)
        preferences = {
            'current_date': leap_day,
            'location': 'Vancouver',
            'has_school_kids': True
        }
        context = self.context_builder.build_context(preferences)
        
        self.assertEqual(context['season'], 'winter')
        self.assertEqual(context['day_name'], 'Thursday')
        self.assertEqual(context['day_type'], 'weekday')
        self.assertEqual(context['occasion'], 'school day')
    
    def test_year_boundary_dates(self):
        """Test dates at year boundaries."""
        # New Year's Eve
        nye = datetime(2024, 12, 31)
        preferences = {
            'current_date': nye,
            'location': 'Vancouver',
            'has_school_kids': False
        }
        context = self.context_builder.build_context(preferences)
        
        self.assertEqual(context['season'], 'winter')
        self.assertEqual(context['day_name'], 'Tuesday')
        
        # New Year's Day
        nyd = datetime(2025, 1, 1)
        preferences['current_date'] = nyd
        context = self.context_builder.build_context(preferences)
        
        self.assertEqual(context['season'], 'winter')
        self.assertEqual(context['day_name'], 'Wednesday')
    
    def test_complete_context_structure(self):
        """Test that build_context returns all required fields."""
        date = datetime(2024, 9, 15)  # Sunday in fall
        preferences = {
            'current_date': date,
            'location': 'Seattle, WA',
            'has_school_kids': True
        }
        context = self.context_builder.build_context(preferences)
        
        # Verify all expected keys are present
        expected_keys = {
            'day_type', 'day_name', 'occasion', 'season',
            'location', 'has_school_kids', 'date_str'
        }
        self.assertEqual(set(context.keys()), expected_keys)
        
        # Verify correct values
        self.assertEqual(context['day_type'], 'weekend')
        self.assertEqual(context['day_name'], 'Sunday')
        self.assertEqual(context['occasion'], 'weekend')
        self.assertEqual(context['season'], 'fall')
        self.assertEqual(context['location'], 'Seattle, WA')
        self.assertEqual(context['has_school_kids'], True)
        self.assertEqual(context['date_str'], 'Sunday, September 15, 2024')


if __name__ == '__main__':
    unittest.main()