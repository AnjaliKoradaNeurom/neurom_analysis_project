"""
URL validation and verification system with Google Search integration
"""

import asyncio
import aiohttp
import logging
import re
import os
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse, urljoin
from datetime import datetime, timedelta
import json
import ssl
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from models.schemas import ValidationResult, GoogleSearchResult, URLVerificationResult
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class URLValidator:
    """
    Advanced URL validator with Google Search integration for real website verification
    """
    
    def __init__(self):
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.google_search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        self.lighthouse_path = os.getenv('LIGHTHOUSE_PATH')
        
        # Initialize Google Search API
        self.search_service = None
        if self.google_api_key and self.google_search_engine_id:
            try:
                self.search_service = build('customsearch', 'v1', developerKey=self.google_api_key)
                logger.info("✅ Google Search API initialized")
            except Exception as e:
                logger.warning(f"⚠️ Google Search API initialization failed: {e}")
        
        # Common fake/suspicious URL patterns
        self.fake_url_patterns = [
            r'bit\.ly',
            r'tinyurl\.com',
            r'goo\.gl',
            r't\.co',
            r'ow\.ly',
            r'is\.gd',
            r'buff\.ly',
            r'adf\.ly',
            r'short\.link',
            r'tiny\.cc',
            r'rb\.gy',
            r'cutt\.ly',
            r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}',  # IP addresses
            r'localhost',
            r'127\.0\.0\.1',
            r'192\.168\.',
            r'10\.',
            r'172\.(1[6-9]|2[0-9]|3[0-1])\.',
            r'[a-z0-9]{10,}\.com',  # Random character domains
            r'[a-z0-9]{10,}\.net',
            r'[a-z0-9]{10,}\.org',
            r'test\.',
            r'example\.',
            r'sample\.',
            r'demo\.',
            r'fake\.',
            r'phishing\.',
            r'malware\.',
            r'spam\.'
        ]
        
        # Trusted domain patterns
        self.trusted_patterns = [
            r'amazon\.(com|in|co\.uk|de|fr|it|es|ca|com\.au|com\.br|com\.mx)',
            r'google\.(com|co\.in|co\.uk|de|fr|it|es|ca|com\.au|com\.br|com\.mx)',
            r'microsoft\.(com|co\.in|co\.uk|de|fr|it|es|ca|com\.au|com\.br|com\.mx)',
            r'apple\.(com|co\.in|co\.uk|de|fr|it|es|ca|com\.au|com\.br|com\.mx)',
            r'facebook\.(com|co\.in|co\.uk|de|fr|it|es|ca|com\.au|com\.br|com\.mx)',
            r'twitter\.(com|co\.in|co\.uk|de|fr|it|es|ca|com\.au|com\.br|com\.mx)',
            r'linkedin\.(com|co\.in|co\.uk|de|fr|it|es|ca|com\.au|com\.br|com\.mx)',
            r'youtube\.(com|co\.in|co\.uk|de|fr|it|es|ca|com\.au|com\.br|com\.mx)',
            r'instagram\.(com|co\.in|co\.uk|de|fr|it|es|ca|com\.au|com\.br|com\.mx)',
            r'github\.(com|io)',
            r'stackoverflow\.com',
            r'wikipedia\.org',
            r'reddit\.com',
            r'medium\.com',
            r'wordpress\.(com|org)',
            r'shopify\.com',
            r'wix\.com',
            r'squarespace\.com'
        ]
    
    async def validate_url(self, url: str) -> ValidationResult:
        """
        Comprehensive URL validation with real website verification
        """
        try:
            logger.info(f"🔍 Validating URL: {url}")
            
            # Basic URL format validation
            normalized_url = self._normalize_url(url)
            if not normalized_url:
                return ValidationResult(
                    is_valid=False,
                    error="Invalid URL format"
                )
            
            # Check for fake/suspicious patterns
            if self._is_suspicious_url(normalized_url):
                logger.warning(f"⚠️ Suspicious URL detected: {normalized_url}")
                return ValidationResult(
                    is_valid=False,
                    error="Suspicious or potentially fake URL detected"
                )
            
            # Check if URL is accessible
            accessibility_result = await self._check_url_accessibility(normalized_url)
            
            if not accessibility_result['accessible']:
                return ValidationResult(
                    is_valid=False,
                    normalized_url=normalized_url,
                    error=accessibility_result['error'],
                    status_code=accessibility_result.get('status_code', 0)
                )
            
            # Verify with Google Search (if available)
            verification_result = await self._verify_with_google_search(normalized_url)
            
            # Final validation decision
            is_valid = (
                accessibility_result['accessible'] and
                (verification_result.is_real or self._is_trusted_domain(normalized_url))
            )
            
            if not is_valid and not verification_result.is_real:
                return ValidationResult(
                    is_valid=False,
                    normalized_url=normalized_url,
                    error="Website not found in search results and not recognized as legitimate",
                    status_code=accessibility_result.get('status_code', 200)
                )
            
            logger.info(f"✅ URL validation successful: {normalized_url}")
            return ValidationResult(
                is_valid=True,
                normalized_url=normalized_url,
                status_code=accessibility_result.get('status_code', 200),
                redirect_chain=accessibility_result.get('redirect_chain', [])
            )
            
        except Exception as e:
            logger.error(f"❌ URL validation failed: {str(e)}")
            return ValidationResult(
                is_valid=False,
                error=f"Validation failed: {str(e)}"
            )
    
    def _normalize_url(self, url: str) -> Optional[str]:
        """Normalize URL format"""
        try:
            url = url.strip()
            
            # Remove common tracking parameters
            parsed = urlparse(url)
            
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Parse again after adding protocol
            parsed = urlparse(url)
            
            # Basic validation
            if not parsed.netloc:
                return None
            
            # Remove fragment
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                # Keep essential query parameters, remove tracking
                clean_url += f"?{parsed.query}"
            
            return clean_url
            
        except Exception:
            return None
    
    def _is_suspicious_url(self, url: str) -> bool:
        """Check if URL matches suspicious patterns"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Check against fake URL patterns
            for pattern in self.fake_url_patterns:
                if re.search(pattern, domain, re.IGNORECASE):
                    return True
            
            # Check for suspicious characteristics
            suspicious_indicators = [
                len(domain) > 50,  # Very long domain
                domain.count('-') > 3,  # Too many hyphens
                domain.count('.') > 3,  # Too many subdomains
                re.search(r'\d{4,}', domain),  # Long numbers in domain
                re.search(r'[^a-zA-Z0-9.-]', domain),  # Special characters
                domain.startswith('www.') and len(domain.replace('www.', '')) < 4,  # Very short domain
            ]
            
            return sum(suspicious_indicators) >= 2
            
        except Exception:
            return False
    
    def _is_trusted_domain(self, url: str) -> bool:
        """Check if URL is from a trusted domain"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            for pattern in self.trusted_patterns:
                if re.search(pattern, domain, re.IGNORECASE):
                    return True
            
            return False
            
        except Exception:
            return False
    
    async def _check_url_accessibility(self, url: str) -> Dict[str, Any]:
        """Check if URL is accessible"""
        try:
            timeout = aiohttp.ClientTimeout(total=15, connect=10)
            redirect_chain = []
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                try:
                    async with session.get(url, allow_redirects=True) as response:
                        # Track redirect chain
                        for redirect in response.history:
                            redirect_chain.append(str(redirect.url))
                        redirect_chain.append(str(response.url))
                        
                        if response.status == 200:
                            return {
                                'accessible': True,
                                'status_code': response.status,
                                'redirect_chain': redirect_chain,
                                'final_url': str(response.url)
                            }
                        else:
                            return {
                                'accessible': False,
                                'status_code': response.status,
                                'error': f"HTTP {response.status}",
                                'redirect_chain': redirect_chain
                            }
                            
                except aiohttp.ClientError as e:
                    return {
                        'accessible': False,
                        'error': f"Connection failed: {str(e)}",
                        'status_code': 0
                    }
                    
        except Exception as e:
            return {
                'accessible': False,
                'error': f"Accessibility check failed: {str(e)}",
                'status_code': 0
            }
    
    async def _verify_with_google_search(self, url: str) -> URLVerificationResult:
        """Verify URL using Google Search API"""
        try:
            if not self.search_service:
                logger.warning("⚠️ Google Search API not available")
                return URLVerificationResult(
                    is_real=True,  # Assume real if can't verify
                    is_indexed=False,
                    verification_method="no_search_api",
                    confidence=0.5
                )
            
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # Search for the domain
            search_queries = [
                f'site:{domain}',
                f'"{domain}"',
                domain.replace('www.', '').replace('.com', '').replace('.org', '').replace('.net', '')
            ]
            
            all_results = []
            is_indexed = False
            
            for query in search_queries:
                try:
                    result = self.search_service.cse().list(
                        q=query,
                        cx=self.google_search_engine_id,
                        num=10
                    ).execute()
                    
                    if 'items' in result:
                        for item in result['items']:
                            search_result = GoogleSearchResult(
                                title=item.get('title', ''),
                                link=item.get('link', ''),
                                snippet=item.get('snippet', ''),
                                position=len(all_results) + 1
                            )
                            all_results.append(search_result)
                            
                            # Check if exact domain is indexed
                            if domain.lower() in item.get('link', '').lower():
                                is_indexed = True
                    
                    # Small delay between requests
                    await asyncio.sleep(0.1)
                    
                except HttpError as e:
                    logger.warning(f"⚠️ Google Search API error: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"⚠️ Search query failed: {e}")
                    continue
            
            # Determine if website is real based on search results
            is_real = len(all_results) > 0 or is_indexed or self._is_trusted_domain(url)
            
            # Calculate confidence
            confidence = min(1.0, len(all_results) / 10.0)
            if is_indexed:
                confidence = max(confidence, 0.8)
            if self._is_trusted_domain(url):
                confidence = max(confidence, 0.9)
            
            logger.info(f"🔍 Google verification: {domain} - Real: {is_real}, Indexed: {is_indexed}, Results: {len(all_results)}")
            
            return URLVerificationResult(
                is_real=is_real,
                is_indexed=is_indexed,
                search_results=all_results[:5],  # Top 5 results
                verification_method="google_search",
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"❌ Google verification failed: {str(e)}")
            return URLVerificationResult(
                is_real=True,  # Assume real if verification fails
                is_indexed=False,
                verification_method="verification_failed",
                confidence=0.5
            )
    
    async def batch_validate_urls(self, urls: List[str]) -> List[ValidationResult]:
        """Validate multiple URLs concurrently"""
        try:
            logger.info(f"🔄 Batch validating {len(urls)} URLs")
            
            # Limit concurrent requests
            semaphore = asyncio.Semaphore(5)
            
            async def validate_with_semaphore(url):
                async with semaphore:
                    return await self.validate_url(url)
            
            tasks = [validate_with_semaphore(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            validated_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    validated_results.append(ValidationResult(
                        is_valid=False,
                        error=f"Validation failed: {str(result)}"
                    ))
                else:
                    validated_results.append(result)
            
            logger.info(f"✅ Batch validation completed: {len(validated_results)} results")
            return validated_results
            
        except Exception as e:
            logger.error(f"❌ Batch validation failed: {str(e)}")
            return [ValidationResult(is_valid=False, error=str(e)) for _ in urls]
