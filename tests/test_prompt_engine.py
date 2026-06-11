"""
Unit tests for the PromptEngine module.

Tests prompt assembly with various weather and context scenarios,
as well as output sanitization for Alexa SSML compatibility.
"""

import unittest
from unittest.mock import patch
from prompt_engine import PromptEngine


class TestPromptEngine(unittest.TestCase):
    """Test cases for PromptEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.prompt_engine = PromptEngine()
        
        # Standard test weather data
        self.base_weather_data = {
            "temp_min": 15.0,
            "temp_max": 22.0,
            "description": "partly cloudy",
            "max_precipitation_prob": 0.3,
            "wind_speed": 5.2,
            "humidity": 65,
            "location": "Vancouver, CA"
        }
        
        # Standard test context data
        self.base_context_data = {
            "day_type": "weekday",
            "day_name": "Monday",
            "occasion": "work day",
            "season": "spring",
            "location": "Vancouver, BC",
            "has_school_kids": False,
            "date_str": "Monday, April 15, 2024"
        }
    
    def test_build_prompt_basic_functionality(self):
        """Test basic prompt building with standard inputs."""
        prompt = self.prompt_engine.build_prompt(
            self.base_weather_data, 
            self.base_context_data
        )
        
        # Verify prompt contains key components
        self.assertIn("You are a friendly morning weather assistant", prompt)
        self.assertIn("50-70 words exactly", prompt)
        self.assertIn("Vancouver, CA", prompt)
        self.assertIn("15-22°C", prompt)
        self.assertIn("partly cloudy", prompt)
        self.assertIn("30%", prompt)  # precipitation percentage
        self.assertIn("Monday", prompt)
        self.assertIn("work day", prompt)
        self.assertIn("Spring weather", prompt)
    
    def test_build_prompt_school_day_context(self):
        """Test prompt generation for school day context."""
        school_context = self.base_context_data.copy()
        school_context["occasion"] = "school day"
        
        prompt = self.prompt_engine.build_prompt(
            self.base_weather_data, 
            school_context
        )
        
        self.assertIn("school day", prompt)
        self.assertIn("school-related activities", prompt)
        self.assertIn("appropriate clothing for kids", prompt)
    
    def test_build_prompt_weekend_context(self):
        """Test prompt generation for weekend context."""
        weekend_context = self.base_context_data.copy()
        weekend_context["occasion"] = "weekend"
        weekend_context["day_name"] = "Saturday"
        
        prompt = self.prompt_engine.build_prompt(
            self.base_weather_data,
            weekend_context
        )
        
        self.assertIn("weekend", prompt)
        self.assertIn("leisure activities", prompt)
        self.assertIn("casual comfort", prompt)
        self.assertIn("Saturday", prompt)
    
    def test_build_prompt_different_seasons(self):
        """Test prompt generation with different seasonal contexts."""
        seasons_and_expectations = {
            "summer": "sun protection and heat comfort",
            "winter": "warmth and weather protection",
            "fall": "seasonal clothing and potential weather changes",
            "spring": "Spring weather can be variable"
        }
        
        for season, expected_text in seasons_and_expectations.items():
            with self.subTest(season=season):
                context = self.base_context_data.copy()
                context["season"] = season
                
                prompt = self.prompt_engine.build_prompt(
                    self.base_weather_data,
                    context
                )
                
                self.assertIn(expected_text, prompt)
    
    def test_build_prompt_temperature_formatting(self):
        """Test temperature formatting in different scenarios."""
        # Test close temperature range (within 2 degrees)
        close_temp_weather = self.base_weather_data.copy()
        close_temp_weather["temp_min"] = 20.0
        close_temp_weather["temp_max"] = 21.5
        
        prompt = self.prompt_engine.build_prompt(
            close_temp_weather,
            self.base_context_data
        )
        
        self.assertIn("around 22°C", prompt)  # Should use single temperature
        
        # Test wide temperature range
        wide_temp_weather = self.base_weather_data.copy()
        wide_temp_weather["temp_min"] = 10.0
        wide_temp_weather["temp_max"] = 25.0
        
        prompt = self.prompt_engine.build_prompt(
            wide_temp_weather,
            self.base_context_data
        )
        
        self.assertIn("10-25°C", prompt)  # Should use range
    
    def test_build_prompt_precipitation_probability_formatting(self):
        """Test precipitation probability formatting."""
        test_cases = [
            (0.0, "0%"),
            (0.15, "15%"),
            (0.50, "50%"),
            (0.95, "95%"),
            (1.0, "100%")
        ]
        
        for prob, expected_text in test_cases:
            with self.subTest(probability=prob):
                weather = self.base_weather_data.copy()
                weather["max_precipitation_prob"] = prob
                
                prompt = self.prompt_engine.build_prompt(
                    weather,
                    self.base_context_data
                )
                
                self.assertIn(expected_text, prompt)
    
    def test_build_prompt_validation_weather_data(self):
        """Test validation of weather data input."""
        # Test missing required field
        incomplete_weather = self.base_weather_data.copy()
        del incomplete_weather["temp_min"]
        
        with self.assertRaises(ValueError) as cm:
            self.prompt_engine.build_prompt(incomplete_weather, self.base_context_data)
        self.assertIn("Missing required weather field: temp_min", str(cm.exception))
        
        # Test invalid temperature type
        invalid_weather = self.base_weather_data.copy()
        invalid_weather["temp_max"] = "hot"
        
        with self.assertRaises(ValueError) as cm:
            self.prompt_engine.build_prompt(invalid_weather, self.base_context_data)
        self.assertIn("temp_max must be a number", str(cm.exception))
        
        # Test invalid precipitation probability range
        invalid_weather = self.base_weather_data.copy()
        invalid_weather["max_precipitation_prob"] = 1.5
        
        with self.assertRaises(ValueError) as cm:
            self.prompt_engine.build_prompt(invalid_weather, self.base_context_data)
        self.assertIn("max_precipitation_prob must be between 0.0 and 1.0", str(cm.exception))
        
        # Test empty description
        invalid_weather = self.base_weather_data.copy()
        invalid_weather["description"] = ""
        
        with self.assertRaises(ValueError) as cm:
            self.prompt_engine.build_prompt(invalid_weather, self.base_context_data)
        self.assertIn("description must be a non-empty string", str(cm.exception))
    
    def test_build_prompt_validation_context_data(self):
        """Test validation of context data input."""
        # Test missing required field
        incomplete_context = self.base_context_data.copy()
        del incomplete_context["day_name"]
        
        with self.assertRaises(ValueError) as cm:
            self.prompt_engine.build_prompt(self.base_weather_data, incomplete_context)
        self.assertIn("Missing required context field: day_name", str(cm.exception))
        
        # Test invalid occasion
        invalid_context = self.base_context_data.copy()
        invalid_context["occasion"] = "party day"
        
        with self.assertRaises(ValueError) as cm:
            self.prompt_engine.build_prompt(self.base_weather_data, invalid_context)
        self.assertIn("occasion must be one of", str(cm.exception))
        
        # Test invalid season
        invalid_context = self.base_context_data.copy()
        invalid_context["season"] = "monsoon"
        
        with self.assertRaises(ValueError) as cm:
            self.prompt_engine.build_prompt(self.base_weather_data, invalid_context)
        self.assertIn("season must be one of", str(cm.exception))
    
    def test_sanitize_output_basic_functionality(self):
        """Test basic output sanitization."""
        raw_output = "Good morning! It's partly cloudy with temperatures around 20°C. Have a great day!"
        
        result = self.prompt_engine.sanitize_output(raw_output)
        
        self.assertEqual(result, raw_output)  # Should be unchanged for clean input
    
    def test_sanitize_output_html_removal(self):
        """Test HTML tag and entity removal."""
        test_cases = [
            ("<b>Bold text</b>", "Bold text"),
            ("Temperature &amp; humidity", "Temperature humidity"),
            ("<p>Paragraph <strong>with</strong> tags</p>", "Paragraph with tags"),
            ("Rain &#8211; 30% chance", "Rain 30% chance"),
            ("<span style='color: red'>Warning</span>", "Warning")
        ]
        
        for raw_input, expected in test_cases:
            with self.subTest(input=raw_input):
                result = self.prompt_engine.sanitize_output(raw_input)
                self.assertEqual(result, expected)
    
    def test_sanitize_output_markdown_removal(self):
        """Test Markdown formatting removal."""
        test_cases = [
            ("**Bold** text", "Bold text"),
            ("*Italic* text", "Italic text"),
            ("__Bold__ text", "Bold text"),
            ("_Italic_ text", "Italic text"),
            ("`Code` snippet", "Code snippet"),
            ("# Header\nContent", "Header Content"),
            ("[Link text](http://example.com)", "Link text"),
        ]
        
        for raw_input, expected in test_cases:
            with self.subTest(input=raw_input):
                result = self.prompt_engine.sanitize_output(raw_input)
                # Normalize whitespace for comparison
                result = ' '.join(result.split())
                expected = ' '.join(expected.split())
                self.assertEqual(result, expected)
    
    def test_sanitize_output_ssml_unsafe_characters(self):
        """Test removal of SSML-unsafe characters."""
        test_cases = [
            ("Temperature < 20°C", "Temperature 20°C"),
            ("Wind > 10 m/s", "Wind 10 m/s"),
            ("Rain & shine", "Rain shine"),
            ('Say "hello" today', "Say 'hello' today"),  # Quotes -> apostrophes
        ]
        
        for raw_input, expected in test_cases:
            with self.subTest(input=raw_input):
                result = self.prompt_engine.sanitize_output(raw_input)
                self.assertEqual(result, expected)
    
    def test_sanitize_output_whitespace_normalization(self):
        """Test whitespace normalization."""
        test_cases = [
            ("Multiple   spaces", "Multiple spaces"),
            ("  Leading and trailing  ", "Leading and trailing"),
            ("Line\n\nbreaks\t\ttabs", "Line breaks tabs"),
        ]
        
        for raw_input, expected in test_cases:
            with self.subTest(input=raw_input):
                result = self.prompt_engine.sanitize_output(raw_input)
                self.assertEqual(result, expected)
    
    def test_sanitize_output_complex_example(self):
        """Test sanitization with complex mixed formatting."""
        raw_input = """
        <p>**Good morning!** The weather is <em>partly cloudy</em> with temperatures 
        around 20°C. There's a `30% chance` of rain, so you might want to bring 
        an umbrella & jacket. Check out [weather.com](http://weather.com) for updates.</p>
        
        ```
        Temperature: 20°C
        Humidity: 65%
        ```
        
        Have a "great" day!
        """
        
        result = self.prompt_engine.sanitize_output(raw_input)
        
        # Should be clean, natural text
        expected_content = [
            "Good morning!", "partly cloudy", "20°C", "30% chance", 
            "umbrella", "jacket", "weather.com", "Have a 'great' day!"
        ]
        
        for content in expected_content:
            self.assertIn(content, result)
        
        # Should not contain HTML, Markdown, or code blocks
        unwanted_chars = ['<', '>', '**', '`', '[', ']', '&']
        for char in unwanted_chars:
            self.assertNotIn(char, result)
    
    def test_sanitize_output_validation(self):
        """Test input validation for sanitize_output."""
        # Test None input
        with self.assertRaises(ValueError) as cm:
            self.prompt_engine.sanitize_output(None)
        self.assertIn("must be a non-empty string", str(cm.exception))
        
        # Test empty string
        with self.assertRaises(ValueError) as cm:
            self.prompt_engine.sanitize_output("")
        self.assertIn("must be a non-empty string", str(cm.exception))
        
        # Test non-string input
        with self.assertRaises(ValueError) as cm:
            self.prompt_engine.sanitize_output(123)
        self.assertIn("must be a non-empty string", str(cm.exception))
    
    def test_sanitize_output_empty_after_cleaning(self):
        """Test handling of output that becomes empty after sanitization."""
        # Input that becomes empty after cleaning
        raw_input = "```  \n  \n```"
        
        with self.assertRaises(ValueError) as cm:
            self.prompt_engine.sanitize_output(raw_input)
        self.assertIn("Sanitized output is empty after cleaning", str(cm.exception))
    
    @patch('prompt_engine.logger')
    def test_sanitize_output_long_text_warning(self, mock_logger):
        """Test warning for overly long output."""
        long_text = "A" * 600  # Over 500 character limit
        
        result = self.prompt_engine.sanitize_output(long_text)
        
        # Should still return the text but log warning
        self.assertEqual(result, long_text)
        mock_logger.warning.assert_called_once()
        self.assertIn("may be too verbose for voice", mock_logger.warning.call_args[0][0])
    
    def test_prompt_includes_all_required_constraints(self):
        """Test that generated prompts include all required constraints from requirements."""
        prompt = self.prompt_engine.build_prompt(
            self.base_weather_data,
            self.base_context_data
        )
        
        # Requirements 2.1, 2.2, 2.3, 2.4 - Natural language constraints
        self.assertIn("50-70 words exactly", prompt)
        self.assertIn("natural, conversational", prompt)
        self.assertIn("rain probability", prompt)
        self.assertIn("clothing appropriate", prompt)
        self.assertIn("preparations", prompt)
        
        # Requirements 3.2, 3.3 - Context awareness
        self.assertIn("work day", prompt)  # or school day/weekend
        
        # Voice optimization requirements
        self.assertIn("voice interaction", prompt)
        self.assertIn("Plain text only", prompt)
        self.assertIn("suitable for voice synthesis", prompt)


class TestPromptEngineComprehensiveScenarios(unittest.TestCase):
    """Comprehensive test scenarios for PromptEngine with various weather/context combinations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.prompt_engine = PromptEngine()
    
    def test_weather_context_combinations_matrix(self):
        """Test prompt building with comprehensive matrix of weather and context combinations."""
        weather_scenarios = [
            {
                "temp_min": -15.0,
                "temp_max": -8.0,
                "description": "heavy snow",
                "max_precipitation_prob": 0.95,
                "wind_speed": 12.0,
                "humidity": 85,
                "location": "Winnipeg, CA"
            },
            {
                "temp_min": 32.0,
                "temp_max": 38.0,
                "description": "scorching sun",
                "max_precipitation_prob": 0.0,
                "wind_speed": 2.0,
                "humidity": 15,
                "location": "Phoenix, AZ"
            },
            {
                "temp_min": 18.0,
                "temp_max": 19.0,
                "description": "light drizzle",
                "max_precipitation_prob": 0.45,
                "wind_speed": 6.5,
                "humidity": 78,
                "location": "London, UK"
            }
        ]
        
        context_scenarios = [
            {
                "day_type": "weekday",
                "day_name": "Monday",
                "occasion": "school day",
                "season": "winter",
                "location": "Test City",
                "has_school_kids": True,
                "date_str": "Monday, January 15, 2024"
            },
            {
                "day_type": "weekend",
                "day_name": "Saturday",
                "occasion": "weekend",
                "season": "summer", 
                "location": "Test City",
                "has_school_kids": False,
                "date_str": "Saturday, July 20, 2024"
            },
            {
                "day_type": "weekday",
                "day_name": "Friday",
                "occasion": "work day",
                "season": "spring",
                "location": "Test City",
                "has_school_kids": False,
                "date_str": "Friday, April 12, 2024"
            }
        ]
        
        # Test all combinations
        for weather in weather_scenarios:
            for context in context_scenarios:
                with self.subTest(weather=weather['location'], context=context['occasion']):
                    prompt = self.prompt_engine.build_prompt(weather, context)
                    
                    # Verify core components are present
                    self.assertIn("You are a friendly morning weather assistant", prompt)
                    self.assertIn("50-70 words exactly", prompt)
                    
                    # Verify weather data inclusion
                    self.assertIn(weather['location'], prompt)
                    self.assertIn(weather['description'], prompt)
                    
                    # Verify context inclusion
                    self.assertIn(context['day_name'], prompt)
                    self.assertIn(context['occasion'], prompt)
                    
                    # Verify seasonal considerations
                    season_keywords = {
                        'winter': 'warmth and weather protection',
                        'summer': 'sun protection and heat comfort',
                        'spring': 'Spring weather can be variable',
                        'fall': 'seasonal clothing'
                    }
                    self.assertIn(season_keywords[context['season']], prompt)
    
    def test_edge_case_weather_data_handling(self):
        """Test prompt building with edge case weather data."""
        edge_cases = [
            # Extreme temperature ranges
            {
                "weather": {
                    "temp_min": -40.0,
                    "temp_max": -35.0,
                    "description": "arctic blast",
                    "max_precipitation_prob": 0.0,
                    "wind_speed": 25.0,
                    "humidity": 95,
                    "location": "Yellowknife, CA"
                },
                "expected_temp": "-40--35°C"
            },
            
            # Very close temperatures (should use single value)
            {
                "weather": {
                    "temp_min": 23.8,
                    "temp_max": 24.2,
                    "description": "perfect conditions",
                    "max_precipitation_prob": 0.0,
                    "wind_speed": 1.0,
                    "humidity": 45,
                    "location": "San Diego, CA"
                },
                "expected_temp": "around 24°C"
            },
            
            # Maximum precipitation probability
            {
                "weather": {
                    "temp_min": 15.0,
                    "temp_max": 18.0,
                    "description": "torrential downpour",
                    "max_precipitation_prob": 1.0,
                    "wind_speed": 15.0,
                    "humidity": 100,
                    "location": "Mumbai, India"
                },
                "expected_precip": "100%"
            }
        ]
        
        base_context = {
            "day_type": "weekday",
            "day_name": "Wednesday",
            "occasion": "work day",
            "season": "summer",
            "location": "Test City",
            "has_school_kids": False,
            "date_str": "Wednesday, August 15, 2024"
        }
        
        for case in edge_cases:
            with self.subTest(location=case['weather']['location']):
                prompt = self.prompt_engine.build_prompt(case['weather'], base_context)
                
                if 'expected_temp' in case:
                    self.assertIn(case['expected_temp'], prompt)
                if 'expected_precip' in case:
                    self.assertIn(case['expected_precip'], prompt)
                    
                # Should still be well-formed
                self.assertIn("WEATHER DATA:", prompt)
                self.assertIn("CONTEXT:", prompt)
    
    def test_prompt_validation_comprehensive(self):
        """Test comprehensive input validation scenarios."""
        valid_weather = {
            "temp_min": 15.0,
            "temp_max": 22.0,
            "description": "partly cloudy",
            "max_precipitation_prob": 0.3,
            "wind_speed": 5.2,
            "humidity": 65,
            "location": "Vancouver, CA"
        }
        
        valid_context = {
            "day_type": "weekday",
            "day_name": "Monday", 
            "occasion": "work day",
            "season": "spring",
            "location": "Vancouver, BC",
            "has_school_kids": False,
            "date_str": "Monday, April 15, 2024"
        }
        
        # Test invalid weather data types
        invalid_weather_cases = [
            ("temp_min", "cold", "temp_min must be a number"),
            ("temp_max", [22], "temp_max must be a number"),
            ("description", 123, "description must be a non-empty string"),
            ("description", "", "description must be a non-empty string"),
            ("max_precipitation_prob", "maybe", "max_precipitation_prob must be a number"),
            ("max_precipitation_prob", -0.1, "max_precipitation_prob must be between 0.0 and 1.0"),
            ("max_precipitation_prob", 1.1, "max_precipitation_prob must be between 0.0 and 1.0"),
            ("location", None, "location must be a non-empty string"),
        ]
        
        for field, invalid_value, expected_error in invalid_weather_cases:
            with self.subTest(field=field, value=invalid_value):
                bad_weather = valid_weather.copy()
                bad_weather[field] = invalid_value
                
                with self.assertRaises(ValueError) as cm:
                    self.prompt_engine.build_prompt(bad_weather, valid_context)
                self.assertIn(expected_error, str(cm.exception))
        
        # Test invalid context data
        invalid_context_cases = [
            ("day_name", "", "day_name must be a non-empty string"),
            ("occasion", "party time", "occasion must be one of"),
            ("season", "monsoon", "season must be one of"),
        ]
        
        for field, invalid_value, expected_error in invalid_context_cases:
            with self.subTest(field=field, value=invalid_value):
                bad_context = valid_context.copy()
                bad_context[field] = invalid_value
                
                with self.assertRaises(ValueError) as cm:
                    self.prompt_engine.build_prompt(valid_weather, bad_context)
                self.assertIn(expected_error, str(cm.exception))
    
    def test_sanitization_comprehensive_scenarios(self):
        """Test output sanitization with comprehensive formatting scenarios."""
        complex_formatting_cases = [
            # Mixed HTML and Markdown
            {
                "input": "<div>**Good morning!** Today is <em>*partly cloudy*</em> with <strong>__temperatures__</strong> around `20°C`.</div>",
                "expected_contains": ["Good morning!", "partly cloudy", "temperatures", "20°C"],
                "expected_excludes": ["<div>", "**", "<em>", "__", "`"]
            },
            
            # Code blocks and complex structures
            {
                "input": """
                # Weather Briefing
                ```python
                temperature = 22
                condition = "sunny"
                ```
                Today will be **sunny** with temps around 22°C.
                """,
                "expected_contains": ["Weather Briefing", "Today will be", "sunny", "22°C"],
                "expected_excludes": ["```", "python", "temperature =", "#"]
            },
            
            # Links and special characters
            {
                "input": "Check [weather.com](http://weather.com) for updates. Temperature > 20°C & humidity < 50%. Say \"hello\" to sunshine!",
                "expected_contains": ["weather.com", "updates", "20°C", "humidity", "50%", "'hello'", "sunshine"],
                "expected_excludes": ["[", "]", "(http://", ")", ">", "<", "&", "\""]
            },
            
            # Excessive whitespace and formatting
            {
                "input": "   Multiple    spaces   and\n\n\nline\t\tbreaks   everywhere   ",
                "expected_result": "Multiple spaces and line breaks everywhere"
            }
        ]
        
        for i, case in enumerate(complex_formatting_cases):
            with self.subTest(case=i):
                result = self.prompt_engine.sanitize_output(case["input"])
                
                if "expected_result" in case:
                    self.assertEqual(result, case["expected_result"])
                else:
                    for expected in case["expected_contains"]:
                        self.assertIn(expected, result)
                    for excluded in case["expected_excludes"]:
                        self.assertNotIn(excluded, result)
    
    def test_prompt_structure_and_sections(self):
        """Test that prompts have proper structure and all required sections."""
        weather_data = {
            "temp_min": 18.0,
            "temp_max": 24.0,
            "description": "mostly sunny",
            "max_precipitation_prob": 0.2,
            "wind_speed": 3.5,
            "humidity": 55,
            "location": "Seattle, WA"
        }
        
        context_data = {
            "day_type": "weekday",
            "day_name": "Thursday",
            "occasion": "work day",
            "season": "fall",
            "location": "Seattle, WA",
            "has_school_kids": False,
            "date_str": "Thursday, October 10, 2024"
        }
        
        prompt = self.prompt_engine.build_prompt(weather_data, context_data)
        
        # Check major sections are present
        required_sections = [
            "You are a friendly morning weather assistant",
            "CONSTRAINTS:",
            "50-70 words exactly",
            "natural, conversational",
            "rain probability",
            "clothing appropriate",
            "OUTPUT REQUIREMENTS:",
            "Plain text only",
            "suitable for voice synthesis",
            "WEATHER DATA:",
            "Location:",
            "Temperature:",
            "Conditions:",
            "Rain probability:",
            "CONTEXT:",
            "Day:",
            "Occasion:",
            "Generate your weather briefing now"
        ]
        
        for section in required_sections:
            self.assertIn(section, prompt)
        
        # Check weather data formatting
        self.assertIn("18-24°C", prompt)  # Temperature range
        self.assertIn("20%", prompt)  # Precipitation percentage
        self.assertIn("mostly sunny", prompt)
        self.assertIn("Seattle, WA", prompt)
        
        # Check context formatting 
        self.assertIn("Thursday", prompt)
        self.assertIn("work day", prompt)
        self.assertIn("Fall weather", prompt)
    
    @patch('prompt_engine.logger')
    def test_sanitization_logging_and_edge_cases(self, mock_logger):
        """Test sanitization logging behavior and edge cases."""
        # Test very long input (should log warning)
        very_long_input = "A" * 600 + " weather briefing content"
        result = self.prompt_engine.sanitize_output(very_long_input)
        
        self.assertEqual(result, very_long_input)  # Should not truncate
        mock_logger.warning.assert_called()
        warning_message = mock_logger.warning.call_args[0][0]
        self.assertIn("may be too verbose for voice", warning_message)
        
        # Test input that becomes empty after cleaning
        empty_after_cleaning = "```   \n  \t  \n```"
        
        with self.assertRaises(ValueError) as cm:
            self.prompt_engine.sanitize_output(empty_after_cleaning)
        self.assertIn("Sanitized output is empty after cleaning", str(cm.exception))
    
    def test_temperature_formatting_precision(self):
        """Test precise temperature formatting scenarios."""
        base_context = {
            "day_type": "weekday",
            "day_name": "Monday",
            "occasion": "work day", 
            "season": "spring",
        }
        
        temperature_cases = [
            # Exactly 2 degree difference (edge case)
            {"temp_min": 20.0, "temp_max": 22.0, "expected": "20-22°C"},
            
            # Just under 2 degree difference
            {"temp_min": 20.0, "temp_max": 21.9, "expected": "around 22°C"},
            
            # Decimal temperatures
            {"temp_min": 15.3, "temp_max": 18.7, "expected": "15-19°C"},
            
            # Single temperature
            {"temp_min": 25.0, "temp_max": 25.0, "expected": "around 25°C"},
        ]
        
        for case in temperature_cases:
            weather_data = {
                "temp_min": case["temp_min"],
                "temp_max": case["temp_max"],
                "description": "test conditions",
                "max_precipitation_prob": 0.0,
                "location": "Test City"
            }
            
            prompt = self.prompt_engine.build_prompt(weather_data, base_context)
            self.assertIn(case["expected"], prompt)
    
    def test_seasonal_context_instructions(self):
        """Test that seasonal context generates appropriate instructions."""
        base_weather = {
            "temp_min": 20.0,
            "temp_max": 25.0,
            "description": "partly cloudy",
            "max_precipitation_prob": 0.2,
            "location": "Test City"
        }
        
        seasonal_expectations = {
            "winter": {
                "instruction": "Winter weather - emphasize warmth and weather protection.",
                "keywords": ["warmth", "weather protection"]
            },
            "summer": {
                "instruction": "Summer weather - consider sun protection and heat comfort.",
                "keywords": ["sun protection", "heat comfort"]
            },
            "spring": {
                "instruction": "Spring weather can be variable - mention layering if appropriate.",
                "keywords": ["variable", "layering"]
            },
            "fall": {
                "instruction": "Fall weather - mention seasonal clothing and potential weather changes.",
                "keywords": ["seasonal clothing", "weather changes"]
            }
        }
        
        for season, expectations in seasonal_expectations.items():
            context_data = {
                "day_type": "weekday",
                "day_name": "Tuesday",
                "occasion": "work day",
                "season": season,
            }
            
            prompt = self.prompt_engine.build_prompt(base_weather, context_data)
            
            # Should contain the instruction
            self.assertIn(expectations["instruction"], prompt)
            
            # Should contain relevant keywords
            for keyword in expectations["keywords"]:
                self.assertIn(keyword, prompt)


if __name__ == '__main__':
    unittest.main()