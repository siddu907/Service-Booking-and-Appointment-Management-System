import fnmatch
import os
import time


class RedisClient:
    def __init__(self):
        self.client = None
        self.store: dict[str, str] = {}
        self.expirations: dict[str, float | None] = {}

        try:
            import redis

            host = os.getenv("REDIS_HOST", "localhost")
            port = int(os.getenv("REDIS_PORT", "6379"))
            self.client = redis.Redis(host=host, port=port, decode_responses=True, protocol=2)
            self.client.ping()
        except Exception:
            self.client = None

    def _cleanup(self):
        now = time.time()
        for key in list(self.expirations):
            expiry = self.expirations.get(key)
            if expiry is not None and expiry <= now:
                self.store.pop(key, None)
                self.expirations.pop(key, None)

    def get(self, key: str):
        if self.client:
            try:
                return self.client.get(key)
            except Exception:
                self.client = None
        self._cleanup()
        return self.store.get(key)

    def set(self, key: str, value, ttl: int | None = None):
        if self.client:
            try:
                if ttl is not None:
                    return self.client.setex(key, ttl, value)
                return self.client.set(key, value)
            except Exception:
                self.client = None
        self._cleanup()
        self.store[key] = value
        self.expirations[key] = time.time() + ttl if ttl is not None else None
        return True

    def delete(self, key: str):
        if self.client:
            try:
                return self.client.delete(key)
            except Exception:
                self.client = None
        self._cleanup()
        self.store.pop(key, None)
        self.expirations.pop(key, None)
        return True

    def keys(self, pattern: str):
        if self.client:
            try:
                return self.client.keys(pattern)
            except Exception:
                self.client = None
        self._cleanup()
        return [key for key in self.store if fnmatch.fnmatch(key, pattern)]
