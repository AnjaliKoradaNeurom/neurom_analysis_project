import aiohttp
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
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

class SEOAnalyzer:
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    async def analyze(self, url: str) -> ModuleResult:
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; NeuromBot/1.0)'}) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}")
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Analyze SEO factors
                    seo_data = await self._analyze_seo_factors(soup, url)
                    score = self._calculate_seo_score(seo_data)
                    recommendations = self._generate_recommendations(seo_data)
                    
                    return ModuleResult(
                        name="SEO & Metadata",
                        score=score,
                        description="Search engine optimization and meta tags analysis",
                        explanation=self._generate_explanation(score, seo_data),
                        recommendations=recommendations
                    )
        
        except Exception as e:
            return ModuleResult(
                name="SEO & Metadata",
                score=0,
                description="SEO analysis failed",
                explanation=f"Unable to analyze SEO: {str(e)}",
                recommendations=[Recommendation(
                    priority="High",
                    title="Analysis Failed",
                    message="Could not retrieve or parse the webpage for SEO analysis.",
                    doc_link="https://developers.google.com/search/docs"
                )]
            )
    
    async def _analyze_seo_factors(self, soup: BeautifulSoup, url: str) -> Dict:
        return {
            'title': self._check_title(soup),
            'meta_description': self._check_meta_description(soup),
            'headings': self._check_headings(soup),
            'images': self._check_images(soup),
            'links': self._check_links(soup, url),
            'schema': self._check_schema(soup),
            'open_graph': self._check_open_graph(soup),
            'canonical': self._check_canonical(soup)
        }
    
    def _check_title(self, soup: BeautifulSoup) -> Dict:
        title_tag = soup.find('title')
        if not title_tag:
            return {'exists': False, 'length': 0, 'text': ''}
        
        title_text = title_tag.get_text().strip()
        return {
            'exists': True,
            'length': len(title_text),
            'text': title_text,
            'optimal': 30 <= len(title_text) <= 60
        }
    
    def _check_meta_description(self, soup: BeautifulSoup) -> Dict:
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if not meta_desc or not meta_desc.get('content'):
            return {'exists': False, 'length': 0, 'text': ''}
        
        desc_text = meta_desc.get('content').strip()
        return {
            'exists': True,
            'length': len(desc_text),
            'text': desc_text,
            'optimal': 120 <= len(desc_text) <= 160
        }
    
    def _check_headings(self, soup: BeautifulSoup) -> Dict:
        headings = {'h1': [], 'h2': [], 'h3': [], 'h4': [], 'h5': [], 'h6': []}
        
        for level in headings.keys():
            tags = soup.find_all(level)
            headings[level] = [tag.get_text().strip() for tag in tags]
        
        return {
            'structure': headings,
            'h1_count': len(headings['h1']),
            'has_h1': len(headings['h1']) > 0,
            'proper_hierarchy': self._check_heading_hierarchy(headings)
        }
    
    def _check_heading_hierarchy(self, headings: Dict) -> bool:
        # Simple check for proper heading hierarchy
        has_h1 = len(headings['h1']) > 0
        has_multiple_h1 = len(headings['h1']) > 1
        return has_h1 and not has_multiple_h1
    
    def _check_images(self, soup: BeautifulSoup) -> Dict:
        images = soup.find_all('img')
        total_images = len(images)
        images_with_alt = len([img for img in images if img.get('alt')])
        
        return {
            'total': total_images,
            'with_alt': images_with_alt,
            'alt_percentage': (images_with_alt / total_images * 100) if total_images > 0 else 100
        }
    
    def _check_links(self, soup: BeautifulSoup, base_url: str) -> Dict:
        links = soup.find_all('a', href=True)
        internal_links = []
        external_links = []
        
        base_domain = urlparse(base_url).netloc
        
        for link in links:
            href = link.get('href')
            if href.startswith('http'):
                if urlparse(href).netloc == base_domain:
                    internal_links.append(href)
                else:
                    external_links.append(href)
            elif href.startswith('/'):
                internal_links.append(urljoin(base_url, href))
        
        return {
            'total': len(links),
            'internal': len(internal_links),
            'external': len(external_links)
        }
    
    def _check_schema(self, soup: BeautifulSoup) -> Dict:
        schema_scripts = soup.find_all('script', type='application/ld+json')
        return {
            'exists': len(schema_scripts) > 0,
            'count': len(schema_scripts)
        }
    
    def _check_open_graph(self, soup: BeautifulSoup) -> Dict:
        og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
        required_og = ['og:title', 'og:description', 'og:image', 'og:url']
        
        found_og = [tag.get('property') for tag in og_tags]
        missing_og = [tag for tag in required_og if tag not in found_og]
        
        return {
            'exists': len(og_tags) > 0,
            'count': len(og_tags),
            'missing': missing_og,
            'complete': len(missing_og) == 0
        }
    
    def _check_canonical(self, soup: BeautifulSoup) -> Dict:
        canonical = soup.find('link', rel='canonical')
        return {
            'exists': canonical is not None,
            'url': canonical.get('href') if canonical else None
        }
    
    def _calculate_seo_score(self, data: Dict) -> int:
        score = 0
        max_score = 100
        
        # Title (20 points)
        if data['title']['exists']:
            score += 10
            if data['title']['optimal']:
                score += 10
        
        # Meta description (20 points)
        if data['meta_description']['exists']:
            score += 10
            if data['meta_description']['optimal']:
                score += 10
        
        # Headings (15 points)
        if data['headings']['has_h1']:
            score += 10
        if data['headings']['proper_hierarchy']:
            score += 5
        
        # Images (15 points)
        if data['images']['alt_percentage'] >= 80:
            score += 15
        elif data['images']['alt_percentage'] >= 50:
            score += 10
        elif data['images']['alt_percentage'] >= 25:
            score += 5
        
        # Open Graph (15 points)
        if data['open_graph']['exists']:
            score += 5
        if data['open_graph']['complete']:
            score += 10
        
        # Schema (10 points)
        if data['schema']['exists']:
            score += 10
        
        # Canonical (5 points)
        if data['canonical']['exists']:
            score += 5
        
        return min(score, max_score)
    
    def _generate_explanation(self, score: int, data: Dict) -> str:
        if score >= 90:
            return "Excellent SEO optimization with comprehensive meta tags, proper heading structure, and good content organization."
        elif score >= 70:
            return "Good SEO foundation with room for improvement in meta tags, content structure, or technical SEO elements."
        else:
            return "SEO needs significant improvement. Missing critical elements like meta descriptions, proper headings, or structured data."
    
    def _generate_recommendations(self, data: Dict) -> List[Recommendation]:
        recommendations = []
        
        # Title recommendations
        if not data['title']['exists']:
            recommendations.append(Recommendation(
                priority="High",
                title="Missing Page Title",
                message="Add a descriptive title tag to improve search engine visibility.",
                code_snippet='<title>Your Page Title Here</title>',
                doc_link="https://developers.google.com/search/docs/appearance/title-link"
            ))
        elif not data['title']['optimal']:
            recommendations.append(Recommendation(
                priority="Medium",
                title="Optimize Title Length",
                message="Title should be between 30-60 characters for optimal display in search results.",
                code_snippet='<title>Optimized Title (30-60 chars)</title>',
                doc_link="https://developers.google.com/search/docs/appearance/title-link"
            ))
        
        # Meta description recommendations
        if not data['meta_description']['exists']:
            recommendations.append(Recommendation(
                priority="High",
                title="Missing Meta Description",
                message="Add a compelling meta description to improve click-through rates from search results.",
                code_snippet='<meta name="description" content="Your compelling page description here (120-160 chars)">',
                doc_link="https://developers.google.com/search/docs/appearance/snippet"
            ))
        elif not data['meta_description']['optimal']:
            recommendations.append(Recommendation(
                priority="Medium",
                title="Optimize Meta Description Length",
                message="Meta description should be between 120-160 characters for optimal display.",
                code_snippet='<meta name="description" content="Optimized description (120-160 chars)">',
                doc_link="https://developers.google.com/search/docs/appearance/snippet"
            ))
        
        # Heading recommendations
        if not data['headings']['has_h1']:
            recommendations.append(Recommendation(
                priority="High",
                title="Missing H1 Tag",
                message="Add a single H1 tag to clearly define the main topic of the page.",
                code_snippet='<h1>Main Page Heading</h1>',
                doc_link="https://developer.mozilla.org/en-US/docs/Web/HTML/Element/Heading_Elements"
            ))
        
        if not data['headings']['proper_hierarchy']:
            recommendations.append(Recommendation(
                priority="Medium",
                title="Improve Heading Structure",
                message="Use proper heading hierarchy (H1 > H2 > H3) for better content organization.",
                code_snippet='<h1>Main Title</h1>\n<h2>Section Title</h2>\n<h3>Subsection</h3>',
                doc_link="https://developer.mozilla.org/en-US/docs/Web/HTML/Element/Heading_Elements"
            ))
        
        # Image recommendations
        if data['images']['alt_percentage'] < 80:
            recommendations.append(Recommendation(
                priority="Medium",
                title="Add Alt Text to Images",
                message="Improve accessibility and SEO by adding descriptive alt text to all images.",
                code_snippet='<img src="image.jpg" alt="Descriptive alt text" />',
                doc_link="https://developer.mozilla.org/en-US/docs/Web/API/HTMLImageElement/alt"
            ))
        
        # Open Graph recommendations
        if not data['open_graph']['complete']:
            recommendations.append(Recommendation(
                priority="Medium",
                title="Add Open Graph Tags",
                message="Implement Open Graph meta tags for better social media sharing.",
                code_snippet='<meta property="og:title" content="Page Title">\n<meta property="og:description" content="Page description">\n<meta property="og:image" content="image-url">',
                doc_link="https://ogp.me/"
            ))
        
        # Schema recommendations
        if not data['schema']['exists']:
            recommendations.append(Recommendation(
                priority="Low",
                title="Add Structured Data",
                message="Implement JSON-LD structured data to help search engines understand your content.",
                code_snippet='<script type="application/ld+json">\n{\n  "@context": "https://schema.org",\n  "@type": "WebPage",\n  "name": "Page Name"\n}\n</script>',
                doc_link="https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data"
            ))
        
        return recommendations
