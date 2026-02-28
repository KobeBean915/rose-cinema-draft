"""
DRAFT ROOM — FastAPI Server (v2: Session-Persistent)
=====================================================
WebSocket-driven draft simulation with REST endpoints for static data.

Changes from v1:
  - Engine lives in SessionState, not a separate dict
  - Command routing with structured error propagation → ERROR events
  - resume_from handshake uses replay_or_sync (buffer → full sync fallback)
  - Engine auto-starts on first "start" or reattaches on reconnect
  - All engine calls wrapped in try/except → client gets shake animation

Endpoints:
  WS  /ws/draft/{session_id}?team={team}  — Live draft simulation
  GET /api/prospects                        — Full prospect list
  GET /api/prospects/{rank}                 — Single prospect by rank
  GET /api/team-needs                       — All team needs
  GET /api/team-needs/{team}                — Single team's needs
  GET /api/draft-order                      — 2026 draft order
  GET /api/health                           — Health check
"""

import asyncio
import json
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Optional, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from connection_manager import ConnectionManager, SessionState, manager
from draft_engine_async import AsyncDraftEngine

# Import original data modules — UNCHANGED
from sparring_benchmarks.benchmarks import (
    PROSPECT_CARDS,
    get_prospect_by_rank,
    get_consensus_top_n,
    get_prospects_by_position,
)
from team_data_2026.teams import (
    DRAFT_ORDER_2026,
    TEAM_NEEDS_2026,
    TEAM_AGGRESSION_2026,
)
from iron_logic import TEAM_AGGRESSION, TEAM_COACHING_TREE

# Import original types for ERROR event construction
from draft_room_v3 import (
    DraftEvent,
    EventType,
    UIHints,
    HapticType,
    UrgencyLevel,
    generate_id,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("draft_room.api")


# =============================================================================
# APPLICATION LIFECYCLE
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    await manager.start()
    logger.info("Draft Room API started")
    yield
    await manager.shutdown()
    logger.info("Draft Room API shutdown complete")


app = FastAPI(
    title="Draft Room API",
    description="NFL Draft Simulation Engine — Iron Logic AI",
    version="3.0.0",
    lifespan=lifespan,
)

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# ENGINE FACTORY — Creates and wires an engine to a session
# =============================================================================

async def create_engine_for_session(session: SessionState) -> AsyncDraftEngine:
    """
    Create an AsyncDraftEngine and wire its event callback to the session.

    The callback closure captures session_id, not the WebSocket reference.
    This means the callback survives reconnections — it always routes
    through manager.send_event, which checks the current socket.
    """
    engine = AsyncDraftEngine(user_team=session.user_team)
    session_id = session.session_id

    async def send_event_callback(event: Dict[str, Any], sid=session_id):
        await manager.send_event(sid, event)

    engine.set_event_callback(send_event_callback)
    session.engine = engine
    return engine


def build_error_event(
    message: str,
    engine: Optional[AsyncDraftEngine] = None,
    prospect_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build an ERROR DraftEvent dict for sending to the client.

    Includes prospect_id so the frontend can trigger the shake
    animation on the specific optimistic pick that was rejected.
    """
    current_pick = engine.state.current_pick if engine else 1
    current_round = engine.state.get_round(current_pick) if engine else 1
    picks_remaining = 257 - current_pick + 1 if engine else 257
    seq = engine._next_sequence() if engine else 0

    event = DraftEvent(
        type=EventType.ERROR,
        sequence_number=seq,
        ui_hints=UIHints(
            haptic=HapticType.ERROR,
            urgency=UrgencyLevel.HIGH,
            shake_animation=True,
        ),
        payload={
            "message": message,
            "prospect_id": prospect_id,
        },
        current_pick=current_pick,
        current_round=current_round,
        picks_remaining=picks_remaining,
    )
    return event.to_swift_dict()


# =============================================================================
# COMMAND ROUTER — Maps client actions to engine methods
# =============================================================================

async def route_command(
    session: SessionState,
    action: str,
    message: Dict[str, Any],
    websocket: WebSocket,
) -> None:
    """
    Route an incoming client command to the appropriate engine method.

    All engine calls are wrapped in try/except. Exceptions produce
    ERROR events that propagate to the frontend (triggering shake
    animation and rollback via the Zustand store's error handler).
    """
    engine = session.engine

    # ── start ────────────────────────────────────────────────────
    if action == "start":
        if session.engine_started and engine:
            # Engine already running — send a sync instead of restarting
            await engine.request_sync()
            logger.info(f"Session {session.session_id}: engine already running, sent sync")
            return

        # Create and start a new engine
        engine = await create_engine_for_session(session)
        session.engine_started = True
        await engine.start()
        logger.info(f"Session {session.session_id}: engine started (team={session.user_team})")
        return

    # ── All other commands require a running engine ──────────────
    if not engine or not session.engine_started:
        error = build_error_event("Engine not started. Send 'start' first.")
        try:
            await websocket.send_json(error)
        except Exception:
            pass
        return

    try:
        # ── pick ─────────────────────────────────────────────────
        if action == "pick":
            prospect_id = message.get("prospect_id", "")
            if not prospect_id:
                error = build_error_event("Missing prospect_id", engine)
                await websocket.send_json(error)
                return

            # Validate the prospect exists and hasn't been drafted
            if prospect_id not in engine.prospects:
                error = build_error_event(
                    f"Unknown prospect: {prospect_id}",
                    engine,
                    prospect_id=prospect_id,
                )
                await websocket.send_json(error)
                return

            if prospect_id in engine.state.prospects_drafted:
                error = build_error_event(
                    f"Prospect already drafted: {engine.prospects[prospect_id].name}",
                    engine,
                    prospect_id=prospect_id,
                )
                await websocket.send_json(error)
                return

            await engine.submit_pick(prospect_id)

        # ── accept_trade ─────────────────────────────────────────
        elif action == "accept_trade":
            await engine.submit_trade_decision(True)

        # ── reject_trade ─────────────────────────────────────────
        elif action == "reject_trade":
            await engine.submit_trade_decision(False)

        # ── undo ─────────────────────────────────────────────────
        elif action == "undo":
            await engine.request_undo()

        # ── redo ─────────────────────────────────────────────────
        elif action == "redo":
            await engine.request_redo()

        # ── pause ────────────────────────────────────────────────
        elif action == "pause":
            await engine.request_pause()

        # ── resume ───────────────────────────────────────────────
        elif action == "resume":
            await engine.request_resume()

        # ── sync (Layer 3 truth request) ─────────────────────────
        elif action == "sync":
            await engine.request_sync()

        # ── resume_from (reconnection handshake) ─────────────────
        elif action == "resume_from":
            last_seq = message.get("last_sequence", 0)
            result = await manager.replay_or_sync(
                session.session_id, last_seq
            )
            logger.info(
                f"Session {session.session_id}: resume_from(seq={last_seq}) "
                f"→ {result['method']} ({result['count']} events)"
            )

        # ── unknown ──────────────────────────────────────────────
        else:
            await websocket.send_json({
                "error": f"Unknown action: {action}",
                "valid_actions": [
                    "start", "pick", "accept_trade", "reject_trade",
                    "undo", "redo", "pause", "resume", "sync", "resume_from",
                ],
            })

    except asyncio.CancelledError:
        raise  # Don't catch task cancellation

    except Exception as e:
        # Catch-all: any engine exception becomes an ERROR event
        # with enough context for the frontend to roll back.
        prospect_id = message.get("prospect_id")
        logger.error(
            f"Session {session.session_id}: command '{action}' failed: {e}",
            exc_info=True,
        )
        error = build_error_event(
            f"Command failed: {str(e)}",
            engine,
            prospect_id=prospect_id,
        )
        try:
            await websocket.send_json(error)
        except Exception:
            pass


# =============================================================================
# WEBSOCKET ENDPOINT
# =============================================================================

@app.websocket("/ws/draft/{session_id}")
async def websocket_draft(
    websocket: WebSocket,
    session_id: str,
    team: str = Query(default="NYG"),
):
    """
    WebSocket endpoint for live draft simulation.

    Protocol:
      Client → Server (JSON):
        { "action": "start" }
        { "action": "pick", "prospect_id": "uuid" }
        { "action": "accept_trade" }
        { "action": "reject_trade" }
        { "action": "undo" }
        { "action": "redo" }
        { "action": "pause" }
        { "action": "resume" }
        { "action": "sync" }
        { "action": "resume_from", "last_sequence": 42 }

      Server → Client (JSON):
        DraftEvent objects (same schema as to_swift_dict())
    """
    # Connect — preserves existing session if reconnecting
    session = await manager.connect(websocket, session_id, user_team=team)

    logger.info(f"WS connected: session={session_id}, team={team}")

    try:
        while True:
            message = await manager.receive_message(session_id)
            if message is None:
                break

            action = message.get("action", "")
            await route_command(session, action, message, websocket)

    except WebSocketDisconnect:
        logger.info(f"WS disconnected: session={session_id}")
    except Exception as e:
        logger.error(f"WS error: session={session_id}, error={e}", exc_info=True)
    finally:
        await manager.disconnect(session_id)
        # NOTE: Engine keeps running. Client can reconnect and resume.
        # Session cleanup happens via the stale session reaper (30 min timeout).


# =============================================================================
# REST — STATIC DATA ENDPOINTS (UNCHANGED)
# =============================================================================

@app.get("/api/prospects")
async def get_prospects(
    position: Optional[str] = None,
    top_n: int = 32,
):
    """Get prospect list, optionally filtered by position."""
    if position:
        cards = get_prospects_by_position(position.upper())
    else:
        cards = get_consensus_top_n(top_n)

    return [
        {
            "id": getattr(c, "id", None) or f"p{c.consensus_rank}",
            "name": c.name,
            "position": c.position,
            "school": c.school,
            "tier": c.tier,
            "rank": c.consensus_rank,
            "consensusRank": c.consensus_rank,
            "height": c.height,
            "weight": c.weight,
            "fortyTime": c.forty_time,
            "primaryTrait": c.primary_trait,
            "proComp": c.pro_comp,
            "systemFit": c.system_fit,
            "isHybridEraser": c.is_hybrid_eraser,
            "isGenerational": c.is_generational,
            "warRoomSecret": c.war_room_secret,
            "measurables": {
                "fortyTime": c.forty_time,
                "height": c.height,
                "weight": c.weight,
            },
        }
        for c in cards
    ]


@app.get("/api/prospects/{rank}")
async def get_prospect(rank: int):
    """Get a single prospect by consensus rank."""
    card = get_prospect_by_rank(rank)
    if not card:
        raise HTTPException(status_code=404, detail=f"No prospect at rank {rank}")

    return {
        "id": getattr(card, "id", None) or f"p{card.consensus_rank}",
        "name": card.name,
        "position": card.position,
        "school": card.school,
        "tier": card.tier,
        "rank": card.consensus_rank,
        "consensusRank": card.consensus_rank,
        "height": card.height,
        "weight": card.weight,
        "fortyTime": card.forty_time,
        "primaryTrait": card.primary_trait,
        "proComp": card.pro_comp,
        "systemFit": card.system_fit,
        "isHybridEraser": card.is_hybrid_eraser,
        "isGenerational": card.is_generational,
        "warRoomSecret": card.war_room_secret,
        "measurables": {
            "fortyTime": card.forty_time,
            "height": card.height,
            "weight": card.weight,
        },
    }


@app.get("/api/team-needs")
async def get_all_team_needs():
    """Get all team needs for 2026."""
    return TEAM_NEEDS_2026


@app.get("/api/team-needs/{team}")
async def get_team_needs(team: str):
    """Get needs for a specific team."""
    team_upper = team.upper()
    needs = TEAM_NEEDS_2026.get(team_upper)
    if needs is None:
        raise HTTPException(status_code=404, detail=f"Unknown team: {team_upper}")

    return {
        "team": team_upper,
        "needs": needs,
        "aggression": TEAM_AGGRESSION_2026.get(team_upper, 5.0),
        "coachingTree": TEAM_COACHING_TREE.get(team_upper, "default"),
    }


@app.get("/api/draft-order")
async def get_draft_order():
    """Get 2026 first-round draft order."""
    return {
        "round1": DRAFT_ORDER_2026,
        "total_picks": 257,
        "rounds": 7,
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    active_sessions = sum(
        1 for s in manager._sessions.values() if s.engine_started
    )
    connected_sessions = sum(
        1 for s in manager._sessions.values() if s.is_connected
    )
    return {
        "status": "healthy",
        "engine": "Iron Logic v3.0",
        "prospects_loaded": len(PROSPECT_CARDS),
        "teams_loaded": len(TEAM_NEEDS_2026),
        "active_sessions": active_sessions,
        "connected_sessions": connected_sessions,
    }
