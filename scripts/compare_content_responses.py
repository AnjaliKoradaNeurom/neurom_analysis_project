#!/usr/bin/env python3
"""
Compare content responses across different request configurations
"""

import asyncio
import aiohttp
import hashlib
import json
import time
from typing import Dict, List, Any
from bs4 import BeautifulSoup
import ssl
import certifi

class ContentComparator:
    """Compare content responses to identify variations"""
    
    def __init__(self):
        self.test_url = "https://www.mywishcare.com/"
        self.results = {}
    
    async def compare_responses(self):
        """Compare responses across different configurations"""
        print("🔍 Comparing Content Responses")
        print("=" * 50)
        
        # Different request configurations
        configs = {
            "Standard Browser": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            },
            "Bot User Agent": {
                "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate"
            },
            "Minimal Headers": {
                "User-Agent": "Python/aiohttp"
            },
            "No Compression": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
        }
        
        responses = {}
        
        # Test each configuration
        for config_name, headers in configs.items():
            print(f"\n📡 Testing: {config_name}")
            
            try:
                response_data = await self._fetch_with_config(headers)
                responses[config_name] = response_data
                
                print(f"   ✅ Status: {response_data['status']}")
                print(f"   ✅ Size: {response_data['content_size']} bytes")
                print(f"   ✅ Hash: {response_data['content_hash'][:16]}...")
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                responses[config_name] = {"error": str(e)}
        
        # Analyze responses
        await self._analyze_responses(responses)
        
        # Save results
        self._save_comparison_results(responses)
    
    async def _fetch_with_config(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Fetch content with specific headers"""
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.test_url, 
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                content = await response.read()
                load_time = time.time() - start_time
                
                # Calculate hash
                content_hash = hashlib.md5(content).hexdigest()
                
                # Parse content for feature extraction
                soup = BeautifulSoup(content, 'html.parser')
                features = self._extract_features(soup, content)
                
                return {
                    "status": response.status,
                    "content_size": len(content),
                    "content_hash": content_hash,
                    "load_time": load_time,
                    "headers": dict(response.headers),
                    "features": features
                }
    
    def _extract_features(self, soup: BeautifulSoup, content: bytes) -> Dict[str, Any]:
        """Extract features from content"""
        # Title
        title = soup.find('title')
        title_text = title.get_text().strip() if title else ""
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        meta_desc_text = meta_desc.get('content', '').strip() if meta_desc else ""
        
        # Count elements
        h1_count = len(soup.find_all('h1'))
        h2_count = len(soup.find_all('h2'))
        image_count = len(soup.find_all('img'))
        link_count = len(soup.find_all('a'))
        
        # Text content
        text_content = soup.get_text()
        word_count = len(text_content.split())
        
        return {
            "title_length": len(title_text),
            "meta_description_length": len(meta_desc_text),
            "h1_count": h1_count,
            "h2_count": h2_count,
            "image_count": image_count,
            "link_count": link_count,
            "word_count": word_count,
            "content_size_bytes": len(content)
        }
    
    async def _analyze_responses(self, responses: Dict[str, Dict[str, Any]]):
        """Analyze response differences"""
        print(f"\n🔍 CONTENT ANALYSIS")
        print("=" * 30)
        
        # Filter successful responses
        successful_responses = {k: v for k, v in responses.items() if "error" not in v}
        
        if len(successful_responses) < 2:
            print("❌ Not enough successful responses to compare")
            return
        
        # Analyze content hashes
        print(f"📊 Content Hash Analysis:")
        hashes = {}
        for config, data in successful_responses.items():
            hash_val = data["content_hash"]
            if hash_val not in hashes:
                hashes[hash_val] = []
            hashes[hash_val].append(config)
        
        print(f"   Total responses: {len(successful_responses)}")
        print(f"   Unique content versions: {len(hashes)}")
        
        if len(hashes) > 1:
            print(f"   ⚠️  Different content versions detected!")
            for i, (hash_val, configs) in enumerate(hashes.items(), 1):
                print(f"   Version {i} ({hash_val[:16]}...): {', '.join(configs)}")
        else:
            print(f"   ✅ All content identical")
        
        # Analyze features
        print(f"\n📊 Feature Comparison:")
        feature_names = ["title_length", "meta_description_length", "h1_count", "h2_count", "image_count", "link_count", "word_count", "content_size_bytes"]
        
        for feature in feature_names:
            values = {}
            for config, data in successful_responses.items():
                if "features" in data and feature in data["features"]:
                    value = data["features"][feature]
                    if value not in values:
                        values[value] = []
                    values[value].append(config)
            
            if len(values) == 1:
                value = list(values.keys())[0]
                print(f"   ✅ {feature}: {value} (consistent)")
            else:
                print(f"   ⚠️  {feature}: varies - {dict(zip(successful_responses.keys(), [data['features'][feature] for data in successful_responses.values() if 'features' in data]))}")
        
        # Analyze performance
        print(f"\n📊 Performance Comparison:")
        for config, data in successful_responses.items():
            if "load_time" in data:
                print(f"   {config}: {data['load_time']:.3f}s")
        
        load_times = [data["load_time"] for data in successful_responses.values() if "load_time" in data]
        if load_times:
            min_time = min(load_times)
            max_time = max(load_times)
            print(f"   Time difference: {max_time - min_time:.3f}s")
        
        # Scoring impact analysis
        print(f"\n🎯 SCORING IMPACT ANALYSIS:")
        if len(hashes) > 1:
            print(f"   ❌ Content differences detected - will cause score variations")
        else:
            print(f"   ✅ Content consistent - no content-based score variations")
        
        if load_times and (max(load_times) - min(load_times)) > 0.5:
            print(f"   ⚠️  Performance varies significantly")
        else:
            print(f"   ✅ Performance is relatively consistent")
    
    def _save_comparison_results(self, responses: Dict[str, Dict[str, Any]]):
        """Save comparison results to file"""
        timestamp = int(time.time())
        filename = f"content_comparison_{timestamp}.json"
        
        # Prepare data for JSON serialization
        json_data = {}
        for config, data in responses.items():
            json_data[config] = {}
            for key, value in data.items():
                if key == "headers":
                    json_data[config][key] = dict(value) if hasattr(value, 'items') else value
                else:
                    json_data[config][key] = value
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, default=str)
        
        print(f"\n📁 Detailed comparison saved to {filename}")

async def main():
    """Main function"""
    comparator = ContentComparator()
    await comparator.compare_responses()

if __name__ == "__main__":
    asyncio.run(main())
