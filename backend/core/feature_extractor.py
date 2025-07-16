"""
Feature extraction from HTML content and web pages
"""

import re
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Comment
import json
from models.schemas import CrawlabilityFeatures
import math

logger = logging.getLogger(__name__)

class FeatureExtractor:
    """
    Extract features from HTML content for crawlability analysis
    """
    
    def __init__(self):
        self.structured_data_types = [
            'application/ld+json',
            'application/json',
            'text/turtle',
            'application/rdf+xml'
        ]
        
        self.security_headers = [
            'strict-transport-security',
            'content-security-policy',
            'x-frame-options',
            'x-content-type-options',
            'x-xss-protection',
            'referrer-policy',
            'permissions-policy'
        ]
        
        self.seo_keywords = [
            'title', 'description', 'keywords', 'author', 'robots',
            'canonical', 'og:', 'twitter:', 'schema', 'json-ld'
        ]
        
        self.performance_indicators = [
            'async', 'defer', 'lazy', 'preload', 'prefetch',
            'critical', 'above-fold', 'minified'
        ]
    
    async def extract_features(self, crawl_result: Dict[str, Any]) -> CrawlabilityFeatures:
        """
        Extract all features from crawl result
        """
        try:
            start_time = time.time()
            logger.info(f"🔍 Extracting features from: {crawl_result.get('url', 'Unknown')}")
            
            if not crawl_result.get('success', False):
                return self._create_empty_features()
            
            url = crawl_result['url']
            content = crawl_result.get('html', '')
            headers = crawl_result.get('headers', {})
            status_code = crawl_result.get('status_code', 0)
            
            # Parse HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract all features
            features = CrawlabilityFeatures(
                url=url,
                status_code=status_code,
                https_enabled=url.startswith('https://'),
                ssl_certificate_valid=not crawl_result.get('ssl_error', False),
                html_size=len(content.encode('utf-8')),
                word_count=self._count_words(soup),
                page_load_time=crawl_result.get('crawl_time', 0.0)
            )
            
            # Security features
            features.security_headers_count = self._count_security_headers(headers)
            
            # Meta tags
            features.title_length = self._get_title_length(soup)
            features.title_tag_present = features.title_length > 0
            features.meta_description_length = self._get_meta_description_length(soup)
            features.meta_description_present = features.meta_description_length > 0
            
            # Heading structure
            features.h1_count = len(soup.find_all('h1'))
            features.h2_count = len(soup.find_all('h2'))
            features.h3_count = len(soup.find_all('h3'))
            
            # Get H1 text
            h1_tag = soup.find('h1')
            features.h1_text = h1_tag.get_text().strip() if h1_tag else ""
            
            # Links analysis
            internal_links, external_links = self._analyze_links(soup, url)
            features.internal_links_count = internal_links
            features.external_links_count = external_links
            
            # Images analysis
            images_data = self._analyze_images(soup)
            features.images_count = images_data['total']
            features.images_with_alt_count = images_data['with_alt']
            features.lazy_loading_images = images_data['lazy_loading']
            
            # Technical SEO
            features.canonical_tag_present = self._has_canonical_tag(soup)
            features.meta_robots_noindex = self._has_noindex_meta(soup)
            features.structured_data_present = self._has_structured_data(soup)
            features.open_graph_tags_count = self._count_open_graph_tags(soup)
            features.open_graph_present = features.open_graph_tags_count > 0
            features.twitter_cards_present = self._has_twitter_card(soup)
            
            # Mobile and viewport
            features.viewport_configured = self._has_viewport_meta(soup)
            features.mobile_friendly = self._is_mobile_friendly(soup, content)
            
            # External resources
            features.external_scripts_count = self._count_external_scripts(soup, url)
            features.external_stylesheets_count = self._count_external_stylesheets(soup, url)
            
            # Additional features
            features.favicon_present = self._has_favicon(soup)
            features.lang_attribute_present = self._has_lang_attribute(soup)
            features.charset_declared = self._has_charset_declaration(soup, content)
            features.inline_css_count = len(soup.find_all('style'))
            features.inline_js_count = len(soup.find_all('script', src=False))
            
            # Performance features
            features.compression_enabled = 'gzip' in headers.get('content-encoding', '').lower() or \
                                         'br' in headers.get('content-encoding', '').lower()
            
            cache_headers = ['cache-control', 'expires', 'etag', 'last-modified']
            features.cache_headers_present = any(h in [k.lower() for k in headers.keys()] for h in cache_headers)
            
            # Calculate scores
            features.accessibility_score = self._calculate_accessibility_score(soup)
            features.performance_score = self._calculate_performance_score(features, crawl_result)
            features.seo_score = self._calculate_seo_score(features, soup)
            
            # Additional raw features for extensibility
            features.raw_features = {
                'has_favicon': self._has_favicon(soup),
                'has_lang_attribute': self._has_lang_attribute(soup),
                'has_charset_declaration': self._has_charset_declaration(soup, content),
                'inline_styles_count': len(soup.find_all('style')),
                'inline_scripts_count': len(soup.find_all('script', src=False)),
                'comment_count': len(soup.find_all(string=lambda text: isinstance(text, Comment))),
                'form_count': len(soup.find_all('form')),
                'iframe_count': len(soup.find_all('iframe')),
                'video_count': len(soup.find_all(['video', 'embed', 'object'])),
                'audio_count': len(soup.find_all('audio')),
                'table_count': len(soup.find_all('table')),
                'list_count': len(soup.find_all(['ul', 'ol'])),
                'button_count': len(soup.find_all(['button', 'input[type="button"]', 'input[type="submit"]'])),
                'input_count': len(soup.find_all('input')),
                'select_count': len(soup.find_all('select')),
                'textarea_count': len(soup.find_all('textarea')),
                'has_search_functionality': self._has_search_functionality(soup),
                'has_breadcrumbs': self._has_breadcrumbs(soup),
                'has_pagination': self._has_pagination(soup),
                'has_social_media_links': self._has_social_media_links(soup),
                'content_to_html_ratio': self._calculate_content_ratio(soup, content),
                'text_compression_ratio': self._calculate_text_compression_ratio(content),
                'duplicate_title_tags': len(soup.find_all('title')) > 1,
                'duplicate_h1_tags': len(soup.find_all('h1')) > 1,
                'missing_alt_images': images_data['total'] - images_data['with_alt'],
                'broken_links_indicators': self._detect_broken_link_indicators(soup),
                'has_print_stylesheet': self._has_print_stylesheet(soup),
                'has_rss_feed': self._has_rss_feed(soup),
                'has_sitemap_reference': self._has_sitemap_reference(soup),
                'page_depth_estimate': self._estimate_page_depth(url),
                'url_length': len(url),
                'url_parameters_count': len(urlparse(url).query.split('&')) if urlparse(url).query else 0,
                'has_www_prefix': url.startswith('https://www.') or url.startswith('http://www.'),
                'domain_extension': urlparse(url).netloc.split('.')[-1] if '.' in urlparse(url).netloc else '',
                'has_hreflang': self._has_hreflang_tags(soup),
                'has_amp_version': self._has_amp_version(soup),
                'has_mobile_app_links': self._has_mobile_app_links(soup),
                'performance_hints': self._detect_performance_hints(soup),
                'accessibility_features': self._detect_accessibility_features(soup),
                'seo_friendly_urls': self._has_seo_friendly_urls(soup, url)
            }
            
            extraction_time = time.time() - start_time
            logger.info(f"✅ Feature extraction completed in {extraction_time:.2f}s")
            
            return features
            
        except Exception as e:
            logger.error(f"❌ Feature extraction failed: {str(e)}")
            return self._create_empty_features()
    
    def _create_empty_features(self) -> CrawlabilityFeatures:
        """Create empty features object for failed crawls"""
        return CrawlabilityFeatures(
            url='',
            status_code=0,
            https_enabled=False,
            ssl_certificate_valid=False,
            html_size=0,
            word_count=0,
            page_load_time=0.0
        )
    
    def _count_security_headers(self, headers: Dict[str, str]) -> int:
        """Count security headers present"""
        count = 0
        headers_lower = {k.lower(): v for k, v in headers.items()}
        
        for header in self.security_headers:
            if header in headers_lower:
                count += 1
        
        return count
    
    def _count_words(self, soup: BeautifulSoup) -> int:
        """Count words in visible text content"""
        try:
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text and count words
            text = soup.get_text()
            words = re.findall(r'\b\w+\b', text)
            return len(words)
        except:
            return 0
    
    def _get_title_length(self, soup: BeautifulSoup) -> int:
        """Get title tag length"""
        try:
            title_tag = soup.find('title')
            return len(title_tag.get_text().strip()) if title_tag else 0
        except:
            return 0
    
    def _get_meta_description_length(self, soup: BeautifulSoup) -> int:
        """Get meta description length"""
        try:
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                return len(meta_desc['content'].strip())
            return 0
        except:
            return 0
    
    def _analyze_links(self, soup: BeautifulSoup, base_url: str) -> Tuple[int, int]:
        """Analyze internal and external links"""
        try:
            base_domain = urlparse(base_url).netloc.lower()
            internal_count = 0
            external_count = 0
            
            for link in soup.find_all('a', href=True):
                href = link['href'].strip()
                if not href or href.startswith('#') or href.startswith('mailto:') or href.startswith('tel:'):
                    continue
                
                # Resolve relative URLs
                full_url = urljoin(base_url, href)
                link_domain = urlparse(full_url).netloc.lower()
                
                if link_domain == base_domain:
                    internal_count += 1
                elif link_domain:  # External link with valid domain
                    external_count += 1
            
            return internal_count, external_count
        except:
            return 0, 0
    
    def _analyze_images(self, soup: BeautifulSoup) -> Dict[str, int]:
        """Analyze images for alt text and lazy loading"""
        try:
            images = soup.find_all('img')
            total = len(images)
            with_alt = 0
            lazy_loading = 0
            
            for img in images:
                # Check for alt text
                if img.get('alt') is not None:
                    with_alt += 1
                
                # Check for lazy loading
                if (img.get('loading') == 'lazy' or 
                    'lazy' in img.get('class', []) or
                    img.get('data-src')):
                    lazy_loading += 1
            
            return {
                'total': total,
                'with_alt': with_alt,
                'lazy_loading': lazy_loading
            }
        except:
            return {'total': 0, 'with_alt': 0, 'lazy_loading': 0}
    
    def _has_canonical_tag(self, soup: BeautifulSoup) -> bool:
        """Check for canonical link tag"""
        try:
            canonical = soup.find('link', rel='canonical')
            return canonical is not None and canonical.get('href')
        except:
            return False
    
    def _has_noindex_meta(self, soup: BeautifulSoup) -> bool:
        """Check for noindex meta robots tag"""
        try:
            robots_meta = soup.find('meta', attrs={'name': 'robots'})
            if robots_meta and robots_meta.get('content'):
                content = robots_meta['content'].lower()
                return 'noindex' in content
            return False
        except:
            return False
    
    def _has_structured_data(self, soup: BeautifulSoup) -> bool:
        """Check for structured data (JSON-LD, microdata, etc.)"""
        try:
            # JSON-LD
            json_ld = soup.find('script', type='application/ld+json')
            if json_ld:
                return True
            
            # Microdata
            microdata = soup.find(attrs={'itemscope': True})
            if microdata:
                return True
            
            # RDFa
            rdfa = soup.find(attrs={'typeof': True})
            if rdfa:
                return True
            
            return False
        except:
            return False
    
    def _count_open_graph_tags(self, soup: BeautifulSoup) -> int:
        """Count Open Graph meta tags"""
        try:
            og_tags = soup.find_all('meta', attrs={'property': re.compile(r'^og:')})
            return len(og_tags)
        except:
            return 0
    
    def _has_twitter_card(self, soup: BeautifulSoup) -> bool:
        """Check for Twitter Card meta tags"""
        try:
            twitter_card = soup.find('meta', attrs={'name': 'twitter:card'})
            return twitter_card is not None
        except:
            return False
    
    def _has_viewport_meta(self, soup: BeautifulSoup) -> bool:
        """Check for viewport meta tag"""
        try:
            viewport = soup.find('meta', attrs={'name': 'viewport'})
            return viewport is not None and viewport.get('content')
        except:
            return False
    
    def _is_mobile_friendly(self, soup: BeautifulSoup, content: str) -> bool:
        """Basic mobile-friendliness check"""
        try:
            # Check for viewport meta tag
            if not self._has_viewport_meta(soup):
                return False
            
            # Check for responsive CSS indicators
            responsive_indicators = [
                '@media',
                'max-width',
                'min-width',
                'screen and',
                'mobile',
                'responsive'
            ]
            
            content_lower = content.lower()
            for indicator in responsive_indicators:
                if indicator in content_lower:
                    return True
            
            return False
        except:
            return False
    
    def _count_external_scripts(self, soup: BeautifulSoup, base_url: str) -> int:
        """Count external JavaScript files"""
        try:
            base_domain = urlparse(base_url).netloc.lower()
            external_count = 0
            
            for script in soup.find_all('script', src=True):
                src = script['src'].strip()
                if src.startswith('//') or src.startswith('http'):
                    script_domain = urlparse(src).netloc.lower()
                    if script_domain and script_domain != base_domain:
                        external_count += 1
            
            return external_count
        except:
            return 0
    
    def _count_external_stylesheets(self, soup: BeautifulSoup, base_url: str) -> int:
        """Count external CSS files"""
        try:
            base_domain = urlparse(base_url).netloc.lower()
            external_count = 0
            
            for link in soup.find_all('link', rel='stylesheet', href=True):
                href = link['href'].strip()
                if href.startswith('//') or href.startswith('http'):
                    css_domain = urlparse(href).netloc.lower()
                    if css_domain and css_domain != base_domain:
                        external_count += 1
            
            return external_count
        except:
            return 0
    
    # Additional helper methods for raw features
    def _has_favicon(self, soup: BeautifulSoup) -> bool:
        """Check for favicon"""
        try:
            favicon = soup.find('link', rel=re.compile(r'icon', re.I))
            return favicon is not None
        except:
            return False
    
    def _has_lang_attribute(self, soup: BeautifulSoup) -> bool:
        """Check for lang attribute on html tag"""
        try:
            html_tag = soup.find('html')
            return html_tag is not None and html_tag.get('lang')
        except:
            return False
    
    def _has_charset_declaration(self, soup: BeautifulSoup, content: str) -> bool:
        """Check for charset declaration"""
        try:
            # Check meta charset
            charset_meta = soup.find('meta', charset=True)
            if charset_meta:
                return True
            
            # Check http-equiv content-type
            content_type = soup.find('meta', attrs={'http-equiv': 'Content-Type'})
            if content_type and content_type.get('content'):
                return 'charset' in content_type['content'].lower()
            
            return False
        except:
            return False
    
    def _has_search_functionality(self, soup: BeautifulSoup) -> bool:
        """Check for search functionality"""
        try:
            # Look for search forms
            search_forms = soup.find_all('form', attrs={'role': 'search'})
            if search_forms:
                return True
            
            # Look for search inputs
            search_inputs = soup.find_all('input', attrs={'type': 'search'})
            if search_inputs:
                return True
            
            # Look for common search patterns
            search_patterns = soup.find_all(['input', 'form'], attrs={'name': re.compile(r'search', re.I)})
            return len(search_patterns) > 0
        except:
            return False
    
    def _has_breadcrumbs(self, soup: BeautifulSoup) -> bool:
        """Check for breadcrumb navigation"""
        try:
            # Look for breadcrumb patterns
            breadcrumb_indicators = [
                soup.find(attrs={'class': re.compile(r'breadcrumb', re.I)}),
                soup.find(attrs={'id': re.compile(r'breadcrumb', re.I)}),
                soup.find('nav', attrs={'aria-label': re.compile(r'breadcrumb', re.I)}),
                soup.find('ol', attrs={'class': re.compile(r'breadcrumb', re.I)})
            ]
            
            return any(indicator is not None for indicator in breadcrumb_indicators)
        except:
            return False
    
    def _has_pagination(self, soup: BeautifulSoup) -> bool:
        """Check for pagination"""
        try:
            pagination_indicators = [
                soup.find(attrs={'class': re.compile(r'pag', re.I)}),
                soup.find('a', string=re.compile(r'next|previous|prev', re.I)),
                soup.find('link', rel='next'),
                soup.find('link', rel='prev')
            ]
            
            return any(indicator is not None for indicator in pagination_indicators)
        except:
            return False
    
    def _has_social_media_links(self, soup: BeautifulSoup) -> bool:
        """Check for social media links"""
        try:
            social_domains = [
                'facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com',
                'youtube.com', 'pinterest.com', 'tiktok.com', 'snapchat.com'
            ]
            
            for link in soup.find_all('a', href=True):
                href = link['href'].lower()
                if any(domain in href for domain in social_domains):
                    return True
            
            return False
        except:
            return False
    
    def _calculate_content_ratio(self, soup: BeautifulSoup, html_content: str) -> float:
        """Calculate text content to HTML ratio"""
        try:
            # Remove script and style elements
            soup_copy = BeautifulSoup(html_content, 'html.parser')
            for script in soup_copy(["script", "style"]):
                script.decompose()
            
            text_content = soup_copy.get_text()
            text_length = len(text_content.strip())
            html_length = len(html_content)
            
            return text_length / html_length if html_length > 0 else 0.0
        except:
            return 0.0
    
    def _calculate_text_compression_ratio(self, content: str) -> float:
        """Estimate text compression ratio"""
        try:
            import gzip
            original_size = len(content.encode('utf-8'))
            compressed_size = len(gzip.compress(content.encode('utf-8')))
            return compressed_size / original_size if original_size > 0 else 1.0
        except:
            return 1.0
    
    def _detect_broken_link_indicators(self, soup: BeautifulSoup) -> int:
        """Detect potential broken link indicators"""
        try:
            broken_indicators = 0
            
            for link in soup.find_all('a', href=True):
                href = link['href'].lower()
                # Common broken link patterns
                if any(pattern in href for pattern in ['#', 'javascript:', 'void(0)', 'undefined']):
                    broken_indicators += 1
            
            return broken_indicators
        except:
            return 0
    
    def _has_print_stylesheet(self, soup: BeautifulSoup) -> bool:
        """Check for print stylesheet"""
        try:
            print_css = soup.find('link', attrs={'media': re.compile(r'print', re.I)})
            return print_css is not None
        except:
            return False
    
    def _has_rss_feed(self, soup: BeautifulSoup) -> bool:
        """Check for RSS feed link"""
        try:
            rss_link = soup.find('link', type=re.compile(r'rss|atom', re.I))
            return rss_link is not None
        except:
            return False
    
    def _has_sitemap_reference(self, soup: BeautifulSoup) -> bool:
        """Check for sitemap reference"""
        try:
            sitemap_link = soup.find('a', href=re.compile(r'sitemap', re.I))
            return sitemap_link is not None
        except:
            return False
    
    def _estimate_page_depth(self, url: str) -> int:
        """Estimate page depth from URL structure"""
        try:
            path = urlparse(url).path
            return len([p for p in path.split('/') if p])
        except:
            return 0
    
    def _has_hreflang_tags(self, soup: BeautifulSoup) -> bool:
        """Check for hreflang tags"""
        try:
            hreflang = soup.find('link', hreflang=True)
            return hreflang is not None
        except:
            return False
    
    def _has_amp_version(self, soup: BeautifulSoup) -> bool:
        """Check for AMP version link"""
        try:
            amp_link = soup.find('link', rel='amphtml')
            return amp_link is not None
        except:
            return False
    
    def _has_mobile_app_links(self, soup: BeautifulSoup) -> bool:
        """Check for mobile app links"""
        try:
            app_links = soup.find_all('meta', attrs={'property': re.compile(r'al:|app:', re.I)})
            return len(app_links) > 0
        except:
            return False
    
    def _detect_performance_hints(self, soup: BeautifulSoup) -> Dict[str, bool]:
        """Detect performance optimization hints"""
        try:
            hints = {
                'preload': bool(soup.find('link', rel='preload')),
                'prefetch': bool(soup.find('link', rel='prefetch')),
                'preconnect': bool(soup.find('link', rel='preconnect')),
                'dns_prefetch': bool(soup.find('link', rel='dns-prefetch')),
                'async_scripts': bool(soup.find('script', async_=True)),
                'defer_scripts': bool(soup.find('script', defer=True))
            }
            return hints
        except:
            return {}
    
    def _detect_accessibility_features(self, soup: BeautifulSoup) -> Dict[str, bool]:
        """Detect accessibility features"""
        try:
            features = {
                'skip_links': bool(soup.find('a', href='#main') or soup.find('a', href='#content')),
                'aria_labels': bool(soup.find(attrs={'aria-label': True})),
                'aria_describedby': bool(soup.find(attrs={'aria-describedby': True})),
                'role_attributes': bool(soup.find(attrs={'role': True})),
                'alt_text_images': len(soup.find_all('img', alt=True)) > 0,
                'form_labels': len(soup.find_all('label')) > 0,
                'heading_structure': len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])) > 0
            }
            return features
        except:
            return {}
    
    def _has_seo_friendly_urls(self, soup: BeautifulSoup, base_url: str) -> bool:
        """Check if URLs are SEO-friendly"""
        try:
            # Check current URL
            parsed_url = urlparse(base_url)
            path = parsed_url.path.lower()
            
            # SEO-friendly indicators
            seo_indicators = [
                '-' in path,  # Hyphens instead of underscores
                not any(char in path for char in ['?', '&', '=']),  # No query parameters in path
                len(path.split('/')) <= 5,  # Not too deep
                not re.search(r'\d{4,}', path)  # No long numbers
            ]
            
            return sum(seo_indicators) >= 2
        except:
            return False
    
    def _calculate_accessibility_score(self, soup: BeautifulSoup) -> float:
        """Calculate accessibility score"""
        try:
            score = 0.0
            max_score = 10.0
            
            # Alt text on images
            images = soup.find_all('img')
            if images:
                images_with_alt = sum(1 for img in images if img.get('alt'))
                score += (images_with_alt / len(images)) * 2.0
            else:
                score += 2.0  # No images is fine
            
            # Form labels
            forms = soup.find_all('form')
            if forms:
                inputs = soup.find_all('input')
                labels = soup.find_all('label')
                if inputs and len(labels) >= len(inputs) * 0.8:
                    score += 2.0
            else:
                score += 2.0  # No forms is fine
            
            # Heading structure
            h1_tags = soup.find_all('h1')
            if len(h1_tags) == 1:
                score += 2.0
            elif len(h1_tags) > 1:
                score += 1.0
            
            # Language attribute
            html_tag = soup.find('html')
            if html_tag and html_tag.get('lang'):
                score += 2.0
            
            # Skip links
            skip_links = soup.find_all('a', href=re.compile(r'^#'))
            if skip_links:
                score += 1.0
            
            # ARIA attributes
            aria_elements = soup.find_all(attrs={'aria-label': True})
            aria_elements += soup.find_all(attrs={'aria-labelledby': True})
            if aria_elements:
                score += 1.0
            
            return min(score / max_score, 1.0)
            
        except Exception:
            return 0.0
    
    def _calculate_performance_score(self, features: CrawlabilityFeatures, crawl_result: Dict[str, Any]) -> float:
        """Calculate performance score"""
        try:
            score = 0.0
            max_score = 10.0
            
            # Page load time
            load_time = features.page_load_time
            if load_time < 1.0:
                score += 3.0
            elif load_time < 2.0:
                score += 2.0
            elif load_time < 3.0:
                score += 1.0
            
            # HTML size
            html_size = features.html_size
            if html_size < 50000:  # 50KB
                score += 2.0
            elif html_size < 100000:  # 100KB
                score += 1.0
            
            # Resource optimization
            if features.compression_enabled:
                score += 1.0
            
            if features.cache_headers_present:
                score += 1.0
            
            if features.lazy_loading_images > 0:
                score += 1.0
            
            # External resources
            total_external = features.external_scripts_count + features.external_stylesheets_count
            if total_external < 5:
                score += 1.0
            elif total_external < 10:
                score += 0.5
            
            # Inline resources (penalty)
            if features.inline_css_count + features.inline_js_count < 3:
                score += 1.0
            
            return min(score / max_score, 1.0)
            
        except Exception:
            return 0.0
    
    def _calculate_seo_score(self, features: CrawlabilityFeatures, soup: BeautifulSoup) -> float:
        """Calculate SEO score"""
        try:
            score = 0.0
            max_score = 10.0
            
            # Title tag
            if features.title_tag_present:
                if 30 <= features.title_length <= 60:
                    score += 2.0
                elif features.title_length > 0:
                    score += 1.0
            
            # Meta description
            if features.meta_description_present:
                if 120 <= features.meta_description_length <= 160:
                    score += 2.0
                elif features.meta_description_length > 0:
                    score += 1.0
            
            # H1 tags
            if features.h1_count == 1:
                score += 1.0
            elif features.h1_count > 1:
                score += 0.5
            
            # Canonical tag
            if features.canonical_tag_present:
                score += 1.0
            
            # Structured data
            if features.structured_data_present:
                score += 1.0
            
            # Open Graph
            if features.open_graph_present:
                score += 1.0
            
            # Mobile friendly
            if features.mobile_friendly:
                score += 1.0
            
            # HTTPS
            if features.https_enabled:
                score += 1.0
            
            return min(score / max_score, 1.0)
            
        except Exception:
            return 0.0
