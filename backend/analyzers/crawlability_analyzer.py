import aiohttp
import asyncio
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET
import ssl
import certifi
import time
import hashlib
from typing import List, Dict
from bs4 import BeautifulSoup
from pydantic import BaseModel

from ..models.schemas import Recommendation

class ModuleResult(BaseModel):
    name: str
    score: int
    description: str
    explanation: str
    recommendations: List[Recommendation]
    metadata: Dict = None

class CrawlabilityAnalyzer:
    """
    Crawlability analyzer with environment normalization for consistent results
    """
    
    def __init__(self):
        # Standardized configuration to ensure consistency
        self.timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=20)
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        # Standardized headers (Linux Chrome for consistency across environments)
        self.standard_headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        self.max_load_time = 15.0  # Cap load time to reduce environment impact
        self.retry_attempts = 3
        self.retry_delay = 1.0
    
    async def analyze(self, url: str) -> ModuleResult:
        """
        Perform normalized crawlability analysis
        """
        try:
            # Perform normalized crawl with multiple attempts
            crawl_result = await self.normalized_crawl(url)
            
            if not crawl_result['success']:
                return self._create_failed_result(url, crawl_result.get('error', 'Unknown error'))
            
            # Calculate normalized score
            features = crawl_result['features']
            score = self._calculate_normalized_crawlability_score(features)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(features, crawl_result)
            
            # Create explanation
            explanation = self._generate_explanation(score, features)
            
            return ModuleResult(
                name='Crawlability',
                score=score,
                description='Search engine crawling accessibility (normalized)',
                explanation=explanation,
                recommendations=recommendations,
                metadata={
                    'normalization_applied': True,
                    'load_time_raw': crawl_result.get('raw_load_time', 0),
                    'load_time_normalized': crawl_result.get('normalized_load_time', 0),
                    'content_hash': crawl_result.get('content_hash', ''),
                    'strategy': crawl_result.get('strategy', 'normalized')
                }
            )
            
        except Exception as e:
            return self._create_failed_result(url, str(e))
    
    async def normalized_crawl(self, url: str) -> Dict:
        """
        Perform normalized crawl with multiple attempts and median selection
        """
        attempts = []
        
        for attempt in range(self.retry_attempts):
            try:
                if attempt > 0:
                    await asyncio.sleep(self.retry_delay)
                
                result = await self._single_normalized_attempt(url, attempt + 1)
                
                if result['success']:
                    attempts.append(result)
                    
            except Exception as e:
                continue
        
        if not attempts:
            return {
                'success': False,
                'error': 'All normalized crawl attempts failed',
                'strategy': 'normalized_failed'
            }
        
        # Use median result to reduce outlier impact
        if len(attempts) >= 2:
            attempts.sort(key=lambda x: x['load_time'])
            selected_result = attempts[len(attempts) // 2]
        else:
            selected_result = attempts[0]
        
        # Apply normalization to the selected result
        normalized_result = self._apply_normalization(selected_result)
        
        return normalized_result
    
    async def _single_normalized_attempt(self, url: str, attempt_num: int) -> Dict:
        """Single normalized crawl attempt"""
        start_time = time.time()
        
        try:
            connector = aiohttp.TCPConnector(
                ssl=self.ssl_context,
                limit=10,
                limit_per_host=5,
                keepalive_timeout=30,
                enable_cleanup_closed=True,
                force_close=True,  # Ensure clean connections
                use_dns_cache=False  # Disable DNS cache for consistency
            )
            
            async with aiohttp.ClientSession(
                timeout=self.timeout,
                headers=self.standard_headers,
                connector=connector
            ) as session:
                
                async with session.get(url) as response:
                    if response.status != 200:
                        return {
                            'success': False,
                            'error': f'HTTP {response.status}',
                            'attempt': attempt_num
                        }
                    
                    content = await response.text()
                    load_time = time.time() - start_time
                    
                    return {
                        'success': True,
                        'url': str(response.url),
                        'status_code': response.status,
                        'load_time': load_time,
                        'content': content,
                        'headers': dict(response.headers),
                        'attempt': attempt_num,
                        'content_hash': hashlib.md5(content.encode()).hexdigest()
                    }
                    
        except asyncio.TimeoutError:
            return {
                'success': False,
                'error': 'Request timeout',
                'attempt': attempt_num
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'attempt': attempt_num
            }
    
    def _apply_normalization(self, crawl_result: Dict) -> Dict:
        """Apply normalization to reduce environment-specific variations"""
        
        # Normalize load time (major source of score differences)
        raw_load_time = crawl_result['load_time']
        normalized_load_time = min(raw_load_time, self.max_load_time)
        
        # Apply load time smoothing to reduce network jitter impact
        if normalized_load_time <= 1.0:
            smoothed_load_time = normalized_load_time
        elif normalized_load_time <= 3.0:
            # Reduce sensitivity in the 1-3 second range
            smoothed_load_time = 1.0 + (normalized_load_time - 1.0) * 0.8
        else:
            # Further reduce sensitivity for slower loads
            smoothed_load_time = 2.6 + (normalized_load_time - 3.0) * 0.5
        
        # Parse content with consistent settings
        soup = BeautifulSoup(crawl_result['content'], 'html.parser')
        
        # Extract normalized features
        normalized_features = self._extract_normalized_features(
            soup, 
            crawl_result['content'], 
            crawl_result, 
            smoothed_load_time
        )
        
        # Add normalization metadata
        crawl_result.update({
            'normalized_load_time': smoothed_load_time,
            'raw_load_time': raw_load_time,
            'normalization_applied': True,
            'features': normalized_features,
            'strategy': 'normalized'
        })
        
        return crawl_result
    
    def _extract_normalized_features(self, soup: BeautifulSoup, content: str, 
                                   crawl_result: Dict, load_time: float) -> Dict:
        """Extract features with normalization applied"""
        
        # Content normalization - remove scripts and styles for consistent word counting
        content_soup = BeautifulSoup(content, 'html.parser')
        for element in content_soup(['script', 'style', 'noscript']):
            element.decompose()
        
        # Normalize text extraction
        text_content = content_soup.get_text(separator=' ', strip=True)
        words = [word for word in text_content.split() if len(word) > 1]  # Filter very short words
        
        # Title normalization
        title_tag = soup.find('title')
        title_text = title_tag.get_text().strip() if title_tag else ""
        
        # Meta description normalization
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if not meta_desc:
            meta_desc = soup.find('meta', attrs={'property': 'og:description'})
        meta_description = meta_desc.get('content', '').strip() if meta_desc else ""
        
        # Heading analysis with normalization
        h1_tags = soup.find_all('h1')
        h2_tags = soup.find_all('h2')
        h3_tags = soup.find_all('h3')
        
        # Link analysis with domain normalization
        all_links = soup.find_all('a', href=True)
        internal_links = 0
        external_links = 0
        
        base_domain = urlparse(crawl_result['url']).netloc.lower()
        
        for link in all_links:
            href = link.get('href', '').strip()
            if not href or href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                continue
                
            if href.startswith('http'):
                try:
                    link_domain = urlparse(href).netloc.lower()
                    if link_domain == base_domain:
                        internal_links += 1
                    elif link_domain:  # Valid external domain
                        external_links += 1
                except:
                    continue
            elif href.startswith('/'):
                internal_links += 1
        
        # Image analysis
        images = soup.find_all('img')
        images_with_alt = sum(1 for img in images if img.get('alt', '').strip())
        
        # Technical features
        has_viewport = bool(soup.find('meta', attrs={'name': 'viewport'}))
        has_canonical = bool(soup.find('link', rel='canonical'))
        has_robots_meta = bool(soup.find('meta', attrs={'name': 'robots'}))
        has_ssl = crawl_result['url'].startswith('https://')
        
        # Content size normalization
        content_size = len(content.encode('utf-8'))
        
        # Compression detection
        compression_enabled = any(
            encoding in crawl_result.get('headers', {}).get('content-encoding', '').lower()
            for encoding in ['gzip', 'br', 'deflate']
        )
        
        return {
            # Content features (normalized)
            'title_length': len(title_text),
            'title_present': len(title_text) > 0,
            'meta_description_length': len(meta_description),
            'meta_description_present': len(meta_description) > 0,
            'word_count': len(words),
            
            # Structure features
            'h1_count': len(h1_tags),
            'h2_count': len(h2_tags), 
            'h3_count': len(h3_tags),
            'internal_links_count': internal_links,
            'external_links_count': external_links,
            'images_count': len(images),
            'images_with_alt_count': images_with_alt,
            
            # Technical features
            'has_viewport': has_viewport,
            'has_canonical': has_canonical,
            'has_robots_meta': has_robots_meta,
            'has_ssl': has_ssl,
            'compression_enabled': compression_enabled,
            
            # Performance features (normalized)
            'load_time': load_time,
            'content_size': content_size,
            'load_time_score': self._calculate_normalized_load_time_score(load_time),
            'content_size_score': self._calculate_normalized_content_size_score(content_size),
            
            # Quality indicators
            'content_quality_score': self._calculate_content_quality_score(len(words), title_text, meta_description),
            'technical_quality_score': self._calculate_technical_quality_score(
                has_ssl, has_viewport, has_canonical
            )
        }
    
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
    
    def _calculate_normalized_load_time_score(self, load_time: float) -> int:
        """Calculate load time score with normalization"""
        if load_time <= 1.0:
            return 40
        elif load_time <= 1.5:
            return 38
        elif load_time <= 2.0:
            return 35
        elif load_time <= 2.5:
            return 32
        elif load_time <= 3.0:
            return 28
        elif load_time <= 4.0:
            return 25
        elif load_time <= 5.0:
            return 20
        else:
            return 15
    
    def _calculate_normalized_content_size_score(self, content_size: int) -> int:
        """Calculate content size score with normalization"""
        size_mb = content_size / (1024 * 1024)
        
        if size_mb <= 0.3:
            return 20
        elif size_mb <= 0.5:
            return 18
        elif size_mb <= 1.0:
            return 15
        elif size_mb <= 2.0:
            return 12
        elif size_mb <= 3.0:
            return 8
        else:
            return 5
    
    def _calculate_content_quality_score(self, word_count: int, title: str, meta_desc: str) -> int:
        """Calculate content quality score"""
        score = 0
        
        # Word count scoring
        if word_count >= 500:
            score += 15
        elif word_count >= 300:
            score += 12
        elif word_count >= 150:
            score += 8
        elif word_count >= 50:
            score += 5
        
        # Title quality
        title_len = len(title)
        if 30 <= title_len <= 60:
            score += 10
        elif 20 <= title_len <= 80:
            score += 7
        elif title_len > 0:
            score += 3
        
        # Meta description quality
        meta_len = len(meta_desc)
        if 120 <= meta_len <= 160:
            score += 10
        elif 80 <= meta_len <= 200:
            score += 7
        elif meta_len > 0:
            score += 3
        
        return min(score, 35)
    
    def _calculate_technical_quality_score(self, has_ssl: bool, has_viewport: bool, has_canonical: bool) -> int:
        """Calculate technical quality score"""
        score = 0
        
        if has_ssl:
            score += 15
        if has_viewport:
            score += 10
        if has_canonical:
            score += 5
        
        return min(score, 40)
    
    def _generate_recommendations(self, features: Dict, crawl_result: Dict) -> List[Recommendation]:
        """Generate recommendations based on normalized analysis"""
        recommendations = []
        
        # Content recommendations
        if features.get('word_count', 0) < 300:
            recommendations.append(Recommendation(
                category="Content",
                title="Increase Content Length",
                description=f"Your page has {features.get('word_count', 0)} words. Add more quality content (aim for 300+ words).",
                priority="medium",
                impact="Improved search engine ranking",
                effort="Medium - 1-2 hours",
                resources=["https://developers.google.com/search/docs/fundamentals/creating-helpful-content"]
            ))
        
        if not features.get('title_present', False):
            recommendations.append(Recommendation(
                category="SEO",
                title="Add Page Title",
                description="Your page is missing a title tag, which is crucial for SEO.",
                priority="high",
                impact="Significantly improved search visibility",
                effort="Low - 5 minutes",
                resources=["https://developers.google.com/search/docs/appearance/title-link"]
            ))
        
        if not features.get('has_viewport', False):
            recommendations.append(Recommendation(
                category="Mobile",
                title="Add Viewport Meta Tag",
                description="Add viewport meta tag for mobile responsiveness.",
                priority="high",
                impact="Improved mobile rankings",
                effort="Low - 5 minutes",
                resources=["https://developers.google.com/search/docs/crawling-indexing/mobile/mobile-sites-mobile-first-indexing"]
            ))
        
        # Performance recommendations
        load_time = features.get('load_time', 0)
        if load_time > 3.0:
            recommendations.append(Recommendation(
                category="Performance",
                title="Improve Page Load Speed",
                description=f"Page loads in {load_time:.2f} seconds. Optimize for faster loading.",
                priority="medium",
                impact="Better user experience and rankings",
                effort="High - 4-8 hours",
                resources=["https://developers.google.com/speed/docs/insights/rules"]
            ))
        
        return recommendations[:6]  # Return top 6 recommendations
    
    def _generate_explanation(self, score: int, features: Dict) -> str:
        """Generate explanation based on score and features"""
        if score >= 90:
            return "Excellent crawlability with strong SEO fundamentals and good performance."
        elif score >= 80:
            return "Good crawlability with solid foundation. Minor optimizations could improve accessibility."
        elif score >= 70:
            return "Fair crawlability with room for improvement in content quality or technical SEO."
        elif score >= 60:
            return "Poor crawlability with significant issues affecting search engine access."
        else:
            return "Critical crawlability issues detected. Major improvements required."
    
    def _create_failed_result(self, url: str, error: str) -> Dict:
        """Create result for failed analysis"""
        return {
            'name': 'Crawlability',
            'score': 0,
            'description': 'Crawlability analysis failed',
            'explanation': f"Unable to analyze crawlability: {error}",
            'recommendations': [Recommendation(
                category="Error",
                title="Analysis Failed",
                description=f"Could not analyze website: {error}",
                priority="high",
                impact="Unable to provide recommendations",
                effort="N/A",
                resources=[]
            )]
        }
