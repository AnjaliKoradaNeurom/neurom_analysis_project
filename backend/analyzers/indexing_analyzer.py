import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Dict
from pydantic import BaseModel

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

class IndexingAnalyzer:
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    async def analyze(self, url: str) -> ModuleResult:
        try:
            indexing_data = await self._analyze_indexing(url)
            score = self._calculate_indexing_score(indexing_data)
            recommendations = self._generate_recommendations(indexing_data)
            
            return ModuleResult(
                name="Indexing",
                score=score,
                description="Search engine indexing optimization",
                explanation=self._generate_explanation(score, indexing_data),
                recommendations=recommendations
            )
        
        except Exception as e:
            return ModuleResult(
                name="Indexing",
                score=0,
                description="Indexing analysis failed",
                explanation=f"Unable to analyze indexing: {str(e)}",
                recommendations=[Recommendation(
                    priority="High",
                    title="Indexing Analysis Failed",
                    message="Could not analyze canonical tags, meta robots, or indexing directives.",
                    doc_link="https://developers.google.com/search/docs/crawling-indexing"
                )]
            )
    
    async def _analyze_indexing(self, url: str) -> Dict:
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; NeuromBot/1.0)'}) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                return {
                    'canonical': self._check_canonical(soup, url),
                    'meta_robots': self._check_meta_robots(soup),
                    'duplicate_content': self._check_duplicate_content(soup),
                    'noindex_tags': self._check_noindex_tags(soup),
                    'hreflang': self._check_hreflang(soup)
                }
    
    def _check_canonical(self, soup: BeautifulSoup, current_url: str) -> Dict:
        canonical_tag = soup.find('link', rel='canonical')
        
        if not canonical_tag:
            return {'exists': False, 'url': None, 'self_referencing': False}
        
        canonical_url = canonical_tag.get('href')
        if not canonical_url:
            return {'exists': False, 'url': None, 'self_referencing': False}
        
        # Check if canonical is self-referencing
        parsed_current = urlparse(current_url)
        parsed_canonical = urlparse(canonical_url)
        
        self_referencing = (
            parsed_current.netloc == parsed_canonical.netloc and
            parsed_current.path == parsed_canonical.path
        )
        
        return {
            'exists': True,
            'url': canonical_url,
            'self_referencing': self_referencing
        }
    
    def _check_meta_robots(self, soup: BeautifulSoup) -> Dict:
        robots_tag = soup.find('meta', attrs={'name': 'robots'})
        
        if not robots_tag:
            return {'exists': False, 'content': '', 'noindex': False, 'nofollow': False}
        
        content = robots_tag.get('content', '').lower()
        
        return {
            'exists': True,
            'content': content,
            'noindex': 'noindex' in content,
            'nofollow': 'nofollow' in content,
            'index': 'index' in content or ('noindex' not in content and content != ''),
            'follow': 'follow' in content or ('nofollow' not in content and content != '')
        }
    
    def _check_duplicate_content(self, soup: BeautifulSoup) -> Dict:
        # Simple duplicate content indicators
        title = soup.find('title')
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        h1_tags = soup.find_all('h1')
        
        # Check for multiple H1 tags (potential duplicate content issue)
        multiple_h1 = len(h1_tags) > 1
        
        # Check for very short or missing content
        body = soup.find('body')
        content_length = len(body.get_text().strip()) if body else 0
        thin_content = content_length < 300
        
        return {
            'multiple_h1': multiple_h1,
            'thin_content': thin_content,
            'content_length': content_length,
            'has_title': title is not None,
            'has_meta_desc': meta_desc is not None
        }
    
    def _check_noindex_tags(self, soup: BeautifulSoup) -> Dict:
        # Check for noindex in meta robots
        meta_robots = soup.find('meta', attrs={'name': 'robots'})
        robots_noindex = False
        
        if meta_robots:
            content = meta_robots.get('content', '').lower()
            robots_noindex = 'noindex' in content
        
        # Check for X-Robots-Tag (would need to be checked in HTTP headers in real implementation)
        return {
            'meta_robots_noindex': robots_noindex,
            'blocking_indexing': robots_noindex
        }
    
    def _check_hreflang(self, soup: BeautifulSoup) -> Dict:
        hreflang_tags = soup.find_all('link', rel='alternate', hreflang=True)
        
        return {
            'exists': len(hreflang_tags) > 0,
            'count': len(hreflang_tags),
            'languages': [tag.get('hreflang') for tag in hreflang_tags]
        }
    
    def _calculate_indexing_score(self, data: Dict) -> int:
        score = 0
        
        # Canonical tag (25 points)
        if data['canonical']['exists']:
            score += 15
            if data['canonical']['self_referencing']:
                score += 10
        
        # Meta robots (25 points)
        if data['meta_robots']['exists']:
            score += 10
            if data['meta_robots']['index'] and data['meta_robots']['follow']:
                score += 15
        else:
            # Default behavior is index,follow
            score += 25
        
        # Duplicate content (30 points)
        dup_content = data['duplicate_content']
        if not dup_content['multiple_h1']:
            score += 10
        if not dup_content['thin_content']:
            score += 20
        
        # Noindex issues (20 points)
        if not data['noindex_tags']['blocking_indexing']:
            score += 20
        
        return min(score, 100)
    
    def _generate_explanation(self, score: int, data: Dict) -> str:
        if score >= 90:
            return "Excellent indexing optimization with proper canonical tags, meta robots, and no duplicate content issues."
        elif score >= 70:
            return "Good indexing setup with minor issues that could be optimized for better search engine understanding."
        else:
            return "Indexing needs improvement. Issues with canonical tags, duplicate content, or indexing directives may affect search visibility."
    
    def _generate_recommendations(self, data: Dict) -> List[Recommendation]:
        recommendations = []
        
        # Canonical recommendations
        if not data['canonical']['exists']:
            recommendations.append(Recommendation(
                priority="High",
                title="Add Canonical Tags",
                message="Implement canonical tags to prevent duplicate content issues and consolidate page authority.",
                code_snippet='<link rel="canonical" href="https://example.com/preferred-url">',
                doc_link="https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls"
            ))
        elif not data['canonical']['self_referencing']:
            recommendations.append(Recommendation(
                priority="Medium",
                title="Review Canonical URL",
                message="Ensure canonical tag points to the correct preferred version of this page.",
                doc_link="https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls"
            ))
        
        # Meta robots recommendations
        if data['meta_robots']['noindex']:
            recommendations.append(Recommendation(
                priority="High",
                title="Review Noindex Directive",
                message="This page is blocked from indexing. Remove noindex if you want it to appear in search results.",
                code_snippet='<meta name="robots" content="index, follow">',
                doc_link="https://developers.google.com/search/docs/crawling-indexing/block-indexing"
            ))
        
        # Duplicate content recommendations
        dup_content = data['duplicate_content']
        if dup_content['multiple_h1']:
            recommendations.append(Recommendation(
                priority="Medium",
                title="Fix Multiple H1 Tags",
                message="Use only one H1 tag per page to avoid duplicate content signals.",
                code_snippet='<h1>Single Main Heading</h1>\n<h2>Subheading</h2>',
                doc_link="https://developer.mozilla.org/en-US/docs/Web/HTML/Element/Heading_Elements"
            ))
        
        if dup_content['thin_content']:
            recommendations.append(Recommendation(
                priority="Medium",
                title="Increase Content Length",
                message="Add more valuable, unique content to improve indexing and ranking potential.",
                doc_link="https://developers.google.com/search/docs/fundamentals/creating-helpful-content"
            ))
        
        return recommendations
