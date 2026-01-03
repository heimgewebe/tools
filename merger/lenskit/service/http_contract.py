"""Lightweight HTTP contract used by the service layer.

This module defines the minimal interfaces the service logic depends on
without binding directly to FastAPI. Framework-specific adapters (e.g.
FastAPI) supply concrete implementations to satisfy these protocols.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, AsyncIterable, Awaitable, Callable, Iterable, Mapping, Protocol, Union


class RequestLike(Protocol):
    """Subset of FastAPI's Request used by the service.

    Only the headers mapping and ``is_disconnected`` hook are required.
    """

    headers: Mapping[str, str]

    async def is_disconnected(self) -> bool: ...


StreamContent = Union[Iterable[Any], AsyncIterable[Any]]


class StreamingResponder(Protocol):
    """Callable that wraps an async/sync iterator into an HTTP response."""

    def __call__(self, content: StreamContent, media_type: str = "text/plain") -> Any: ...


class FileResponder(Protocol):
    """Callable that returns a file response."""

    def __call__(self, path: str, status_code: int = 200) -> Any: ...


class DependencyFactory(Protocol):
    """Represents FastAPI dependency declaration helpers (Depends/Query/Body)."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...


@dataclass(frozen=True)
class HTTPBindings:
    """Collection of HTTP-related bindings supplied by an adapter layer."""

    Request: type
    HTTPException: type
    BackgroundTasks: type
    Query: DependencyFactory
    Depends: DependencyFactory
    Body: DependencyFactory
    StaticFiles: type
    CORSMiddleware: type
    StreamingResponse: StreamingResponder
    FileResponse: FileResponder
    run_in_threadpool: Callable[..., Awaitable[Any]]

