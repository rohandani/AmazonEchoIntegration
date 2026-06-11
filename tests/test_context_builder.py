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


class TestContextBuilderComprehensiveScenarios(unittest.TestCase):
    """Comprehensive test scenarios for ContextBuilder with edge cases and various configurations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.context_builder = ContextBuilder()
    
    def test_extensive_weekday_weekend_boundaries(self):
        """Test weekday/weekend detection across different time zones and edge cases."""
        # Test all days of the week
        test_dates = [
            (datetime(2024, 1, 1), 'Monday', 'weekday'),  # New Year's Day Monday
            (datetime(2024, 1, 2), 'Tuesday', 'weekday'),
            (datetime(2024, 1, 3), 'Wednesday', 'weekday'),
            (datetime(2024, 1, 4), 'Thursday', 'weekday'),
            (datetime(2024, 1, 5), 'Friday', 'weekday'),
            (datetime(2024, 1, 6), 'Saturday', 'weekend'),
            (datetime(2024, 1, 7), 'Sunday', 'weekend'),
        ]
        
        for test_date, expected_day, expected_type in test_dates:
            preferences = {
                'current_date': test_date,
                'location': 'Test City',
                'has_school_kids': False
            }
            
            context = self.context_builder.build_context(preferences)
            
            self.assertEqual(context['day_name'], expected_day)
            self.assertEqual(context['day_type'], expected_type)
    
    def test_holiday_and_special_dates(self):
        """Test context building for holidays and special calendar dates."""
        special_dates = [
            datetime(2024, 12, 25),  # Christmas Day
            datetime(2024, 7, 4),    # Independence Day  
            datetime(2024, 2, 29),   # Leap Day
            datetime(2024, 12, 31),  # New Year's Eve
            datetime(2024, 1, 1),    # New Year's Day
        ]
        
        for special_date in special_dates:
            preferences = {
                'current_date': special_date,
                'location': 'Holiday City',
                'has_school_kids': True
            }
            
            context = self.context_builder.build_context(preferences)
            
            # Should still correctly identify day type regardless of holiday
            expected_day_type = 'weekend' if special_date.weekday() >= 5 else 'weekday'
            self.assertEqual(context['day_type'], expected_day_type)
            
            # Should have proper occasion based on day type and school kids
            if expected_day_type == 'weekday':
                self.assertEqual(context['occasion'], 'school day')
            else:
                self.assertEqual(context['occasion'], 'weekend')
    
    def test_different_years_and_leap_years(self):
        """Test season calculation across different years including leap years."""
        test_cases = [
            # Regular year
            (datetime(2023, 3, 15), 'spring'),
            (datetime(2023, 6, 21), 'summer'),
            (datetime(2023, 9, 22), 'fall'),
            (datetime(2023, 12, 21), 'winter'),
            
            # Leap year
            (datetime(2024, 2, 29), 'winter'),  # Leap day
            (datetime(2024, 5, 15), 'spring'),
            (datetime(2024, 8, 10), 'summer'),
            (datetime(2024, 11, 5), 'fall'),
            
            # Future year
            (datetime(2025, 4, 1), 'spring'),
            (datetime(2025, 7, 15), 'summer'),
        ]
        
        for test_date, expected_season in test_cases:
            preferences = {
                'current_date': test_date,
                'location': 'Seasonal City',
                'has_school_kids': False
            }
            
            context = self.context_builder.build_context(preferences)
            self.assertEqual(context['season'], expected_season)
    
    def test_month_boundary_edge_cases(self):
        """Test season transitions at month boundaries."""
        boundary_dates = [
            # Winter to Spring boundary
            (datetime(2024, 2, 29), 'winter'),  # Last day of Feb (leap year)
            (datetime(2024, 3, 1), 'spring'),   # First day of March
            
            # Spring to Summer boundary  
            (datetime(2024, 5, 31), 'spring'),  # Last day of May
            (datetime(2024, 6, 1), 'summer'),   # First day of June
            
            # Summer to Fall boundary
            (datetime(2024, 8, 31), 'summer'),  # Last day of August
            (datetime(2024, 9, 1), 'fall'),     # First day of September
            
            # Fall to Winter boundary
            (datetime(2024, 11, 30), 'fall'),   # Last day of November
            (datetime(2024, 12, 1), 'winter'),  # First day of December
        ]
        
        for test_date, expected_season in boundary_dates:
            preferences = {
                'current_date': test_date,
                'location': 'Boundary City',
                'has_school_kids': False
            }
            
            context = self.context_builder.build_context(preferences)
            self.assertEqual(context['season'], expected_season)
    
    def test_family_configuration_combinations(self):
        """Test all combinations of family configurations with different day types."""
        family_configs = [
            {'has_school_kids': True, 'expected_weekday': 'school day', 'expected_weekend': 'weekend'},
            {'has_school_kids': False, 'expected_weekday': 'work day', 'expected_weekend': 'weekend'},
        ]
        
        test_dates = [
            (datetime(2024, 1, 2), 'weekday'),   # Tuesday
            (datetime(2024, 1, 5), 'weekday'),   # Friday  
            (datetime(2024, 1, 6), 'weekend'),   # Saturday
            (datetime(2024, 1, 7), 'weekend'),   # Sunday
        ]
        
        for config in family_configs:
            for test_date, day_type in test_dates:
                preferences = {
                    'current_date': test_date,
                    'location': 'Family City',
                    'has_school_kids': config['has_school_kids']
                }
                
                context = self.context_builder.build_context(preferences)
                
                expected_occasion = (config['expected_weekday'] if day_type == 'weekday' 
                                   else config['expected_weekend'])
                
                self.assertEqual(context['occasion'], expected_occasion)
                self.assertEqual(context['has_school_kids'], config['has_school_kids'])
    
    def test_location_variations_and_edge_cases(self):
        """Test various location formats and edge cases."""
        location_test_cases = [
            ('Vancouver, BC', 'Vancouver, BC'),
            ('New York City, NY', 'New York City, NY'),
            ('', 'your area'),  # Empty location
            ('   ', 'your area'),  # Whitespace location
            ('London, UK', 'London, UK'),
            ('Toronto', 'Toronto'),  # No province/state
            ('Mumbai, Maharashtra, India', 'Mumbai, Maharashtra, India'),  # Long format
        ]
        
        for input_location, expected_location in location_test_cases:
            preferences = {
                'current_date': datetime(2024, 6, 15),
                'location': input_location,
                'has_school_kids': False
            }
            
            context = self.context_builder.build_context(preferences)
            self.assertEqual(context['location'], expected_location)
    
    def test_date_formatting_across_cultures(self):
        """Test date string formatting for various dates."""
        date_cases = [
            (datetime(2024, 1, 1), 'Monday, January 01, 2024'),
            (datetime(2024, 12, 31), 'Tuesday, December 31, 2024'),
            (datetime(2024, 7, 4), 'Thursday, July 04, 2024'),
            (datetime(2024, 2, 29), 'Thursday, February 29, 2024'),  # Leap day
            (datetime(2024, 11, 28), 'Thursday, November 28, 2024'),  # Thanksgiving
        ]
        
        for test_date, expected_format in date_cases:
            preferences = {
                'current_date': test_date,
                'location': 'Date City',
                'has_school_kids': False
            }
            
            context = self.context_builder.build_context(preferences)
            self.assertEqual(context['date_str'], expected_format)
    
    def test_missing_and_default_preferences(self):
        """Test behavior with missing or default preference values."""
        # Test completely empty preferences (should use defaults)
        minimal_prefs = {}
        context = self.context_builder.build_context(minimal_prefs)
        
        # Should have all required keys with default values
        required_keys = ['day_type', 'day_name', 'occasion', 'season', 'location', 'has_school_kids', 'date_str']
        for key in required_keys:
            self.assertIn(key, context)
        
        # Defaults should be sensible
        self.assertEqual(context['location'], 'your area')
        self.assertEqual(context['has_school_kids'], False)
        self.assertIn(context['day_type'], ['weekday', 'weekend'])
        self.assertIn(context['season'], ['spring', 'summer', 'fall', 'winter'])
        
        # Test partial preferences
        partial_prefs = {'location': 'Partial City'}
        context = self.context_builder.build_context(partial_prefs)
        
        self.assertEqual(context['location'], 'Partial City')
        self.assertEqual(context['has_school_kids'], False)  # Should default
    
    def test_timezone_and_datetime_edge_cases(self):
        """Test edge cases around datetime handling."""
        # Test datetime at midnight
        midnight = datetime(2024, 6, 15, 0, 0, 0)
        preferences = {
            'current_date': midnight,
            'location': 'Midnight City',
            'has_school_kids': True
        }
        
        context = self.context_builder.build_context(preferences)
        
        self.assertEqual(context['day_name'], 'Saturday')
        self.assertEqual(context['day_type'], 'weekend')
        self.assertEqual(context['season'], 'summer')
        
        # Test datetime at end of day
        end_of_day = datetime(2024, 6, 14, 23, 59, 59)
        preferences['current_date'] = end_of_day
        
        context = self.context_builder.build_context(preferences)
        
        self.assertEqual(context['day_name'], 'Friday')
        self.assertEqual(context['day_type'], 'weekday')
    
    def test_context_consistency_across_multiple_calls(self):
        """Test that context building is consistent across multiple calls."""
        fixed_date = datetime(2024, 8, 15)  # Thursday in summer
        preferences = {
            'current_date': fixed_date,
            'location': 'Consistency City',
            'has_school_kids': True
        }
        
        # Build context multiple times
        contexts = []
        for _ in range(5):
            context = self.context_builder.build_context(preferences)
            contexts.append(context)
        
        # All contexts should be identical
        first_context = contexts[0]
        for context in contexts[1:]:
            self.assertEqual(context, first_context)
        
        # Verify expected values
        expected_context = {
            'day_type': 'weekday',
            'day_name': 'Thursday', 
            'occasion': 'school day',
            'season': 'summer',
            'location': 'Consistency City',
            'has_school_kids': True,
            'date_str': 'Thursday, August 15, 2024'
        }
        
        self.assertEqual(first_context, expected_context)
    
    def test_dataclass_integration(self):
        """Test integration with BriefingContext dataclass."""
        test_date = datetime(2024, 9, 20)  # Friday in fall
        preferences = {
            'current_date': test_date,
            'location': 'Dataclass City',
            'has_school_kids': False
        }
        
        context_dict = self.context_builder.build_context(preferences)
        
        # Should be able to create BriefingContext from result
        briefing_context = BriefingContext(**context_dict)
        
        self.assertEqual(briefing_context.day_type, 'weekday')
        self.assertEqual(briefing_context.day_name, 'Friday')
        self.assertEqual(briefing_context.occasion, 'work day')
        self.assertEqual(briefing_context.season, 'fall')
        self.assertEqual(briefing_context.location, 'Dataclass City')
        self.assertEqual(briefing_context.has_school_kids, False)
        self.assertEqual(briefing_context.date_str, 'Friday, September 20, 2024')


if __name__ == '__main__':
    unittest.main()