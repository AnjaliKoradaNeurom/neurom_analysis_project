#!/usr/bin/env python3
"""
Debug script to identify environment differences causing score variations
"""

import asyncio
import aiohttp
import time
import json
import hashlib
import platform
import sys
import ssl
import certifi
from datetime import datetime
from typing import Dict, List, Any
from urllib.parse import urlparse
import socket

class EnvironmentDebugger:
    """Debug environment differences that affect crawlability scoring"""
    
    def __init__(self):
        self.test_url = "https://www.mywishcare.com/"
        self.results = {}
    
    async def run_full_debug(self):
        """Run comprehensive environment debugging"""
        print("🔍 Environment Debugging Analysis")
        print("=" * 50)
        
        # System information
        await self._debug_system_info()
        
        # Network debugging
        await self._debug_network_performance()
        
        # SSL/TLS debugging
        await self._debug_ssl_configuration()
        
        # Content debugging
        await self._debug_content_variations()
        
        # Performance debugging
        await self._debug_performance_consistency()
        
        # Save results
        self._save_debug_report()
        
        print("\n🎯 SUMMARY")
        print("=" * 30)
        self._print_summary()
    
    async def _debug_system_info(self):
        """Debug system information"""
        print("\n📊 System Information")
        print("-" * 30)
        
        system_info = {
            "platform": platform.platform(),
            "python_version": sys.version,
            "architecture": platform.architecture(),
            "processor": platform.processor(),
            "hostname": socket.gethostname(),
            "ssl_version": ssl.OPENSSL_VERSION,
            "certifi_path": certifi.where()
        }
        
        self.results["system_info"] = system_info
        
        for key, value in system_info.items():
            print(f"  {key}: {value}")
    
    async def _debug_network_performance(self):
        """Debug network performance"""
        print("\n🌐 Network Performance")
        print("-" * 30)
        
        # DNS resolution test
        start_time = time.time()
        try:
            parsed = urlparse(self.test_url)
            socket.gethostbyname(parsed.hostname)
            dns_time = time.time() - start_time
            print(f"  DNS Resolution: {dns_time:.3f}s")
        except Exception as e:
            dns_time = None
            print(f"  DNS Resolution: FAILED - {e}")
        
        # Connection test
        connection_times = []
        for i in range(3):
            start_time = time.time()
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.test_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        await response.read()
                        connection_time = time.time() - start_time
                        connection_times.append(connection_time)
                        print(f"  Connection Test {i+1}: {connection_time:.3f}s")
            except Exception as e:
                print(f"  Connection Test {i+1}: FAILED - {e}")
        
        avg_connection_time = sum(connection_times) / len(connection_times) if connection_times else None
        
        self.results["network_performance"] = {
            "dns_time": dns_time,
            "connection_times": connection_times,
            "avg_connection_time": avg_connection_time
        }
    
    async def _debug_ssl_configuration(self):
        """Debug SSL/TLS configuration"""
        print("\n🔒 SSL/TLS Configuration")
        print("-" * 30)
        
        ssl_info = {
            "ssl_version": ssl.OPENSSL_VERSION,
            "ssl_version_info": ssl.OPENSSL_VERSION_INFO,
            "default_verify_paths": ssl.get_default_verify_paths()._asdict(),
            "ca_bundle_path": certifi.where()
        }
        
        # Test SSL connection
        try:
            context = ssl.create_default_context()
            parsed = urlparse(self.test_url)
            
            with socket.create_connection((parsed.hostname, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=parsed.hostname) as ssock:
                    ssl_info["cipher"] = ssock.cipher()
                    ssl_info["version"] = ssock.version()
                    ssl_info["peer_cert"] = ssock.getpeercert()
            
            print(f"  SSL Version: {ssl_info['version']}")
            print(f"  Cipher: {ssl_info['cipher']}")
            print("  SSL Connection: SUCCESS")
            
        except Exception as e:
            ssl_info["ssl_error"] = str(e)
            print(f"  SSL Connection: FAILED - {e}")
        
        self.results["ssl_info"] = ssl_info
    
    async def _debug_content_variations(self):
        """Debug content variations with different headers"""
        print("\n📄 Content Variations")
        print("-" * 30)
        
        headers_configs = {
            "standard_browser": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            },
            "bot_user_agent": {
                "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate"
            },
            "minimal_headers": {
                "User-Agent": "Python/aiohttp"
            },
            "no_compression": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
        }
        
        content_results = {}
        
        for config_name, headers in headers_configs.items():
            try:
                async with aiohttp.ClientSession() as session:
                    start_time = time.time()
                    async with session.get(self.test_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                        content = await response.read()
                        load_time = time.time() - start_time
                        
                        content_hash = hashlib.md5(content).hexdigest()[:16]
                        
                        content_results[config_name] = {
                            "status": response.status,
                            "size": len(content),
                            "hash": content_hash,
                            "load_time": load_time,
                            "headers": dict(response.headers)
                        }
                        
                        print(f"  {config_name}:")
                        print(f"    Status: {response.status}")
                        print(f"    Size: {len(content)} bytes")
                        print(f"    Hash: {content_hash}")
                        print(f"    Load Time: {load_time:.3f}s")
                        
            except Exception as e:
                content_results[config_name] = {"error": str(e)}
                print(f"  {config_name}: FAILED - {e}")
        
        self.results["content_variations"] = content_results
        
        # Analyze content differences
        hashes = [result.get("hash") for result in content_results.values() if "hash" in result]
        unique_hashes = set(hashes)
        
        print(f"\n  Content Analysis:")
        print(f"    Total responses: {len(content_results)}")
        print(f"    Unique content versions: {len(unique_hashes)}")
        
        if len(unique_hashes) > 1:
            print("    ⚠️  Different content versions detected!")
        else:
            print("    ✅ Consistent content across all requests")
    
    async def _debug_performance_consistency(self):
        """Debug performance consistency"""
        print("\n⚡ Performance Consistency")
        print("-" * 30)
        
        load_times = []
        content_sizes = []
        
        for i in range(5):
            try:
                async with aiohttp.ClientSession() as session:
                    start_time = time.time()
                    async with session.get(self.test_url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                        content = await response.read()
                        load_time = time.time() - start_time
                        
                        load_times.append(load_time)
                        content_sizes.append(len(content))
                        
                        print(f"  Test {i+1}: {load_time:.3f}s, {len(content)} bytes")
                        
            except Exception as e:
                print(f"  Test {i+1}: FAILED - {e}")
        
        if load_times:
            avg_load_time = sum(load_times) / len(load_times)
            min_load_time = min(load_times)
            max_load_time = max(load_times)
            load_time_variance = max_load_time - min_load_time
            
            print(f"\n  Performance Summary:")
            print(f"    Average Load Time: {avg_load_time:.3f}s")
            print(f"    Min Load Time: {min_load_time:.3f}s")
            print(f"    Max Load Time: {max_load_time:.3f}s")
            print(f"    Variance: {load_time_variance:.3f}s")
            
            if load_time_variance > 0.5:
                print("    ⚠️  High load time variance detected!")
            else:
                print("    ✅ Consistent load times")
        
        self.results["performance_consistency"] = {
            "load_times": load_times,
            "content_sizes": content_sizes,
            "avg_load_time": avg_load_time if load_times else None,
            "load_time_variance": load_time_variance if load_times else None
        }
    
    def _save_debug_report(self):
        """Save debug report to file"""
        timestamp = int(time.time())
        filename = f"environment_debug_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📁 Debug report saved to: {filename}")
    
    def _print_summary(self):
        """Print summary of findings"""
        issues = []
        
        # Check for content variations
        if "content_variations" in self.results:
            hashes = [result.get("hash") for result in self.results["content_variations"].values() if "hash" in result]
            if len(set(hashes)) > 1:
                issues.append("Content varies based on request headers")
        
        # Check for performance issues
        if "performance_consistency" in self.results:
            variance = self.results["performance_consistency"].get("load_time_variance")
            if variance and variance > 0.5:
                issues.append(f"High load time variance: {variance:.3f}s")
        
        # Check for network issues
        if "network_performance" in self.results:
            avg_time = self.results["network_performance"].get("avg_connection_time")
            if avg_time and avg_time > 3.0:
                issues.append(f"Slow network performance: {avg_time:.3f}s average")
        
        if issues:
            print("❌ Issues Found:")
            for issue in issues:
                print(f"  • {issue}")
        else:
            print("✅ No major issues detected")
        
        print("\n💡 Recommendations:")
        print("  • Use standardized request headers")
        print("  • Implement load time normalization")
        print("  • Use multiple attempts with median scoring")
        print("  • Consider caching for consistent results")

async def main():
    """Main function"""
    debugger = EnvironmentDebugger()
    await debugger.run_full_debug()

if __name__ == "__main__":
    asyncio.run(main())
