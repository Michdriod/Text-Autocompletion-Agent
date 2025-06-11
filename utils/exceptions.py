# Custom exceptions for the Multi-Mode Text Enrichment System
# Provides specific error types for better error handling and debugging

class TextEnrichmentError(Exception):
    """Base exception for text enrichment system."""
    pass

class ValidationError(TextEnrichmentError):
    """Raised when input validation fails."""
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message)

class GenerationError(TextEnrichmentError):
    """Raised when text generation fails."""
    def __init__(self, message: str, model: str = None, retry_count: int = 0):
        self.model = model
        self.retry_count = retry_count
        super().__init__(message)

class APIError(TextEnrichmentError):
    """Raised when external API calls fail."""
    def __init__(self, message: str, status_code: int = None, response_body: str = None):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)

class ConfigurationError(TextEnrichmentError):
    """Raised when configuration is invalid or missing."""
    pass

class CacheError(TextEnrichmentError):
    """Raised when cache operations fail."""
    pass

class RateLimitError(TextEnrichmentError):
    """Raised when rate limits are exceeded."""
    def __init__(self, message: str, retry_after: int = None):
        self.retry_after = retry_after
        super().__init__(message)

class ModelNotSupportedError(TextEnrichmentError):
    """Raised when an unsupported model is requested."""
    def __init__(self, model: str, supported_models: list = None):
        self.model = model
        self.supported_models = supported_models or []
        super().__init__(f"Model '{model}' is not supported. Supported models: {', '.join(self.supported_models)}")

class InputTooLongError(ValidationError):
    """Raised when input exceeds maximum length limits."""
    def __init__(self, current_length: int, max_length: int, field: str = "input"):
        self.current_length = current_length
        self.max_length = max_length
        super().__init__(
            f"{field.capitalize()} length ({current_length}) exceeds maximum allowed length ({max_length})",
            field=field
        )

class InsufficientInputError(ValidationError):
    """Raised when input doesn't meet minimum requirements."""
    def __init__(self, current_words: int, min_words: int, field: str = "input"):
        self.current_words = current_words
        self.min_words = min_words
        super().__init__(
            f"{field.capitalize()} has {current_words} words but requires at least {min_words} words",
            field=field
        )

class InvalidJSONError(ValidationError):
    """Raised when JSON input is malformed."""
    def __init__(self, json_error: str, field: str = "body"):
        self.json_error = json_error
        super().__init__(f"Invalid JSON in {field}: {json_error}", field=field)

class TimeoutError(APIError):
    """Raised when API requests timeout."""
    def __init__(self, timeout_duration: float):
        self.timeout_duration = timeout_duration
        super().__init__(f"Request timed out after {timeout_duration} seconds")

class QuotaExceededError(APIError):
    """Raised when API quota is exceeded."""
    def __init__(self, message: str = "API quota exceeded"):
        super().__init__(message, status_code=429)

class AuthenticationError(APIError):
    """Raised when API authentication fails."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)
