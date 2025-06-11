# Configuration management for the Multi-Mode Text Enrichment System
# Centralizes all configuration settings with environment variable support

import os
from typing import Dict, Any, Optional
from pydantic import BaseSettings, Field
from enum import Enum

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

class AppConfig(BaseSettings):
    """Application configuration with environment variable support."""
    
    # API Configuration
    groq_api_key: str = Field(..., env="GROQ_API_KEY")
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")
    api_reload: bool = Field(False, env="API_RELOAD")
    
    # CORS Configuration
    cors_origins: list = Field(["*"], env="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(True, env="CORS_ALLOW_CREDENTIALS")
    
    # Groq API Configuration
    groq_base_url: str = Field("https://api.groq.com/openai/v1/chat/completions", env="GROQ_BASE_URL")
    groq_default_model: str = Field("llama-3.3-70b-versatile", env="GROQ_DEFAULT_MODEL")
    groq_timeout: float = Field(30.0, env="GROQ_TIMEOUT")
    groq_max_retries: int = Field(3, env="GROQ_MAX_RETRIES")
    
    # Cache Configuration
    cache_enabled: bool = Field(True, env="CACHE_ENABLED")
    cache_ttl: int = Field(300, env="CACHE_TTL")  # 5 minutes
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(False, env="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(3600, env="RATE_LIMIT_WINDOW")  # 1 hour
    
    # Logging
    log_level: LogLevel = Field(LogLevel.INFO, env="LOG_LEVEL")
    log_format: str = Field("%(asctime)s - %(name)s - %(levelname)s - %(message)s", env="LOG_FORMAT")
    
    # Input Validation
    max_input_length: int = Field(20000, env="MAX_INPUT_LENGTH")
    max_output_tokens: int = Field(1000, env="MAX_OUTPUT_TOKENS")
    
    # Mode-specific defaults
    mode_1_min_words: int = Field(20, env="MODE_1_MIN_WORDS")
    mode_2_min_words: int = Field(2, env="MODE_2_MIN_WORDS")
    mode_3_min_words: int = Field(0, env="MODE_3_MIN_WORDS")
    mode_4_min_words: int = Field(2, env="MODE_4_MIN_WORDS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Global configuration instance
_config_instance: Optional[AppConfig] = None

def get_config() -> AppConfig:
    """Get or create singleton configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = AppConfig()
    return _config_instance

def reload_config() -> AppConfig:
    """Reload configuration from environment variables."""
    global _config_instance
    _config_instance = AppConfig()
    return _config_instance

# Model configurations for different Groq models
MODEL_CONFIGS = {
    "llama3-8b-8192": {
        "max_tokens": 8192,
        "temperature": 0.3,
        "top_p": 0.9,
        "description": "Fast 8B parameter model with 8K context window",
        "cost_per_token": 0.00001  # Example cost
    },
    "llama3-70b-8192": {
        "max_tokens": 8192,
        "temperature": 0.3,
        "top_p": 0.9,
        "description": "Powerful 70B parameter model with 8K context window",
        "cost_per_token": 0.00005
    },
    "llama-3.1-8b-instant": {
        "max_tokens": 2048,
        "temperature": 0.3,
        "top_p": 0.9,
        "description": "Quick 8B parameter model optimized for instant responses",
        "cost_per_token": 0.00001
    },
    "llama-3.3-70b-versatile": {
        "max_tokens": 4096,
        "temperature": 0.3,
        "top_p": 0.9,
        "description": "Versatile 70B parameter model with balanced performance",
        "cost_per_token": 0.00003
    }
}

# Mode-specific generation parameters
MODE_GENERATION_PARAMS = {
    "mode_1": {"temperature": 0.3, "top_p": 0.95},  # Context-aware completion
    "mode_2": {"temperature": 0.4, "top_p": 0.9},   # Structured enrichment
    "mode_3": {"temperature": 0.1, "top_p": 0.98},  # Input refinement
    "mode_4": {"temperature": 0.2, "top_p": 0.95}   # Description agent
}

def get_model_config(model_name: str) -> Dict[str, Any]:
    """Get configuration for a specific model."""
    return MODEL_CONFIGS.get(model_name, MODEL_CONFIGS["llama-3.3-70b-versatile"])

def get_mode_params(mode: str) -> Dict[str, float]:
    """Get generation parameters for a specific mode."""
    return MODE_GENERATION_PARAMS.get(mode, {"temperature": 0.3, "top_p": 0.9})
