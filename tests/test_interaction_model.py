"""
Tests for Alexa Skill interaction model configuration and intent resolution.

Validates that the skill.json manifest and interaction model are properly
configured with correct intents, sample utterances, and invocation name.
"""

import json
import pytest
from pathlib import Path


class TestInteractionModel:
    """Test Alexa Skill interaction model configuration."""
    
    @pytest.fixture
    def skill_manifest(self):
        """Load skill.json manifest."""
        skill_path = Path("skill-package/skill.json")
        with open(skill_path, 'r') as f:
            return json.load(f)
    
    @pytest.fixture
    def interaction_model(self):
        """Load interaction model for en-US."""
        model_path = Path("skill-package/interactionModels/custom/en-US.json")
        with open(model_path, 'r') as f:
            return json.load(f)
    
    def test_skill_manifest_structure(self, skill_manifest):
        """Test that skill.json has proper manifest structure."""
        # Validate top-level structure
        assert "manifest" in skill_manifest
        manifest = skill_manifest["manifest"]
        
        # Check required sections
        assert "publishingInformation" in manifest
        assert "apis" in manifest
        assert "manifestVersion" in manifest
        assert "permissions" in manifest
        assert "privacyAndCompliance" in manifest
        
        # Validate manifest version
        assert manifest["manifestVersion"] == "1.0"
    
    def test_publishing_information(self, skill_manifest):
        """Test publishing information configuration."""
        pub_info = skill_manifest["manifest"]["publishingInformation"]
        
        # Check locales
        assert "locales" in pub_info
        assert "en-US" in pub_info["locales"]
        
        en_us = pub_info["locales"]["en-US"]
        
        # Validate required fields
        assert "name" in en_us
        assert en_us["name"] == "Morning Briefing"
        
        assert "summary" in en_us
        assert "weather briefings" in en_us["summary"].lower()
        
        assert "description" in en_us
        assert "morning briefing" in en_us["description"].lower()
        
        # Check example phrases
        assert "examplePhrases" in en_us
        example_phrases = en_us["examplePhrases"]
        assert len(example_phrases) >= 3
        
        # Validate that key phrases are present
        phrases_text = " ".join(example_phrases).lower()
        assert "morning briefing" in phrases_text
        assert "weather" in phrases_text
        
        # Check category
        assert pub_info["category"] == "WEATHER"
    
    def test_api_configuration(self, skill_manifest):
        """Test API configuration for custom skill."""
        apis = skill_manifest["manifest"]["apis"]
        
        # Check custom API configuration
        assert "custom" in apis
        custom = apis["custom"]
        
        # Validate endpoint structure
        assert "endpoint" in custom
        assert "uri" in custom["endpoint"]
        
        # Should be Lambda ARN format (placeholder is OK for testing)
        endpoint_uri = custom["endpoint"]["uri"]
        assert endpoint_uri.startswith("arn:aws:lambda:")
        assert "function:" in endpoint_uri
        
        # Interfaces should be empty list (no special interfaces needed)
        assert "interfaces" in custom
        assert isinstance(custom["interfaces"], list)
    
    def test_permissions_configuration(self, skill_manifest):
        """Test permissions configuration."""
        permissions = skill_manifest["manifest"]["permissions"]
        
        # Should be empty list for this skill (no special permissions needed)
        assert isinstance(permissions, list)
        assert len(permissions) == 0  # No special permissions required
    
    def test_privacy_compliance(self, skill_manifest):
        """Test privacy and compliance configuration."""
        privacy = skill_manifest["manifest"]["privacyAndCompliance"]
        
        # Validate privacy settings
        assert "allowsPurchases" in privacy
        assert privacy["allowsPurchases"] is False
        
        assert "usesPersonalInfo" in privacy
        assert privacy["usesPersonalInfo"] is False
        
        assert "isChildDirected" in privacy
        assert privacy["isChildDirected"] is False
        
        assert "containsAds" in privacy
        assert privacy["containsAds"] is False
        
        assert "isExportCompliant" in privacy
        assert privacy["isExportCompliant"] is True
    
    def test_interaction_model_structure(self, interaction_model):
        """Test interaction model basic structure."""
        # Validate top-level structure
        assert "interactionModel" in interaction_model
        model = interaction_model["interactionModel"]
        
        # Check language model
        assert "languageModel" in model
        lang_model = model["languageModel"]
        
        # Validate required fields
        assert "invocationName" in lang_model
        assert "intents" in lang_model
        assert "types" in lang_model
    
    def test_invocation_name(self, interaction_model):
        """Test that invocation name is correctly set."""
        lang_model = interaction_model["interactionModel"]["languageModel"]
        
        # Validate invocation name
        assert lang_model["invocationName"] == "morning briefing"
    
    def test_required_amazon_intents(self, interaction_model):
        """Test that all required Amazon built-in intents are present."""
        lang_model = interaction_model["interactionModel"]["languageModel"]
        intents = lang_model["intents"]
        
        # Extract intent names
        intent_names = {intent["name"] for intent in intents}
        
        # Validate required Amazon intents
        required_intents = {
            "AMAZON.CancelIntent",
            "AMAZON.HelpIntent", 
            "AMAZON.StopIntent"
        }
        
        for required_intent in required_intents:
            assert required_intent in intent_names, f"Missing required intent: {required_intent}"
    
    def test_morning_briefing_intent(self, interaction_model):
        """Test MorningBriefingIntent configuration."""
        lang_model = interaction_model["interactionModel"]["languageModel"]
        intents = lang_model["intents"]
        
        # Find MorningBriefingIntent
        morning_intent = None
        for intent in intents:
            if intent["name"] == "MorningBriefingIntent":
                morning_intent = intent
                break
        
        assert morning_intent is not None, "MorningBriefingIntent not found"
        
        # Validate intent structure
        assert "samples" in morning_intent
        assert "slots" in morning_intent
        
        # Should have no slots (simple intent)
        assert isinstance(morning_intent["slots"], list)
        assert len(morning_intent["slots"]) == 0
        
        # Validate sample utterances
        samples = morning_intent["samples"]
        assert isinstance(samples, list)
        assert len(samples) >= 5, "Should have at least 5 sample utterances"
        
        # Convert samples to lowercase for checking
        samples_text = " ".join(samples).lower()
        
        # Check for key phrases that should be covered
        expected_phrases = [
            "weather",
            "briefing", 
            "wear today",
            "weather like",
            "outside"
        ]
        
        for phrase in expected_phrases:
            assert phrase in samples_text, f"Missing sample utterance coverage for: {phrase}"
    
    def test_sample_utterance_variety(self, interaction_model):
        """Test that sample utterances cover different ways to invoke the skill."""
        lang_model = interaction_model["interactionModel"]["languageModel"]
        intents = lang_model["intents"]
        
        # Find MorningBriefingIntent
        morning_intent = None
        for intent in intents:
            if intent["name"] == "MorningBriefingIntent":
                morning_intent = intent
                break
        
        samples = morning_intent["samples"]
        
        # Check for variety in utterance patterns
        utterance_patterns = {
            "question": False,  # "what's the weather like"
            "command": False,   # "give me the weather"
            "clothing": False,  # "what should I wear today"
            "general": False    # "weather briefing"
        }
        
        for sample in samples:
            sample_lower = sample.lower()
            
            if sample_lower.startswith("what"):
                utterance_patterns["question"] = True
            if "give me" in sample_lower or "weather briefing" in sample_lower:
                utterance_patterns["command"] = True
            if "wear" in sample_lower or "clothing" in sample_lower:
                utterance_patterns["clothing"] = True
            if "weather" in sample_lower and not sample_lower.startswith("what"):
                utterance_patterns["general"] = True
        
        # Ensure we have variety in utterance types
        assert utterance_patterns["question"], "Missing question-style utterances"
        assert utterance_patterns["command"], "Missing command-style utterances"  
        assert utterance_patterns["clothing"], "Missing clothing-related utterances"
    
    def test_intent_resolution_coverage(self, interaction_model):
        """Test that intent resolution covers the main use cases."""
        lang_model = interaction_model["interactionModel"]["languageModel"]
        
        # Test cases that should resolve to MorningBriefingIntent
        test_utterances = [
            "give me the weather",
            "what's the weather like",
            "weather briefing", 
            "what should I wear today",
            "how's the weather",
            "weather update",
            "daily briefing",
            "what's it like outside"
        ]
        
        # Get MorningBriefingIntent samples
        morning_intent = None
        for intent in lang_model["intents"]:
            if intent["name"] == "MorningBriefingIntent":
                morning_intent = intent
                break
        
        samples = morning_intent["samples"]
        
        # Each test utterance should match at least one sample (exact match for this test)
        for test_utterance in test_utterances:
            assert test_utterance in samples, f"Test utterance not covered: {test_utterance}"
    
    def test_no_conflicting_intents(self, interaction_model):
        """Test that there are no conflicting intent patterns."""
        lang_model = interaction_model["interactionModel"]["languageModel"]
        intents = lang_model["intents"]
        
        # Collect all sample utterances
        all_samples = []
        for intent in intents:
            if "samples" in intent:
                for sample in intent["samples"]:
                    all_samples.append((intent["name"], sample))
        
        # Check for duplicate samples across different intents
        sample_counts = {}
        for intent_name, sample in all_samples:
            if sample in sample_counts:
                # Same sample used in multiple intents
                pytest.fail(f"Duplicate sample utterance '{sample}' found in intents: {sample_counts[sample]} and {intent_name}")
            sample_counts[sample] = intent_name
    
    def test_types_configuration(self, interaction_model):
        """Test custom slot types configuration."""
        lang_model = interaction_model["interactionModel"]["languageModel"]
        
        # Should be empty list (no custom slot types needed)
        assert "types" in lang_model
        types = lang_model["types"]
        assert isinstance(types, list)
        assert len(types) == 0  # No custom types needed for this skill


class TestIntentResolutionSimulation:
    """Simulate intent resolution to validate utterance handling."""
    
    @pytest.fixture
    def interaction_model(self):
        """Load interaction model for testing."""
        model_path = Path("skill-package/interactionModels/custom/en-US.json")
        with open(model_path, 'r') as f:
            return json.load(f)
    
    def test_morning_briefing_utterances(self, interaction_model):
        """Test that common user utterances would resolve to MorningBriefingIntent."""
        lang_model = interaction_model["interactionModel"]["languageModel"]
        
        # Common user utterances that should work
        common_utterances = [
            "give me the weather",
            "what's the weather like today",
            "what should I wear",
            "weather briefing please",
            "how's the weather outside",
            "daily weather update"
        ]
        
        # Get MorningBriefingIntent samples for reference
        morning_samples = []
        for intent in lang_model["intents"]:
            if intent["name"] == "MorningBriefingIntent":
                morning_samples = intent["samples"]
                break
        
        # Simulate basic intent resolution (keyword matching)
        for utterance in common_utterances:
            should_match = False
            utterance_lower = utterance.lower()
            
            # Check if utterance contains key weather-related terms
            weather_keywords = ["weather", "briefing", "wear", "outside"]
            for keyword in weather_keywords:
                if keyword in utterance_lower:
                    should_match = True
                    break
            
            assert should_match, f"Utterance '{utterance}' should match MorningBriefingIntent"
            
            # Additional check: utterance should be similar to existing samples
            # (In a real implementation, this would use NLU similarity)
            has_similar_sample = False
            for sample in morning_samples:
                sample_words = set(sample.lower().split())
                utterance_words = set(utterance_lower.split())
                
                # Simple overlap check (at least 1 word in common)
                if sample_words & utterance_words:
                    has_similar_sample = True
                    break
            
            assert has_similar_sample, f"Utterance '{utterance}' should have similar samples in training data"
    
    def test_help_intent_utterances(self, interaction_model):
        """Test utterances that should resolve to AMAZON.HelpIntent."""
        # These should NOT match MorningBriefingIntent
        help_utterances = [
            "help",
            "what can you do",
            "how does this work",
            "help me"
        ]
        
        lang_model = interaction_model["interactionModel"]["languageModel"]
        morning_samples = []
        for intent in lang_model["intents"]:
            if intent["name"] == "MorningBriefingIntent":
                morning_samples = [s.lower() for s in intent["samples"]]
                break
        
        # These utterances should not be in MorningBriefingIntent samples
        for utterance in help_utterances:
            assert utterance.lower() not in morning_samples, f"Help utterance '{utterance}' should not be in MorningBriefingIntent"
    
    def test_stop_cancel_intent_utterances(self, interaction_model):
        """Test utterances that should resolve to stop/cancel intents."""
        stop_cancel_utterances = [
            "stop",
            "cancel", 
            "exit",
            "quit"
        ]
        
        lang_model = interaction_model["interactionModel"]["languageModel"]
        morning_samples = []
        for intent in lang_model["intents"]:
            if intent["name"] == "MorningBriefingIntent":
                morning_samples = [s.lower() for s in intent["samples"]]
                break
        
        # These utterances should not be in MorningBriefingIntent samples
        for utterance in stop_cancel_utterances:
            assert utterance.lower() not in morning_samples, f"Stop/cancel utterance '{utterance}' should not be in MorningBriefingIntent"