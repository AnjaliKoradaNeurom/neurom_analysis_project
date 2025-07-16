#!/usr/bin/env python3
"""
Test script for environment consistency fixes
"""

import asyncio
import aiohttp
import time
import json
import hashlib
import statistics
from typing import Dict, List, Any
from bs4 import BeautifulSoup
import ssl
import certifi

class ConsistencyTester:
    """Test environment consistency fixes"""
    
    def __init__(self):
        self.test_url = "https://www.mywishcare.com/"
        self.results = []
    
    async def test_normalized_analysis(self):
        """Test normalized analysis approach"""
        print("🔧 Testing Normalized Analysis")
        print("=" * 40)
        
        # Run multiple tests
        for i in range(5):
            print(f"\n📊 Test Run {i+1}/5")
            print("-" * 20)
            
            result = await self._run_normalized_crawl()
            self.results.append(result)
            
            print(f"  Score: {result['score']}")
            print(f"  Load Time: {result['load_time']:.3f}s")
            print(f"  Content Size: {result['content_size']} bytes")
            print(f"  Word Count: {result['word_count']}")
        
        # Analyze consistency
        self._analyze_consistency()
    
    async def _run_normalized_crawl(self):
        """Run a single normalized crawl"""
        # Standardized headers for consistency
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; WebAnalyzer/2.0; +https://example.com/bot)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
        
        # SSL context for consistency
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        
        # Multiple attempts for stability
        attempts = []
        
        for attempt in range(3):
            try:
                connector = aiohttp.TCPConnector(ssl=ssl_context)
                timeout = aiohttp.ClientTimeout(total=10, connect=5)
                
                async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                    start_time = time.time()
                    
                    async with session.get(self.test_url, headers=headers) as response:
                        content = await response.read()
                        load_time = time.time() - start_time
                        
                        # Parse content
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Extract features
                        features = self._extract_normalized_features(soup, content, load_time)
                        attempts.append(features)
                        
            except Exception as e:
                print(f"    Attempt {attempt + 1} failed: {e}")
                continue
        
        if not attempts:
            return {"error": "All attempts failed"}
        
        # Use median values for stability
        return self._get_median_result(attempts)
    
    def _extract_normalized_features(self, soup: BeautifulSoup, content: bytes, load_time: float) -> Dict:
        """Extract normalized features"""
        # Basic content features
        title = soup.find('title')
        title_text = title.get_text().strip() if title else ""
        
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        meta_desc_text = meta_desc.get('content', '').strip() if meta_desc else ""
        
        # Count elements
        h1_count = len(soup.find_all('h1'))
        h2_count = len(soup.find_all('h2'))
        img_count = len(soup.find_all('img'))
        link_count = len(soup.find_all('a'))
        
        # Text content
        text_content = soup.get_text()
        word_count = len(text_content.split())
        
        # Technical features
        has_viewport = bool(soup.find('meta', attrs={'name': 'viewport'}))
        has_ssl = self.test_url.startswith('https://')
        
        # Normalize load time (cap at 5 seconds to reduce variance)
        normalized_load_time = min(load_time, 5.0)
        
        # Calculate scores
        content_quality_score = self._calculate_content_score(
            len(title_text), len(meta_desc_text), word_count, h1_count
        )
        
        technical_quality_score = self._calculate_technical_score(
            has_ssl, has_viewport, h1_count, img_count
        )
        
        performance_score = self._calculate_performance_score(
            normalized_load_time, len(content)
        )
        
        # Overall score
        overall_score = int(
            content_quality_score * 0.35 +
            technical_quality_score * 0.40 +
            performance_score * 0.25
        )
        
        return {
            "score": overall_score,
            "load_time": normalized_load_time,
            "content_size": len(content),
            "word_count": word_count,
            "title_length": len(title_text),
            "meta_desc_length": len(meta_desc_text),
            "h1_count": h1_count,
            "h2_count": h2_count,
            "img_count": img_count,
            "link_count": link_count,
            "has_viewport": has_viewport,
            "has_ssl": has_ssl,
            "content_quality_score": content_quality_score,
            "technical_quality_score": technical_quality_score,
            "performance_score": performance_score
        }
    
    def _calculate_content_score(self, title_len: int, desc_len: int, word_count: int, h1_count: int) -> float:
        """Calculate content quality score"""
        score = 0
        
        # Title score (0-10)
        if 30 <= title_len <= 60:
            score += 10
        elif title_len > 0:
            score += 5
        
        # Meta description score (0-10)
        if 120 <= desc_len <= 160:
            score += 10
        elif desc_len > 0:
            score += 5
        
        # Word count score (0-10)
        if word_count >= 300:
            score += 10
        elif word_count >= 100:
            score += 7
        elif word_count > 0:
            score += 3
        
        # H1 score (0-5)
        if h1_count == 1:
            score += 5
        elif h1_count > 1:
            score += 2
        
        return score
    
    def _calculate_technical_score(self, has_ssl: bool, has_viewport: bool, h1_count: int, img_count: int) -> float:
        """Calculate technical quality score"""
        score = 0
        
        # SSL score (0-15)
        if has_ssl:
            score += 15
        
        # Viewport score (0-10)
        if has_viewport:
            score += 10
        
        # Structure score (0-10)
        if h1_count == 1:
            score += 10
        elif h1_count > 0:
            score += 5
        
        # Images score (0-5)
        if img_count > 0:
            score += 5
        
        return score
    
    def _calculate_performance_score(self, load_time: float, content_size: int) -> float:
        """Calculate performance score"""
        score = 0
        
        # Load time score (0-15)
        if load_time <= 1.0:
            score += 15
        elif load_time <= 2.0:
            score += 12
        elif load_time <= 3.0:
            score += 8
        elif load_time <= 5.0:
            score += 4
        
        # Content size score (0-10)
        size_mb = content_size / (1024 * 1024)
        if size_mb <= 0.5:
            score += 10
        elif size_mb <= 1.0:
            score += 8
        elif size_mb <= 2.0:
            score += 5
        elif size_mb <= 5.0:
            score += 2
        
        return score
    
    def _get_median_result(self, attempts: List[Dict]) -> Dict:
        """Get median result from multiple attempts"""
        if len(attempts) == 1:
            return attempts[0]
        
        # Calculate median for numeric values
        scores = [a['score'] for a in attempts]
        load_times = [a['load_time'] for a in attempts]
        content_sizes = [a['content_size'] for a in attempts]
        word_counts = [a['word_count'] for a in attempts]
        
        # Use the attempt closest to median score
        median_score = statistics.median(scores)
        closest_attempt = min(attempts, key=lambda x: abs(x['score'] - median_score))
        
        # Override with median values for key metrics
        result = closest_attempt.copy()
        result['score'] = int(median_score)
        result['load_time'] = statistics.median(load_times)
        result['content_size'] = int(statistics.median(content_sizes))
        result['word_count'] = int(statistics.median(word_counts))
        
        return result
    
    def _analyze_consistency(self):
        """Analyze consistency of results"""
        print("\n📊 Consistency Analysis")
        print("=" * 30)
        
        if not self.results:
            print("❌ No results to analyze")
            return
        
        # Extract scores
        scores = [r['score'] for r in self.results if 'score' in r]
        load_times = [r['load_time'] for r in self.results if 'load_time' in r]
        
        if not scores:
            print("❌ No valid scores found")
            return
        
        # Calculate statistics
        avg_score = statistics.mean(scores)
        min_score = min(scores)
        max_score = max(scores)
        score_variance = max_score - min_score
        std_dev = statistics.stdev(scores) if len(scores) > 1 else 0
        
        avg_load_time = statistics.mean(load_times) if load_times else 0
        load_time_variance = max(load_times) - min(load_times) if load_times else 0
        
        print(f"Score Statistics:")
        print(f"  Average: {avg_score:.1f}")
        print(f"  Range: {min_score} - {max_score}")
        print(f"  Variance: {score_variance} points")
        print(f"  Standard Deviation: {std_dev:.2f}")
        
        print(f"\nLoad Time Statistics:")
        print(f"  Average: {avg_load_time:.3f}s")
        print(f"  Variance: {load_time_variance:.3f}s")
        
        # Consistency assessment
        print(f"\n🎯 Consistency Assessment:")
        
        if score_variance <= 2:
            print("  ✅ Excellent score consistency (≤2 points)")
        elif score_variance <= 5:
            print("  ⚠️  Good score consistency (≤5 points)")
        elif score_variance <= 10:
            print("  ⚠️  Fair score consistency (≤10 points)")
        else:
            print("  ❌ Poor score consistency (>10 points)")
        
        if load_time_variance <= 0.5:
            print("  ✅ Excellent load time consistency")
        elif load_time_variance <= 1.0:
            print("  ⚠️  Good load time consistency")
        else:
            print("  ❌ Poor load time consistency")
        
        # Save results
        timestamp = int(time.time())
        filename = f"consistency_test_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "test_results": self.results,
                "statistics": {
                    "avg_score": avg_score,
                    "score_variance": score_variance,
                    "std_dev": std_dev,
                    "avg_load_time": avg_load_time,
                    "load_time_variance": load_time_variance
                }
            }, f, indent=2, default=str)
        
        print(f"\n📁 Results saved to: {filename}")

async def main():
    """Main function"""
    tester = ConsistencyTester()
    await tester.test_normalized_analysis()

if __name__ == "__main__":
    asyncio.run(main())
