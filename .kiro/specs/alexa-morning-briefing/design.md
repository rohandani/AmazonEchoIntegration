# Design Document

## Overview

The Alexa Morning Briefing Skill is designed as a serverless, voice-first application that leverages Amazon's Alexa Skills Kit (ASK) to deliver personalized weather briefings. The system integrates multiple free-tier APIs to create natural language weather summaries while maintaining zero infrastructure costs. The architecture prioritizes reliability through cascading fallback mechanisms and optimizes for voice interaction with sub-8-second response times.

## Architecture

### System Architecture Diagram

```
┌─────────────────┐    Voice Commands    ┌─────────────────┐
│   Amazon Echo   │◄──────────────────►│  Alexa Skills   │
│    Devices      │    TTS Responses    │     Kit (ASK)   │
└─────────────────┘                     └─────────────────┘
                                                 │
                                        HTTPS JSON Request
                                                 │
                                                 ▼
┌──────────────────────────────────────────────────────────┐
│              AWS Lambda (Alexa-Hosted)                   │
│  ┌─────────────────────────────────────────────────────┐ │
│  │           Main Handler (lambda_function.py)         │ │
│  │  ┌────────────────┐  ┌────────────────┐             │ │
│  │  │ WeatherClient  │  │ ContextBuilder │             │ │
│  │  └────────────────┘  └────────────────┘             │ │
│  │  ┌────────────────┐  ┌────────────────┐             │ │
│  │  │ PromptEngine   │  │   LLMClient    │             │ │
│  │  └────────────────┘  └────────────────┘             │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
                        │                    │
              ┌─────────▼─────────┐ ┌─────────▼─────────────┐
              │ OpenWeatherMap    │ │     LLM Services      │
              │  (Free Tier)      │ │  ┌─────────────────┐  │
              │ 1,000 calls/day   │ │  │ Groq (Primary)  │  │
              └───────────────────┘ │  │ 14,400 req/day  │  │
                                    │  └─────────────────┘  │
                                    │  ┌─────────────────┐  │
                                    │  │ Gemini (Backup) │  │
                                    │  │ 1,500 req/day   │  │
                                    │  └─────────────────┘  │
                                    └─────────────────────────┘
```

### Technology Stack

| Layer | Technology | Version/Plan | Cost |
|-------|------------|--------------|------|
| Voice Interface | Amazon Alexa | ASK v1.0 | Free |
| Backend Runtime | AWS Lambda | Python 3.12 | Free (Alexa-Hosted) |
| SDK | ask-sdk-core | v1.19.0+ | Free |
| Weather Data | OpenWeatherMap API | Free tier | $0/month |
| Primary LLM | Groq API | llama-3.3-70b-versatile | $0/month |
| Fallback LLM | Google Gemini | gemini-2.0-flash | $0/month |
| HTTP Client | requests | v2.31.0 | Free |

## Components and Interfaces

### 1. Main Handler (`lambda_function.py`)

**Purpose:** Entry point for all Alexa requests, implements ASK request handlers

**Key Classes:**
- `LaunchRequestHandler`: Handles "Alexa, open Morning Briefing"  
- `MorningBriefingIntentHandler`: Core logic orchestrator
- `HelpIntentHandler`: Provides usage instructions
- `CancelAndStopIntentHandler`: Session termination
- `SessionEndedRequestHandler`: Cleanup

**Interface:**
```python
def lambda_handler(event, context):
    # ASK SDK entry point
    return skill_builder.lambda_handler()(event, context)
```

### 2. Weather Client (`weather_client.py`)

**Purpose:** Abstracts OpenWeatherMap API integration with error handling

**Key Methods:**
```python
class WeatherClient:
    def __init__(self, api_key: str, city: str):
        pass
    
    def get_forecast(self) -> Dict[str, Any]:
        # Returns normalized weather data for next 12 hours
        pass
```

**Output Schema:**
```python
{
    "temp_min": float,           # Celsius
    "temp_max": float,           # Celsius  
    "description": str,          # "light rain", "clear sky"
    "max_precipitation_prob": float,  # 0.0 to 1.0
    "wind_speed": float,         # m/s
    "humidity": int,             # percentage
    "location": str              # "Vancouver, CA"
}
```

### 3. Context Builder (`context_builder.py`)

**Purpose:** Generates contextual metadata for personalized briefings

**Key Methods:**
```python
class ContextBuilder:
    def build_context(self, user_preferences: Dict) -> Dict[str, Any]:
        # Returns day/season/occasion context
        pass
```

**Output Schema:**
```python
{
    "day_type": str,        # "weekday" | "weekend"
    "day_name": str,        # "Monday", "Tuesday", etc.
    "occasion": str,        # "school day" | "work day" | "weekend"
    "season": str,          # "spring", "summer", "fall", "winter"
    "location": str,        # "Vancouver, BC"
    "has_school_kids": bool # from environment variable
}
```

### 4. Prompt Engine (`prompt_engine.py`)

**Purpose:** Assembles LLM prompts with weather data and context

**Key Methods:**
```python
class PromptEngine:
    def build_prompt(self, weather_data: Dict, context: Dict) -> str:
        # Returns complete LLM prompt string
        pass
```

**Template Structure:**
- System instruction (voice-optimized, 70-word limit)
- Current date and day type
- Weather data injection
- Context-aware instructions (school vs weekend)

### 5. LLM Client (`llm_client.py`)

**Purpose:** Manages LLM API calls with automatic fallback logic

**Key Methods:**
```python
class LLMClient:
    def __init__(self, groq_key: str, gemini_key: str):
        pass
    
    def generate_briefing(self, prompt: str) -> str:
        # Primary: Groq -> Fallback: Gemini -> Hardcoded template
        pass
```

**Fallback Chain:**
1. Groq API (200-400ms typical)
2. Google Gemini API (500-800ms typical)  
3. Template-based fallback (always succeeds)

## Data Models

### Weather Data Model
```python
@dataclass
class WeatherForecast:
    temp_min: float
    temp_max: float
    description: str
    precipitation_probability: float
    wind_speed: float
    humidity: int
    location: str
    timestamp: datetime
```

### Context Model
```python
@dataclass  
class BriefingContext:
    day_type: str
    day_name: str
    occasion: str
    season: str
    location: str
    has_school_kids: bool
    date_str: str
```

### Configuration Model
```python
@dataclass
class SkillConfig:
    owm_api_key: str
    groq_api_key: str
    gemini_api_key: str
    user_city: str
    has_school_kids: bool
    
    @classmethod
    def from_environment(cls):
        # Load from Lambda environment variables
        pass
```

## Error Handling

### Error Categories and Responses

| Error Type | Detection | Response Strategy |
|------------|-----------|------------------|
| Weather API Failure | HTTP 4xx/5xx, timeout | Return friendly message: "I couldn't get today's weather. Have a great day!" |
| Groq API Failure | HTTP 4xx/5xx, timeout | Fallback to Gemini API automatically |
| Gemini API Failure | HTTP 4xx/5xx, timeout | Use hardcoded template with basic weather data |
| Invalid API Keys | HTTP 401/403 | Log error, use fallback chain |
| Network Timeouts | requests.Timeout | Retry once, then fallback |
| JSON Parse Errors | ValueError, KeyError | Log error, use fallback data |

### Fallback Response Template
```python
def generate_fallback_response(weather_data: Dict) -> str:
    return f"I'm unable to generate a personalized briefing today. Today in {weather_data.get('location', 'your area')}: {weather_data.get('temp_max', 'N/A')} degrees, {weather_data.get('description', 'conditions unavailable')}. Have a great day!"
```

### Timeout Configuration
```python
TIMEOUTS = {
    'weather_api': 5.0,      # seconds
    'groq_api': 6.0,         # seconds  
    'gemini_api': 6.0,       # seconds
    'lambda_total': 8.0      # Alexa hard limit
}
```

## Testing Strategy

### Unit Testing Approach
- **Mocked External APIs:** Use `responses` library to mock HTTP calls
- **Test Fixtures:** JSON response samples for various weather conditions
- **Coverage Target:** >= 85% code coverage
- **Test Categories:**
  - Weather data parsing (sunny, rainy, extreme conditions)
  - LLM client fallback logic 
  - Prompt template assembly
  - Context generation (weekday vs weekend)

### Integration Testing
- **Real API Calls:** Limited testing with actual API keys
- **End-to-End Verification:** Alexa Simulator testing
- **Device Testing:** Real Echo device validation
- **Performance Testing:** Response time validation under 8 seconds

### Test Data Management
```
tests/
├── fixtures/
│   ├── owm_sunny_day.json
│   ├── owm_rainy_day.json  
│   ├── groq_response.json
│   └── gemini_response.json
└── integration/
    └── test_real_apis.py
```

## Security Considerations

### API Key Management
- **Storage:** Lambda Environment Variables only
- **Access:** No hardcoded keys in source code
- **Rotation:** Manual key rotation supported
- **Validation:** Keys validated on first use

### Request Validation  
- **Alexa Signature Verification:** Handled automatically by ask-sdk-core
- **Input Sanitization:** Weather data sanitized before LLM injection
- **Output Sanitization:** LLM responses stripped of SSML-unsafe characters

### Data Privacy
- **No PII Storage:** No user data persisted beyond request scope
- **API Logs:** External API calls logged without sensitive data
- **Error Logging:** Exception details logged without API keys