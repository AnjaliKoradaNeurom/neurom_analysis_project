"""
Models package for the Web Audit Tool.
Contains all Pydantic models and schemas.
"""

from .schemas import (
    URLRequest,
    BatchAnalysisRequest,
    ExportRequest,
    CrawlabilityFeatures,
    Recommendation,
    AIAnalysisResult,
    AnalysisResult,
    BatchAnalysisResult,
    HealthResponse,
    ErrorResponse,
    RateLimitInfo,
    ExportResponse,
    ValidationResult,
    AnalysisStatus,
    RecommendationPriority,
    ExportFormat
)

__all__ = [
    "URLRequest",
    "BatchAnalysisRequest", 
    "ExportRequest",
    "CrawlabilityFeatures",
    "Recommendation",
    "AIAnalysisResult",
    "AnalysisResult",
    "BatchAnalysisResult",
    "HealthResponse",
    "ErrorResponse",
    "RateLimitInfo",
    "ExportResponse",
    "ValidationResult",
    "AnalysisStatus",
    "RecommendationPriority",
    "ExportFormat"
]
