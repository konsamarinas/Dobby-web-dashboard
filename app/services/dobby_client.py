import logging
import threading
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)


class DobbyAPIError(Exception):
    def __init__(self, message: str, status_code: int | None = None, kind: str = "api"):
        super().__init__(message)
        self.status_code = status_code
        self.kind = kind


class DobbyClient:
    def __init__(
        self,
        base_url: str,
        timeout: tuple[float, float] = (5, 45),
        cache_ttl: int = 30,
        retries: int = 1,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        self.retries = max(0, retries)
        self._cache: dict[str, tuple[float, Any]] = {}
        self._cache_lock = threading.Lock()

    def _request(self, method: str, path: str, **kwargs) -> Any:
        url = f"{self.base_url}{path}"
        attempts = 1 + (self.retries if method.upper() == "GET" else 0)
        for attempt in range(attempts):
            started = time.perf_counter()
            try:
                response = requests.request(method, url, timeout=self.timeout, **kwargs)
                duration_ms = round((time.perf_counter() - started) * 1000, 1)
                if response.status_code >= 400:
                    logger.warning(
                        "DOBBY API response endpoint=%s duration_ms=%s status=%s attempt=%s/%s",
                        path,
                        duration_ms,
                        response.status_code,
                        attempt + 1,
                        attempts,
                    )
                    if (
                        response.status_code in {429, 500, 502, 503, 504}
                        and attempt + 1 < attempts
                    ):
                        time.sleep(0.1 * (attempt + 1))
                        continue
                    response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict):
                    logger.warning(
                        "DOBBY API invalid response endpoint=%s duration_ms=%s status=%s exception=non-object JSON",
                        path,
                        duration_ms,
                        response.status_code,
                    )
                    raise DobbyAPIError("The DOBBY API returned an unexpected response.", kind="response")
                logger.info(
                    "DOBBY API response endpoint=%s duration_ms=%s status=%s",
                    path,
                    duration_ms,
                    response.status_code,
                )
                return data
            except DobbyAPIError:
                raise
            except requests.Timeout as exc:
                duration_ms = round((time.perf_counter() - started) * 1000, 1)
                logger.warning(
                    "DOBBY API timeout endpoint=%s duration_ms=%s exception=%s attempt=%s/%s",
                    path,
                    duration_ms,
                    exc,
                    attempt + 1,
                    attempts,
                )
                if attempt + 1 < attempts:
                    continue
                raise DobbyAPIError(
                    "The DOBBY API timed out while waiting for a response. Please retry.",
                    status_code=504,
                    kind="timeout",
                ) from exc
            except requests.ConnectionError as exc:
                duration_ms = round((time.perf_counter() - started) * 1000, 1)
                logger.warning(
                    "DOBBY API connection error endpoint=%s duration_ms=%s exception=%s attempt=%s/%s",
                    path,
                    duration_ms,
                    exc,
                    attempt + 1,
                    attempts,
                )
                if attempt + 1 < attempts:
                    continue
                raise DobbyAPIError(
                    "The DOBBY API connection failed. Please retry.",
                    status_code=502,
                    kind="connection",
                ) from exc
            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else 502
                duration_ms = round((time.perf_counter() - started) * 1000, 1)
                logger.warning(
                    "DOBBY API HTTP error endpoint=%s duration_ms=%s status=%s exception=%s",
                    path,
                    duration_ms,
                    status,
                    exc,
                )
                raise DobbyAPIError(
                    f"The DOBBY API returned HTTP {status}.",
                    status_code=status,
                    kind="http",
                ) from exc
            except requests.RequestException as exc:
                duration_ms = round((time.perf_counter() - started) * 1000, 1)
                logger.warning(
                    "DOBBY API request failed endpoint=%s duration_ms=%s exception=%s",
                    path,
                    duration_ms,
                    exc,
                )
                raise DobbyAPIError("The DOBBY API request failed. Please retry.", status_code=502, kind="request") from exc
            except ValueError as exc:
                logger.warning(
                    "DOBBY API invalid JSON endpoint=%s duration_ms=%s status=%s exception=%s",
                    path,
                    duration_ms,
                    getattr(response, "status_code", None),
                    exc,
                )
                raise DobbyAPIError("The DOBBY API returned invalid JSON.", kind="response") from exc
        raise DobbyAPIError("The DOBBY API request failed.", status_code=502, kind="request")

    def _cached_get(self, path: str, params: dict | None = None) -> Any:
        key = f"{path}?{sorted((params or {}).items())}"
        now = time.monotonic()
        with self._cache_lock:
            cached = self._cache.get(key)
            if cached and now - cached[0] < self.cache_ttl:
                return cached[1]
        data = self._request("GET", path, params=params or {})
        with self._cache_lock:
            self._cache[key] = (time.monotonic(), data)
        return data

    def health(self) -> dict:
        return self._cached_get("/health")

    def metrics(self) -> dict:
        return self._cached_get("/metrics")

    def recommendations(self, payload: dict) -> dict:
        return self._request("POST", "/recommendations", json=payload)

    def forecast(self, params: dict) -> dict:
        allowed = {"business_id", "level", "id", "start_date", "horizon", "order_type"}
        return self._request("GET", "/forecast", params={k: v for k, v in params.items() if k in allowed and v != ""})
