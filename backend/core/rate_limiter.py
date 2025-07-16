"""
Production-grade rate limiter with sliding window algorithm
"""

import time
import logging
from typing import Dict, Any, Optional
from collections import defaultdict, deque
import threading

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Sliding window rate limiter for API endpoints
    """
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)  # IP -> deque of timestamps
        self.lock = threading.Lock()
        
        logger.info(f"🚦 Rate limiter initialized: {max_requests} requests per {window_seconds} seconds")
    
    def allow_request(self, client_ip: str) -> bool:
        """
        Check if request is allowed for given client IP
        """
        try:
            with self.lock:
                current_time = time.time()
                client_requests = self.requests[client_ip]
                
                # Remove old requests outside the window
                while client_requests and client_requests[0] <= current_time - self.window_seconds:
                    client_requests.popleft()
                
                # Check if under limit
                if len(client_requests) < self.max_requests:
                    client_requests.append(current_time)
                    return True
                else:
                    logger.warning(f"⚠️ Rate limit exceeded for IP: {client_ip}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Rate limiter error: {str(e)}")
            return True  # Allow request on error
    
    def get_remaining_requests(self, client_ip: str) -> int:
        """
        Get remaining requests for client IP
        """
        try:
            with self.lock:
                current_time = time.time()
                client_requests = self.requests[client_ip]
                
                # Remove old requests
                while client_requests and client_requests[0] <= current_time - self.window_seconds:
                    client_requests.popleft()
                
                return max(0, self.max_requests - len(client_requests))
                
        except Exception:
            return self.max_requests
    
    def get_reset_time(self, client_ip: str) -> Optional[float]:
        """
        Get time when rate limit resets for client IP
        """
        try:
            with self.lock:
                client_requests = self.requests[client_ip]
                if client_requests:
                    return client_requests[0] + self.window_seconds
                return None
                
        except Exception:
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get rate limiter statistics
        """
        try:
            with self.lock:
                current_time = time.time()
                active_clients = 0
                total_requests = 0
                
                for client_ip, client_requests in self.requests.items():
                    # Remove old requests
                    while client_requests and client_requests[0] <= current_time - self.window_seconds:
                        client_requests.popleft()
                    
                    if client_requests:
                        active_clients += 1
                        total_requests += len(client_requests)
                
                return {
                    "max_requests_per_window": self.max_requests,
                    "window_seconds": self.window_seconds,
                    "active_clients": active_clients,
                    "total_active_requests": total_requests,
                    "total_tracked_ips": len(self.requests)
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get rate limiter stats: {str(e)}")
            return {}
    
    def cleanup_old_entries(self):
        """
        Clean up old entries to prevent memory leaks
        """
        try:
            with self.lock:
                current_time = time.time()
                ips_to_remove = []
                
                for client_ip, client_requests in self.requests.items():
                    # Remove old requests
                    while client_requests and client_requests[0] <= current_time - self.window_seconds:
                        client_requests.popleft()
                    
                    # Mark empty deques for removal
                    if not client_requests:
                        ips_to_remove.append(client_ip)
                
                # Remove empty entries
                for ip in ips_to_remove:
                    del self.requests[ip]
                
                if ips_to_remove:
                    logger.info(f"🧹 Cleaned up {len(ips_to_remove)} old rate limiter entries")
                    
        except Exception as e:
            logger.error(f"❌ Rate limiter cleanup failed: {str(e)}")
