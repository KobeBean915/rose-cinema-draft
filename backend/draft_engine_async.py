"""
DRAFT ROOM — Async Engine Adapter
==================================
Wraps the original DraftRoom/IronLogicStepEngine in an async interface
suitable for WebSocket streaming.

DESIGN PRINCIPLE: ZERO modification to iron_logic.py, sparring_benchmarks.py,
or the core algorithmic functions. This adapter only:
  1. Replaces threading primitives with asyncio equivalents
  2. Converts the synchronous generator into an async event emitter
  3. Adds session isolation (no global state)
"""

import asyncio
import json
import uuid
import logging
from typing import Dict, Optional, Any, Callable, Awaitable
from dataclasses import dataclass, field

# Import original modules — UNCHANGED
from iron_logic import (
    IronLogicEngine,
    get_trade_up_probability,
    get_overpay_willingness,
    get_rival_jump_bonus,
    TEAM_AGGRESSION,
    POSITION_DVM,
    PositionTier,
    get_position_dvm,
    get_coaching_tree_boost,
)
from sparring_benchmarks.benchmarks import (
    PROSPECT_CARDS,
    get_war_room_secret,
    get_consensus_top_n,
)
from team_data_2026.teams import (
    DRAFT_ORDER_2026,
    TEAM_NEEDS_2026,
    TEAM_AGGRESSION_2026,
)

# Import original draft room types (minimally modified)
from draft_room_v3 import (
    Prospect,
    DraftState,
    DraftEvent,
    EventType,
    UIHints,
    HapticType,
    UrgencyLevel,
    ValueEngine,
    MakePickCommand,
    generate_id,
)

import random

logger = logging.getLogger("draft_room.engine")


class AsyncInterruptBuffer:
    """
    Replaces the threading-based InterruptBuffer with asyncio primitives.
    
    Original used: threading.RLock, queue.PriorityQueue
    Now uses: asyncio.Lock, sorted list, asyncio.Event
    """
    
    PRIORITIES = {
        "pause": 100,
        "resume": 99,
        "undo": 90,
        "redo": 89,
        "trade_decision": 80,
        "user_trade": 70,
        "force_sync": 50,
    }
    
    def __init__(self):
        self._queue: list = []  # (negative_priority, interrupt_dict)
        self._lock = asyncio.Lock()
        self._is_paused = False
        self._has_items = asyncio.Event()
    
    async def push(self, interrupt_type: str, payload: Optional[Dict] = None) -> None:
        async with self._lock:
            priority = -self.PRIORITIES.get(interrupt_type, 0)
            item = {
                "type": interrupt_type,
                "id": str(uuid.uuid4()),
                "payload": payload or {},
            }
            self._queue.append((priority, item))
            self._queue.sort(key=lambda x: x[0])
            self._has_items.set()
    
    async def pop(self) -> Optional[Dict]:
        async with self._lock:
            if not self._queue:
                self._has_items.clear()
                return None
            _, item = self._queue.pop(0)
            if not self._queue:
                self._has_items.clear()
            return item
    
    async def has_pending(self) -> bool:
        async with self._lock:
            return len(self._queue) > 0
    
    async def pause(self) -> None:
        async with self._lock:
            self._is_paused = True
    
    async def resume(self) -> None:
        async with self._lock:
            self._is_paused = False
    
    @property
    def is_paused(self) -> bool:
        # Note: not perfectly async-safe for reads, but acceptable for boolean flag
        return self._is_paused


class AsyncCommandHistory:
    """
    Replaces ThreadSafeCommandHistory with asyncio.Lock.
    
    Same command pattern, same undo/redo logic, async lock instead of threading.RLock.
    """
    
    def __init__(self, max_history: int = 100):
        self._history: list = []
        self._redo_stack: list = []
        self._lock = asyncio.Lock()
        self._max_history = max_history
        self._sequence = 0
    
    async def execute(self, command: MakePickCommand, state: DraftState) -> Optional[DraftEvent]:
        async with self._lock:
            event = command.execute(state)
            self._history.append(command)
            self._redo_stack.clear()
            if len(self._history) > self._max_history:
                self._history.pop(0)
            self._sequence += 1
            return event
    
    async def undo(self, state: DraftState) -> Optional[DraftEvent]:
        async with self._lock:
            if not self._history:
                return None
            command = self._history.pop()
            command.undo(state)
            self._redo_stack.append(command)
            self._sequence += 1
            return DraftEvent(
                type=EventType.UNDO_COMPLETE,
                sequence_number=self._sequence,
                ui_hints=UIHints.for_interrupt(),
                payload={"undone": command.description()},
                current_pick=state.current_pick,
                current_round=state.get_round(state.current_pick),
                picks_remaining=257 - state.current_pick + 1,
            )
    
    async def redo(self, state: DraftState) -> Optional[DraftEvent]:
        async with self._lock:
            if not self._redo_stack:
                return None
            command = self._redo_stack.pop()
            event = command.execute(state)
            self._history.append(command)
            self._sequence += 1
            return DraftEvent(
                type=EventType.REDO_COMPLETE,
                sequence_number=self._sequence,
                ui_hints=UIHints.for_interrupt(),
                payload={"redone": command.description()},
                current_pick=state.current_pick,
                current_round=state.get_round(state.current_pick),
                picks_remaining=257 - state.current_pick + 1,
            )
    
    def can_undo(self) -> bool:
        return len(self._history) > 0
    
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0
    
    def get_undo_description(self) -> Optional[str]:
        return self._history[-1].description() if self._history else None


class AsyncDraftEngine:
    """
    Async adaptation of IronLogicStepEngine.
    
    WHAT CHANGED from original:
    - threading.RLock → asyncio.Lock (in AsyncCommandHistory, AsyncInterruptBuffer)
    - Generator yield → async event callback
    - yield None (wait) → await asyncio.Event
    - self._user_pick polling → asyncio.Future per user turn
    
    WHAT DID NOT CHANGE:
    - _ai_select_prospect() logic — IDENTICAL
    - _get_recommendations() logic — IDENTICAL
    - _should_ai_propose_trade() logic — IDENTICAL
    - _generate_ai_trade_offer() logic — IDENTICAL
    - ValueEngine — IDENTICAL
    - All Iron Logic calls — IDENTICAL
    """
    
    HEARTBEAT_INTERVAL = 10
    AI_PICK_DELAY = 0.8  # Seconds between AI picks (for drama)
    
    def __init__(self, user_team: str = "NYG"):
        self.user_team = user_team
        
        # Build prospects — SAME as DraftRoom._build_prospects()
        self.prospects_list = self._build_prospects()
        self.prospects = {p.id: p for p in self.prospects_list}
        self.prospects_by_rank = sorted(self.prospects_list, key=lambda p: p.rank)
        
        # Initialize state — SAME as original
        self.state = DraftState(user_team=user_team)
        self.value_engine = ValueEngine()
        self.team_needs = dict(TEAM_NEEDS_2026)  # Use 2026 data
        
        # Iron Logic — UNCHANGED
        self.iron_logic = IronLogicEngine()
        
        # Async replacements for threading primitives
        self.command_history = AsyncCommandHistory()
        self.interrupt_buffer = AsyncInterruptBuffer()
        
        # User interaction — asyncio.Future replaces polling
        self._user_pick_future: Optional[asyncio.Future] = None
        self._trade_decision_future: Optional[asyncio.Future] = None
        
        # Sequence tracking
        self._sequence = 0
        self._picks_since_sync = 0
        
        # Running state
        self._is_running = False
        self._run_task: Optional[asyncio.Task] = None
        
        # Event callback — replaces generator yield
        self._event_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
    
    def _build_prospects(self) -> list:
        """Build prospect list from sparring benchmarks — IDENTICAL to original."""
        prospects = []
        for name, card in PROSPECT_CARDS.items():
            prospects.append(Prospect.from_prospect_card(card))
        prospects.sort(key=lambda p: p.rank)
        return prospects
    
    def _next_sequence(self) -> int:
        self._sequence += 1
        return self._sequence
    
    def _get_available_prospects(self) -> list:
        return [p for p in self.prospects_by_rank if p.id not in self.state.prospects_drafted]
    
    # =========================================================================
    # AI LOGIC — IDENTICAL to original IronLogicStepEngine
    # =========================================================================
    
    def _ai_select_prospect(self, team: str) -> Optional[Prospect]:
        """AI prospect selection — UNCHANGED from draft_room_v3.py."""
        available = self._get_available_prospects()
        if not available:
            return None
        
        needs = self.team_needs.get(team, [])
        scarcity = self.iron_logic.scarcity_tracker.get_scarcity_positions(
            self.state.current_pick
        )
        
        scored_prospects = []
        for prospect in available[:20]:
            evaluation = self.iron_logic.evaluate_prospect_for_team(
                prospect_name=prospect.name,
                prospect_position=prospect.position,
                prospect_rank=prospect.rank,
                team=team,
                team_needs=needs,
            )
            score = evaluation["final_score"]
            if prospect.position in scarcity:
                if prospect.position in needs[:3]:
                    score *= 0.7
            scored_prospects.append((score, prospect))
        
        scored_prospects.sort(key=lambda x: x[0])
        
        roll = random.random()
        if roll < 0.80 and len(scored_prospects) >= 1:
            selection = scored_prospects[0][1]
        elif roll < 0.95 and len(scored_prospects) >= 2:
            selection = scored_prospects[1][1]
        elif len(scored_prospects) >= 3:
            selection = scored_prospects[2][1]
        else:
            selection = scored_prospects[0][1]
        
        self.iron_logic.record_pick(self.state.current_pick, selection.position)
        return selection
    
    def _get_recommendations(self, team: str, count: int = 5) -> list:
        """Get AI recommendations — UNCHANGED from original."""
        available = self._get_available_prospects()
        needs = self.team_needs.get(team, [])
        
        recommendations = []
        for prospect in available[:count]:
            evaluation = self.iron_logic.evaluate_prospect_for_team(
                prospect_name=prospect.name,
                prospect_position=prospect.position,
                prospect_rank=prospect.rank,
                team=team,
                team_needs=needs,
            )
            reasons = []
            if evaluation["fills_need"]:
                reasons.append(f"Fills {prospect.position} need")
            if evaluation["is_hybrid_eraser"]:
                reasons.append("Elite hybrid defender")
            if evaluation["is_generational"]:
                reasons.append("Generational talent")
            if evaluation["dvm"] >= 1.5:
                reasons.append("Premium position value")
            if evaluation["tree_boost"] > 1.0:
                reasons.append("Scheme fit")
            
            reason = "; ".join(reasons) if reasons else "Best available"
            recommendations.append({
                "id": prospect.id,
                "name": prospect.name,
                "position": prospect.position,
                "school": prospect.school,
                "rank": prospect.rank,
                "reason": reason,
                "proComp": prospect.pro_comp,
                "primaryTrait": prospect.primary_trait,
            })
        
        return recommendations
    
    def _should_ai_propose_trade(self, current_team: str) -> bool:
        """Trade probability — UNCHANGED from original."""
        if current_team == self.state.user_team:
            return False
        
        desperation = self.iron_logic.scarcity_tracker.get_desperation_for_team(
            current_team,
            self.team_needs.get(current_team, []),
            self.state.current_pick,
        )
        trade_prob = get_trade_up_probability(current_team, desperation)
        round_num = self.state.get_round(self.state.current_pick)
        trade_prob *= max(0.3, 1.0 - (round_num - 1) * 0.15)
        return random.random() < trade_prob
    
    def _generate_ai_trade_offer(self, ai_team: str) -> Optional[Dict]:
        """Generate trade offer — UNCHANGED logic from original."""
        user_picks = self.state.get_team_picks(self.state.user_team)
        ai_picks = self.state.get_team_picks(ai_team)
        
        user_upcoming = [p for p in user_picks if p > self.state.current_pick]
        if not user_upcoming or not ai_picks:
            return None
        
        target_pick = user_upcoming[0]
        target_value = self.value_engine.get_pick_value(target_pick)
        overpay_mult = get_overpay_willingness(ai_team)
        rival_bonus = get_rival_jump_bonus(ai_team, self.state.user_team)
        overpay_mult += rival_bonus
        
        ai_available = [p for p in ai_picks if p > self.state.current_pick]
        if not ai_available:
            return None
        
        offer_picks = []
        offer_value = 0
        target_offer_value = target_value * overpay_mult
        
        for pick in sorted(ai_available):
            offer_picks.append(pick)
            offer_value += self.value_engine.get_pick_value(pick)
            if offer_value >= target_offer_value or len(offer_picks) >= 3:
                break
        
        if offer_value < target_value * 0.85:
            return None
        
        valuation = self.value_engine.calculate_trade_value(
            offering_picks=offer_picks,
            receiving_picks=[target_pick],
            offering_team=ai_team,
            receiving_team=self.state.user_team,
        )
        
        return {
            "id": generate_id(),
            "offering_team": ai_team,
            "receiving_team": self.state.user_team,
            "offering_picks": offer_picks,
            "receiving_picks": [target_pick],
            "valuation": valuation,
        }
    
    # =========================================================================
    # ASYNC EVENT EMISSION — replaces generator yield
    # =========================================================================
    
    async def _emit(self, event: DraftEvent) -> None:
        """Send event to the WebSocket callback."""
        if self._event_callback:
            await self._event_callback(event.to_swift_dict())
    
    # =========================================================================
    # PUBLIC API — async versions of submit_pick, etc.
    # =========================================================================
    
    def set_event_callback(self, callback: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        """Set the async callback that receives draft events (WebSocket sender)."""
        self._event_callback = callback
    
    async def submit_pick(self, prospect_id: str) -> None:
        """User submits their pick. Resolves the pending future."""
        if self._user_pick_future and not self._user_pick_future.done():
            self._user_pick_future.set_result(prospect_id)
    
    async def submit_trade_decision(self, accept: bool) -> None:
        """User accepts or rejects a trade. Resolves the pending future."""
        if self._trade_decision_future and not self._trade_decision_future.done():
            self._trade_decision_future.set_result(accept)
    
    async def request_undo(self) -> None:
        await self.interrupt_buffer.push("undo")
    
    async def request_redo(self) -> None:
        await self.interrupt_buffer.push("redo")
    
    async def request_pause(self) -> None:
        await self.interrupt_buffer.push("pause")
    
    async def request_resume(self) -> None:
        await self.interrupt_buffer.push("resume")
    
    async def request_sync(self) -> None:
        await self.interrupt_buffer.push("force_sync")
    
    def get_state_snapshot(self) -> Dict[str, Any]:
        return self.state.to_snapshot()
    
    def get_all_prospects(self) -> list:
        """Get all prospects for the Big Board."""
        return [p.to_swift_dict() for p in self.prospects_by_rank]
    
    # =========================================================================
    # MAIN RUN LOOP — async version of IronLogicStepEngine.run()
    # =========================================================================
    
    async def start(self) -> None:
        """Start the draft simulation as an async task."""
        self._is_running = True
        self._run_task = asyncio.create_task(self._run())
    
    async def stop(self) -> None:
        """Stop the draft simulation."""
        self._is_running = False
        if self._run_task:
            self._run_task.cancel()
            try:
                await self._run_task
            except asyncio.CancelledError:
                pass
    
    async def _process_interrupts(self) -> None:
        """Process pending interrupts — async version."""
        while await self.interrupt_buffer.has_pending():
            interrupt = await self.interrupt_buffer.pop()
            if not interrupt:
                break
            
            itype = interrupt["type"]
            
            if itype == "undo":
                event = await self.command_history.undo(self.state)
                if event:
                    await self._emit(event)
            elif itype == "redo":
                event = await self.command_history.redo(self.state)
                if event:
                    await self._emit(event)
            elif itype == "pause":
                await self.interrupt_buffer.pause()
                await self._emit(DraftEvent(
                    type=EventType.INTERRUPT_ACK,
                    sequence_number=self._next_sequence(),
                    ui_hints=UIHints.for_interrupt(),
                    payload={"action": "paused"},
                    current_pick=self.state.current_pick,
                    current_round=self.state.get_round(self.state.current_pick),
                    picks_remaining=257 - self.state.current_pick + 1,
                ))
            elif itype == "resume":
                await self.interrupt_buffer.resume()
                await self._emit(DraftEvent(
                    type=EventType.INTERRUPT_ACK,
                    sequence_number=self._next_sequence(),
                    ui_hints=UIHints.for_interrupt(),
                    payload={"action": "resumed"},
                    current_pick=self.state.current_pick,
                    current_round=self.state.get_round(self.state.current_pick),
                    picks_remaining=257 - self.state.current_pick + 1,
                ))
            elif itype == "force_sync":
                await self._emit_sync("forced")
    
    async def _emit_sync(self, reason: str = "heartbeat") -> None:
        """Emit state sync event."""
        self._picks_since_sync = 0
        await self._emit(DraftEvent(
            type=EventType.SYNC_STATE,
            sequence_number=self._next_sequence(),
            ui_hints=UIHints.for_sync_state(),
            payload={
                "reason": reason,
                "snapshot": self.state.to_snapshot(),
                "can_undo": self.command_history.can_undo(),
                "can_redo": self.command_history.can_redo(),
                "undo_description": self.command_history.get_undo_description(),
            },
            current_pick=self.state.current_pick,
            current_round=self.state.get_round(self.state.current_pick),
            picks_remaining=257 - self.state.current_pick + 1,
        ))
    
    async def _run(self) -> None:
        """
        Main draft simulation loop — async version of IronLogicStepEngine.run().
        
        Structure is IDENTICAL to the original generator, but:
        - `yield event` → `await self._emit(event)`
        - `yield None` (wait) → `await asyncio.sleep(0.05)` or `await future`
        - Polling loops → asyncio.Future resolution
        """
        # Draft start
        await self._emit(DraftEvent(
            type=EventType.DRAFT_START,
            sequence_number=self._next_sequence(),
            ui_hints=UIHints(haptic=HapticType.HEAVY, urgency=UrgencyLevel.HIGH),
            payload={
                "user_team": self.state.user_team,
                "prospects": self.get_all_prospects(),
                "team_needs": self.team_needs,
            },
            current_pick=1,
            current_round=1,
            picks_remaining=257,
        ))
        
        current_round = 1
        
        while self.state.current_pick <= 257 and self._is_running:
            # Process interrupts
            await self._process_interrupts()
            
            # Wait while paused
            while self.interrupt_buffer.is_paused and self._is_running:
                await self._process_interrupts()
                await asyncio.sleep(0.1)
            
            if not self._is_running:
                break
            
            # Heartbeat sync
            if self._picks_since_sync >= self.HEARTBEAT_INTERVAL:
                await self._emit_sync()
            
            # Round transition
            new_round = self.state.get_round(self.state.current_pick)
            if new_round != current_round:
                await self._emit(DraftEvent(
                    type=EventType.ROUND_END,
                    sequence_number=self._next_sequence(),
                    ui_hints=UIHints(haptic=HapticType.SUCCESS, urgency=UrgencyLevel.HIGH, confetti=True),
                    payload={"round": current_round},
                    current_pick=self.state.current_pick,
                    current_round=new_round,
                    picks_remaining=257 - self.state.current_pick + 1,
                ))
                current_round = new_round
                await self._emit(DraftEvent(
                    type=EventType.ROUND_START,
                    sequence_number=self._next_sequence(),
                    ui_hints=UIHints(haptic=HapticType.MEDIUM, urgency=UrgencyLevel.MEDIUM),
                    payload={"round": current_round},
                    current_pick=self.state.current_pick,
                    current_round=current_round,
                    picks_remaining=257 - self.state.current_pick + 1,
                ))
            
            # Get current team
            current_team = self.state.pick_ownership.get(self.state.current_pick, "UNK")
            
            # Check for AI trade attempt
            if self._should_ai_propose_trade(current_team):
                offer = self._generate_ai_trade_offer(current_team)
                if offer:
                    fairness = offer["valuation"].get("fairness_category", "fair")
                    
                    await self._emit(DraftEvent(
                        type=EventType.TRADE_OFFER,
                        sequence_number=self._next_sequence(),
                        ui_hints=UIHints.for_trade_offer(fairness),
                        payload={
                            "offer_id": offer["id"],
                            "from_team": offer["offering_team"],
                            "to_team": offer["receiving_team"],
                            "you_receive": offer["offering_picks"],
                            "you_give": offer["receiving_picks"],
                            "valuation": offer["valuation"],
                        },
                        current_pick=self.state.current_pick,
                        current_round=current_round,
                        picks_remaining=257 - self.state.current_pick + 1,
                        requires_ack=True,
                    ))
                    
                    # Wait for trade decision via Future
                    self._trade_decision_future = asyncio.get_event_loop().create_future()
                    try:
                        accepted = await asyncio.wait_for(self._trade_decision_future, timeout=60.0)
                    except asyncio.TimeoutError:
                        accepted = False
                    
                    if accepted:
                        for give_pick in offer["receiving_picks"]:
                            self.state.pick_ownership[give_pick] = offer["offering_team"]
                        for recv_pick in offer["offering_picks"]:
                            self.state.pick_ownership[recv_pick] = offer["receiving_team"]
                        
                        self.state.trades.append({
                            "pick": self.state.current_pick,
                            "from": offer["offering_team"],
                            "to": offer["receiving_team"],
                            "sent": offer["offering_picks"],
                            "received": offer["receiving_picks"],
                        })
                        
                        await self._emit(DraftEvent(
                            type=EventType.TRADE_ACCEPTED,
                            sequence_number=self._next_sequence(),
                            ui_hints=UIHints.for_trade_offer("steal"),
                            payload={"offer_id": offer["id"]},
                            current_pick=self.state.current_pick,
                            current_round=current_round,
                            picks_remaining=257 - self.state.current_pick + 1,
                        ))
                    else:
                        await self._emit(DraftEvent(
                            type=EventType.TRADE_REJECTED,
                            sequence_number=self._next_sequence(),
                            ui_hints=UIHints(haptic=HapticType.LIGHT),
                            payload={"offer_id": offer["id"]},
                            current_pick=self.state.current_pick,
                            current_round=current_round,
                            picks_remaining=257 - self.state.current_pick + 1,
                        ))
                    continue
            
            # USER TURN or AI TURN
            if current_team == self.state.user_team:
                recommendations = self._get_recommendations(current_team)
                
                await self._emit(DraftEvent(
                    type=EventType.USER_TURN,
                    sequence_number=self._next_sequence(),
                    ui_hints=UIHints.for_user_pick(),
                    payload={
                        "pick": self.state.current_pick,
                        "team": current_team,
                        "recommendations": recommendations,
                        "available_count": len(self._get_available_prospects()),
                    },
                    current_pick=self.state.current_pick,
                    current_round=current_round,
                    picks_remaining=257 - self.state.current_pick + 1,
                    requires_ack=True,
                ))
                
                # Wait for user pick via Future (replaces polling)
                self._user_pick_future = asyncio.get_event_loop().create_future()
                try:
                    prospect_id = await asyncio.wait_for(self._user_pick_future, timeout=300.0)
                except asyncio.TimeoutError:
                    # Auto-pick best available
                    available = self._get_available_prospects()
                    prospect_id = available[0].id if available else None
                
                if prospect_id and prospect_id in self.prospects:
                    prospect = self.prospects[prospect_id]
                    command = MakePickCommand(
                        pick_number=self.state.current_pick,
                        team=current_team,
                        prospect=prospect,
                        sequence_getter=self._next_sequence,
                    )
                    event = await self.command_history.execute(command, self.state)
                    if event:
                        event.ui_hints = UIHints.for_user_pick()
                        event.ui_hints.confetti = True
                        await self._emit(event)
                    
                    self.iron_logic.record_pick(self.state.current_pick - 1, prospect.position)
                    self._picks_since_sync += 1
            else:
                # AI TURN — add delay for drama/realism
                await asyncio.sleep(self.AI_PICK_DELAY)
                
                prospect = self._ai_select_prospect(current_team)
                if prospect:
                    command = MakePickCommand(
                        pick_number=self.state.current_pick,
                        team=current_team,
                        prospect=prospect,
                        sequence_getter=self._next_sequence,
                    )
                    event = await self.command_history.execute(command, self.state)
                    if event:
                        await self._emit(event)
                    self._picks_since_sync += 1
        
        # Draft complete
        await self._emit(DraftEvent(
            type=EventType.DRAFT_COMPLETE,
            sequence_number=self._next_sequence(),
            ui_hints=UIHints(haptic=HapticType.SUCCESS, urgency=UrgencyLevel.CRITICAL, confetti=True),
            payload={
                "total_picks": len(self.state.draft_history),
                "total_trades": len(self.state.trades),
                "user_roster": [
                    h for h in self.state.draft_history
                    if h["team"] == self.state.user_team
                ],
            },
            current_pick=257,
            current_round=7,
            picks_remaining=0,
        ))
