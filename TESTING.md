# Testing Guide for Alexa Morning Briefing Skill

This guide explains how to run the comprehensive test suite for the Alexa Morning Briefing Skill.

## Test Structure

The project includes two types of testing:

### 1. Unit Tests (No API Keys Required)
- **Location**: `tests/` (excluding `tests/integration/`)
- **Purpose**: Test individual components with mocked dependencies
- **Coverage**: 192+ tests across all modules
- **Runtime**: ~12 seconds

### 2. Integration Tests (API Keys Required)
- **Location**: `tests/integration/`
- **Purpose**: Test real API interactions and end-to-end workflows
- **Coverage**: Weather API, LLM APIs, complete pipeline
- **Runtime**: Variable (depends on API response times)

## Running Unit Tests

Unit tests run automatically with pre-configured test environment variables. No setup needed:

```bash
# Run all unit tests
python -m pytest tests/ -v -k "not integration"

# Run specific modules
python -m pytest tests/test_weather_client.py -v
python -m pytest tests/test_llm_client.py -v
python -m pytest tests/test_context_builder.py -v
python -m pytest tests/test_prompt_engine.py -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html -k "not integration"
```

### Test Environment Variables

Unit tests automatically use these test values:
```bash
OWM_API_KEY=test_openweathermap_api_key_for_unit_tests
GROQ_API_KEY=test_groq_api_key_for_unit_tests  
GEMINI_API_KEY=test_gemini_api_key_for_unit_tests
USER_CITY=TestCity,CA
HAS_SCHOOL_KIDS=false
```

## Running Integration Tests

Integration tests require real API keys. See [`tests/integration/README.md`](tests/integration/README.md) for detailed setup.

### Quick Start

1. **Get API Keys** (all free tier):
   - [OpenWeatherMap](https://openweathermap.org/api) (required)
   - [Groq](https://console.groq.com/) (optional)  
   - [Gemini](https://aistudio.google.com/app/apikey) (optional)

2. **Set Environment Variables**:
   ```bash
   export OWM_API_KEY=your_openweathermap_key
   export GROQ_API_KEY=your_groq_key      # optional
   export GEMINI_API_KEY=your_gemini_key  # optional
   ```

3. **Run Integration Tests**:
   ```bash
   # Use the test runner (recommended)
   python run_integration_tests.py --all
   
   # Or use pytest directly
   pytest tests/integration/ -v
   ```

## Environment Configuration

### For Development (.env file)

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
# Edit .env with your actual API keys
```

### For CI/CD

Set these environment variables in your CI system:

```bash
OWM_API_KEY=your_weather_api_key
GROQ_API_KEY=your_groq_key      # optional
GEMINI_API_KEY=your_gemini_key  # optional  
USER_CITY=Vancouver,CA
HAS_SCHOOL_KIDS=false
```

## Test Configuration Requirements

The system requires:

1. **Weather API Key** (always required): `OWM_API_KEY`
2. **At least one LLM API Key**: `GROQ_API_KEY` OR `GEMINI_API_KEY` 
3. **User Configuration**: `USER_CITY` in format "City,CountryCode"
4. **Optional Settings**: `HAS_SCHOOL_KIDS` (defaults to false)

### Fallback Behavior

The system gracefully handles missing LLM API keys:
- **Both present**: Uses Groq first, falls back to Gemini
- **Groq only**: Uses Groq, falls back to template
- **Gemini only**: Uses Gemini, falls back to template  
- **Neither present**: Uses template only (error in production)

## Common Testing Commands

```bash
# Run all tests (unit + integration if keys available)
python -m pytest

# Run only unit tests (fast, no API keys needed)
python -m pytest -k "not integration"

# Run only integration tests
python -m pytest tests/integration/ -v

# Run with verbose output and stop on first failure
python -m pytest -v -x

# Run specific test function
python -m pytest tests/test_weather_client.py::TestWeatherClient::test_get_forecast_sunny_day -v

# Run tests matching a pattern
python -m pytest -k "weather" -v
```

## Troubleshooting

### Unit Tests Failing
- Check that you're using Python 3.12+ 
- Install dependencies: `pip install -r requirements.txt`
- Run: `python -m pytest tests/test_config.py -v` to verify environment setup

### Integration Tests Skipping  
- Verify API keys are set: `echo $OWM_API_KEY`
- Check API key validity by testing manually
- Review [`tests/integration/README.md`](tests/integration/README.md) for detailed troubleshooting

### Configuration Errors
- Ensure `USER_CITY` format is "City,CountryCode" (e.g., "Vancouver,CA")
- Verify at least one LLM API key is set (`GROQ_API_KEY` or `GEMINI_API_KEY`)
- Check API keys are not placeholder values

## Test Coverage

Current test coverage includes:

- **Weather Client**: API integration, error handling, data normalization
- **LLM Client**: Groq/Gemini APIs, fallback logic, template system
- **Context Builder**: Date/time logic, seasonal calculations, family context
- **Prompt Engine**: Template assembly, output sanitization, validation
- **Lambda Handlers**: Alexa request handling, error scenarios
- **Configuration**: Environment loading, validation, error handling

## Performance Testing

Integration tests include performance validation:
- **Weather API**: < 5 seconds per call
- **LLM APIs**: < 6 seconds per call
- **Complete Pipeline**: < 8 seconds (Alexa requirement)
- **Concurrent Load**: Multiple simultaneous requests

Run performance tests specifically:
```bash
python -m pytest tests/integration/test_real_apis.py::TestSystemPerformance -v
```