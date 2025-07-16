"""
Advanced web crawler with multiple fallback strategies
"""

import asyncio
import aiohttp
import logging
import time
import ssl
import certifi
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class WebCrawler:
    """
    Production-grade web crawler with multiple fallback strategies
    """
    
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=30, connect=15)
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # SSL context for secure connections
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        # User agents for different strategies
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0"
        ]
    
    async def crawl_website(self, url: str) -> Dict[str, Any]:
        """
        Crawl website with multiple fallback strategies
        """
        logger.info(f"🕷️ Starting crawl for: {url}")
        start_time = time.time()
        
        # Strategy 1: Standard HTTPS request
        result = await self._try_standard_crawl(url)
        if result['success']:
            result['crawl_time'] = time.time() - start_time
            result['strategy'] = 'standard'
            return result
        
        # Strategy 2: HTTP fallback
        if url.startswith('https://'):
            http_url = url.replace('https://', 'http://')
            result = await self._try_standard_crawl(http_url)
            if result['success']:
                result['crawl_time'] = time.time() - start_time
                result['strategy'] = 'http_fallback'
                return result
        
        # Strategy 3: Different user agents
        for i, user_agent in enumerate(self.user_agents):
            result = await self._try_with_user_agent(url, user_agent)
            if result['success']:
                result['crawl_time'] = time.time() - start_time
                result['strategy'] = f'user_agent_{i}'
                return result
        
        # Strategy 4: Minimal headers
        result = await self._try_minimal_request(url)
        if result['success']:
            result['crawl_time'] = time.time() - start_time
            result['strategy'] = 'minimal'
            return result
        
        # Strategy 5: HEAD request to check accessibility
        result = await self._try_head_request(url)
        if result['success']:
            result['crawl_time'] = time.time() - start_time
            result['strategy'] = 'head_only'
            return result
        
        # All strategies failed
        logger.error(f"❌ All crawl strategies failed for: {url}")
        return {
            'success': False,
            'error': 'Website is not accessible or blocks crawlers',
            'crawl_time': time.time() - start_time,
            'strategy': 'failed'
        }
    
    async def _try_standard_crawl(self, url: str) -> Dict[str, Any]:
        """Standard crawl with full headers"""
        try:
            headers = {
                'User-Agent': self.user_agents[0],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            }
            
            async with aiohttp.ClientSession(
                timeout=self.timeout,
                headers=headers,
                connector=aiohttp.TCPConnector(ssl=self.ssl_context)
            ) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        return await self._parse_content(url, content, response)
                    else:
                        return {
                            'success': False,
                            'error': f'HTTP {response.status}',
                            'status_code': response.status
                        }
                        
        except Exception as e:
            logger.warning(f"⚠️ Standard crawl failed for {url}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _try_with_user_agent(self, url: str, user_agent: str) -> Dict[str, Any]:
        """Try with specific user agent"""
        try:
            headers = {'User-Agent': user_agent}
            
            async with aiohttp.ClientSession(
                timeout=self.timeout,
                headers=headers,
                connector=aiohttp.TCPConnector(ssl=self.ssl_context)
            ) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        return await self._parse_content(url, content, response)
                    else:
                        return {'success': False, 'error': f'HTTP {response.status}'}
                        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _try_minimal_request(self, url: str) -> Dict[str, Any]:
        """Try with minimal headers"""
        try:
            async with aiohttp.ClientSession(
                timeout=self.timeout,
                connector=aiohttp.TCPConnector(ssl=self.ssl_context)
            ) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        return await self._parse_content(url, content, response)
                    else:
                        return {'success': False, 'error': f'HTTP {response.status}'}
                        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _try_head_request(self, url: str) -> Dict[str, Any]:
        """Try HEAD request to check if site is accessible"""
        try:
            async with aiohttp.ClientSession(
                timeout=self.timeout,
                connector=aiohttp.TCPConnector(ssl=self.ssl_context)
            ) as session:
                async with session.head(url) as response:
                    if response.status == 200:
                        # Site is accessible, return minimal data
                        return {
                            'success': True,
                            'html': '',
                            'status_code': response.status,
                            'headers': dict(response.headers),
                            'url': str(response.url),
                            'title': '',
                            'meta_description': '',
                            'h1_tags': [],
                            'links': [],
                            'images': [],
                            'scripts': [],
                            'stylesheets': []
                        }
                    else:
                        return {'success': False, 'error': f'HTTP {response.status}'}
                        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _parse_content(self, url: str, content: str, response) -> Dict[str, Any]:
        """Parse HTML content and extract data"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract basic information
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ''
            
            # Meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            meta_description = meta_desc.get('content', '').strip() if meta_desc else ''
            
            # H1 tags
            h1_tags = [h1.get_text().strip() for h1 in soup.find_all('h1')]
            
            # Links
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                absolute_url = urljoin(url, href)
                links.append({
                    'url': absolute_url,
                    'text': link.get_text().strip(),
                    'internal': self._is_internal_link(url, absolute_url)
                })
            
            # Images
            images = []
            for img in soup.find_all('img'):
                src = img.get('src', '')
                if src:
                    absolute_url = urljoin(url, src)
                    images.append({
                        'src': absolute_url,
                        'alt': img.get('alt', ''),
                        'title': img.get('title', '')
                    })
            
            # Scripts
            scripts = []
            for script in soup.find_all('script'):
                src = script.get('src')
                if src:
                    absolute_url = urljoin(url, src)
                    scripts.append(absolute_url)
            
            # Stylesheets
            stylesheets = []
            for link in soup.find_all('link', rel='stylesheet'):
                href = link.get('href')
                if href:
                    absolute_url = urljoin(url, href)
                    stylesheets.append(absolute_url)
            
            return {
                'success': True,
                'html': content,
                'status_code': response.status,
                'headers': dict(response.headers),
                'url': str(response.url),
                'title': title_text,
                'meta_description': meta_description,
                'h1_tags': h1_tags,
                'links': links,
                'images': images,
                'scripts': scripts,
                'stylesheets': stylesheets,
                'word_count': len(content.split()),
                'html_size': len(content.encode('utf-8'))
            }
            
        except Exception as e:
            logger.error(f"❌ Content parsing failed: {str(e)}")
            return {'success': False, 'error': f'Content parsing failed: {str(e)}'}
    
    def _is_internal_link(self, base_url: str, link_url: str) -> bool:
        """Check if link is internal"""
        try:
            base_domain = urlparse(base_url).netloc
            link_domain = urlparse(link_url).netloc
            return base_domain == link_domain
        except:
            return False
    
    async def check_robots_txt(self, url: str) -> Dict[str, Any]:
        """Check robots.txt file"""
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(robots_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Check if robots.txt blocks crawling
                        blocks_crawling = self._check_robots_blocking(content)
                        
                        return {
                            'exists': True,
                            'content': content,
                            'blocks_crawling': blocks_crawling
                        }
                    else:
                        return {'exists': False, 'blocks_crawling': False}
                        
        except Exception as e:
            logger.warning(f"⚠️ Robots.txt check failed: {str(e)}")
            return {'exists': False, 'blocks_crawling': False}
    
    def _check_robots_blocking(self, robots_content: str) -> bool:
        """Check if robots.txt blocks crawling"""
        try:
            lines = robots_content.lower().split('\n')
            current_user_agent = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('user-agent:'):
                    current_user_agent = line.split(':', 1)[1].strip()
                elif line.startswith('disallow:') and current_user_agent in ['*', 'googlebot']:
                    disallow_path = line.split(':', 1)[1].strip()
                    if disallow_path == '/':
                        return True
            
            return False
            
        except Exception:
            return False
    
    async def check_sitemap(self, url: str) -> Dict[str, Any]:
        """Check for XML sitemap"""
        try:
            parsed_url = urlparse(url)
            sitemap_urls = [
                f"{parsed_url.scheme}://{parsed_url.netloc}/sitemap.xml",
                f"{parsed_url.scheme}://{parsed_url.netloc}/sitemap_index.xml",
                f"{parsed_url.scheme}://{parsed_url.netloc}/sitemaps.xml"
            ]
            
            for sitemap_url in sitemap_urls:
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    try:
                        async with session.get(sitemap_url) as response:
                            if response.status == 200:
                                content = await response.text()
                                return {
                                    'exists': True,
                                    'url': sitemap_url,
                                    'content': content[:1000]  # First 1000 chars
                                }
                    except:
                        continue
            
            return {'exists': False}
            
        except Exception as e:
            logger.warning(f"⚠️ Sitemap check failed: {str(e)}")
            return {'exists': False}
