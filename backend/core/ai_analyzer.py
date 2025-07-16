"""
AI-powered website analysis using OpenAI GPT-4
"""

import asyncio
import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import openai
from models.schemas import CrawlabilityFeatures, AIAnalysisResult, Recommendation

logger = logging.getLogger(__name__)

class AIAnalyzer:
    """
    AI-powered website analysis using OpenAI GPT models
    """
    
    def __init__(self):
        # Get API key from environment (should already be loaded by main.py)
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # Model priority list - try these in order
        self.model_priority = [
            "gpt-4o-mini",      # Most cost-effective GPT-4 class model
            "gpt-4o",           # Latest GPT-4 model
            "gpt-4-turbo",      # GPT-4 Turbo
            "gpt-4",            # Original GPT-4
            "gpt-3.5-turbo",    # Fallback to GPT-3.5
        ]
        
        self.model = None  # Will be set during initialization
        self.is_loaded = False
        
        # Log the API key status for debugging
        if self.openai_api_key:
            logger.info(f"✅ OpenAI API key found (length: {len(self.openai_api_key)})")
        else:
            logger.warning("⚠️ OpenAI API key not found in environment variables")
            logger.info("Available environment variables starting with 'OPENAI': " + 
                       str([k for k in os.environ.keys() if k.startswith('OPENAI')]))
        
        # Analysis rules and weights
        self.analysis_rules = {
            'technical_seo': {
                'weight': 0.25,
                'factors': [
                    'title_tag_present', 'meta_description_present', 'h1_count',
                    'canonical_tag_present', 'structured_data_present'
                ]
            },
            'crawlability': {
                'weight': 0.20,
                'factors': [
                    'robots_txt_exists', 'sitemap_exists', 'status_code',
                    'robots_txt_blocks_crawling', 'meta_robots_noindex'
                ]
            },
            'performance': {
                'weight': 0.20,
                'factors': [
                    'page_load_time', 'html_size', 'compression_enabled',
                    'cache_headers_present', 'lazy_loading_images'
                ]
            },
            'mobile_friendliness': {
                'weight': 0.15,
                'factors': [
                    'mobile_friendly', 'viewport_configured'
                ]
            },
            'security': {
                'weight': 0.10,
                'factors': [
                    'https_enabled', 'ssl_certificate_valid', 'security_headers_count'
                ]
            },
            'accessibility': {
                'weight': 0.10,
                'factors': [
                    'images_with_alt_count', 'lang_attribute_present',
                    'accessibility_score'
                ]
            }
        }
    
    async def load_model(self):
        """Initialize OpenAI client and find available model"""
        try:
            if not self.openai_api_key:
                logger.warning("⚠️ OpenAI API key not found, using rule-based analysis only")
                logger.info("💡 To enable AI analysis, set OPENAI_API_KEY in your .env file")
                self.is_loaded = True
                return
            
            # Validate API key format
            if not self.openai_api_key.startswith('sk-'):
                logger.error("❌ Invalid OpenAI API key format (should start with 'sk-')")
                self.is_loaded = True
                return
            
            # Set OpenAI API key
            openai.api_key = self.openai_api_key
            
            # Try to find an available model
            available_model = await self._find_available_model()
            
            if available_model:
                self.model = available_model
                logger.info(f"✅ OpenAI API connection successful using model: {self.model}")
                self.is_loaded = True
            else:
                logger.warning("⚠️ No compatible OpenAI models available, using rule-based analysis")
                self.is_loaded = True
                
        except Exception as e:
            logger.error(f"❌ AI model loading failed: {e}")
            self.is_loaded = True  # Still mark as loaded to use rule-based fallback
    
    async def _find_available_model(self) -> Optional[str]:
        """Find the first available model from our priority list"""
        for model_name in self.model_priority:
            try:
                logger.info(f"🔍 Testing model: {model_name}")
                
                # Test the model with a minimal request
                response = await openai.ChatCompletion.acreate(
                    model=model_name,
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=5,
                    timeout=10
                )
                
                logger.info(f"✅ Model {model_name} is available and working")
                return model_name
                
            except openai.error.InvalidRequestError as e:
                if "does not exist" in str(e) or "do not have access" in str(e):
                    logger.info(f"❌ Model {model_name} not available: {e}")
                    continue
                else:
                    logger.warning(f"⚠️ Model {model_name} error: {e}")
                    continue
            except openai.error.AuthenticationError:
                logger.error("❌ OpenAI API authentication failed - check your API key")
                return None
            except openai.error.RateLimitError:
                logger.warning(f"⚠️ Rate limit reached for {model_name}, trying next model")
                continue
            except Exception as e:
                logger.warning(f"⚠️ Error testing model {model_name}: {e}")
                continue
        
        return None
    
    async def analyze_crawlability(self, features: CrawlabilityFeatures) -> AIAnalysisResult:
        """
        Analyze website crawlability using AI and rule-based methods
        """
        try:
            logger.info("🤖 Starting AI analysis")
            
            # Rule-based analysis (always performed)
            rule_based_result = await self._rule_based_analysis(features)
            
            # AI enhancement (if available)
            if self.openai_api_key and self.model:
                try:
                    ai_enhanced_result = await self._ai_enhanced_analysis(features, rule_based_result)
                    logger.info("✅ AI-enhanced analysis completed")
                    return ai_enhanced_result
                except Exception as e:
                    logger.warning(f"⚠️ AI analysis failed, using rule-based result: {e}")
            
            logger.info("✅ Rule-based analysis completed")
            return rule_based_result
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {str(e)}")
            return self._create_fallback_result(features)
    
    async def _rule_based_analysis(self, features: CrawlabilityFeatures) -> AIAnalysisResult:
        """
        Perform rule-based analysis
        """
        try:
            scores = {}
            recommendations = []
            
            # Calculate category scores
            for category, config in self.analysis_rules.items():
                category_score = self._calculate_category_score(features, config['factors'])
                scores[category] = category_score
                
                # Generate recommendations for low scores
                if category_score < 0.7:
                    category_recommendations = self._generate_category_recommendations(
                        category, features, category_score
                    )
                    recommendations.extend(category_recommendations)
            
            # Calculate overall score
            overall_score = sum(
                scores[category] * config['weight']
                for category, config in self.analysis_rules.items()
            )
            
            # Determine label and confidence
            label = self._determine_label(overall_score)
            confidence = self._calculate_confidence(features, overall_score)
            
            return AIAnalysisResult(
                score=overall_score * 100,  # Convert to percentage
                confidence=confidence,
                label=label,
                recommendations=recommendations[:10],  # Top 10 recommendations
                category_scores=scores,
                analysis_method="rule_based"
            )
            
        except Exception as e:
            logger.error(f"❌ Rule-based analysis failed: {str(e)}")
            return self._create_fallback_result(features)
    
    async def _ai_enhanced_analysis(self, features: CrawlabilityFeatures, rule_result: AIAnalysisResult) -> AIAnalysisResult:
        """
        Enhance analysis with AI insights
        """
        try:
            # Prepare context for AI
            context = self._prepare_ai_context(features, rule_result)
            
            # AI prompt
            prompt = f"""
            As an expert SEO and web performance analyst, analyze this website data and provide insights:

            {context}

            Please provide:
            1. An overall crawlability score (0-100)
            2. Confidence level (0-1)
            3. A descriptive label (e.g., "Excellent", "Good", "Needs Improvement", "Poor")
            4. Top 5 specific recommendations with priority levels
            5. Brief explanation of key issues

            Respond in JSON format:
            {{
                "score": 85,
                "confidence": 0.9,
                "label": "Good",
                "recommendations": [
                    {{
                        "priority": "High",
                        "title": "Fix Title Tag",
                        "message": "Add a descriptive title tag",
                        "impact_score": 8
                    }}
                ],
                "explanation": "Brief analysis summary"
            }}
            """
            
            # Call OpenAI API
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert SEO and web performance analyst."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3,
                timeout=30
            )
            
            # Parse AI response
            ai_content = response.choices[0].message.content
            ai_result = json.loads(ai_content)
            
            # Convert AI recommendations to our format
            ai_recommendations = []
            for rec in ai_result.get('recommendations', []):
                ai_recommendations.append(Recommendation(
                    priority=rec.get('priority', 'Medium'),
                    title=rec.get('title', ''),
                    message=rec.get('message', ''),
                    impact_score=rec.get('impact_score', 5)
                ))
            
            # Combine with rule-based recommendations
            all_recommendations = ai_recommendations + rule_result.recommendations
            
            return AIAnalysisResult(
                score=ai_result.get('score', rule_result.score),
                confidence=ai_result.get('confidence', rule_result.confidence),
                label=ai_result.get('label', rule_result.label),
                recommendations=all_recommendations[:10],
                category_scores=rule_result.category_scores,
                analysis_method="ai_enhanced",
                ai_explanation=ai_result.get('explanation', '')
            )
            
        except Exception as e:
            logger.warning(f"⚠️ AI enhancement failed: {str(e)}")
            return rule_result
    
    def _calculate_category_score(self, features: CrawlabilityFeatures, factors: List[str]) -> float:
        """
        Calculate score for a specific category
        """
        try:
            total_score = 0.0
            factor_count = len(factors)
            
            for factor in factors:
                factor_score = self._evaluate_factor(features, factor)
                total_score += factor_score
            
            return total_score / factor_count if factor_count > 0 else 0.0
            
        except Exception:
            return 0.0
    
    def _evaluate_factor(self, features: CrawlabilityFeatures, factor: str) -> float:
        """
        Evaluate individual factor
        """
        try:
            value = getattr(features, factor, None)
            
            if value is None:
                return 0.0
            
            # Boolean factors
            if isinstance(value, bool):
                return 1.0 if value else 0.0
            
            # Numeric factors with specific logic
            if factor == 'status_code':
                return 1.0 if value == 200 else 0.0
            elif factor == 'h1_count':
                return 1.0 if value == 1 else (0.5 if value > 1 else 0.0)
            elif factor == 'page_load_time':
                if value < 1.0:
                    return 1.0
                elif value < 2.0:
                    return 0.8
                elif value < 3.0:
                    return 0.6
                else:
                    return 0.3
            elif factor == 'html_size':
                if value < 50000:  # 50KB
                    return 1.0
                elif value < 100000:  # 100KB
                    return 0.8
                elif value < 200000:  # 200KB
                    return 0.6
                else:
                    return 0.3
            elif factor == 'security_headers_count':
                return min(value / 5.0, 1.0)  # Max 5 security headers
            elif factor == 'images_with_alt_count':
                total_images = getattr(features, 'images_count', 1)
                return value / total_images if total_images > 0 else 1.0
            elif factor == 'lazy_loading_images':
                return min(value / 5.0, 1.0)  # Normalize to max 5 lazy images
            elif factor == 'accessibility_score':
                return value  # Already normalized 0-1
            else:
                # Default numeric handling
                return min(float(value), 1.0)
                
        except Exception:
            return 0.0
    
    def _generate_category_recommendations(self, category: str, features: CrawlabilityFeatures, score: float) -> List[Recommendation]:
        """
        Generate recommendations for specific category
        """
        recommendations = []
        
        try:
            if category == 'technical_seo':
                if not features.title_tag_present:
                    recommendations.append(Recommendation(
                        priority="High",
                        title="Add Title Tag",
                        message="Add a descriptive title tag to improve search engine visibility",
                        impact_score=9
                    ))
                
                if not features.meta_description_present:
                    recommendations.append(Recommendation(
                        priority="High",
                        title="Add Meta Description",
                        message="Add a compelling meta description to improve click-through rates",
                        impact_score=8
                    ))
                
                if features.h1_count != 1:
                    recommendations.append(Recommendation(
                        priority="Medium",
                        title="Optimize H1 Structure",
                        message="Use exactly one H1 tag per page for better SEO",
                        impact_score=6
                    ))
            
            elif category == 'crawlability':
                if not features.robots_txt_exists:
                    recommendations.append(Recommendation(
                        priority="Medium",
                        title="Create Robots.txt",
                        message="Add a robots.txt file to guide search engine crawlers",
                        impact_score=7
                    ))
                
                if not features.sitemap_exists:
                    recommendations.append(Recommendation(
                        priority="Medium",
                        title="Create XML Sitemap",
                        message="Generate and submit an XML sitemap to help search engines discover content",
                        impact_score=7
                    ))
            
            elif category == 'performance':
                if features.page_load_time > 3.0:
                    recommendations.append(Recommendation(
                        priority="High",
                        title="Improve Page Load Speed",
                        message="Optimize images, minify CSS/JS, and enable compression to reduce load time",
                        impact_score=9
                    ))
                
                if not features.compression_enabled:
                    recommendations.append(Recommendation(
                        priority="Medium",
                        title="Enable Compression",
                        message="Enable Gzip or Brotli compression to reduce file sizes",
                        impact_score=6
                    ))
            
            elif category == 'mobile_friendliness':
                if not features.mobile_friendly:
                    recommendations.append(Recommendation(
                        priority="High",
                        title="Implement Responsive Design",
                        message="Make your website mobile-friendly with responsive design",
                        impact_score=8
                    ))
            
            elif category == 'security':
                if not features.https_enabled:
                    recommendations.append(Recommendation(
                        priority="High",
                        title="Enable HTTPS",
                        message="Secure your website with SSL/TLS encryption",
                        impact_score=9
                    ))
            
            elif category == 'accessibility':
                if features.images_count > 0 and features.images_with_alt_count < features.images_count:
                    recommendations.append(Recommendation(
                        priority="Medium",
                        title="Add Alt Text to Images",
                        message="Provide alternative text for all images to improve accessibility",
                        impact_score=6
                    ))
        
        except Exception as e:
            logger.warning(f"⚠️ Failed to generate recommendations for {category}: {e}")
        
        return recommendations
    
    def _determine_label(self, score: float) -> str:
        """
        Determine descriptive label based on score
        """
        if score >= 0.9:
            return "Excellent"
        elif score >= 0.8:
            return "Very Good"
        elif score >= 0.7:
            return "Good"
        elif score >= 0.6:
            return "Fair"
        elif score >= 0.4:
            return "Needs Improvement"
        else:
            return "Poor"
    
    def _calculate_confidence(self, features: CrawlabilityFeatures, score: float) -> float:
        """
        Calculate confidence level based on available data
        """
        try:
            # Base confidence
            confidence = 0.7
            
            # Increase confidence if we have good data
            if features.status_code == 200:
                confidence += 0.1
            
            if features.html_size > 1000:  # Has substantial content
                confidence += 0.1
            
            if features.title_tag_present and features.meta_description_present:
                confidence += 0.05
            
            if features.robots_txt_exists or features.sitemap_exists:
                confidence += 0.05
            
            # Decrease confidence for edge cases
            if score < 0.2 or score > 0.95:
                confidence -= 0.1
            
            return min(max(confidence, 0.5), 0.95)
            
        except Exception:
            return 0.7
    
    def _prepare_ai_context(self, features: CrawlabilityFeatures, rule_result: AIAnalysisResult) -> str:
        """
        Prepare context for AI analysis
        """
        try:
            context = f"""
            Website Analysis Data:
            - URL: {features.url}
            - Status Code: {features.status_code}
            - HTTPS Enabled: {features.https_enabled}
            - Title Present: {features.title_tag_present} (Length: {features.title_length})
            - Meta Description: {features.meta_description_present} (Length: {features.meta_description_length})
            - H1 Count: {features.h1_count}
            - Page Load Time: {features.page_load_time}s
            - HTML Size: {features.html_size} bytes
            - Mobile Friendly: {features.mobile_friendly}
            - Images: {features.images_count} (Alt text: {features.images_with_alt_count})
            - Internal Links: {features.internal_links_count}
            - External Links: {features.external_links_count}
            - Robots.txt: {features.robots_txt_exists}
            - Sitemap: {features.sitemap_exists}
            - Structured Data: {features.structured_data_present}
            
            Rule-based Analysis:
            - Score: {rule_result.score}
            - Label: {rule_result.label}
            - Category Scores: {rule_result.category_scores}
            """
            
            return context
            
        except Exception:
            return "Limited data available for analysis"
    
    def _create_fallback_result(self, features: CrawlabilityFeatures) -> AIAnalysisResult:
        """
        Create fallback result when analysis fails
        """
        return AIAnalysisResult(
            score=50.0,
            confidence=0.5,
            label="Analysis Incomplete",
            recommendations=[
                Recommendation(
                    priority="High",
                    title="Analysis Error",
                    message="Unable to complete full analysis. Please try again.",
                    impact_score=5
                )
            ],
            category_scores={},
            analysis_method="fallback"
        )
