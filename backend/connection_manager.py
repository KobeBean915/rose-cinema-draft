"""
DRAFT ROOM — Connection Manager (v2: Session-Persistent)
=========================================================
Multi-session WebSocket management with engine-aware session state.

Changes from v1:
  - SessionState now OWNS the AsyncDraftEngine instance
  - event_buffer uses OrderedDict for O(1) ordered iteration
  - replay_or_sync: attempts buffer replay, falls back to full sync
  - asyncio.Lock per session (not just on the manager) to prevent
    race conditions during simultaneous reconnect + engine emit
  - Engine callback wired at session creation, survives reconnects
"""

import asyncio
import logging
from collections import OrderedDict
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("draft_room.connections")


# =============================================================================
# SESSION STATE — Engine-Aware, Buffer-Backed
# =============================================================================

@dataclass
class SessionState:
    """
    Tracks a single draft session's connection, engine, and event history.

    The engine instance lives HERE, not in a separate dict. This ensures:
      1. Reconnection reuses the same engine (no state loss)
      2. Engine cleanup happens when the session is garbage-collected
      3. Event buffer and engine are always in sync
    """
    session_id: str
    user_team: str
    websocket: Optional[WebSocket] = None
    is_connected: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)

    # Engine reference — None until first "start" command
    engine: Any = None  # AsyncDraftEngine (avoid circular import at module level)
    engine_started: bool = False

    # Per-session lock: guards websocket swap during reconnect
    # while the engine's _emit callback may be firing concurrently.
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    # ── Event Buffer ──────────────────────────────────────────────
    # OrderedDict keyed by sequence_number → DraftEvent dict.
    # Insertion order = sequence order (monotonically increasing).
    BUFFER_MAX: int = 100
    event_buffer: OrderedDict = field(default_factory=OrderedDict)
    last_sequence: int = 0

    @property
    def buffer_floor(self) -> int:
        """Lowest sequence number still in buffer, or last_sequence+1 if empty."""
        if self.event_buffer:
            return next(iter(self.event_buffer))
        return self.last_sequence + 1

    def buffer_event(self, event: Dict[str, Any]) -> None:
        """
        Store an event in the rolling buffer.

        Called by the engine's event callback on every emission —
        BEFORE the event is sent over the wire. This guarantees
        even if the WebSocket send fails, the event is captured
        for replay on reconnect.
        """
        seq = event.get("sequenceNumber", 0)
        if seq <= 0:
            return

        self.event_buffer[seq] = event
        self.last_sequence = max(self.last_sequence, seq)

        # Evict oldest entries beyond rolling window
        while len(self.event_buffer) > self.BUFFER_MAX:
            self.event_buffer.popitem(last=False)

    def get_events_since(self, since_sequence: int) -> List[Dict[str, Any]]:
        """
        Get all buffered events with sequence_number > since_sequence.
        Returns in ascending order (guaranteed by OrderedDict insertion order).
        """
        return [
            ev for seq, ev in self.event_buffer.items()
            if seq > since_sequence
        ]

    def can_replay_from(self, since_sequence: int) -> bool:
        """
        Check if the buffer covers the requested resume point.

        True if:
          - since_sequence >= buffer_floor - 1 (we have everything after it)
          - OR since_sequence >= last_sequence (client is fully caught up)

        False if:
          - since_sequence < buffer_floor - 1 (events were evicted, gap exists)
        """
        if since_sequence >= self.last_sequence:
            return True  # Already caught up
        return since_sequence >= self.buffer_floor - 1


# =============================================================================
# CONNECTION MANAGER
# =============================================================================

class ConnectionManager:
    """
    Manages WebSocket connections across multiple draft sessions.

    v2 changes:
      - Engine lifecycle integrated into session (not separate dict)
      - replay_or_sync: intelligent resume with buffer-or-full-sync fallback
      - send_event buffers BEFORE sending (crash-safe ordering)
      - Per-session lock prevents reconnect/emit race conditions
    """

    SESSION_TIMEOUT = timedelta(minutes=30)

    def __init__(self):
        self._sessions: Dict[str, SessionState] = {}
        self._lock = asyncio.Lock()  # Guards _sessions dict mutations
        self._cleanup_task: Optional[asyncio.Task] = None

    # ─── Lifecycle ─────────────────────────────────────────────────

    async def start(self) -> None:
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("ConnectionManager started")

    async def shutdown(self) -> None:
        if self._cleanup_task:
            self._cleanup_task.cancel()

        async with self._lock:
            for session in self._sessions.values():
                if session.engine and session.engine_started:
                    try:
                        await session.engine.stop()
                    except Exception:
                        pass
                if session.websocket and session.is_connected:
                    try:
                        await session.websocket.close(code=1001, reason="Server shutdown")
                    except Exception:
                        pass
            self._sessions.clear()

        logger.info("ConnectionManager shutdown complete")

    # ─── Connect / Disconnect ──────────────────────────────────────

    async def connect(
        self,
        websocket: WebSocket,
        session_id: str,
        user_team: str = "NYG",
    ) -> SessionState:
        """
        Register a WebSocket connection for a session.

        Reconnection: preserves engine, buffer, all state. Swaps socket.
        New session: creates SessionState (engine=None until "start").
        """
        await websocket.accept()

        async with self._lock:
            if session_id in self._sessions:
                session = self._sessions[session_id]

                # Swap socket under session lock to prevent
                # engine _emit from sending to old socket
                async with session._lock:
                    if session.websocket and session.is_connected:
                        try:
                            await session.websocket.close(
                                code=1000, reason="Replaced by new connection"
                            )
                        except Exception:
                            pass

                    session.websocket = websocket
                    session.is_connected = True
                    session.last_activity = datetime.utcnow()

                logger.info(
                    f"Session {session_id} reconnected "
                    f"(last_seq={session.last_sequence}, "
                    f"engine_running={session.engine_started})"
                )
            else:
                session = SessionState(
                    session_id=session_id,
                    user_team=user_team,
                    websocket=websocket,
                    is_connected=True,
                )
                self._sessions[session_id] = session
                logger.info(f"Session {session_id} connected (team={user_team})")

        return session

    async def disconnect(self, session_id: str) -> None:
        """
        Mark session as disconnected. Preserve engine + buffer for reconnect.
        The engine keeps running — AI picks accumulate in the buffer.
        """
        session = self._sessions.get(session_id)
        if not session:
            return

        async with session._lock:
            session.is_connected = False
            session.websocket = None

        logger.info(f"Session {session_id} disconnected (engine preserved)")

    # ─── Event Emission ────────────────────────────────────────────

    async def send_event(self, session_id: str, event: Dict[str, Any]) -> bool:
        """
        Buffer + send a draft event to a session's WebSocket.

        CRITICAL ORDER: buffer FIRST, send SECOND.
        If the send fails, the event is still in the buffer for replay.
        """
        session = self._sessions.get(session_id)
        if not session:
            return False

        # Buffer and grab socket ref under lock
        async with session._lock:
            session.buffer_event(event)
            session.last_activity = datetime.utcnow()
            ws = session.websocket
            connected = session.is_connected

        # Send outside session lock (I/O can be slow)
        if ws and connected:
            try:
                await ws.send_json(event)
                return True
            except (WebSocketDisconnect, RuntimeError, ConnectionError) as e:
                logger.debug(f"Send failed for {session_id}: {e}")
                await self.disconnect(session_id)
                return False

        return False

    # ─── Resume: Replay or Full Sync ──────────────────────────────

    async def replay_or_sync(
        self,
        session_id: str,
        since_sequence: int,
    ) -> Dict[str, Any]:
        """
        Intelligent resume handler.

        1. Buffer covers the gap → replay buffered events in order
        2. Buffer evicted past that point → trigger engine full sync
        3. Client already caught up → no-op

        Returns { "method": "replay"|"sync"|"none", "count": int }
        """
        session = self._sessions.get(session_id)
        if not session:
            return {"method": "none", "count": 0}

        async with session._lock:
            can_replay = session.can_replay_from(since_sequence)
            events = session.get_events_since(since_sequence) if can_replay else []
            ws = session.websocket
            connected = session.is_connected

        if not ws or not connected:
            return {"method": "none", "count": 0}

        if can_replay and events:
            count = 0
            for event in events:
                try:
                    await ws.send_json(event)
                    count += 1
                except (WebSocketDisconnect, RuntimeError):
                    await self.disconnect(session_id)
                    break

            logger.info(
                f"Replayed {count}/{len(events)} events to {session_id} "
                f"(since seq {since_sequence})"
            )
            return {"method": "replay", "count": count}

        elif can_replay and not events:
            logger.debug(f"Session {session_id} caught up (seq {since_sequence})")
            return {"method": "replay", "count": 0}

        else:
            # Buffer miss — fall back to engine full sync
            if session.engine and session.engine_started:
                await session.engine.request_sync()
                logger.info(
                    f"Buffer miss for {session_id}: "
                    f"requested seq {since_sequence}, floor {session.buffer_floor}. "
                    f"Triggered full sync."
                )
                return {"method": "sync", "count": 0}
            else:
                logger.warning(
                    f"Buffer miss for {session_id} but engine not running"
                )
                return {"method": "none", "count": 0}

    # ─── Message Receiving ─────────────────────────────────────────

    async def receive_message(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Receive a JSON message from a session's WebSocket."""
        session = self._sessions.get(session_id)
        if not session:
            return None

        async with session._lock:
            ws = session.websocket
            connected = session.is_connected

        if not ws or not connected:
            return None

        try:
            data = await ws.receive_json()
            async with session._lock:
                session.last_activity = datetime.utcnow()
            return data
        except (WebSocketDisconnect, RuntimeError):
            await self.disconnect(session_id)
            return None

    # ─── Session Access ────────────────────────────────────────────

    def get_session(self, session_id: str) -> Optional[SessionState]:
        return self._sessions.get(session_id)

    def is_connected(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        return session.is_connected if session else False

    # ─── Session Removal ───────────────────────────────────────────

    async def remove_session(self, session_id: str) -> None:
        """Permanently remove a session: stop engine, close socket, free memory."""
        async with self._lock:
            session = self._sessions.pop(session_id, None)

        if not session:
            return

        if session.engine and session.engine_started:
            try:
                await session.engine.stop()
            except Exception as e:
                logger.error(f"Error stopping engine for {session_id}: {e}")

        if session.websocket and session.is_connected:
            try:
                await session.websocket.close(code=1000)
            except Exception:
                pass

        logger.info(f"Session {session_id} removed (engine stopped, buffer cleared)")

    # ─── Stale Session Cleanup ─────────────────────────────────────

    async def _cleanup_loop(self) -> None:
        while True:
            try:
                await asyncio.sleep(300)
                await self._cleanup_stale_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    async def _cleanup_stale_sessions(self) -> None:
        now = datetime.utcnow()
        stale_ids = []

        async with self._lock:
            for sid, session in self._sessions.items():
                if not session.is_connected:
                    if (now - session.last_activity) > self.SESSION_TIMEOUT:
                        stale_ids.append(sid)

        for sid in stale_ids:
            await self.remove_session(sid)
            logger.info(f"Cleaned up stale session {sid}")


# Singleton
manager = ConnectionManager()
