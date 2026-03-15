"""
Lightweight in-process Pub/Sub event bus for decoupled notifications.
"""

import asyncio
import logging
from typing import Any, Callable, Coroutine, Dict, List

logger = logging.getLogger(__name__)

# Type alias for async event handlers
EventHandler = Callable[..., Coroutine[Any, Any, None]]


class EventBus:
    """Simple async event bus using the observer pattern."""

    def __init__(self):
        self._subscribers: Dict[str, List[EventHandler]] = {}

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        """Register a handler for a given event name."""
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(handler)
        logger.info(f"[EVENT_BUS] Subscribed {handler.__name__} to '{event_name}'")

    async def publish(self, event_name: str, **kwargs) -> None:
        """
        Publish an event. All registered handlers are called concurrently.
        Errors in individual handlers are logged but do not block others.
        """
        handlers = self._subscribers.get(event_name, [])
        if not handlers:
            logger.debug(f"[EVENT_BUS] No subscribers for '{event_name}'")
            return

        logger.info(f"[EVENT_BUS] Publishing '{event_name}' to {len(handlers)} handler(s)")
        tasks = [self._safe_call(handler, event_name, **kwargs) for handler in handlers]
        await asyncio.gather(*tasks)

    async def _safe_call(self, handler: EventHandler, event_name: str, **kwargs) -> None:
        """Call a handler and catch any exceptions so one failure doesn't block others."""
        try:
            await handler(**kwargs)
        except Exception as e:
            logger.error(
                f"[EVENT_BUS] Handler {handler.__name__} failed for '{event_name}': {e}",
                exc_info=True,
            )


# Global singleton
event_bus = EventBus()


# ── Event name constants ─────────────────────────────────────────────
USER_REGISTERED = "user_registered"
ADMIN_ACTION_COMPLETED = "admin_action_completed"
