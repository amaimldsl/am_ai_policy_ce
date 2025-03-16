import time
import logging
import json

class DeepSeekWrapper:
    """Wrapper for DeepSeek API calls to handle errors and retry logic"""
    
    def __init__(self, api_key, api_base, model):
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.logger = logging.getLogger(__name__)
    
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
                return response
                
            except Exception as e:
                self.logger.warning(f"DeepSeek API error (attempt {attempt+1}/{max_retries}): {str(e)}")
                
                if attempt < max_retries - 1:
                    wait_time = backoff * (2 ** attempt)  # Exponential backoff
                    self.logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Max retries reached. DeepSeek API call failed.")
                    raise