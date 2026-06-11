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


if __name__ == '__main__':
    unittest.main()