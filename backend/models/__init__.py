"""
Data models and schemas for the website analyzer
"""

from .schemas import (
    CrawlabilityFeatures,
    AIAnalysisResult,
    Recommendation,
    PriorityLevel,
    Priority,  # Backward compatibility alias
    AnalysisRequest,
    AnalysisResult,
    BatchAnalysisRequest,
    BatchAnalysisResult,
    ValidationResult,
    GoogleSearchResult,
    URLVerificationResult,
    HealthCheckResult
)

__all__ = [
    'CrawlabilityFeatures',
    'AIAnalysisResult', 
    'Recommendation',
    'PriorityLevel',
    'Priority',  # Backward compatibility
    'AnalysisRequest',
    'AnalysisResult',
    'BatchAnalysisRequest',
    'BatchAnalysisResult',
    'ValidationResult',
    'GoogleSearchResult',
    'URLVerificationResult',
    'HealthCheckResult'
]
