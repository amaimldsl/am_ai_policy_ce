# Add this to a new file called deepseek_wrapper.py in your project directory

import time
import logging
from typing import Dict, Any, Optional
import json

class DeepSeekWrapper:
    """Wrapper for DeepSeek API calls to handle errors and retry logic"""
    
    def __init__(self, api_key, api_base, model):
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.logger = logging.getLogger(__name__)
    
    def process_api_response(self, response):
        """Process and validate API response"""
        try:
            # If response is already a Python object, no need to parse
            if isinstance(response, dict):
                return response
                
            # Try parsing as JSON
            parsed_response = json.loads(response)
            return parsed_response
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse DeepSeek API response: {e}")
            self.logger.error(f"Raw response: {response[:500]}...")
            
            # Return a simplified response that won't cause further errors
            return {
                "choices": [
                    {
                        "message": {
                            "content": f"Error processing API response. Please try with smaller input or different parameters."
                        }
                    }
                ]
            }
    
    def chat_completion(self, messages, max_tokens=1024, temperature=0.2):
        """Wrapper for chat completion API with error handling"""
        import openai
        
        # Configure OpenAI client for DeepSeek
        client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.api_base
        )
        
        max_retries = 3
        backoff = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                # Return the validated response
                return self.process_api_response(response)
                
            except Exception as e:
                self.logger.warning(f"DeepSeek API error (attempt {attempt+1}/{max_retries}): {str(e)}")
                
                if attempt < max_retries - 1:
                    wait_time = backoff * (2 ** attempt)  # Exponential backoff
                    self.logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Max retries reached. DeepSeek API call failed.")
                    raise