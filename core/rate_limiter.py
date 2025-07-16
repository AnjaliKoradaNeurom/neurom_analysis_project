import time
import asyncio
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
import threading

logger = logging.getLogger(__name__)

class TokenBucket:
    """Token bucket implementation for rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket
        
        Args:
            capacity: Maximum number of tokens in bucket
            refill_rate: Rate at which tokens are added (tokens per second)
        """
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False if not enough tokens available
        """
        with self.lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        
        # Add tokens based on elapsed time
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def get_tokens(self) -> int:
        """Get current number of tokens"""
        with self.lock:
            self._refill()
            return int(self.tokens)
    
    def time_until_tokens(self, required_tokens: int) -> float:
        """
        Calculate time until required tokens are available
        
        Args:
            required_tokens: Number of tokens needed
            
        Returns:
            Time in seconds until tokens are available (0 if already available)
        """
        with self.lock:
            self._refill()
            
            if self.tokens >= required_tokens:
                return 0.0
            
            tokens_needed = required_tokens - self.tokens
            return tokens_needed / self.refill_rate


class RateLimiter:
    """
    Rate limiter with multiple strategies and per-client tracking
    """
    
    def __init__(self, 
                 requests_per_minute: int = 60,
                 requests_per_hour: int = 1000,
                 burst_capacity: int = 10):
        """
        Initialize rate limiter
        
        Args:
            requests_per_minute: Maximum requests per minute per client
            requests_per_hour: Maximum requests per hour per client
            burst_capacity: Maximum burst requests allowed
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_capacity = burst_capacity
        
        # Per-client token buckets
        self.minute_buckets: Dict[str, TokenBucket] = {}
        self.hour_buckets: Dict[str, TokenBucket] = {}
        self.burst_buckets: Dict[str, TokenBucket] = {}
        
        # Request tracking
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Cleanup tracking
        self.last_cleanup = time.time()
        self.cleanup_interval = 3600  # 1 hour
        
        # Thread safety
        self.lock = threading.Lock()
    
    def is_allowed(self, client_id: str, tokens: int = 1) -> Tuple[bool, Dict[str, any]]:
        """
        Check if request is allowed for client
        
        Args:
            client_id: Unique identifier for client (IP, user ID, etc.)
            tokens: Number of tokens to consume
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        with self.lock:
            # Cleanup old buckets periodically
            self._cleanup_if_needed()
            
            # Get or create buckets for client
            minute_bucket = self._get_or_create_bucket(client_id, 'minute')
            hour_bucket = self._get_or_create_bucket(client_id, 'hour')
            burst_bucket = self._get_or_create_bucket(client_id, 'burst')
            
            # Check all rate limits
            minute_allowed = minute_bucket.consume(tokens)
            hour_allowed = hour_bucket.consume(tokens) if minute_allowed else False
            burst_allowed = burst_bucket.consume(tokens) if hour_allowed else False
            
            # If any limit is exceeded, restore tokens to successful buckets
            if not (minute_allowed and hour_allowed and burst_allowed):
                if minute_allowed and not hour_allowed:
                    minute_bucket.tokens += tokens
                elif minute_allowed and hour_allowed and not burst_allowed:
                    minute_bucket.tokens += tokens
                    hour_bucket.tokens += tokens
                
                # Calculate retry after time
                retry_after = max(
                    minute_bucket.time_until_tokens(tokens) if not minute_allowed else 0,
                    hour_bucket.time_until_tokens(tokens) if not hour_allowed else 0,
                    burst_bucket.time_until_tokens(tokens) if not burst_allowed else 0
                )
                
                rate_limit_info = {
                    'allowed': False,
                    'retry_after': retry_after,
                    'minute_remaining': minute_bucket.get_tokens(),
                    'hour_remaining': hour_bucket.get_tokens(),
                    'burst_remaining': burst_bucket.get_tokens(),
                    'reset_time': datetime.utcnow() + timedelta(seconds=retry_after)
                }
                
                return False, rate_limit_info
            
            # Record successful request
            self.request_history[client_id].append(time.time())
            
            rate_limit_info = {
                'allowed': True,
                'minute_remaining': minute_bucket.get_tokens(),
                'hour_remaining': hour_bucket.get_tokens(),
                'burst_remaining': burst_bucket.get_tokens(),
                'reset_time': datetime.utcnow() + timedelta(minutes=1)
            }
            
            return True, rate_limit_info
    
    def _get_or_create_bucket(self, client_id: str, bucket_type: str) -> TokenBucket:
        """Get or create token bucket for client and type"""
        if bucket_type == 'minute':
            if client_id not in self.minute_buckets:
                self.minute_buckets[client_id] = TokenBucket(
                    capacity=self.requests_per_minute,
                    refill_rate=self.requests_per_minute / 60.0  # per second
                )
            return self.minute_buckets[client_id]
        
        elif bucket_type == 'hour':
            if client_id not in self.hour_buckets:
                self.hour_buckets[client_id] = TokenBucket(
                    capacity=self.requests_per_hour,
                    refill_rate=self.requests_per_hour / 3600.0  # per second
                )
            return self.hour_buckets[client_id]
        
        elif bucket_type == 'burst':
            if client_id not in self.burst_buckets:
                self.burst_buckets[client_id] = TokenBucket(
                    capacity=self.burst_capacity,
                    refill_rate=self.burst_capacity / 10.0  # refill burst in 10 seconds
                )
            return self.burst_buckets[client_id]
        
        else:
            raise ValueError(f"Unknown bucket type: {bucket_type}")
    
    def _cleanup_if_needed(self):
        """Clean up old buckets and request history"""
        now = time.time()
        if now - self.last_cleanup < self.cleanup_interval:
            return
        
        # Remove buckets for clients with no recent activity
        cutoff_time = now - 7200  # 2 hours
        
        # Clean minute buckets
        inactive_clients = []
        for client_id, bucket in self.minute_buckets.items():
            if bucket.last_refill < cutoff_time:
                inactive_clients.append(client_id)
        
        for client_id in inactive_clients:
            self.minute_buckets.pop(client_id, None)
            self.hour_buckets.pop(client_id, None)
            self.burst_buckets.pop(client_id, None)
        
        # Clean request history
        history_cutoff = now - 3600  # 1 hour
        for client_id, history in list(self.request_history.items()):
            # Remove old requests
            while history and history[0] < history_cutoff:
                history.popleft()
            
            # Remove empty histories
            if not history:
                del self.request_history[client_id]
        
        self.last_cleanup = now
    
    def get_client_stats(self, client_id: str) -> Dict[str, any]:
        """
        Get statistics for a specific client
        
        Args:
            client_id: Client identifier
            
        Returns:
            Dictionary with client statistics
        """
        with self.lock:
            stats = {
                'client_id': client_id,
                'minute_remaining': 0,
                'hour_remaining': 0,
                'burst_remaining': 0,
                'total_requests': 0,
                'recent_requests': 0
            }
            
            # Get remaining tokens
            if client_id in self.minute_buckets:
                stats['minute_remaining'] = self.minute_buckets[client_id].get_tokens()
            else:
                stats['minute_remaining'] = self.requests_per_minute
            
            if client_id in self.hour_buckets:
                stats['hour_remaining'] = self.hour_buckets[client_id].get_tokens()
            else:
                stats['hour_remaining'] = self.requests_per_hour
            
            if client_id in self.burst_buckets:
                stats['burst_remaining'] = self.burst_buckets[client_id].get_tokens()
            else:
                stats['burst_remaining'] = self.burst_capacity
            
            # Get request history
            if client_id in self.request_history:
                history = self.request_history[client_id]
                stats['total_requests'] = len(history)
                
                # Count recent requests (last 5 minutes)
                recent_cutoff = time.time() - 300
                stats['recent_requests'] = sum(1 for req_time in history if req_time > recent_cutoff)
            
            return stats
    
    def get_global_stats(self) -> Dict[str, any]:
        """Get global rate limiter statistics"""
        with self.lock:
            total_clients = len(set(
                list(self.minute_buckets.keys()) + 
                list(self.hour_buckets.keys()) + 
                list(self.burst_buckets.keys())
            ))
            
            total_requests = sum(len(history) for history in self.request_history.values())
            
            # Recent activity (last 5 minutes)
            recent_cutoff = time.time() - 300
            recent_requests = sum(
                sum(1 for req_time in history if req_time > recent_cutoff)
                for history in self.request_history.values()
            )
            
            return {
                'total_clients': total_clients,
                'total_requests': total_requests,
                'recent_requests': recent_requests,
                'active_minute_buckets': len(self.minute_buckets),
                'active_hour_buckets': len(self.hour_buckets),
                'active_burst_buckets': len(self.burst_buckets),
                'requests_per_minute_limit': self.requests_per_minute,
                'requests_per_hour_limit': self.requests_per_hour,
                'burst_capacity': self.burst_capacity
            }
    
    def reset_client(self, client_id: str):
        """
        Reset rate limits for a specific client
        
        Args:
            client_id: Client identifier to reset
        """
        with self.lock:
            self.minute_buckets.pop(client_id, None)
            self.hour_buckets.pop(client_id, None)
            self.burst_buckets.pop(client_id, None)
            self.request_history.pop(client_id, None)
    
    async def wait_for_capacity(self, client_id: str, tokens: int = 1, timeout: float = 60.0) -> bool:
        """
        Wait until capacity is available for client
        
        Args:
            client_id: Client identifier
            tokens: Number of tokens needed
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if capacity became available, False if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            allowed, info = self.is_allowed(client_id, tokens)
            if allowed:
                return True
            
            # Wait for a short time before checking again
            wait_time = min(info.get('retry_after', 1.0), 5.0)
            await asyncio.sleep(wait_time)
        
        return False


# Global rate limiter instance
default_rate_limiter = RateLimiter(
    requests_per_minute=60,
    requests_per_hour=1000,
    burst_capacity=10
)


def get_client_id(request) -> str:
    """
    Extract client ID from request (IP address, user ID, etc.)
    
    Args:
        request: FastAPI request object
        
    Returns:
        Client identifier string
    """
    # Try to get real IP from headers (for reverse proxy setups)
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    # Fall back to direct client IP
    return request.client.host if request.client else 'unknown'
