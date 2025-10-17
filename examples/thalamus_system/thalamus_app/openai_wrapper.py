#!/usr/bin/env python3
"""
Thalamus OpenAI API Wrapper

Copyright (C) 2025 Mark "Rizzn" Hopkins, Athena Vernal, John Casaretto

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
from logging_config import setup_logging, get_logger

# Initialize centralized logging
setup_logging()
logger = get_logger(__name__)

# Load environment variables
load_dotenv()

"""Lazy-initialized OpenAI client to avoid import-time failures in tests.

Tests often patch the module-level `client` symbol. We therefore expose a
module-level `client` variable initialized to None and only construct the
real client on first use inside `call_openai_text` if it hasn't been patched
by tests and an API key is available in the environment.
"""
client = None  # Will be created on first use or patched by tests

def call_openai_text(prompt: str) -> str:
    """Call OpenAI API with text prompt and return response."""
    try:
        # Ensure prompt is a string
        if isinstance(prompt, dict):
            prompt = json.dumps(prompt)
        
        # Create the client on first use if tests haven't patched it
        global client
        if client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY is not set and no test client is patched")
            client = OpenAI(api_key=api_key)

        # Call OpenAI API using modern client
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides responses in valid JSON format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=100
        )
        
        # Extract response text
        response_text = response.choices[0].message.content
        
        # Log response for debugging
        logger.debug(f"OpenAI Response: {response_text}")
        
        return response_text
        
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        raise

if __name__ == '__main__':
    # Test the API
    try:
        result = call_openai_text("Hello, how are you?")
        print(result)
    except Exception as e:
        logger.error("Error in test call: %s", e)
        print("Error:", e)
