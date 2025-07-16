import asyncio
import aiohttp
import logging
from urllib.parse import urlparse, urljoin
from typing import Optional
from models.schemas import ValidationResult

logger = logging.getLogger(__name__)

class URLValidator:
    """Validates and normalizes URLs"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = None
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'Neurom-WebAudit-Bot/2.0 (+https://neurom.ai)'
                }
            )
        return self.session
    
    async def validate_url(self, url: str) -> ValidationResult:
        """Validate and normalize a URL"""
        try:
            # Basic URL parsing
            parsed = urlparse(url)
            
            # Add scheme if missing
            if not parsed.scheme:
                url = f"https://{url}"
                parsed = urlparse(url)
            
            # Validate scheme
            if parsed.scheme not in ['http', 'https']:
                return ValidationResult(
                    is_valid=False,
                    error="Invalid URL scheme. Only HTTP and HTTPS are supported."
                )
            
            # Validate domain
            if not parsed.netloc:
                return ValidationResult(
                    is_valid=False,
                    error="Invalid URL: No domain specified."
                )
            
            # Normalize URL
            normalized_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                normalized_url += f"?{parsed.query}"
            
            # Test connectivity
            session = await self._get_session()
            try:
                async with session.head(normalized_url, allow_redirects=True) as response:
                    final_url = str(response.url)
                    status_code = response.status
                    
                    if status_code >= 400:
                        return ValidationResult(
                            is_valid=False,
                            error=f"URL returned status code {status_code}",
                            status_code=status_code
                        )
                    
                    return ValidationResult(
                        is_valid=True,
                        normalized_url=final_url,
                        redirect_url=final_url if final_url != normalized_url else None,
                        status_code=status_code
                    )
                    
            except aiohttp.ClientError as e:
                return ValidationResult(
                    is_valid=False,
                    error=f"Connection failed: {str(e)}"
                )
            
        except Exception as e:
            logger.error(f"URL validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                error=f"Validation error: {str(e)}"
            )
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def __del__(self):
        """Cleanup on deletion"""
        if hasattr(self, 'session') and self.session and not self.session.closed:
            try:
                asyncio.create_task(self.session.close())
            except:
                pass
