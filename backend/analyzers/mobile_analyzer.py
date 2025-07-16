import aiohttp
from bs4 import BeautifulSoup
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

class MobileAnalyzer:
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    async def analyze(self, url: str) -> ModuleResult:
        try:
            mobile_data = await self._analyze_mobile_friendliness(url)
            score = self._calculate_mobile_score(mobile_data)
            recommendations = self._generate_recommendations(mobile_data)
            
            return ModuleResult(
                name="Mobile Friendliness",
                score=score,
                description="Mobile device compatibility and usability",
                explanation=self._generate_explanation(score, mobile_data),
                recommendations=recommendations
            )
        
        except Exception as e:
            return ModuleResult(
                name="Mobile Friendliness",
                score=0,
                description="Mobile analysis failed",
                explanation=f"Unable to analyze mobile friendliness: {str(e)}",
                recommendations=[Recommendation(
                    priority="High",
                    title="Mobile Analysis Failed",
                    message="Could not analyze mobile compatibility and responsive design.",
                    doc_link="https://developers.google.com/web/fundamentals/design-and-ux/responsive"
                )]
            )
    
    async def _analyze_mobile_friendliness(self, url: str) -> Dict:
        # Analyze with mobile user agent
        mobile_headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1'
        }
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(url, headers=mobile_headers) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                return {
                    'viewport': self._check_viewport(soup),
                    'responsive_images': self._check_responsive_images(soup),
                    'touch_targets': self._check_touch_targets(soup),
                    'font_sizes': self._check_font_sizes(soup),
                    'content_width': self._check_content_width(soup)
                }
    
    def _check_viewport(self, soup: BeautifulSoup) -> Dict:
        viewport_tag = soup.find('meta', attrs={'name': 'viewport'})
        
        if not viewport_tag:
            return {'exists': False, 'content': ''}
        
        content = viewport_tag.get('content', '')
        
        # Check for responsive viewport settings
        has_width_device = 'width=device-width' in content
        has_initial_scale = 'initial-scale=1' in content
        
        return {
            'exists': True,
            'content': content,
            'responsive': has_width_device and has_initial_scale
        }
    
    def _check_responsive_images(self, soup: BeautifulSoup) -> Dict:
        images = soup.find_all('img')
        total_images = len(images)
        
        if total_images == 0:
            return {'total': 0, 'responsive': 0, 'percentage': 100}
        
        responsive_images = 0
        for img in images:
            # Check for responsive image attributes
            if (img.get('srcset') or 
                img.get('sizes') or 
                'responsive' in img.get('class', []) or
                img.get('style', '').find('max-width') != -1):
                responsive_images += 1
        
        return {
            'total': total_images,
            'responsive': responsive_images,
            'percentage': (responsive_images / total_images) * 100
        }
    
    def _check_touch_targets(self, soup: BeautifulSoup) -> Dict:
        # Check for common interactive elements
        interactive_elements = soup.find_all(['button', 'a', 'input[type="button"]', 'input[type="submit"]'])
        
        # This is a simplified check - in a real implementation, you'd analyze CSS
        # to determine actual touch target sizes
        total_elements = len(interactive_elements)
        
        # Assume elements with proper classes or inline styles are properly sized
        properly_sized = 0
        for element in interactive_elements:
            classes = element.get('class', [])
            style = element.get('style', '')
            
            # Simple heuristic for touch-friendly elements
            if (any('btn' in cls.lower() for cls in classes) or
                'padding' in style or
                'min-height' in style or
                'min-width' in style):
                properly_sized += 1
        
        return {
            'total': total_elements,
            'properly_sized': properly_sized,
            'percentage': (properly_sized / total_elements * 100) if total_elements > 0 else 100
        }
    
    def _check_font_sizes(self, soup: BeautifulSoup) -> Dict:
        # Check for font-size declarations in style tags
        style_tags = soup.find_all('style')
        
        small_fonts_found = False
        for style_tag in style_tags:
            content = style_tag.get_text()
            # Look for font sizes smaller than 16px (not mobile-friendly)
            if any(f'font-size:{size}px' in content for size in range(1, 16)):
                small_fonts_found = True
                break
        
        return {
            'has_small_fonts': small_fonts_found,
            'mobile_friendly': not small_fonts_found
        }
    
    def _check_content_width(self, soup: BeautifulSoup) -> Dict:
        # Check for fixed-width content that might not be mobile-friendly
        style_tags = soup.find_all('style')
        
        fixed_width_found = False
        for style_tag in style_tags:
            content = style_tag.get_text()
            # Look for fixed widths greater than mobile screen sizes
            if 'width:' in content and any(f'{width}px' in content for width in range(600, 2000)):
                fixed_width_found = True
                break
        
        return {
            'has_fixed_width': fixed_width_found,
            'mobile_friendly': not fixed_width_found
        }
    
    def _calculate_mobile_score(self, data: Dict) -> int:
        score = 0
        
        # Viewport (30 points)
        if data['viewport']['exists']:
            score += 15
            if data['viewport']['responsive']:
                score += 15
        
        # Responsive images (25 points)
        img_percentage = data['responsive_images']['percentage']
        score += int((img_percentage / 100) * 25)
        
        # Touch targets (25 points)
        touch_percentage = data['touch_targets']['percentage']
        score += int((touch_percentage / 100) * 25)
        
        # Font sizes (10 points)
        if data['font_sizes']['mobile_friendly']:
            score += 10
        
        # Content width (10 points)
        if data['content_width']['mobile_friendly']:
            score += 10
        
        return min(score, 100)
    
    def _generate_explanation(self, score: int, data: Dict) -> str:
        if score >= 90:
            return "Excellent mobile experience with responsive design, proper viewport, and touch-friendly interface."
        elif score >= 70:
            return "Good mobile compatibility with minor improvements needed for optimal user experience."
        else:
            return "Mobile experience needs significant improvement. Issues with responsive design, viewport, or touch targets."
    
    def _generate_recommendations(self, data: Dict) -> List[Recommendation]:
        recommendations = []
        
        # Viewport recommendations
        if not data['viewport']['exists']:
            recommendations.append(Recommendation(
                priority="High",
                title="Add Viewport Meta Tag",
                message="Add a viewport meta tag to ensure proper mobile rendering.",
                code_snippet='<meta name="viewport" content="width=device-width, initial-scale=1.0">',
                doc_link="https://developers.google.com/web/fundamentals/design-and-ux/responsive"
            ))
        elif not data['viewport']['responsive']:
            recommendations.append(Recommendation(
                priority="High",
                title="Fix Viewport Configuration",
                message="Update viewport meta tag for proper responsive behavior.",
                code_snippet='<meta name="viewport" content="width=device-width, initial-scale=1.0">',
                doc_link="https://developers.google.com/web/fundamentals/design-and-ux/responsive"
            ))
        
        # Responsive images
        if data['responsive_images']['percentage'] < 80:
            recommendations.append(Recommendation(
                priority="Medium",
                title="Implement Responsive Images",
                message="Use responsive image techniques for better mobile performance.",
                code_snippet='<img src="image.jpg" srcset="image-320w.jpg 320w, image-640w.jpg 640w" sizes="(max-width: 320px) 280px, 640px" alt="Description">',
                doc_link="https://developer.mozilla.org/en-US/docs/Learn/HTML/Multimedia_and_embedding/Responsive_images"
            ))
        
        # Touch targets
        if data['touch_targets']['percentage'] < 80:
            recommendations.append(Recommendation(
                priority="Medium",
                title="Optimize Touch Targets",
                message="Ensure buttons and links are large enough and properly spaced for touch interaction.",
                code_snippet='.touch-target { min-height: 44px; min-width: 44px; padding: 12px; }',
                doc_link="https://web.dev/accessible-tap-targets/"
            ))
        
        # Font sizes
        if not data['font_sizes']['mobile_friendly']:
            recommendations.append(Recommendation(
                priority="Medium",
                title="Increase Font Sizes",
                message="Use font sizes of at least 16px for better mobile readability.",
                code_snippet='body { font-size: 16px; line-height: 1.5; }',
                doc_link="https://developers.google.com/web/fundamentals/design-and-ux/responsive/typography"
            ))
        
        # Content width
        if not data['content_width']['mobile_friendly']:
            recommendations.append(Recommendation(
                priority="Low",
                title="Avoid Fixed Width Content",
                message="Use flexible layouts instead of fixed widths for better mobile compatibility.",
                code_snippet='.container { max-width: 100%; width: auto; }',
                doc_link="https://developers.google.com/web/fundamentals/design-and-ux/responsive"
            ))
        
        return recommendations
