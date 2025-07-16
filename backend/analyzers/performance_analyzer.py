import asyncio
import subprocess
import json
import tempfile
import os
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

class PerformanceAnalyzer:
    def __init__(self):
        self.lighthouse_available = self._check_lighthouse()
    
    def _check_lighthouse(self) -> bool:
        try:
            subprocess.run(['lighthouse', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    async def analyze(self, url: str) -> ModuleResult:
        if not self.lighthouse_available:
            return self._fallback_analysis(url)
        
        try:
            # Run Lighthouse analysis
            lighthouse_data = await self._run_lighthouse(url)
            score = self._calculate_performance_score(lighthouse_data)
            recommendations = self._generate_recommendations(lighthouse_data)
            
            return ModuleResult(
                name="Performance",
                score=score,
                description="Website speed and performance metrics",
                explanation=self._generate_explanation(score, lighthouse_data),
                recommendations=recommendations
            )
        
        except Exception as e:
            return self._fallback_analysis(url, str(e))
    
    async def _run_lighthouse(self, url: str) -> Dict:
        # Create temporary file for Lighthouse output
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # Run Lighthouse command
            cmd = [
                'lighthouse',
                url,
                '--output=json',
                f'--output-path={tmp_path}',
                '--chrome-flags=--headless --no-sandbox --disable-gpu',
                '--quiet'
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)
            
            if process.returncode != 0:
                raise Exception(f"Lighthouse failed: {stderr.decode()}")
            
            # Read the results
            with open(tmp_path, 'r') as f:
                lighthouse_data = json.load(f)
            
            return lighthouse_data
        
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def _calculate_performance_score(self, lighthouse_data: Dict) -> int:
        try:
            # Get performance score from Lighthouse (0-1 scale, convert to 0-100)
            performance_score = lighthouse_data.get('categories', {}).get('performance', {}).get('score', 0)
            return int(performance_score * 100) if performance_score else 0
        except:
            return 0
    
    def _generate_explanation(self, score: int, lighthouse_data: Dict) -> str:
        try:
            audits = lighthouse_data.get('audits', {})
            lcp = audits.get('largest-contentful-paint', {}).get('displayValue', 'N/A')
            fid = audits.get('max-potential-fid', {}).get('displayValue', 'N/A')
            cls = audits.get('cumulative-layout-shift', {}).get('displayValue', 'N/A')
            
            if score >= 90:
                return f"Excellent performance with good Core Web Vitals. LCP: {lcp}, FID: {fid}, CLS: {cls}"
            elif score >= 70:
                return f"Good performance with room for improvement. LCP: {lcp}, FID: {fid}, CLS: {cls}"
            else:
                return f"Performance needs significant improvement. LCP: {lcp}, FID: {fid}, CLS: {cls}"
        except:
            return f"Performance analysis completed with score: {score}%"
    
    def _generate_recommendations(self, lighthouse_data: Dict) -> List[Recommendation]:
        recommendations = []
        
        try:
            audits = lighthouse_data.get('audits', {})
            
            # LCP recommendations
            lcp_audit = audits.get('largest-contentful-paint', {})
            if lcp_audit.get('score', 1) < 0.9:
                recommendations.append(Recommendation(
                    priority="High",
                    title="Optimize Largest Contentful Paint (LCP)",
                    message="Improve LCP by optimizing images, removing unused CSS, and upgrading web hosting.",
                    doc_link="https://web.dev/lcp/"
                ))
            
            # CLS recommendations
            cls_audit = audits.get('cumulative-layout-shift', {})
            if cls_audit.get('score', 1) < 0.9:
                recommendations.append(Recommendation(
                    priority="Medium",
                    title="Reduce Cumulative Layout Shift (CLS)",
                    message="Minimize layout shifts by setting dimensions for images and ads.",
                    code_snippet='<img src="image.jpg" width="400" height="300" alt="Description">',
                    doc_link="https://web.dev/cls/"
                ))
            
            # Unused CSS
            unused_css = audits.get('unused-css-rules', {})
            if unused_css.get('score', 1) < 0.9:
                recommendations.append(Recommendation(
                    priority="Medium",
                    title="Remove Unused CSS",
                    message="Remove unused CSS to reduce bundle size and improve loading speed.",
                    doc_link="https://web.dev/unused-css-rules/"
                ))
            
            # Image optimization
            image_audit = audits.get('uses-optimized-images', {})
            if image_audit.get('score', 1) < 0.9:
                recommendations.append(Recommendation(
                    priority="High",
                    title="Optimize Images",
                    message="Compress and properly format images to reduce loading times.",
                    code_snippet='<img src="image.webp" alt="Description" loading="lazy">',
                    doc_link="https://web.dev/fast/#optimize-your-images"
                ))
            
        except Exception as e:
            # Fallback recommendations
            recommendations.append(Recommendation(
                priority="Medium",
                title="General Performance Optimization",
                message="Consider optimizing images, minifying CSS/JS, and enabling compression.",
                doc_link="https://web.dev/fast/"
            ))
        
        return recommendations
    
    def _fallback_analysis(self, url: str, error: str = None) -> ModuleResult:
        return ModuleResult(
            name="Performance",
            score=50,  # Default middle score when analysis fails
            description="Performance analysis (limited)",
            explanation=f"Performance analysis unavailable: {error or 'Lighthouse not installed'}",
            recommendations=[
                Recommendation(
                    priority="High",
                    title="Install Performance Analysis Tools",
                    message="Install Lighthouse for comprehensive performance analysis.",
                    doc_link="https://developers.google.com/web/tools/lighthouse"
                ),
                Recommendation(
                    priority="Medium",
                    title="Basic Performance Optimization",
                    message="Optimize images, minify CSS/JS, and enable compression.",
                    doc_link="https://web.dev/fast/"
                )
            ]
        )
