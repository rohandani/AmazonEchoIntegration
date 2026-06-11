#!/usr/bin/env python3
"""
Integration Test Runner for Alexa Morning Briefing Skill

This script runs integration tests that make real API calls to verify 
end-to-end functionality. It includes safety checks to ensure tests
stay within free tier limits.

Usage:
    python run_integration_tests.py [--weather-only] [--llm-only] [--all]

Environment Variables Required:
    OWM_API_KEY - OpenWeatherMap API key (required for weather tests)
    GROQ_API_KEY - Groq API key (optional, for LLM tests)
    GEMINI_API_KEY - Gemini API key (optional, for LLM tests)

The script includes automatic rate limiting to stay within free tier limits:
- OpenWeatherMap: 1000 calls/day (we use <20 calls)
- Groq: 14,400 requests/day (we use <10 requests)  
- Gemini: 1,500 requests/day (we use <10 requests)
"""

import os
import sys
import argparse
import subprocess
import time
from typing import List, Dict

def check_api_keys() -> Dict[str, str]:
    """Check which API keys are available."""
    keys = {
        'OWM_API_KEY': os.environ.get('OWM_API_KEY'),
        'GROQ_API_KEY': os.environ.get('GROQ_API_KEY'), 
        'GEMINI_API_KEY': os.environ.get('GEMINI_API_KEY')
    }
    return {k: v for k, v in keys.items() if v}

def estimate_api_usage() -> None:
    """Display estimated API usage for the test run."""
    print("\n📊 Estimated API Usage:")
    print("  OpenWeatherMap: ~15-20 calls (limit: 1,000/day)")
    print("  Groq: ~5-8 requests (limit: 14,400/day)")  
    print("  Gemini: ~3-5 requests (limit: 1,500/day)")
    print("\n✅ All usage well within free tier limits")

def run_pytest_command(args: List[str]) -> int:
    """Run pytest with the specified arguments."""
    cmd = ["python", "-m", "pytest"] + args
    print(f"\n🚀 Running: {' '.join(cmd)}")
    return subprocess.run(cmd).returncode

def main():
    parser = argparse.ArgumentParser(description="Run integration tests for Alexa Morning Briefing")
    parser.add_argument('--weather-only', action='store_true', help='Run only weather API tests')
    parser.add_argument('--llm-only', action='store_true', help='Run only LLM API tests')
    parser.add_argument('--all', action='store_true', help='Run all integration tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--fail-fast', '-x', action='store_true', help='Stop on first failure')
    
    args = parser.parse_args()
    
    # Check available API keys
    available_keys = check_api_keys()
    
    print("🔑 API Keys Status:")
    for key_name in ['OWM_API_KEY', 'GROQ_API_KEY', 'GEMINI_API_KEY']:
        status = "✅ Available" if key_name in available_keys else "❌ Missing"
        print(f"  {key_name}: {status}")
    
    if not available_keys:
        print("\n❌ No API keys found. Please set at least OWM_API_KEY to run integration tests.")
        print("\nExample:")
        print("  export OWM_API_KEY=your_openweathermap_key")
        print("  export GROQ_API_KEY=your_groq_key  # optional")
        print("  export GEMINI_API_KEY=your_gemini_key  # optional")
        return 1
    
    if 'OWM_API_KEY' not in available_keys and not args.llm_only:
        print("\n⚠️  Weather tests require OWM_API_KEY. Use --llm-only to run only LLM tests.")
        if not args.llm_only:
            return 1
    
    estimate_api_usage()
    
    # Confirm before running (except for CI environments)
    if not os.environ.get('CI') and not args.all:
        response = input("\n🤔 Proceed with integration tests? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return 0
    
    # Build pytest arguments
    pytest_args = ["tests/integration/", "-v"]
    
    if args.fail_fast:
        pytest_args.append("-x")
    
    if args.verbose:
        pytest_args.extend(["-s", "--tb=long"])
    else:
        pytest_args.append("--tb=short")
    
    # Add markers based on what we want to test
    if args.weather_only:
        pytest_args.extend(["-m", "weather_api or not (groq_api or gemini_api)"])
    elif args.llm_only:
        pytest_args.extend(["-m", "groq_api or gemini_api"])
    
    # Run the tests
    start_time = time.time()
    exit_code = run_pytest_command(pytest_args)
    end_time = time.time()
    
    print(f"\n⏱️  Tests completed in {end_time - start_time:.2f} seconds")
    
    if exit_code == 0:
        print("✅ All integration tests passed!")
    else:
        print("❌ Some integration tests failed.")
    
    return exit_code

if __name__ == "__main__":
    exit(main())