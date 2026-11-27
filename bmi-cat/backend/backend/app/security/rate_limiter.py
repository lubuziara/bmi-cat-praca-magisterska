import hashlib
import math
import time
from collections import deque
from threading import Lock
from fastapi import HTTPException
from app.security.client_ip import resolve_client_ip


def client_ip(request, settings):
    return resolve_client_ip(request, settings)


class MemoryRateLimitStore:
    def __init__(self): self.attempts, self.values, self.lock = {}, {}, Lock()
    def hit(self, key, limit, window):
        now = time.monotonic()
        with self.lock:
            queue = self.attempts.setdefault(key, deque())
            while queue and queue[0] <= now - window: queue.popleft()
            if len(queue) >= limit: return max(1, math.ceil(window - (now - queue[0])))
            queue.append(now); return 0
    def get(self, key):
        with self.lock:
            value = self.values.get(key)
            if not value or value[1] <= time.monotonic(): self.values.pop(key, None); return None
            return value[0]
    def set(self, key, value, ttl):
        with self.lock: self.values[key] = (value, time.monotonic() + ttl)
    def delete(self, key):
        with self.lock: self.values.pop(key, None); self.attempts.pop(key, None)


class RedisRateLimitStore:
    """Optional shared store; imported only when configured."""
    def __init__(self, url):
        try: import redis
        except ImportError: raise RuntimeError("Redis rate limiter requires the redis package") from None
        try:
            self.client = redis.from_url(url, decode_responses=True)
            self.client.ping()
        except Exception:
            raise RuntimeError("Redis rate limiter is unavailable") from None
    def hit(self, key, limit, window):
        now = time.time(); member = f"{now}:{time.time_ns()}"
        script = """redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', ARGV[1]-ARGV[2]); local n=redis.call('ZCARD', KEYS[1]); if n>=tonumber(ARGV[3]) then local o=redis.call('ZRANGE', KEYS[1], 0, 0, 'WITHSCORES'); return math.max(1, math.ceil(ARGV[2]-(ARGV[1]-tonumber(o[2])))); end; redis.call('ZADD', KEYS[1], ARGV[1], ARGV[4]); redis.call('EXPIRE', KEYS[1], ARGV[2]); return 0"""
        return int(self.client.eval(script, 1, key, now, window, limit, member))
    def get(self, key): return self.client.get(key)
    def set(self, key, value, ttl): self.client.set(key, value, ex=ttl)
    def delete(self, key): self.client.delete(key)


class RateLimiter:
    def __init__(self, settings, store=None): self.settings, self.store = settings, store or MemoryRateLimitStore()
    def _key(self, operation, part, value): return f"rl:{operation}:{part}:{hashlib.sha256(value.encode()).hexdigest()}"
    def check(self, operation, request, subject=None):
        policy = self.settings.rate_limits[operation]; keys = [self._key(operation, "ip", client_ip(request, self.settings))]
        if subject: keys.append(self._key(operation, "subject", subject))
        for key in keys:
            cooldown = self.store.get("cooldown:" + key)
            if cooldown: self._blocked(int(cooldown))
            retry = self.store.hit(key, policy["limit"], policy["window"])
            if retry: self._blocked(retry)
    def failure(self, operation, subject):
        if not subject: return
        policy = self.settings.rate_limits[operation]; key = self._key(operation, "subject", subject); failure_key = "failures:" + key
        failures = int(self.store.get(failure_key) or 0) + 1; self.store.set(failure_key, failures, policy["failure_window"])
        if failures >= policy["failure_threshold"]:
            level = min((failures // policy["failure_threshold"]) - 1, len(policy["cooldowns"]) - 1); cooldown = policy["cooldowns"][level]
            self.store.set("cooldown:" + key, cooldown, cooldown)
    def success(self, operation, subject):
        if subject:
            key = self._key(operation, "subject", subject); self.store.delete("failures:" + key); self.store.delete("cooldown:" + key)
    @staticmethod
    def _blocked(retry): raise HTTPException(429, "Za dużo prób. Spróbuj ponownie później.", headers={"Retry-After": str(min(retry, 900))})


def create_rate_limiter(settings):
    if settings.rate_limit_backend == "redis": return RateLimiter(settings, RedisRateLimitStore(settings.redis_url))
    return RateLimiter(settings, MemoryRateLimitStore())
