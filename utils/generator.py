# Groq LLM Generator Utility
# Handles communication with the Groq API for text generation across all modes.
# Provides async generation with error handling and retry logic.

import os
import httpx
import asyncio
from typing import Optional, Dict, Any
import json
import logging
from .cache import get_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GroqGenerator:
    """
    Groq LLM Generator for text completion and enrichment.
    Handles API communication, error handling, and response processing.
    """
    
    def __init__(self, enable_cache: bool = True):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")

        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.3-70b-versatile"  # Default model
        self.timeout = 30.0  # Request timeout in seconds
        self.max_retries = 3  # Maximum retry attempts
        self.enable_cache = enable_cache
        self.cache = get_cache() if enable_cache else None
        
        # Default generation parameters
        self.default_params = {
            "temperature": 0.3,
            "top_p": 0.9,
            "max_tokens": 300,
            "stream": False
        }
        
        # Model-specific configurations
        self.model_configs = {
            "llama3-8b-8192": {
                "max_tokens": 8192,
                "temperature": 0.3,
                "top_p": 0.9,
                "description": "Fast 8B parameter model with 8K context window"
            },
            "llama3-70b-8192": {
                "max_tokens": 8192,
                "temperature": 0.3,
                "top_p": 0.9,
                "description": "Powerful 70B parameter model with 8K context window"
            },
            "llama-3.1-8b-instant": {
                "max_tokens": 2048,
                "temperature": 0.3,
                "top_p": 0.9,
                "description": "Quick 8B parameter model optimized for instant responses"
            },
            "llama-3.3-70b-versatile": {
                "max_tokens": 4096,
                "temperature": 0.3,
                "top_p": 0.9,
                "description": "Versatile 70B parameter model with balanced performance"
            }
        }
    
    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = None,
        top_p: float = None,
        max_tokens: int = None,
        model: str = None,
        use_cache: bool = True
    ) -> str:

        # Check cache first if enabled
        if self.enable_cache and use_cache and self.cache:
            cache_key_params = {
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
                "model": model or self.model
            }
            cached_result = self.cache.get(system_prompt, user_message, **cache_key_params)
            if cached_result:
                logger.info("Returning cached result")
                return cached_result

        # Get model-specific parameters
        model_name = model or self.model
        model_config = self.model_configs.get(model_name, {})
        
        # Prepare request parameters
        params = self.default_params.copy()
        # Only include valid API parameters
        for key in ["max_tokens", "temperature", "top_p"]:
            if key in model_config:
                params[key] = model_config[key]
        
        # Override with provided parameters
        if temperature is not None:
            params["temperature"] = max(0.0, min(1.0, temperature))
        if top_p is not None:
            params["top_p"] = max(0.0, min(1.0, top_p))
        if max_tokens is not None:
            params["max_tokens"] = max(1, min(model_config.get("max_tokens", 4000), max_tokens))
        
        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # Prepare request payload
        payload = {
            "model": model_name,
            "messages": messages,
        }
        # Only add allowed params
        for key in ["temperature", "top_p", "max_tokens"]:
            if key in params:
                payload[key] = params[key]
        
        # Headers for API request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Attempt generation with retry logic
        last_error = None
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    logger.info(f"Attempting Groq API call with model {model_name} (attempt {attempt + 1}/{self.max_retries})")
                    
                    response = await client.post(
                        self.base_url,
                        headers=headers,
                        json=payload
                    )
                    
                    # Handle HTTP errors
                    if response.status_code != 200:
                        error_detail = "Unknown error"
                        try:
                            error_data = response.json()
                            error_detail = error_data.get("error", {}).get("message", str(error_data))
                        except:
                            error_detail = f"HTTP {response.status_code}: {response.text[:200]}"
                        
                        raise httpx.HTTPStatusError(
                            f"Groq API error: {error_detail}",
                            request=response.request,
                            response=response
                        )
                    
                    # Parse successful response
                    result = response.json()
                    
                    # Extract generated text
                    if "choices" not in result or not result["choices"]:
                        raise ValueError("No choices returned from Groq API")
                    
                    choice = result["choices"][0]
                    if "message" not in choice or "content" not in choice["message"]:
                        raise ValueError("Invalid response format from Groq API")
                    
                    generated_text = choice["message"]["content"].strip()
                    
                    if not generated_text:
                        raise ValueError("Empty response from Groq API")

                    # Cache the result if caching is enabled
                    if self.enable_cache and use_cache and self.cache:
                        cache_key_params = {
                            "temperature": params.get("temperature"),
                            "top_p": params.get("top_p"),
                            "max_tokens": params.get("max_tokens"),
                            "model": model_name
                        }
                        self.cache.set(system_prompt, user_message, generated_text, **cache_key_params)

                    logger.info(f"Successfully generated text completion using model {model_name}")
                    return generated_text
                    
            except httpx.TimeoutException as e:
                last_error = f"Request timeout after {self.timeout}s"
                logger.warning(f"Attempt {attempt + 1} timed out: {e}")
                
            except httpx.HTTPStatusError as e:
                last_error = str(e)
                logger.warning(f"Attempt {attempt + 1} HTTP error: {e}")
                
                # Don't retry on certain errors
                if "401" in str(e) or "403" in str(e):  # Auth errors
                    break
                if "429" in str(e):  # Rate limit - wait before retry
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except (json.JSONDecodeError, ValueError) as e:
                last_error = f"Response parsing error: {str(e)}"
                logger.warning(f"Attempt {attempt + 1} parsing error: {e}")
                
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                logger.warning(f"Attempt {attempt + 1} unexpected error: {e}")
            
            # Wait before retry (except on last attempt)
            if attempt < self.max_retries - 1:
                wait_time = 1.0 * (2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                logger.info(f"Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
        
        # All attempts failed
        error_msg = f"Text generation failed after {self.max_retries} attempts. Last error: {last_error}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    async def generate_with_fallback(
        self,
        system_prompt: str,
        user_message: str,
        fallback_models: list = None,
        **kwargs
    ) -> str:
        
        models_to_try = [self.model]
        if fallback_models:
            models_to_try.extend(fallback_models)
        
        last_error = None
        for model in models_to_try:
            try:
                logger.info(f"Trying model: {model}")
                result = await self.generate(
                    system_prompt=system_prompt,
                    user_message=user_message,
                    model=model,
                    **kwargs
                )
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(f"Model {model} failed: {e}")
                continue
        
        # All models failed
        raise Exception(f"All models failed. Last error: {last_error}")
    
    def validate_inputs(self, system_prompt: str, user_message: str) -> None:
       
        if not system_prompt or not system_prompt.strip():
            raise ValueError("System prompt cannot be empty")
        
        if not user_message or not user_message.strip():
            raise ValueError("User message cannot be empty")
        
        # Check for reasonable length limits
        if len(system_prompt) > 10000:
            raise ValueError("System prompt too long (max 10,000 characters)")
        
        if len(user_message) > 20000:
            raise ValueError("User message too long (max 20,000 characters)")
    
    def estimate_tokens(self, text: str) -> int:
        """
        Rough estimation of token count for text.
        Used for planning max_tokens parameter.
        
        Args:
            text: Text to estimate tokens for
        
        Returns:
            Estimated token count
        """
        # Rough approximation: 1 token ≈ 4 characters for English text
        return len(text) // 4
    
    async def health_check(self) -> bool:
        """
        Check if Groq API is accessible and working.
        
        Returns:
            True if API is healthy, False otherwise
        """
        try:
            test_result = await self.generate(
                system_prompt="You are a helpful assistant.",
                user_message="Say 'OK' if you can hear me.",
                max_tokens=10,
                temperature=0.1
            )
            return "OK" in test_result.upper()
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def get_supported_models(self) -> Dict[str, Dict[str, Any]]:
        """
        Get list of supported models with their configurations.
        
        Returns:
            Dictionary of model names and their configurations
        """
        return self.model_configs
    
    def configure_model(self, model: str) -> None:
        """
        Set the default model for generation.
        
        Args:
            model: Model name to use as default
        
        Raises:
            ValueError: If model is not supported
        """
        if model not in self.model_configs:
            raise ValueError(f"Model {model} not supported. Supported models: {list(self.model_configs.keys())}")
        
        self.model = model
        logger.info(f"Default model set to: {model} ({self.model_configs[model]['description']})")
    
    def configure_defaults(
        self,
        temperature: float = None,
        top_p: float = None,
        max_tokens: int = None,
        timeout: float = None
    ) -> None:
        """
        Configure default generation parameters.
        
        Args:
            temperature: Default temperature (0.0 to 1.0)
            top_p: Default top_p (0.0 to 1.0)
            max_tokens: Default max_tokens
            timeout: Default request timeout in seconds
        """
        if temperature is not None:
            self.default_params["temperature"] = max(0.0, min(1.0, temperature))
        
        if top_p is not None:
            self.default_params["top_p"] = max(0.0, min(1.0, top_p))
        
        if max_tokens is not None:
            self.default_params["max_tokens"] = max(1, min(4000, max_tokens))
        
        if timeout is not None:
            self.timeout = max(5.0, timeout)
        
        logger.info(f"Updated default parameters: {self.default_params}")


# Singleton instance for reuse across the application
_generator_instance = None

def get_generator() -> GroqGenerator:
    """
    Get or create singleton GroqGenerator instance.
    
    Returns:
        GroqGenerator instance
    """
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = GroqGenerator()
    return _generator_instance


# Convenience functions for common use cases
async def quick_generate(prompt: str, max_tokens: int = 200, temperature: float = 0.3) -> str:
    """
    Quick text generation with minimal setup.
    
    Args:
        prompt: Text prompt to complete
        max_tokens: Maximum tokens to generate
        temperature: Generation temperature
    
    Returns:
        Generated text
    """
    generator = get_generator()
    return await generator.generate(
        system_prompt="You are a helpful writing assistant.",
        user_message=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        model="llama-3.1-8b-instant"  # Use instant model for quick responses
    )


async def creative_generate(prompt: str, max_tokens: int = 300) -> str:
    """
    Creative text generation with higher temperature.
    
    Args:
        prompt: Creative writing prompt
        max_tokens: Maximum tokens to generate
    
    Returns:
        Generated creative text
    """
    generator = get_generator()
    return await generator.generate(
        system_prompt="You are a creative writing assistant with vivid imagination.",
        user_message=prompt,
        max_tokens=max_tokens,
        temperature=0.7,
        top_p=0.9,
        model="llama-3.3-70b-versatile"  # Use versatile model for creative tasks
    )


async def technical_generate(prompt: str, max_tokens: int = 400) -> str:
    """
    Technical text generation with lower temperature for accuracy.
    
    Args:
        prompt: Technical writing prompt
        max_tokens: Maximum tokens to generate
    
    Returns:
        Generated technical text
    """
    generator = get_generator()
    return await generator.generate(
        system_prompt="You are a technical writing assistant focused on accuracy and clarity.",
        user_message=prompt,
        max_tokens=max_tokens,
        temperature=0.1,
        top_p=0.95,
        model="llama3-70b-8192"  # Use high-capacity model for technical content
    )