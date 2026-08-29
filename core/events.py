"""
Event system for FreeStack.

Provides a typed event bus with sync/async handlers, middleware,
and outbox pattern for reliable event publishing.
"""

import asyncio
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel, Field


T = TypeVar("T", bound="Event")


class Event(BaseModel):
    """Base event class."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "event_type") or cls.event_type == "Event":
            cls.event_type = cls.__name__

    def with_correlation(self, correlation_id: str) -> "Event":
        """Create a new event with correlation ID."""
        return self.model_copy(update={"correlation_id": correlation_id})

    def caused_by(self, causation_id: str) -> "Event":
        """Create a new event with causation ID."""
        return self.model_copy(update={"causation_id": causation_id})


class EventHandler(ABC):
    """Abstract base class for event handlers."""

    @property
    @abstractmethod
    def event_type(self) -> str:
        """The event type this handler processes."""
        pass

    @abstractmethod
    async def handle(self, event: Event) -> None:
        """Handle the event."""
        pass


SyncHandler = Callable[[Event], None]
AsyncHandler = Callable[[Event], Any]  # Returns awaitable


class EventBus:
    """Central event bus for publishing and subscribing to events."""

    def __init__(self) -> None:
        self._sync_handlers: Dict[str, List[SyncHandler]] = defaultdict(list)
        self._async_handlers: Dict[str, List[AsyncHandler]] = defaultdict(list)
        self._middleware: List[Callable[[Event], Any]] = []
        self._outbox: List[Event] = []

    def subscribe_sync(self, event_type: str, handler: SyncHandler) -> None:
        """Subscribe a synchronous handler to an event type."""
        self._sync_handlers[event_type].append(handler)

    def subscribe_async(self, event_type: str, handler: AsyncHandler) -> None:
        """Subscribe an asynchronous handler to an event type."""
        self._async_handlers[event_type].append(handler)

    def subscribe(self, event_type: str, handler: Union[SyncHandler, AsyncHandler]) -> None:
        """Subscribe a handler (auto-detects sync/async)."""
        import inspect
        if inspect.iscoroutinefunction(handler):
            self.subscribe_async(event_type, handler)
        else:
            self.subscribe_sync(event_type, handler)

    def unsubscribe(self, event_type: str, handler: Union[SyncHandler, AsyncHandler]) -> bool:
        """Unsubscribe a handler."""
        removed = False
        if handler in self._sync_handlers[event_type]:
            self._sync_handlers[event_type].remove(handler)
            removed = True
        if handler in self._async_handlers[event_type]:
            self._async_handlers[event_type].remove(handler)
            removed = True
        return removed

    def add_middleware(self, middleware: Callable[[Event], Any]) -> None:
        """Add middleware to process events before handlers."""
        self._middleware.append(middleware)

    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        # Run middleware
        for middleware in self._middleware:
            if asyncio.iscoroutinefunction(middleware):
                await middleware(event)
            else:
                middleware(event)

        # Add to outbox for reliability
        self._outbox.append(event)

        # Execute sync handlers
        for handler in self._sync_handlers.get(event.event_type, []):
            try:
                handler(event)
            except Exception as e:
                # Log error but continue with other handlers
                import logging
                logging.getLogger(__name__).exception(
                    "Sync event handler failed",
                    event_type=event.event_type,
                    handler=handler,
                    error=str(e),
                )

        # Execute async handlers
        async_handlers = self._async_handlers.get(event.event_type, [])
        if async_handlers:
            await asyncio.gather(
                *[handler(event) for handler in async_handlers],
                return_exceptions=True,
            )

    async def publish_async(self, event: Event) -> None:
        """Alias for publish (always async)."""
        await self.publish(event)

    def get_outbox(self) -> List[Event]:
        """Get events in the outbox."""
        return self._outbox.copy()

    def clear_outbox(self) -> None:
        """Clear the outbox."""
        self._outbox.clear()

    def flush_outbox(self) -> List[Event]:
        """Get and clear the outbox."""
        events = self._outbox
        self._outbox = []
        return events


# Global event bus instance
event_bus = EventBus()


def event_handler(event_type: str):
    """Decorator to register an async event handler."""
    def decorator(func: AsyncHandler) -> AsyncHandler:
        event_bus.subscribe_async(event_type, func)
        return func
    return decorator


def sync_event_handler(event_type: str):
    """Decorator to register a sync event handler."""
    def decorator(func: SyncHandler) -> SyncHandler:
        event_bus.subscribe_sync(event_type, func)
        return func
    return decorator


class EventStore:
    """Persistent event store for event sourcing."""

    def __init__(self) -> None:
        self._events: List[Event] = []
        self._snapshots: Dict[str, Any] = {}

    async def append(self, event: Event) -> None:
        """Append an event to the store."""
        self._events.append(event)

    async def get_events(
        self,
        aggregate_id: str,
        from_version: int = 0,
    ) -> List[Event]:
        """Get events for an aggregate."""
        return [
            e for e in self._events
            if e.payload.get("aggregate_id") == aggregate_id
            and e.metadata.get("version", 0) > from_version
        ]

    async def get_all_events(self, from_timestamp: Optional[datetime] = None) -> List[Event]:
        """Get all events, optionally filtered by timestamp."""
        if from_timestamp is None:
            return self._events.copy()
        return [e for e in self._events if e.timestamp >= from_timestamp]

    async def save_snapshot(self, aggregate_id: str, state: Any, version: int) -> None:
        """Save a snapshot of aggregate state."""
        self._snapshots[aggregate_id] = {"state": state, "version": version}

    async def get_snapshot(self, aggregate_id: str) -> Optional[dict]:
        """Get the latest snapshot for an aggregate."""
        return self._snapshots.get(aggregate_id)


# Domain events
class UserCreated(Event):
    """Event fired when a user is created."""
    event_type: str = "user.created"
    payload: Dict[str, Any] = Field(default_factory=lambda: {
        "user_id": "",
        "email": "",
        "roles": [],
    })


class UserUpdated(Event):
    """Event fired when a user is updated."""
    event_type: str = "user.updated"
    payload: Dict[str, Any] = Field(default_factory=lambda: {
        "user_id": "",
        "changes": {},
    })


class UserDeleted(Event):
    """Event fired when a user is deleted."""
    event_type: str = "user.deleted"
    payload: Dict[str, Any] = Field(default_factory=lambda: {
        "user_id": "",
    })


class UserRoleAssigned(Event):
    """Event fired when a role is assigned to a user."""
    event_type: str = "user.role_assigned"
    payload: Dict[str, Any] = Field(default_factory=lambda: {
        "user_id": "",
        "role": "",
    })


class UserRoleRemoved(Event):
    """Event fired when a role is removed from a user."""
    event_type: str = "user.role_removed"
    payload: Dict[str, Any] = Field(default_factory=lambda: {
        "user_id": "",
        "role": "",
    })


class JobStarted(Event):
    """Event fired when a background job starts."""
    event_type: str = "job.started"
    payload: Dict[str, Any] = Field(default_factory=lambda: {
        "job_id": "",
        "job_name": "",
        "args": {},
    })


class JobCompleted(Event):
    """Event fired when a background job completes."""
    event_type: str = "job.completed"
    payload: Dict[str, Any] = Field(default_factory=lambda: {
        "job_id": "",
        "job_name": "",
        "result": {},
    })


class JobFailed(Event):
    """Event fired when a background job fails."""
    event_type: str = "job.failed"
    payload: Dict[str, Any] = Field(default_factory=lambda: {
        "job_id": "",
        "job_name": "",
        "error": "",
    })


# Middleware
async def logging_middleware(event: Event) -> None:
    """Log all events."""
    import logging
    logging.getLogger(__name__).debug(
        "Event published",
        event_id=event.event_id,
        event_type=event.event_type,
        correlation_id=event.correlation_id,
    )


async def metrics_middleware(event: Event) -> None:
    """Record metrics for events."""
    # Could integrate with Prometheus here
    pass


# Register default middleware
event_bus.add_middleware(logging_middleware)
event_bus.add_middleware(metrics_middleware)