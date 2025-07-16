"""
Pydantic schemas for the Web Audit Tool API.
Defines all data models used for request/response validation.
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, HttpUrl, Field, validator
from datetime import datetime
from enum import Enum


class AnalysisStatus(str, Enum):
    """Status of analysis process"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class RecommendationPriority(str, Enum):
    """Priority levels for recommendations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ExportFormat(str, Enum):
    """Supported export formats"""
    PDF = "pdf"
    CSV = "csv"
    JSON = "json"


class ValidationResult(BaseModel):
    """Result of URL validation"""
    is_valid: bool = Field(..., description="Whether the URL is valid")
    normalized_url: Optional[str] = Field(None, description="Normalized URL")
    error: Optional[str] = Field(None, description="Error message if validation failed")
    redirect_url: Optional[str] = Field(None, description="Final URL after redirects")
    status_code: Optional[int] = Field(None, description="HTTP status code")
    domain: Optional[str] = Field(None, description="Domain name")
    ip_address: Optional[str] = Field(None, description="Resolved IP address")


class URLRequest(BaseModel):
    """Request model for URL analysis"""
    url: HttpUrl = Field(..., description="The URL to analyze")
    deep_crawl: bool = Field(default=False, description="Whether to perform deep crawling")
    max_pages: int = Field(default=10, ge=1, le=100, description="Maximum pages to crawl")
    
    @validator('url')
    def validate_url(cls, v):
        """Validate URL format"""
        url_str = str(v)
        if not url_str.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class BatchAnalysisRequest(BaseModel):
    """Request model for batch URL analysis"""
    urls: List[HttpUrl] = Field(..., min_items=1, max_items=50, description="List of URLs to analyze")
    deep_crawl: bool = Field(default=False, description="Whether to perform deep crawling")
    max_pages_per_url: int = Field(default=5, ge=1, le=20, description="Maximum pages per URL")


class ExportRequest(BaseModel):
    """Request model for exporting analysis results"""
    url: HttpUrl = Field(..., description="The URL that was analyzed")
    format: ExportFormat = Field(..., description="Export format")
    include_recommendations: bool = Field(default=True, description="Include recommendations in export")


class CrawlabilityFeatures(BaseModel):
    """Features extracted from website crawling"""
    # Basic page information
    url: str = Field(..., description="The analyzed URL")
    title: Optional[str] = Field(None, description="Page title")
    meta_description: Optional[str] = Field(None, description="Meta description")
    meta_keywords: Optional[str] = Field(None, description="Meta keywords")
    
    # Content analysis
    word_count: int = Field(0, ge=0, description="Total word count")
    heading_count: Dict[str, int] = Field(default_factory=dict, description="Count of headings by level")
    image_count: int = Field(0, ge=0, description="Number of images")
    link_count: int = Field(0, ge=0, description="Number of links")
    
    # Technical features
    page_size: int = Field(0, ge=0, description="Page size in bytes")
    load_time: float = Field(0.0, ge=0, description="Page load time in seconds")
    status_code: int = Field(200, ge=100, le=599, description="HTTP status code")
    
    # SEO features
    has_robots_txt: bool = Field(False, description="Whether robots.txt exists")
    has_sitemap: bool = Field(False, description="Whether sitemap exists")
    has_ssl: bool = Field(False, description="Whether site uses SSL")
    
    # Mobile features
    is_mobile_friendly: bool = Field(False, description="Whether site is mobile-friendly")
    viewport_configured: bool = Field(False, description="Whether viewport is configured")
    
    # Performance features
    first_contentful_paint: Optional[float] = Field(None, ge=0, description="First Contentful Paint time")
    largest_contentful_paint: Optional[float] = Field(None, ge=0, description="Largest Contentful Paint time")
    cumulative_layout_shift: Optional[float] = Field(None, ge=0, description="Cumulative Layout Shift score")
    
    # Security features
    security_headers: Dict[str, bool] = Field(default_factory=dict, description="Security headers present")
    mixed_content_issues: int = Field(0, ge=0, description="Number of mixed content issues")
    
    # Raw features for ML model
    raw_features: Dict[str, Any] = Field(default_factory=dict, description="Raw extracted features")


class Recommendation(BaseModel):
    """Individual recommendation for website improvement"""
    category: str = Field(..., description="Category of recommendation (SEO, Performance, etc.)")
    title: str = Field(..., description="Short title of recommendation")
    description: str = Field(..., description="Detailed description")
    priority: RecommendationPriority = Field(..., description="Priority level")
    impact: str = Field(..., description="Expected impact of implementing this recommendation")
    effort: str = Field(..., description="Estimated effort to implement")
    resources: List[str] = Field(default_factory=list, description="Helpful resources/links")
    
    class Config:
        json_schema_extra = {
            "example": {
                "category": "SEO",
                "title": "Add meta description",
                "description": "Your page is missing a meta description. This is important for search engine results.",
                "priority": "high",
                "impact": "Improved click-through rates from search results",
                "effort": "Low - 5 minutes",
                "resources": ["https://developers.google.com/search/docs/advanced/appearance/snippet"]
            }
        }


class AIAnalysisResult(BaseModel):
    """Result from AI-powered analysis"""
    score: int = Field(..., ge=0, le=100, description="Overall crawlability score")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in the analysis")
    label: str = Field(..., description="Human-readable label for the score")
    
    # Category scores
    seo_score: float = Field(0, ge=0, le=100, description="SEO score")
    performance_score: float = Field(0, ge=0, le=100, description="Performance score")
    security_score: float = Field(0, ge=0, le=100, description="Security score")
    mobile_score: float = Field(0, ge=0, le=100, description="Mobile-friendliness score")
    
    # Detailed analysis
    strengths: List[str] = Field(default_factory=list, description="Identified strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Identified weaknesses")
    recommendations: List[Recommendation] = Field(default_factory=list, description="AI-generated recommendations")
    
    # Feature importance for ML model
    feature_importance: Dict[str, float] = Field(default_factory=dict, description="Feature importance scores")
    
    # Technical details
    model_version: str = Field("2.0.0", description="Version of analysis model used")
    processing_time: float = Field(0, ge=0, description="Time taken for analysis in seconds")


class AnalysisResult(BaseModel):
    """Complete analysis result for a website"""
    # Request information
    url: str = Field(..., description="Analyzed URL")
    timestamp: str = Field(..., description="Analysis timestamp")
    status: AnalysisStatus = Field(AnalysisStatus.COMPLETED, description="Analysis status")
    
    # Analysis results
    crawlability_score: int = Field(..., ge=0, le=100, description="Overall crawlability score")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in analysis")
    label: str = Field(..., description="Human-readable score label")
    features: Dict[str, Any] = Field(default_factory=dict, description="Extracted features")
    recommendations: List[Recommendation] = Field(default_factory=list, description="Recommendations")
    
    # Summary
    grade: str = Field("F", description="Letter grade (A-F)")
    
    # Metadata
    analysis_time: float = Field(..., ge=0, description="Total processing time")
    model_version: str = Field("2.0.0", description="Model version used")
    analysis_id: Optional[str] = Field(None, description="Unique analysis identifier")
    error_message: Optional[str] = Field(None, description="Error message if analysis failed")
    
    @validator('grade', always=True)
    def calculate_grade(cls, v, values):
        """Calculate grade based on crawlability score"""
        if 'crawlability_score' in values:
            score = values['crawlability_score']
            if score >= 90:
                return 'A'
            elif score >= 80:
                return 'B'
            elif score >= 70:
                return 'C'
            elif score >= 60:
                return 'D'
            else:
                return 'F'
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com",
                "timestamp": "2024-01-15T10:30:00Z",
                "status": "completed",
                "crawlability_score": 85,
                "confidence": 0.92,
                "label": "Good",
                "grade": "B",
                "analysis_time": 12.5,
                "model_version": "2.0.0"
            }
        }


class BatchAnalysisResult(BaseModel):
    """Result from batch analysis"""
    batch_id: str = Field(..., description="Unique batch identifier")
    total_urls: int = Field(..., ge=1, description="Total number of URLs in batch")
    completed_urls: int = Field(0, ge=0, description="Number of completed analyses")
    failed_urls: int = Field(0, ge=0, description="Number of failed analyses")
    
    results: List[AnalysisResult] = Field(default_factory=list, description="Individual analysis results")
    
    # Batch statistics
    average_score: float = Field(0, ge=0, le=100, description="Average score across all URLs")
    processing_time: float = Field(..., ge=0, description="Total batch processing time")
    
    # Status
    status: AnalysisStatus = Field(..., description="Batch analysis status")
    started_at: str = Field(..., description="Batch start time")
    completed_at: Optional[str] = Field(None, description="Batch completion time")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field("healthy", description="Service status")
    timestamp: str = Field(..., description="Health check timestamp")
    version: str = Field("2.0.0", description="API version")
    uptime: float = Field(..., ge=0, description="Service uptime in seconds")
    
    # Service details
    database_status: str = Field("connected", description="Database connection status")
    redis_status: str = Field("connected", description="Redis connection status")
    ai_model_status: str = Field("loaded", description="AI model status")
    
    # Performance metrics
    active_analyses: int = Field(0, ge=0, description="Number of active analyses")
    total_analyses: int = Field(0, ge=0, description="Total analyses performed")
    average_response_time: float = Field(0, ge=0, description="Average response time in seconds")


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: str = Field(..., description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier for tracking")


class RateLimitInfo(BaseModel):
    """Rate limiting information"""
    requests_remaining: int = Field(..., ge=0, description="Requests remaining in current window")
    reset_time: str = Field(..., description="When the rate limit resets")
    limit: int = Field(..., ge=1, description="Total requests allowed per window")
    window_seconds: int = Field(..., ge=1, description="Rate limit window in seconds")


class ExportResponse(BaseModel):
    """Response for export requests"""
    export_id: str = Field(..., description="Unique export identifier")
    format: ExportFormat = Field(..., description="Export format")
    download_url: str = Field(..., description="URL to download the exported file")
    expires_at: str = Field(..., description="When the download link expires")
    file_size: int = Field(..., ge=0, description="File size in bytes")
