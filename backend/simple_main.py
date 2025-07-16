from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import logging
from typing import List
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Neurom Website Analyzer API", version="1.0.0")

# CORS middleware - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalysisRequest(BaseModel):
    url: str

class Recommendation(BaseModel):
    priority: str
    title: str
    message: str
    code_snippet: str = None
    doc_link: str = None

class ModuleResult(BaseModel):
    name: str
    score: int
    description: str
    explanation: str
    recommendations: List[Recommendation]

class AnalysisResult(BaseModel):
    url: str
    timestamp: str
    overall_score: int
    modules: List[ModuleResult]
    analysis_time: float

def generate_mock_analysis(url: str) -> AnalysisResult:
    """Generate mock analysis results for testing"""
    
    # Simple hash-based scoring for consistency
    url_hash = hash(url) % 100
    base_score = 60 + (url_hash % 40)  # 60-100 range
    
    modules = [
        ModuleResult(
            name="SEO & Metadata",
            score=min(100, base_score + 5),
            description="Search engine optimization and meta tags analysis",
            explanation="SEO analysis shows good optimization with proper meta tags and content structure.",
            recommendations=[
                Recommendation(
                    priority="Medium",
                    title="Optimize Meta Description",
                    message="Consider improving meta description length for better search results display.",
                    code_snippet='<meta name="description" content="Optimized description (120-160 chars)">',
                    doc_link="https://developers.google.com/search/docs/appearance/snippet"
                )
            ]
        ),
        ModuleResult(
            name="Performance",
            score=min(100, base_score - 10),
            description="Website speed and performance metrics",
            explanation="Performance analysis shows room for improvement in loading speed and optimization.",
            recommendations=[
                Recommendation(
                    priority="High",
                    title="Optimize Images",
                    message="Compress and properly format images to reduce loading times.",
                    code_snippet='<img src="image.webp" alt="Description" loading="lazy">',
                    doc_link="https://web.dev/fast/#optimize-your-images"
                )
            ]
        ),
        ModuleResult(
            name="Security",
            score=min(100, base_score + 15),
            description="HTTPS and security implementation",
            explanation="Security analysis shows good HTTPS implementation with room for header improvements.",
            recommendations=[
                Recommendation(
                    priority="Medium",
                    title="Add Security Headers",
                    message="Implement additional security headers for better protection.",
                    code_snippet="Strict-Transport-Security: max-age=31536000; includeSubDomains",
                    doc_link="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers#security"
                )
            ]
        ),
        ModuleResult(
            name="Mobile Friendliness",
            score=min(100, base_score + 8),
            description="Mobile device compatibility and usability",
            explanation="Mobile analysis shows good responsive design with minor optimization opportunities.",
            recommendations=[
                Recommendation(
                    priority="Low",
                    title="Optimize Touch Targets",
                    message="Ensure all interactive elements are properly sized for touch interaction.",
                    code_snippet='.touch-target { min-height: 44px; min-width: 44px; }',
                    doc_link="https://web.dev/accessible-tap-targets/"
                )
            ]
        ),
        ModuleResult(
            name="Crawlability",
            score=min(100, base_score - 5),
            description="Search engine crawling accessibility",
            explanation="Crawlability analysis shows good structure with some areas for improvement.",
            recommendations=[
                Recommendation(
                    priority="Medium",
                    title="Optimize Robots.txt",
                    message="Review and optimize robots.txt file for better crawling guidance.",
                    code_snippet="User-agent: *\nAllow: /\nSitemap: https://yoursite.com/sitemap.xml",
                    doc_link="https://developers.google.com/search/docs/crawling-indexing/robots/intro"
                )
            ]
        ),
        ModuleResult(
            name="Indexing",
            score=min(100, base_score + 2),
            description="Search engine indexing optimization",
            explanation="Indexing analysis shows proper setup with opportunities for canonical tag optimization.",
            recommendations=[
                Recommendation(
                    priority="Medium",
                    title="Add Canonical Tags",
                    message="Implement canonical tags to prevent duplicate content issues.",
                    code_snippet='<link rel="canonical" href="https://example.com/preferred-url">',
                    doc_link="https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls"
                )
            ]
        )
    ]
    
    overall_score = sum(m.score for m in modules) // len(modules)
    
    return AnalysisResult(
        url=url,
        timestamp=datetime.now().isoformat(),
        overall_score=overall_score,
        modules=modules,
        analysis_time=2.5
    )

@app.get("/")
async def root():
    return {
        "message": "Neurom Website Analyzer API", 
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "POST /analyze",
            "health": "GET /health",
            "docs": "GET /docs"
        }
    }

@app.post("/analyze", response_model=AnalysisResult)
async def analyze_website(request: AnalysisRequest):
    try:
        logger.info(f"Analyzing website: {request.url}")
        
        # Simulate analysis time
        await asyncio.sleep(1)
        
        # Generate mock analysis
        result = generate_mock_analysis(request.url)
        
        logger.info(f"Analysis completed for {request.url} with score {result.overall_score}%")
        return result
        
    except Exception as e:
        logger.error(f"Analysis failed for {request.url}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Neurom Website Analyzer API...")
    print("📊 API Documentation: http://localhost:8000/docs")
    print("🌐 API Endpoint: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
