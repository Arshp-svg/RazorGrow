import time
from collections import defaultdict
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class SlidingWindowRateLimiter:
    def __init__(self, max_requests: int = 30, window_seconds: int = 60, name: str = "default"):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.name = name
        # ip/client_key -> list of timestamp floats
        self._history: dict[str, list[float]] = defaultdict(list)
        self.enabled = True

    def _get_client_key(self, request: Request) -> str:
        # Prioritize X-Forwarded-For if available, otherwise client host
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client and request.client.host:
            return request.client.host
        return "127.0.0.1"

    def check(self, request: Request) -> None:
        if not self.enabled:
            return

        client_key = self._get_client_key(request)
        now = time.time()
        cutoff = now - self.window_seconds

        # Prune old timestamps
        history = [ts for ts in self._history[client_key] if ts > cutoff]
        self._history[client_key] = history

        if len(history) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - history[0])) + 1
            headers = {"Retry-After": str(max(1, retry_after))}
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for {self.name}. Maximum {self.max_requests} requests per {self.window_seconds}s.",
                headers=headers,
            )

        self._history[client_key].append(now)

    def reset(self) -> None:
        self._history.clear()


# Pre-configured instances
auth_limiter = SlidingWindowRateLimiter(max_requests=10, window_seconds=60, name="auth")
agent_limiter = SlidingWindowRateLimiter(max_requests=30, window_seconds=60, name="agent")
checkout_limiter = SlidingWindowRateLimiter(max_requests=25, window_seconds=60, name="checkout")


def rate_limit_auth(request: Request):
    auth_limiter.check(request)


def rate_limit_agent(request: Request):
    agent_limiter.check(request)


def rate_limit_checkout(request: Request):
    checkout_limiter.check(request)
