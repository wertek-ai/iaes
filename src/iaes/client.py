"""IAES Client — generic HTTP client for publishing events to any IAES-compliant endpoint.

This module is part of the IAES open standard SDK. It does NOT assume any specific
backend implementation. The URL and authentication method are user-configured.

Usage::

    from iaes import Client, AssetMeasurement

    client = Client("https://your-iaes-endpoint.example.com", api_key="your-key")

    event = AssetMeasurement(
        asset_id="MOTOR-001",
        measurement_type="vibration_velocity",
        value=4.2,
        unit="mm/s",
        source="acme.sensors.plant1",
    )

    result = client.publish(event)
    print(result)  # {"accepted": 1, "rejected": 0, "results": [...]}

    # Batch publish
    results = client.publish_batch([event1, event2, event3])

    # Async usage
    async with AsyncClient("https://...", api_key="...") as client:
        result = await client.publish(event)
"""

import json
import time
from typing import Any, Dict, List, Optional, Sequence, Union
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class IaesClientError(Exception):
    """Raised when the IAES endpoint returns an error."""

    def __init__(self, message: str, status_code: int = 0, body: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class Client:
    """Synchronous IAES event publisher.

    Works with any IAES-compliant ingest endpoint. No vendor lock-in.

    Args:
        url: Base URL of the IAES-compliant endpoint (e.g. "https://api.example.com").
             The client appends ``/api/v1/iaes/ingest`` automatically.
        api_key: API key for authentication (sent as ``X-API-Key`` header).
        timeout: Request timeout in seconds (default 30).
        headers: Additional headers to include in every request.
        ingest_path: Override the default ingest path (default "/api/v1/iaes/ingest").
    """

    def __init__(
        self,
        url: str,
        api_key: str = "",
        timeout: int = 30,
        headers: Optional[Dict[str, str]] = None,
        ingest_path: str = "/api/v1/iaes/ingest",
    ):
        self.base_url = url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.ingest_path = ingest_path
        self._extra_headers = headers or {}
        self._endpoint = self.base_url + self.ingest_path

    def _build_request(self, body: bytes) -> Request:
        """Build an HTTP request with proper headers."""
        req = Request(
            self._endpoint,
            data=body,
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "iaes-python-sdk/0.2.0")
        if self.api_key:
            req.add_header("X-API-Key", self.api_key)
        for k, v in self._extra_headers.items():
            req.add_header(k, v)
        return req

    def publish(self, event: Any) -> Dict[str, Any]:
        """Publish a single IAES event.

        Args:
            event: An IAES model instance (has ``to_dict()``) or a raw dict.

        Returns:
            Response dict from the endpoint (typically ``{accepted, rejected, results}``).

        Raises:
            IaesClientError: If the endpoint returns a non-2xx status.
        """
        envelope = event.to_dict() if hasattr(event, "to_dict") else event
        return self._send(envelope)

    def publish_batch(self, events: Sequence[Any]) -> Dict[str, Any]:
        """Publish a batch of IAES events in a single request.

        Args:
            events: List of IAES model instances or raw dicts (max 100).

        Returns:
            Response dict from the endpoint.

        Raises:
            IaesClientError: If the endpoint returns a non-2xx status.
        """
        envelopes = [
            e.to_dict() if hasattr(e, "to_dict") else e
            for e in events
        ]
        return self._send(envelopes)

    def _send(self, payload: Union[dict, list]) -> Dict[str, Any]:
        """Send payload to the ingest endpoint."""
        body = json.dumps(payload).encode("utf-8")
        req = self._build_request(body)

        try:
            with urlopen(req, timeout=self.timeout) as resp:
                data = resp.read().decode("utf-8")
                return json.loads(data)
        except HTTPError as e:
            body_text = ""
            try:
                body_text = e.read().decode("utf-8")
            except Exception:
                pass
            raise IaesClientError(
                f"HTTP {e.code}: {body_text[:500]}",
                status_code=e.code,
                body=body_text,
            ) from e
        except URLError as e:
            raise IaesClientError(f"Connection failed: {e.reason}") from e


# Optional async client — only available if httpx is installed
try:
    import httpx as _httpx

    class AsyncClient:
        """Async IAES event publisher (requires ``httpx``).

        Usage::

            async with AsyncClient("https://...", api_key="...") as client:
                result = await client.publish(event)
        """

        def __init__(
            self,
            url: str,
            api_key: str = "",
            timeout: int = 30,
            headers: Optional[Dict[str, str]] = None,
            ingest_path: str = "/api/v1/iaes/ingest",
        ):
            self.base_url = url.rstrip("/")
            self.api_key = api_key
            self.timeout = timeout
            self.ingest_path = ingest_path
            self._endpoint = self.base_url + self.ingest_path

            h = {"Content-Type": "application/json", "User-Agent": "iaes-python-sdk/0.2.0"}
            if api_key:
                h["X-API-Key"] = api_key
            if headers:
                h.update(headers)

            self._client = _httpx.AsyncClient(headers=h, timeout=timeout)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            await self._client.aclose()

        async def publish(self, event: Any) -> Dict[str, Any]:
            """Publish a single IAES event asynchronously."""
            envelope = event.to_dict() if hasattr(event, "to_dict") else event
            return await self._send(envelope)

        async def publish_batch(self, events: Sequence[Any]) -> Dict[str, Any]:
            """Publish a batch of IAES events asynchronously."""
            envelopes = [
                e.to_dict() if hasattr(e, "to_dict") else e
                for e in events
            ]
            return await self._send(envelopes)

        async def _send(self, payload: Union[dict, list]) -> Dict[str, Any]:
            resp = await self._client.post(self._endpoint, json=payload)
            if resp.status_code >= 400:
                raise IaesClientError(
                    f"HTTP {resp.status_code}: {resp.text[:500]}",
                    status_code=resp.status_code,
                    body=resp.text,
                )
            return resp.json()

except ImportError:
    AsyncClient = None  # type: ignore[misc,assignment]
