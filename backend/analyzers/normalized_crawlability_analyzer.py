"""
Normalized crawlability analyzer that provides consistent results across environments
"""

import asyncio
import logging
from typing import Dict, List
from pydantic import BaseModel

from core.environment_normalizer import EnvironmentNormalizer

logger = logging.getLogger(__name__)

class Recommendation(BaseModel):
    category: str
    title: str
    description: str
    priority: str
    impact: str
    effort: str
    resources: List[str] = []

class NormalizedModuleResult(BaseModel):
    name: str
    score: int
    description: str
    explanation: str
    recommendations: List[Recommendation]
    confidence: float = 0.95

class NormalizedCrawlabilityAnalyzer:
    """
    Crawlability analyzer with environment normalization for consistent results
    """
    
    def __init__(self):
        self.normalizer = EnvironmentNormalizer()
    
    async def analyze(self, url: str) -> NormalizedModuleResult:
        """
        Perform normalized crawlability analysis
        """
        try:
            logger.info(f"🔧 Starting normalized crawlability analysis for: {url}")
            
            # Perform normalized crawl
            crawl_result = await self.normalizer.normalized_crawl(url)
            
            if not crawl_result['success']:
                return self._create_failed_result(url, crawl_result.get('error', 'Unknown error'))
            
            # Calculate normalized score
            features = crawl_result['features']
            score = self._calculate_normalized_crawlability_score(features)
            
            # Generate recommendations
            recommendations = self._generate_normalized_recommendations(features, crawl_result)
            
            # Create explanation
            explanation = self._generate_explanation(score, features)
            
            result = NormalizedModuleResult(
                name="Crawlability (Normalized)",
                score=score,
                description="Search engine crawling accessibility with environment normalization",
                explanation=explanation,
                recommendations=recommendations,
                confidence=0.95
            )
            
            logger.info(f"✅ Normalized crawlability analysis completed - Score: {score}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Normalized crawlability analysis failed: {e}")
            return self._create_failed_result(url, str(e))
    
    def _calculate_normalized_crawlability_score(self, features: Dict) -> int:
        """Calculate crawlability score with normalization"""
        total_score = 0
        
        # Content Quality (35 points)
        content_score = features.get('content_quality_score', 0)
        total_score += min(content_score, 35)
        
        # Technical Quality (40 points) 
        technical_score = features.get('technical_quality_score', 0)
        total_score += min(technical_score, 40)
        
        # Performance (25 points)
        load_time_score = features.get('load_time_score', 0)
        content_size_score = features.get('content_size_score', 0)
        performance_score = int(load_time_score * 0.6 + content_size_score * 0.4)
        total_score += min(performance_score, 25)
        
        return min(int(total_score), 100)
    
    def _generate_normalized_recommendations(self, features: Dict, crawl_result: Dict) -> List[Recommendation]:
        """Generate recommendations based on normalized analysis"""
        recommendations = []
        
        # Content recommendations
        if features.get('word_count', 0) < 300:
            recommendations.append(Recommendation(
                category="Content",
                title="Increase Content Length",
                description=f"Your page has {features.get('word_count', 0)} words. Add more quality content (aim for 300+ words) to improve search engine understanding.",
                priority="medium",
                impact="Improved search engine ranking and user engagement",
                effort="Medium - 1-2 hours",
                resources=["https://developers.google.com/search/docs/fundamentals/creating-helpful-content"]
            ))
        
        if not features.get('title_present', False):
            recommendations.append(Recommendation(
                category="SEO",
                title="Add Page Title",
                description="Your page is missing a title tag, which is crucial for SEO and search results.",
                priority="high",
                impact="Significantly improved search engine visibility",
                effort="Low - 5 minutes",
                resources=["https://developers.google.com/search/docs/appearance/title-link"]
            ))
        elif features.get('title_length', 0) < 30 or features.get('title_length', 0) > 60:
            recommendations.append(Recommendation(
                category="SEO", 
                title="Optimize Title Length",
                description=f"Title is {features.get('title_length', 0)} characters. Aim for 30-60 characters for optimal search results.",
                priority="medium",
                impact="Better click-through rates from search results",
                effort="Low - 10 minutes",
                resources=["https://developers.google.com/search/docs/appearance/title-link"]
            ))
        
        if not features.get('meta_description_present', False):
            recommendations.append(Recommendation(
                category="SEO",
                title="Add Meta Description", 
                description="Add a meta description to improve search engine results and click-through rates.",
                priority="high",
                impact="Improved search result appearance and CTR",
                effort="Low - 10 minutes",
                resources=["https://developers.google.com/search/docs/appearance/snippet"]
            ))
        
        # Technical recommendations
        if not features.get('has_ssl', False):
            recommendations.append(Recommendation(
                category="Security",
                title="Enable HTTPS",
                description="Secure your website with SSL certificate for better SEO and user trust.",
                priority="high", 
                impact="Improved search rankings and user security",
                effort="Medium - 1-2 hours",
                resources=["https://developers.google.com/search/docs/crawling-indexing/https"]
            ))
        
        if not features.get('has_viewport', False):
            recommendations.append(Recommendation(
                category="Mobile",
                title="Add Viewport Meta Tag",
                description="Add viewport meta tag for mobile responsiveness and better mobile search rankings.",
                priority="high",
                impact="Improved mobile user experience and rankings",
                effort="Low - 5 minutes", 
                resources=["https://developers.google.com/search/docs/crawling-indexing/mobile/mobile-sites-mobile-first-indexing"]
            ))
        
        if features.get('h1_count', 0) == 0:
            recommendations.append(Recommendation(
                category="Content Structure",
                title="Add H1 Heading",
                description="Add an H1 heading to improve content structure and help search engines understand your page topic.",
                priority="medium",
                impact="Better content organization and SEO",
                effort="Low - 15 minutes",
                resources=["https://developers.google.com/search/docs/appearance/structured-data"]
            ))
        elif features.get('h1_count', 0) > 1:
            recommendations.append(Recommendation(
                category="Content Structure", 
                title="Use Single H1 Tag",
                description=f"Your page has {features.get('h1_count', 0)} H1 tags. Use only one H1 per page for better SEO.",
                priority="low",
                impact="Improved content hierarchy and SEO",
                effort="Low - 10 minutes",
                resources=["https://developers.google.com/search/docs/appearance/structured-data"]
            ))
        
        # Performance recommendations
        load_time = features.get('load_time', 0)
        if load_time > 3.0:
            recommendations.append(Recommendation(
                category="Performance",
                title="Improve Page Load Speed",
                description=f"Your page loads in {load_time:.2f} seconds. Optimize for faster loading (aim for under 2 seconds).",
                priority="medium",
                impact="Better user experience and search rankings",
                effort="High - 4-8 hours",
                resources=["https://developers.google.com/speed/docs/insights/rules"]
            ))
        
        content_size_mb = features.get('content_size', 0) / (1024 * 1024)
        if content_size_mb > 2.0:
            recommendations.append(Recommendation(
                category="Performance",
                title="Optimize Content Size",
                description=f"Your page is {content_size_mb:.2f}MB. Optimize images and content for faster loading.",
                priority="medium",
                impact="Faster page loading and better user experience", 
                effort="Medium - 2-4 hours",
                resources=["https://developers.google.com/speed/docs/insights/OptimizeImages"]
            ))
        
        # Image accessibility
        alt_ratio = features.get('alt_ratio', 0)
        if alt_ratio < 0.8:
            recommendations.append(Recommendation(
                category="Accessibility",
                title="Improve Image Alt Text",
                description=f"Only {alt_ratio*100:.0f}% of your images have alt text. Add descriptive alt text to all images.",
                priority="medium",
                impact="Better accessibility and SEO",
                effort="Medium - 1-2 hours",
                resources=["https://developers.google.com/search/docs/appearance/google-images"]
            ))
        
        # Internal linking
        internal_links = features.get('internal_links_count', 0)
        if internal_links < 3:
            recommendations.append(Recommendation(
                category="SEO",
                title="Improve Internal Linking",
                description=f"Your page has {internal_links} internal links. Add more internal links to help search engines discover content.",
                priority="low",
                impact="Better content discovery and SEO",
                effort="Medium - 1 hour",
                resources=["https://developers.google.com/search/docs/crawling-indexing/links-crawlable"]
            ))
        
        # Sort by priority and return top recommendations
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x.priority, 3))
        
        return recommendations[:8]  # Return top 8 recommendations
    
    def _generate_explanation(self, score: int, features: Dict) -> str:
        """Generate explanation based on score and features"""
        if score >= 90:
            return "Excellent crawlability with strong SEO fundamentals, good performance, and proper technical implementation."
        elif score >= 80:
            return "Good crawlability with solid foundation. Minor optimizations could improve search engine accessibility."
        elif score >= 70:
            return "Fair crawlability with room for improvement in content quality, technical SEO, or performance."
        elif score >= 60:
            return "Poor crawlability with significant issues affecting search engine access. Multiple improvements needed."
        else:
            return "Critical crawlability issues detected. Major improvements required for proper search engine indexing."
    
    def _create_failed_result(self, url: str, error: str) -> NormalizedModuleResult:
        """Create result for failed analysis"""
        return NormalizedModuleResult(
            name="Crawlability (Normalized)",
            score=0,
            description="Crawlability analysis failed",
            explanation=f"Unable to analyze crawlability: {error}",
            recommendations=[Recommendation(
                category="Error",
                title="Analysis Failed",
                description=f"Could not analyze website: {error}",
                priority="high",
                impact="Unable to provide recommendations",
                effort="N/A",
                resources=[]
            )],
            confidence=0.0
        )
