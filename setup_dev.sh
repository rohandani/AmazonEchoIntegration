#!/bin/bash

# Development environment setup script for Alexa Morning Briefing Skill
# This creates a local virtual environment for testing and development

echo "Setting up development environment..."

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

echo "Development environment setup complete!"
echo "To activate the virtual environment, run: source venv/bin/activate"
echo "To deactivate, run: deactivate"
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and add your API keys"
echo "2. Run tests with: pytest"