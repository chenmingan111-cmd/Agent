class AppError(Exception):
    """Base class for application errors."""
    pass

class LLMGenerationError(AppError):
    """Raised when LLM fails to generate valid output."""
    pass

class ValidationError(AppError):
    """Raised when DSL validation fails."""
    pass

class HighRiskBlockedError(AppError):
    """Raised when query is blocked due to high risk."""
    def __init__(self, risk_info: dict):
        self.risk_info = risk_info
        super().__init__(f"Query blocked due to high risk: {risk_info}")

class ESDriverError(AppError):
    """Raised when ES execution fails."""
    pass
