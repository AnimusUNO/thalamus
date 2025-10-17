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
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
from logging_config import setup_logging, get_logger
from error_handler import handle_api_error

# Initialize centralized logging
setup_logging()
logger = get_logger(__name__)

# Load environment variables
load_dotenv()

# Lazily initialized OpenAI client to avoid import-time failures in tests
client: Optional[OpenAI] = None


def get_openai_client() -> OpenAI:
    """Return a shared OpenAI client, creating it on first use."""
    global client
    if client is not None:
        return client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Defer raising to call sites that need the client
        raise RuntimeError("OPENAI_API_KEY is not set; unable to initialize OpenAI client")
    client = OpenAI(api_key=api_key)
    return client

def call_openai_text(prompt: str) -> str:
    """Call OpenAI API with text prompt and return response."""
    try:
        # Ensure prompt is a string
        if isinstance(prompt, dict):
            prompt = json.dumps(prompt)
        
        # Call OpenAI API using modern client
        response = get_openai_client().chat.completions.create(
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
        handle_api_error("call_openai_text", e, rethrow=True)

if __name__ == '__main__':
    # Test the API
    try:
        result = call_openai_text("Hello, how are you?")
        print(result)
    except Exception as e:
        logger.error("Error in test call: %s", e)
        print("Error:", e)
