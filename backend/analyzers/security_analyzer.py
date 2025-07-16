import aiohttp
import ssl
import socket
from urllib.parse import urlparse
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

class SecurityAnalyzer:
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    async def analyze(self, url: str) -> ModuleResult:
        try:
            security_data = await self._analyze_security(url)
            score = self._calculate_security_score(security_data)
            recommendations = self._generate_recommendations(security_data)
            
            return ModuleResult(
                name="Security",
                score=score,
                description="HTTPS and security implementation",
                explanation=self._generate_explanation(score, security_data),
                recommendations=recommendations
            )
        
        except Exception as e:
            return ModuleResult(
                name="Security",
                score=0,
                description="Security analysis failed",
                explanation=f"Unable to analyze security: {str(e)}",
                recommendations=[Recommendation(
                    priority="High",
                    title="Security Analysis Failed",
                    message="Could not analyze security headers and HTTPS configuration.",
                    doc_link="https://developers.google.com/web/fundamentals/security"
                )]
            )
    
    async def _analyze_security(self, url: str) -> Dict:
        parsed_url = urlparse(url)
        
        # Check HTTPS
        https_enabled = parsed_url.scheme == 'https'
        
        # Get security headers
        headers_data = await self._check_security_headers(url)
        
        # Check SSL certificate
        ssl_data = await self._check_ssl_certificate(parsed_url.hostname, parsed_url.port or (443 if https_enabled else 80))
        
        return {
            'https': https_enabled,
            'headers': headers_data,
            'ssl': ssl_data,
            'url_scheme': parsed_url.scheme
        }
    
    async def _check_security_headers(self, url: str) -> Dict:
        security_headers = {
            'strict-transport-security': False,
            'content-security-policy': False,
            'x-frame-options': False,
            'x-content-type-options': False,
            'referrer-policy': False,
            'permissions-policy': False
        }
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; NeuromBot/1.0)'}) as response:
                    headers = response.headers
                    
                    for header in security_headers.keys():
                        security_headers[header] = header in headers or header.replace('-', '_') in headers
                    
                    return {
                        'headers': security_headers,
                        'headers_present': sum(security_headers.values()),
                        'total_headers': len(security_headers)
                    }
        
        except Exception:
            return {
                'headers': security_headers,
                'headers_present': 0,
                'total_headers': len(security_headers)
            }
    
    async def _check_ssl_certificate(self, hostname: str, port: int) -> Dict:
        if not hostname:
            return {'valid': False, 'error': 'No hostname'}
        
        try:
            # Create SSL context
            context = ssl.create_default_context()
            
            # Connect and get certificate info
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    return {
                        'valid': True,
                        'subject': dict(x[0] for x in cert.get('subject', [])),
                        'issuer': dict(x[0] for x in cert.get('issuer', [])),
                        'version': cert.get('version'),
                        'not_after': cert.get('notAfter'),
                        'not_before': cert.get('notBefore')
                    }
        
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def _calculate_security_score(self, data: Dict) -> int:
        score = 0
        
        # HTTPS (40 points)
        if data['https']:
            score += 40
        
        # SSL Certificate (20 points)
        if data['ssl'].get('valid', False):
            score += 20
        
        # Security Headers (40 points total)
        headers_data = data['headers']
        headers_score = (headers_data['headers_present'] / headers_data['total_headers']) * 40
        score += int(headers_score)
        
        return min(score, 100)
    
    def _generate_explanation(self, score: int, data: Dict) -> str:
        if score >= 90:
            return "Excellent security implementation with HTTPS, valid SSL certificate, and comprehensive security headers."
        elif score >= 70:
            return "Good security foundation with HTTPS enabled, but some security headers could be improved."
        elif score >= 40:
            return "Basic security with HTTPS, but missing important security headers and configurations."
        else:
            return "Poor security implementation. HTTPS and security headers need immediate attention."
    
    def _generate_recommendations(self, data: Dict) -> List[Recommendation]:
        recommendations = []
        
        # HTTPS recommendations
        if not data['https']:
            recommendations.append(Recommendation(
                priority="High",
                title="Enable HTTPS",
                message="Secure your website with SSL/TLS encryption for all pages.",
                doc_link="https://developers.google.com/web/fundamentals/security/encrypt-in-transit/why-https"
            ))
        
        # SSL Certificate recommendations
        if not data['ssl'].get('valid', False):
            recommendations.append(Recommendation(
                priority="High",
                title="Fix SSL Certificate",
                message="Ensure your SSL certificate is valid and properly configured.",
                doc_link="https://developers.google.com/web/fundamentals/security/encrypt-in-transit/enable-https"
            ))
        
        # Security Headers recommendations
        headers = data['headers']['headers']
        
        if not headers.get('strict-transport-security', False):
            recommendations.append(Recommendation(
                priority="High",
                title="Add HSTS Header",
                message="Implement HTTP Strict Transport Security to prevent protocol downgrade attacks.",
                code_snippet="Strict-Transport-Security: max-age=31536000; includeSubDomains",
                doc_link="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security"
            ))
        
        if not headers.get('content-security-policy', False):
            recommendations.append(Recommendation(
                priority="Medium",
                title="Add Content Security Policy",
                message="Implement CSP to prevent XSS attacks and other code injection vulnerabilities.",
                code_snippet="Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'",
                doc_link="https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP"
            ))
        
        if not headers.get('x-frame-options', False):
            recommendations.append(Recommendation(
                priority="Medium",
                title="Add X-Frame-Options Header",
                message="Prevent clickjacking attacks by controlling iframe embedding.",
                code_snippet="X-Frame-Options: DENY",
                doc_link="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options"
            ))
        
        if not headers.get('x-content-type-options', False):
            recommendations.append(Recommendation(
                priority="Low",
                title="Add X-Content-Type-Options Header",
                message="Prevent MIME type sniffing vulnerabilities.",
                code_snippet="X-Content-Type-Options: nosniff",
                doc_link="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Content-Type-Options"
            ))
        
        return recommendations
