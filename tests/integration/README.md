# Integration Testing Guide

This directory contains integration tests that verify the Alexa Morning Briefing Skill works correctly with real APIs. These tests make actual network calls to external services to ensure end-to-end functionality.

## Overview

Integration tests verify:
- **Weather API Integration**: Real calls to OpenWeatherMap API
- **LLM API Integration**: Real calls to Groq and/or Gemini APIs  
- **End-to-End Pipeline**: Complete briefing generation workflow
- **Performance Requirements**: Response time and throughput testing
- **Error Handling**: Resilience with API failures and rate limiting

## Setup Requirements

### API Keys Required

You'll need API keys for the services you want to test:

1. **OpenWeatherMap API Key** (Required for weather tests)
   - Get free key at: https://openweathermap.org/api
   - Free tier: 1,000 calls/day
   - Set as: `export OWM_API_KEY=your_key_here`

2. **Groq API Key** (Optional for LLM tests)
   - Get free key at: https://console.groq.com/
   - Free tier: 14,400 requests/day  
   - Set as: `export GROQ_API_KEY=your_key_here`

3. **Gemini API Key** (Optional for LLM tests)
   - Get free key at: https://aistudio.google.com/app/apikey
   - Free tier: 1,500 requests/day
   - Set as: `export GEMINI_API_KEY=your_key_here`

### Environment Variables

```bash
# Required for weather tests
export OWM_API_KEY=your_openweathermap_api_key

# Optional for LLM tests (need at least one)  
export GROQ_API_KEY=your_groq_api_key
export GEMINI_API_KEY=your_gemini_api_key
```

## Running Integration Tests

### Using the Test Runner (Recommended)

```bash
# Run all available tests
python run_integration_tests.py --all

# Run only weather API tests
python run_integration_tests.py --weather-only

# Run only LLM API tests  
python run_integration_tests.py --llm-only

# Run with verbose output
python run_integration_tests.py --all --verbose

# Stop on first failure
python run_integration_tests.py --all --fail-fast
```

### Using pytest directly

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific test classes
pytest tests/integration/test_real_apis.py::TestWeatherClientIntegration -v
pytest tests/integration/test_real_apis.py::TestLLMClientIntegration -v
pytest tests/integration/test_real_apis.py::TestEndToEndIntegration -v

# Run with markers
pytest tests/integration/ -m weather_api -v
pytest tests/integration/ -m groq_api -v
pytest tests/integration/ -m gemini_api -v
```

## Test Categories

### Weather API Tests (`TestWeatherClientIntegration`)

- **Major Cities Test**: Verifies weather data retrieval for cities worldwide
- **Error Handling Test**: Tests invalid city names and API error responses  
- **Performance Test**: Ensures API calls complete within timeout limits

### LLM API Tests (`TestLLMClientIntegration`)

- **Groq API Test**: Tests weather briefing generation with Groq
- **Gemini API Test**: Tests weather briefing generation with Gemini
- **Fallback Integration**: Tests automatic fallback between LLM services

### End-to-End Tests (`TestEndToEndIntegration`)

- **Complete Pipeline**: Tests full weather → context → prompt → LLM → sanitization flow
- **Error Resilience**: Tests graceful degradation with missing API keys
- **Rate Limiting**: Verifies compliance with free tier limits

### Performance Tests (`TestSystemPerformance`)

- **Response Time**: Tests pipeline completes within Alexa's 8-second limit
- **Concurrent Load**: Tests behavior with multiple simultaneous requests

## API Usage and Rate Limits

Our integration tests are designed to stay well within free tier limits:

| Service | Free Tier Limit | Test Usage | Safety Margin |
|---------|-----------------|------------|---------------|
| OpenWeatherMap | 1,000 calls/day | ~20 calls | 98% available |
| Groq | 14,400 requests/day | ~10 requests | 99.9% available |
| Gemini | 1,500 requests/day | ~10 requests | 99.3% available |

### Built-in Rate Limiting

Tests include automatic rate limiting:
- OpenWeatherMap: 1 second between calls
- Groq: 0.5 seconds between calls  
- Gemini: 1 second between calls

## Test Execution Guidance

### Frequency Recommendations

- **Development**: Run weather-only tests frequently (`--weather-only`)
- **Feature Testing**: Run full suite before major changes (`--all`)
- **CI/CD**: Run daily or on release branches (automated)
- **Debugging**: Run specific test classes for focused testing

### Troubleshooting

**Tests Skip with "requires API key"**
- Check environment variables are set correctly
- Verify API keys are valid and active

**Tests Fail with Timeout Errors**
- Check internet connectivity
- Verify API services are operational
- Try running fewer tests concurrently

**Tests Fail with Rate Limit Errors**
- Wait a few minutes and retry
- Check if you've exceeded daily limits
- Increase rate limiting delays if needed

## CI/CD Integration

For automated testing in CI/CD pipelines:

```bash
# Set API keys as secrets in your CI system
export OWM_API_KEY=${{ secrets.OWM_API_KEY }}
export GROQ_API_KEY=${{ secrets.GROQ_API_KEY }}
export GEMINI_API_KEY=${{ secrets.GEMINI_API_KEY }}

# Run tests with CI flag (skips confirmations)
CI=true python run_integration_tests.py --all --fail-fast
```

## Best Practices

1. **Start Small**: Begin with weather-only tests to verify basic connectivity
2. **Gradual Expansion**: Add LLM tests once weather tests are working
3. **Monitor Usage**: Keep track of daily API usage to avoid limits
4. **Test Isolation**: Each test is independent and can run in any order
5. **Error Simulation**: Tests include both success and failure scenarios

## Security Notes

- Never commit API keys to version control
- Use environment variables or secure secret management
- Rotate API keys periodically
- Monitor API key usage in provider dashboards

## Support

If integration tests fail:

1. Check the specific error messages in test output
2. Verify API keys are valid and have sufficient quota
3. Test individual APIs manually using curl or Postman
4. Check API provider status pages for service outages
5. Review rate limiting and adjust delays if needed

For questions or issues, refer to the main project documentation or create an issue in the repository.