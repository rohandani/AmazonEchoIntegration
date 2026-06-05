# Alexa Morning Briefing Skill

A serverless voice-first application that automatically delivers personalized daily weather briefings every morning at 7:00 AM through Amazon Echo devices.

## Features

- Automatic 7:00 AM daily briefings via Alexa Routines
- Natural language weather summaries (50-70 words)
- Personalized recommendations based on location and family context
- Multi-tier fallback system for reliability (Groq → Gemini → Template)
- Zero infrastructure costs using free-tier APIs

## Setup

1. **Environment Setup**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit .env with your API keys and preferences
   ```

2. **API Keys Required**
   - OpenWeatherMap API (Free: 1,000 calls/day)
   - Groq API (Free: 14,400 requests/day) 
   - Google Gemini API (Free: 1,500 requests/day)

3. **Development**
   ```bash
   # Install dependencies (when using local development)
   pip install -r requirements.txt
   
   # Run tests
   pytest
   ```

## Deployment

This skill is designed for Alexa-Hosted Lambda deployment:

1. Create a new Custom Skill in Alexa Developer Console
2. Choose "Alexa-Hosted (Python)" as the backend
3. Upload the code files to the Alexa-Hosted code editor
4. Configure environment variables in the Lambda console
5. Deploy and test

## Architecture

- **Backend**: AWS Lambda (Alexa-Hosted)
- **Voice Interface**: Amazon Alexa Skills Kit (ASK)
- **Weather Data**: OpenWeatherMap API
- **AI Processing**: Groq API (primary), Google Gemini (fallback)
- **Runtime**: Python 3.12

## Requirements

See `.kiro/specs/alexa-morning-briefing/requirements.md` for detailed requirements.

## Design

See `.kiro/specs/alexa-morning-briefing/design.md` for technical design details.

## Implementation Tasks

See `.kiro/specs/alexa-morning-briefing/tasks.md` for the complete implementation plan.