#!/usr/bin/env python3
"""
Thalamus Utility Functions

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
import requests
import json
import re
from typing import Optional, Tuple, Dict, Any
from logging_config import setup_logging, get_logger

# Initialize centralized logging
setup_logging()
logger = get_logger(__name__)

def get_image_dimensions(image_path: str) -> Optional[Tuple[int, int]]:
    """
    Returns (width, height) of a given image file.
    """
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            return img.size  # returns (width, height)
    except ImportError:
        logger.warning("PIL not installed. Image dimension functionality not available.")
        return None
    
def load_prompt(filename: str, prompts_dir: str = "./prompts") -> str:
    """Load a prompt from a markdown (.md) file."""
    prompt_path = os.path.join(prompts_dir, filename)
    try:
        with open(prompt_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        logger.error("Prompt file '%s' not found in '%s'.", filename, prompts_dir)
        raise


def clean_response(response: str, return_dict: bool = False) -> str | Dict[str, Any]:
    """
    Cleans and processes a JSON response safely.

    Steps:
    1. Removes markdown code fences if present.
    2. Strips leading/trailing whitespace.
    3. Uses regex to extract JSON if standard parsing fails.
    
    Args:
        response (str): The raw JSON response string.
        return_dict (bool): If True, returns a Python dictionary. If False (default), returns the cleaned JSON string.

    Returns:
        str | dict: A cleaned JSON string (default) or a parsed Python dictionary.

    Raises:
        json.JSONDecodeError if the input cannot be parsed.
    """

    # Step 1: Remove markdown-style code fences if present.
    if response.startswith("```"):
        lines = response.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        response = "\n".join(lines)

    # Step 2: Ensure response is a string and strip whitespace
    if not isinstance(response, str):
        try:
            response = str(response)
        except Exception as e:
            logging.error("Error converting response to string: %s", e)
            raise e
    response = response.strip()

    # Step 3: If the string is empty, return an empty JSON string or empty dict
    if not response:
        return "{}" if not return_dict else {}

    # Step 4: Try standard JSON parsing
    try:
        parsed_json = json.loads(response)
        return parsed_json if return_dict else json.dumps(parsed_json)
    except json.JSONDecodeError as e:
        # Step 5: Try extracting JSON using regex
        match = re.search(r'({.*})', response, re.DOTALL)
        if match:
            try:
                parsed_json = json.loads(match.group(1))
                return parsed_json if return_dict else match.group(1)
            except json.JSONDecodeError:
                pass
        logger.error("Failed to parse JSON: %s", e)
        raise e


def get_image_url(image_input: str) -> str:
    """
    If the image_input is a URL, return it. Otherwise, ensure the file exists and upload it.
    """
    if image_input.startswith("http://") or image_input.startswith("https://"):
        return image_input
    if not os.path.isfile(image_input):
        raise FileNotFoundError(f"Local file not found: {image_input}")
    return upload_local_file(image_input)

def upload_local_file(file_path: str) -> str:
    """
    Upload a local file to a temporary file hosting service and return the URL.
    """
    upload_url = "https://tmpfiles.org/api/v1/upload"
    with open(file_path, "rb") as f:
        files = {"file": f}
        response = requests.post(upload_url, files=files)
    response.raise_for_status()
    data = response.json()
    if "data" in data:
        file_url = data["data"].get("file") or data["data"].get("url")
    else:
        file_url = data.get("url")
    if not file_url:
        raise Exception("Could not retrieve file URL from tmpfiles.org response: " + str(data))
    if "tmpfiles.org" in file_url and "/dl/" not in file_url:
        file_url = file_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
    return file_url
