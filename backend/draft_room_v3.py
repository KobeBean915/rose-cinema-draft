"""
THE DRAFT ROOM - Production Engine v3.0
=======================================
Complete integration of Iron Logic AI system:
- Team Aggression for trade probability
- Dynamic Value Multipliers for position evaluation
- Coaching Tree scheme fit
- Scarcity Momentum for panic picks
- War Room Secrets for narrative

Designed for Apple-grade SwiftUI integration.
"""

from __future__ import annotations
import uuid
import json
import math
import threading
import queue
import random
from enum import Enum, auto
from dataclasses import dataclass, field, asdict
from typing import (
    List, Dict, Optional, Tuple, Generator, Any, 
    Callable, Set, Union
)
from datetime import datetime
from contextlib import contextmanager
import copy

# Import Iron Logic components
from iron_logic import (
    TEAM_AGGRESSION, AggressionTier, get_aggression_tier,
    get_trade_up_probability, get_overpay_willingness,
    POSITION_DVM, PositionTier, get_position_dvm, calculate_adjusted_rank,
    HYBRID_ERASERS, GENERATIONAL_TALENTS,
    CoachingTree, TEAM_COACHING_TREE, get_coaching_tree_boost,
    ScarcityTracker, TradePersonality, get_trade_personality,
    should_seek_trade_down, get_rival_jump_bonus,
    IronLogicEngine
)

# Import Sparring Benchmarks
from sparring_benchmarks import (
    PROSPECT_CARDS, ProspectCard, get_war_room_secret,
    get_consensus_top_n
)


# =============================================================================
# ID GENERATION
# =============================================================================

def generate_id() -> str:
    """Generate a unique ID for SwiftUI Identifiable protocol."""
    return str(uuid.uuid4())


# =============================================================================
# UI HINT SYSTEM
# =============================================================================

class HapticType(Enum):
    NONE = "none"
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SELECTION = "selection"
    RIGID = "rigid"
    SOFT = "soft"


class UrgencyLevel(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class UIHints:
    id: str = field(default_factory=generate_id)
    haptic: HapticType = HapticType.NONE
    urgency: UrgencyLevel = UrgencyLevel.LOW
    color_hex: str = "#FFFFFF"
    glow_effect: bool = False
    animation_duration_ms: int = 300
    sound_effect: Optional[str] = None
    pulse_animation: bool = False
    shake_animation: bool = False
    confetti: bool = False
    
    @classmethod
    def for_user_pick(cls) -> 'UIHints':
        return cls(
            haptic=HapticType.HEAVY,
            urgency=UrgencyLevel.CRITICAL,
            color_hex="#FFD700",
            glow_effect=True,
            animation_duration_ms=500,
            sound_effect="user_on_clock",
            pulse_animation=True,
        )
    
    @classmethod
    def for_trade_offer(cls, fairness: str) -> 'UIHints':
        configs = {
            "steal": (HapticType.SUCCESS, "#2ECC71", True, False),
            "fair": (HapticType.MEDIUM, "#3498DB", False, False),
            "overpay": (HapticType.WARNING, "#F39C12", False, True),
            "bad": (HapticType.ERROR, "#E74C3C", False, True),
        }
        haptic, color, confetti, shake = configs.get(
            fairness, (HapticType.MEDIUM, "#3498DB", False, False)
        )
        return cls(
            haptic=haptic,
            urgency=UrgencyLevel.HIGH,
            color_hex=color,
            glow_effect=True,
            animation_duration_ms=400,
            sound_effect="trade_offer",
            confetti=confetti,
            shake_animation=shake,
        )
    
    @classmethod
    def for_ai_pick(cls, is_notable: bool = False) -> 'UIHints':
        return cls(
            haptic=HapticType.LIGHT if not is_notable else HapticType.MEDIUM,
            urgency=UrgencyLevel.MEDIUM if is_notable else UrgencyLevel.LOW,
            animation_duration_ms=250,
        )
    
    @classmethod
    def for_sync_state(cls) -> 'UIHints':
        return cls(haptic=HapticType.SOFT, urgency=UrgencyLevel.LOW)
    
    @classmethod
    def for_reconciliation(cls) -> 'UIHints':
        return cls(haptic=HapticType.SOFT, urgency=UrgencyLevel.MEDIUM)
    
    @classmethod
    def for_interrupt(cls) -> 'UIHints':
        return cls(haptic=HapticType.RIGID, urgency=UrgencyLevel.HIGH)

    def to_swift_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "haptic": self.haptic.value,
            "urgency": self.urgency.value,
            "colorHex": self.color_hex,
            "glowEffect": self.glow_effect,
            "animationDurationMs": self.animation_duration_ms,
            "soundEffect": self.sound_effect,
            "pulseAnimation": self.pulse_animation,
            "shakeAnimation": self.shake_animation,
            "confetti": self.confetti,
        }


# =============================================================================
# EVENT TYPES
# =============================================================================

class EventType(Enum):
    PICK = "pick"
    TRADE = "trade"
    ROUND_START = "round_start"
    ROUND_END = "round_end"
    USER_TURN = "user_turn"
    DRAFT_START = "draft_start"
    DRAFT_COMPLETE = "draft_complete"
    TRADE_OFFER = "trade_offer"
    TRADE_ACCEPTED = "trade_accepted"
    TRADE_REJECTED = "trade_rejected"
    CLOCK_TICK = "clock_tick"
    ERROR = "error"
    SYNC_STATE = "sync_state"
    INTERRUPT_ACK = "interrupt_ack"
    RECONCILIATION = "reconciliation"
    UNDO_COMPLETE = "undo_complete"
    REDO_COMPLETE = "redo_complete"


# =============================================================================
# PROSPECT
# =============================================================================

@dataclass
class Prospect:
    id: str
    rank: int
    name: str
    position: str
    school: str
    
    # Extended evaluation (from Iron Logic)
    tier: int = 2
    primary_trait: str = ""
    system_fit: str = ""
    pro_comp: str = ""
    is_hybrid_eraser: bool = False
    is_generational: bool = False
    
    @classmethod
    def from_prospect_card(cls, card: ProspectCard) -> 'Prospect':
        """Create Prospect from sparring benchmark ProspectCard."""
        return cls(
            id=generate_id(),
            rank=card.consensus_rank or 999,
            name=card.name,
            position=card.position,
            school=card.school,
            tier=card.tier,
            primary_trait=card.primary_trait,
            system_fit=card.system_fit,
            pro_comp=card.pro_comp,
            is_hybrid_eraser=card.is_hybrid_eraser,
            is_generational=card.is_generational,
        )
    
    def to_swift_dict(self) -> Dict[str, Any]:
        position_colors = {
            "QB": "#E74C3C", "RB": "#00BCD4", "WR": "#9B59B6",
            "TE": "#E67E22", "OT": "#F1C40F", "IOL": "#F1C40F",
            "EDGE": "#27AE60", "DL": "#27AE60", "DT": "#27AE60",
            "LB": "#1ABC9C", "CB": "#5D6D7E", "S": "#E91E63",
        }
        return {
            "id": self.id,
            "rank": self.rank,
            "name": self.name,
            "position": self.position,
            "school": self.school,
            "positionColorHex": position_colors.get(self.position, "#95A5A6"),
            "primaryTrait": self.primary_trait,
            "proComp": self.pro_comp,
        }


# =============================================================================
# DRAFT EVENT
# =============================================================================

@dataclass
class DraftEvent:
    type: EventType
    sequence_number: int
    ui_hints: UIHints
    payload: Dict[str, Any]
    current_pick: int
    current_round: int
    picks_remaining: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    id: str = field(default_factory=generate_id)
    is_reconciliation: bool = False
    requires_ack: bool = False
    
    def to_swift_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "timestamp": self.timestamp,
            "sequenceNumber": self.sequence_number,
            "uiHints": self.ui_hints.to_swift_dict(),
            "currentPick": self.current_pick,
            "currentRound": self.current_round,
            "picksRemaining": self.picks_remaining,
            "isReconciliation": self.is_reconciliation,
            "requiresAck": self.requires_ack,
            "payload": self.payload,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_swift_dict())


# =============================================================================
# VALUE ENGINE (With DVM Integration)
# =============================================================================

class ValueEngine:
    """Draft pick value calculator with DVM integration."""
    
    # Jimmy Johnson trade chart (simplified)
    BASE_VALUES = {
        1: 3000, 2: 2600, 3: 2200, 4: 1800, 5: 1700,
        6: 1600, 7: 1500, 8: 1400, 9: 1350, 10: 1300,
        11: 1250, 12: 1200, 13: 1150, 14: 1100, 15: 1050,
        16: 1000, 17: 950, 18: 900, 19: 875, 20: 850,
        21: 800, 22: 780, 23: 760, 24: 740, 25: 720,
        26: 700, 27: 680, 28: 660, 29: 640, 30: 620,
        31: 600, 32: 590,
    }
    
    # Round multipliers
    ROUND_DECAY = {1: 1.0, 2: 0.6, 3: 0.4, 4: 0.28, 5: 0.2, 6: 0.14, 7: 0.1}
    
    def __init__(self, qb_tax_enabled: bool = True):
        self.qb_tax_enabled = qb_tax_enabled
        self._cache: Dict[int, int] = {}
    
    def get_pick_value(self, pick: int) -> int:
        if pick in self._cache:
            return self._cache[pick]
        
        if pick <= 32:
            value = self.BASE_VALUES.get(pick, 500)
        else:
            round_num = (pick - 1) // 32 + 1
            pick_in_round = ((pick - 1) % 32) + 1
            base = self.BASE_VALUES.get(pick_in_round, 500)
            decay = self.ROUND_DECAY.get(round_num, 0.08)
            value = int(base * decay)
        
        self._cache[pick] = max(value, 10)
        return self._cache[pick]
    
    def get_prospect_value(
        self, 
        prospect: Prospect, 
        for_team: str,
        team_needs: List[str]
    ) -> float:
        """Calculate prospect value using DVM and coaching tree."""
        # Base value from rank
        base_value = self.get_pick_value(prospect.rank)
        
        # Apply DVM
        dvm = get_position_dvm(prospect.position, prospect.name)
        adjusted_value = base_value * dvm
        
        # Apply coaching tree boost
        tree_boost = get_coaching_tree_boost(for_team, prospect.position)
        adjusted_value *= tree_boost
        
        # Apply need multiplier
        if prospect.position in team_needs:
            need_index = team_needs.index(prospect.position)
            need_mult = 1.3 - (need_index * 0.1)
            adjusted_value *= need_mult
        
        return adjusted_value
    
    def calculate_trade_value(
        self,
        offering_picks: List[int],
        receiving_picks: List[int],
        offering_team: str,
        receiving_team: str,
    ) -> Dict[str, Any]:
        offer_value = sum(self.get_pick_value(p) for p in offering_picks)
        receive_value = sum(self.get_pick_value(p) for p in receiving_picks)
        
        diff = receive_value - offer_value
        diff_pct = (diff / offer_value * 100) if offer_value > 0 else 0
        
        if diff_pct >= 15:
            category = "steal"
        elif diff_pct >= -5:
            category = "fair"
        elif diff_pct >= -15:
            category = "overpay"
        else:
            category = "bad"
        
        return {
            "offer_value": offer_value,
            "receive_value": receive_value,
            "difference": diff,
            "difference_pct": round(diff_pct, 1),
            "is_fair": abs(diff_pct) <= 10,
            "fairness_category": category,
        }


# =============================================================================
# DRAFT STATE
# =============================================================================

@dataclass
class DraftState:
    user_team: str
    current_pick: int = 1
    pick_ownership: Dict[int, str] = field(default_factory=dict)
    prospects_drafted: Set[str] = field(default_factory=set)
    draft_history: List[Dict[str, Any]] = field(default_factory=list)
    trades: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.pick_ownership:
            self._initialize_pick_ownership()
    
    def _initialize_pick_ownership(self):
        # 2026 NFL Draft order (simplified - 32 teams × 7 rounds)
        teams_order = [
            "LV", "NYJ", "ARI", "TEN", "NYG", "CLE", "WAS", "NO",
            "KC", "CIN", "MIA", "DAL", "LAR", "BAL", "TB", "NYJ",
            "DET", "MIN", "CAR", "GB", "PIT", "LAC", "PHI", "JAX",
            "CHI", "BUF", "SF", "HOU", "LAR", "DEN", "NE", "SEA",
        ]
        for pick in range(1, 258):
            round_num = (pick - 1) // 32
            pick_in_round = (pick - 1) % 32
            self.pick_ownership[pick] = teams_order[pick_in_round % len(teams_order)]
    
    def get_round(self, pick: int) -> int:
        return (pick - 1) // 32 + 1
    
    def get_pick_in_round(self, pick: int) -> int:
        return ((pick - 1) % 32) + 1
    
    def get_team_picks(self, team: str) -> List[int]:
        return sorted([p for p, t in self.pick_ownership.items() if t == team])
    
    def record_pick(self, prospect_id: str, team: str, pick_number: int):
        self.prospects_drafted.add(prospect_id)
        self.draft_history.append({
            "pick": pick_number,
            "team": team,
            "prospect_id": prospect_id,
        })
        self.current_pick = pick_number + 1
    
    def undo_pick(self) -> Optional[Dict[str, Any]]:
        if not self.draft_history:
            return None
        last = self.draft_history.pop()
        self.prospects_drafted.discard(last["prospect_id"])
        self.current_pick = last["pick"]
        return last
    
    def to_snapshot(self) -> Dict[str, Any]:
        return {
            "id": generate_id(),
            "current_pick": self.current_pick,
            "user_team": self.user_team,
            "pick_ownership": {str(k): v for k, v in self.pick_ownership.items()},
            "prospects_drafted": list(self.prospects_drafted),
            "total_picks_made": len(self.draft_history),
            "total_trades": len(self.trades),
        }


# =============================================================================
# COMMAND PATTERN (Thread-Safe)
# =============================================================================

class Command:
    def execute(self, state: DraftState) -> Optional[DraftEvent]: ...
    def undo(self, state: DraftState) -> Optional[DraftEvent]: ...
    def description(self) -> str: ...


@dataclass
class MakePickCommand(Command):
    pick_number: int
    team: str
    prospect: Prospect
    sequence_getter: Callable[[], int]
    _was_executed: bool = False
    
    def execute(self, state: DraftState) -> Optional[DraftEvent]:
        state.record_pick(self.prospect.id, self.team, self.pick_number)
        self._was_executed = True
        
        # Get war room secret
        war_room_secret = get_war_room_secret(self.prospect.name)
        
        return DraftEvent(
            type=EventType.PICK,
            sequence_number=self.sequence_getter(),
            ui_hints=UIHints.for_ai_pick(self.prospect.rank <= 10),
            payload={
                "pick": self.pick_number,
                "team": self.team,
                "prospect": self.prospect.to_swift_dict(),
                "war_room_secret": war_room_secret,
            },
            current_pick=state.current_pick,
            current_round=state.get_round(state.current_pick),
            picks_remaining=257 - state.current_pick + 1,
        )
    
    def undo(self, state: DraftState) -> Optional[DraftEvent]:
        if not self._was_executed:
            return None
        state.undo_pick()
        self._was_executed = False
        return None
    
    def description(self) -> str:
        return f"Pick {self.pick_number}: {self.team} selects {self.prospect.name}"


class ThreadSafeCommandHistory:
    def __init__(self, max_history: int = 100):
        self._history: List[Command] = []
        self._redo_stack: List[Command] = []
        self._lock = threading.RLock()
        self._max_history = max_history
        self._sequence = 0
    
    @contextmanager
    def _locked(self):
        self._lock.acquire()
        try:
            yield
        finally:
            self._lock.release()
    
    def execute(self, command: Command, state: DraftState) -> Optional[DraftEvent]:
        with self._locked():
            event = command.execute(state)
            self._history.append(command)
            self._redo_stack.clear()
            if len(self._history) > self._max_history:
                self._history.pop(0)
            self._sequence += 1
            return event
    
    def undo(self, state: DraftState) -> Optional[DraftEvent]:
        with self._locked():
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
    
    def redo(self, state: DraftState) -> Optional[DraftEvent]:
        with self._locked():
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
        with self._locked():
            return len(self._history) > 0
    
    def can_redo(self) -> bool:
        with self._locked():
            return len(self._redo_stack) > 0
    
    def get_undo_description(self) -> Optional[str]:
        with self._locked():
            return self._history[-1].description() if self._history else None


# =============================================================================
# INTERRUPT SYSTEM
# =============================================================================

class InterruptType(Enum):
    UNDO = auto()
    REDO = auto()
    USER_TRADE = auto()
    PAUSE = auto()
    RESUME = auto()
    TRADE_DECISION = auto()
    FORCE_SYNC = auto()


@dataclass(order=True)
class Interrupt:
    priority: int
    type: InterruptType = field(default=InterruptType.FORCE_SYNC, compare=False)
    id: str = field(default_factory=generate_id, compare=False)
    payload: Dict[str, Any] = field(default_factory=dict, compare=False)


class InterruptBuffer:
    PRIORITIES = {
        InterruptType.PAUSE: 100,
        InterruptType.RESUME: 99,
        InterruptType.UNDO: 90,
        InterruptType.REDO: 89,
        InterruptType.TRADE_DECISION: 80,
        InterruptType.USER_TRADE: 70,
        InterruptType.FORCE_SYNC: 50,
    }
    
    def __init__(self):
        self._queue: queue.PriorityQueue = queue.PriorityQueue()
        self._lock = threading.RLock()
        self._is_paused = False
    
    def push(self, interrupt: Interrupt):
        with self._lock:
            priority = -self.PRIORITIES.get(interrupt.type, 0)
            self._queue.put((priority, interrupt))
    
    def pop(self) -> Optional[Interrupt]:
        with self._lock:
            try:
                _, interrupt = self._queue.get_nowait()
                return interrupt
            except queue.Empty:
                return None
    
    def has_pending(self) -> bool:
        with self._lock:
            return not self._queue.empty()
    
    def pause(self):
        with self._lock:
            self._is_paused = True
    
    def resume(self):
        with self._lock:
            self._is_paused = False
    
    @property
    def is_paused(self) -> bool:
        with self._lock:
            return self._is_paused


# =============================================================================
# TRADE OFFER
# =============================================================================

@dataclass
class PendingTradeOffer:
    id: str = field(default_factory=generate_id)
    offering_team: str = ""
    receiving_team: str = ""
    offering_picks: List[int] = field(default_factory=list)
    receiving_picks: List[int] = field(default_factory=list)
    valuation: Dict[str, Any] = field(default_factory=dict)
    expires_at_pick: int = 0


# =============================================================================
# IRON LOGIC INTEGRATED STEP ENGINE
# =============================================================================

class IronLogicStepEngine:
    """
    Draft simulation engine with full Iron Logic AI integration.
    
    Features:
    - Team Aggression for trade decisions
    - DVM for position evaluation
    - Coaching Tree for scheme fit
    - Scarcity Momentum for panic picks
    - War Room Secrets for narrative
    """
    
    HEARTBEAT_INTERVAL = 10
    
    def __init__(
        self,
        state: DraftState,
        prospects: List[Prospect],
        value_engine: ValueEngine,
        team_needs: Dict[str, List[str]],
    ):
        self.state = state
        self.prospects = {p.id: p for p in prospects}
        self.prospects_by_rank = sorted(prospects, key=lambda p: p.rank)
        self.value_engine = value_engine
        self.team_needs = team_needs
        self.command_history = ThreadSafeCommandHistory()
        
        # Iron Logic
        self.iron_logic = IronLogicEngine()
        
        # Interrupt handling
        self.interrupt_buffer = InterruptBuffer()
        
        # User interaction state
        self._user_pick: Optional[str] = None
        self._awaiting_user_input = False
        self._pending_trade: Optional[PendingTradeOffer] = None
        self._awaiting_trade_decision = False
        self._trade_decision: Optional[bool] = None
        
        # Sequence tracking
        self._sequence = 0
        self._picks_since_sync = 0
    
    def _next_sequence(self) -> int:
        self._sequence += 1
        return self._sequence
    
    def _get_available_prospects(self) -> List[Prospect]:
        return [p for p in self.prospects_by_rank if p.id not in self.state.prospects_drafted]
    
    # =========================================================================
    # IRON LOGIC AI PICK SELECTION
    # =========================================================================
    
    def _ai_select_prospect(self, team: str) -> Optional[Prospect]:
        """
        AI prospect selection using full Iron Logic system.
        
        Considers:
        1. Base prospect rank
        2. DVM position multiplier
        3. Coaching tree scheme fit
        4. Team needs
        5. Scarcity momentum
        """
        available = self._get_available_prospects()
        if not available:
            return None
        
        needs = self.team_needs.get(team, [])
        
        # Get scarcity positions (positions with runs)
        scarcity = self.iron_logic.scarcity_tracker.get_scarcity_positions(
            self.state.current_pick
        )
        
        # Score each prospect
        scored_prospects: List[Tuple[float, Prospect]] = []
        
        for prospect in available[:20]:  # Consider top 20 available
            evaluation = self.iron_logic.evaluate_prospect_for_team(
                prospect_name=prospect.name,
                prospect_position=prospect.position,
                prospect_rank=prospect.rank,
                team=team,
                team_needs=needs,
            )
            
            score = evaluation["final_score"]
            
            # Apply scarcity panic bonus
            if prospect.position in scarcity:
                if prospect.position in needs[:3]:
                    score *= 0.7  # MUCH better score (lower = better)
            
            scored_prospects.append((score, prospect))
        
        # Sort by score (lower = better)
        scored_prospects.sort(key=lambda x: x[0])
        
        # Add some variance - 80% chance of best, 15% second best, 5% third
        roll = random.random()
        if roll < 0.80 and len(scored_prospects) >= 1:
            selection = scored_prospects[0][1]
        elif roll < 0.95 and len(scored_prospects) >= 2:
            selection = scored_prospects[1][1]
        elif len(scored_prospects) >= 3:
            selection = scored_prospects[2][1]
        else:
            selection = scored_prospects[0][1]
        
        # Record pick for scarcity tracking
        self.iron_logic.record_pick(self.state.current_pick, selection.position)
        
        return selection
    
    def _get_recommendations(self, team: str, count: int = 5) -> List[Dict[str, Any]]:
        """Get AI recommendations for user pick."""
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
            
            # Build reason string
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
            })
        
        return recommendations
    
    # =========================================================================
    # IRON LOGIC AI TRADE DECISIONS
    # =========================================================================
    
    def _should_ai_propose_trade(self, current_team: str) -> bool:
        """
        Determine if AI team should attempt a trade.
        Uses Team Aggression and current draft context.
        """
        if current_team == self.state.user_team:
            return False
        
        # Get trade probability based on aggression
        desperation = self.iron_logic.scarcity_tracker.get_desperation_for_team(
            current_team,
            self.team_needs.get(current_team, []),
            self.state.current_pick
        )
        
        trade_prob = get_trade_up_probability(current_team, desperation)
        
        # Reduce probability in later rounds
        round_num = self.state.get_round(self.state.current_pick)
        trade_prob *= max(0.3, 1.0 - (round_num - 1) * 0.15)
        
        return random.random() < trade_prob
    
    def _generate_ai_trade_offer(self, ai_team: str) -> Optional[PendingTradeOffer]:
        """Generate trade offer using Iron Logic valuations."""
        user_picks = self.state.get_team_picks(self.state.user_team)
        ai_picks = self.state.get_team_picks(ai_team)
        
        user_upcoming = [p for p in user_picks if p > self.state.current_pick]
        if not user_upcoming or not ai_picks:
            return None
        
        target_pick = user_upcoming[0]
        target_value = self.value_engine.get_pick_value(target_pick)
        
        # Get overpay willingness from team aggression
        overpay_mult = get_overpay_willingness(ai_team)
        
        # Add rival jump bonus
        rival_bonus = get_rival_jump_bonus(ai_team, self.state.user_team)
        overpay_mult += rival_bonus
        
        ai_available = [p for p in ai_picks if p > self.state.current_pick]
        if not ai_available:
            return None
        
        # Build offer
        offer_picks = []
        offer_value = 0
        target_offer_value = target_value * overpay_mult
        
        for pick in sorted(ai_available):
            offer_picks.append(pick)
            offer_value += self.value_engine.get_pick_value(pick)
            if offer_value >= target_offer_value or len(offer_picks) >= 3:
                break
        
        # Validate offer
        if offer_value < target_value * 0.85:
            return None
        
        valuation = self.value_engine.calculate_trade_value(
            offering_picks=offer_picks,
            receiving_picks=[target_pick],
            offering_team=ai_team,
            receiving_team=self.state.user_team,
        )
        
        return PendingTradeOffer(
            offering_team=ai_team,
            receiving_team=self.state.user_team,
            offering_picks=offer_picks,
            receiving_picks=[target_pick],
            valuation=valuation,
            expires_at_pick=self.state.current_pick + 1,
        )
    
    # =========================================================================
    # EVENT CREATION
    # =========================================================================
    
    def _create_sync_event(self, reason: str = "heartbeat") -> DraftEvent:
        self._picks_since_sync = 0
        return DraftEvent(
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
        )
    
    def _create_reconciliation_event(self, interrupt: Interrupt) -> DraftEvent:
        return DraftEvent(
            type=EventType.RECONCILIATION,
            sequence_number=self._next_sequence(),
            ui_hints=UIHints.for_reconciliation(),
            payload={
                "interrupt_id": interrupt.id,
                "interrupt_type": interrupt.type.name,
                "snapshot": self.state.to_snapshot(),
            },
            current_pick=self.state.current_pick,
            current_round=self.state.get_round(self.state.current_pick),
            picks_remaining=257 - self.state.current_pick + 1,
            is_reconciliation=True,
        )
    
    # =========================================================================
    # INTERRUPT HANDLING
    # =========================================================================
    
    def _process_interrupt(self, interrupt: Interrupt) -> Optional[DraftEvent]:
        if interrupt.type == InterruptType.UNDO:
            event = self.command_history.undo(self.state)
            if event:
                self._picks_since_sync = self.HEARTBEAT_INTERVAL
            return event
        
        elif interrupt.type == InterruptType.REDO:
            event = self.command_history.redo(self.state)
            if event:
                self._picks_since_sync = self.HEARTBEAT_INTERVAL
            return event
        
        elif interrupt.type == InterruptType.FORCE_SYNC:
            return self._create_sync_event("forced")
        
        elif interrupt.type == InterruptType.TRADE_DECISION:
            self._trade_decision = interrupt.payload.get("accept", False)
            self._awaiting_trade_decision = False
            return None
        
        elif interrupt.type == InterruptType.PAUSE:
            self.interrupt_buffer.pause()
            return DraftEvent(
                type=EventType.INTERRUPT_ACK,
                sequence_number=self._next_sequence(),
                ui_hints=UIHints.for_interrupt(),
                payload={"action": "paused"},
                current_pick=self.state.current_pick,
                current_round=self.state.get_round(self.state.current_pick),
                picks_remaining=257 - self.state.current_pick + 1,
            )
        
        elif interrupt.type == InterruptType.RESUME:
            self.interrupt_buffer.resume()
            return DraftEvent(
                type=EventType.INTERRUPT_ACK,
                sequence_number=self._next_sequence(),
                ui_hints=UIHints.for_interrupt(),
                payload={"action": "resumed"},
                current_pick=self.state.current_pick,
                current_round=self.state.get_round(self.state.current_pick),
                picks_remaining=257 - self.state.current_pick + 1,
            )
        
        return None
    
    def _check_and_process_interrupts(self) -> Generator[DraftEvent, None, None]:
        while self.interrupt_buffer.has_pending():
            interrupt = self.interrupt_buffer.pop()
            if interrupt:
                event = self._process_interrupt(interrupt)
                if event:
                    yield event
                    yield self._create_reconciliation_event(interrupt)
    
    # =========================================================================
    # PUBLIC API
    # =========================================================================
    
    def submit_pick(self, prospect_id: str):
        self._user_pick = prospect_id
        self._awaiting_user_input = False
    
    def submit_trade_decision(self, accept: bool):
        self.interrupt_buffer.push(Interrupt(
            type=InterruptType.TRADE_DECISION,
            priority=80,
            payload={"accept": accept},
        ))
    
    def request_undo(self):
        self.interrupt_buffer.push(Interrupt(type=InterruptType.UNDO, priority=90))
    
    def request_redo(self):
        self.interrupt_buffer.push(Interrupt(type=InterruptType.REDO, priority=89))
    
    def request_pause(self):
        self.interrupt_buffer.push(Interrupt(type=InterruptType.PAUSE, priority=100))
    
    def request_resume(self):
        self.interrupt_buffer.push(Interrupt(type=InterruptType.RESUME, priority=99))
    
    def request_sync(self):
        self.interrupt_buffer.push(Interrupt(type=InterruptType.FORCE_SYNC, priority=50))
    
    # =========================================================================
    # MAIN GENERATOR
    # =========================================================================
    
    def run(self) -> Generator[DraftEvent, None, None]:
        """Main draft simulation generator."""
        
        # Yield draft start
        yield DraftEvent(
            type=EventType.DRAFT_START,
            sequence_number=self._next_sequence(),
            ui_hints=UIHints(haptic=HapticType.HEAVY, urgency=UrgencyLevel.HIGH),
            payload={"user_team": self.state.user_team},
            current_pick=1,
            current_round=1,
            picks_remaining=257,
        )
        
        current_round = 1
        
        while self.state.current_pick <= 257:
            # Process interrupts
            for event in self._check_and_process_interrupts():
                yield event
            
            # Wait while paused
            while self.interrupt_buffer.is_paused:
                for event in self._check_and_process_interrupts():
                    yield event
                yield None  # Yield control while paused
            
            # Heartbeat sync
            if self._picks_since_sync >= self.HEARTBEAT_INTERVAL:
                yield self._create_sync_event()
            
            # Round transition
            new_round = self.state.get_round(self.state.current_pick)
            if new_round != current_round:
                yield DraftEvent(
                    type=EventType.ROUND_END,
                    sequence_number=self._next_sequence(),
                    ui_hints=UIHints(haptic=HapticType.SUCCESS, urgency=UrgencyLevel.HIGH, confetti=True),
                    payload={"round": current_round},
                    current_pick=self.state.current_pick,
                    current_round=new_round,
                    picks_remaining=257 - self.state.current_pick + 1,
                )
                current_round = new_round
                yield DraftEvent(
                    type=EventType.ROUND_START,
                    sequence_number=self._next_sequence(),
                    ui_hints=UIHints(haptic=HapticType.MEDIUM, urgency=UrgencyLevel.MEDIUM),
                    payload={"round": current_round},
                    current_pick=self.state.current_pick,
                    current_round=current_round,
                    picks_remaining=257 - self.state.current_pick + 1,
                )
            
            # Get current team
            current_team = self.state.pick_ownership.get(
                self.state.current_pick, "UNK"
            )
            
            # Check for AI trade attempt
            if self._should_ai_propose_trade(current_team):
                offer = self._generate_ai_trade_offer(current_team)
                if offer:
                    self._pending_trade = offer
                    self._awaiting_trade_decision = True
                    self._trade_decision = None
                    
                    fairness = offer.valuation.get("fairness_category", "fair")
                    yield DraftEvent(
                        type=EventType.TRADE_OFFER,
                        sequence_number=self._next_sequence(),
                        ui_hints=UIHints.for_trade_offer(fairness),
                        payload={
                            "offer_id": offer.id,
                            "from_team": offer.offering_team,
                            "to_team": offer.receiving_team,
                            "you_receive": offer.offering_picks,
                            "you_give": offer.receiving_picks,
                            "valuation": offer.valuation,
                        },
                        current_pick=self.state.current_pick,
                        current_round=current_round,
                        picks_remaining=257 - self.state.current_pick + 1,
                        requires_ack=True,
                    )
                    
                    # Wait for trade decision
                    while self._awaiting_trade_decision:
                        for event in self._check_and_process_interrupts():
                            yield event
                        yield None
                    
                    # Process decision
                    if self._trade_decision:
                        # Execute trade
                        for give_pick in offer.receiving_picks:
                            self.state.pick_ownership[give_pick] = offer.offering_team
                        for receive_pick in offer.offering_picks:
                            self.state.pick_ownership[receive_pick] = offer.receiving_team
                        
                        self.state.trades.append({
                            "pick": self.state.current_pick,
                            "from": offer.offering_team,
                            "to": offer.receiving_team,
                            "sent": offer.offering_picks,
                            "received": offer.receiving_picks,
                        })
                        
                        yield DraftEvent(
                            type=EventType.TRADE_ACCEPTED,
                            sequence_number=self._next_sequence(),
                            ui_hints=UIHints.for_trade_offer("steal"),
                            payload={"offer_id": offer.id},
                            current_pick=self.state.current_pick,
                            current_round=current_round,
                            picks_remaining=257 - self.state.current_pick + 1,
                        )
                    else:
                        yield DraftEvent(
                            type=EventType.TRADE_REJECTED,
                            sequence_number=self._next_sequence(),
                            ui_hints=UIHints(haptic=HapticType.LIGHT),
                            payload={"offer_id": offer.id},
                            current_pick=self.state.current_pick,
                            current_round=current_round,
                            picks_remaining=257 - self.state.current_pick + 1,
                        )
                    
                    self._pending_trade = None
                    continue
            
            # User turn or AI turn
            if current_team == self.state.user_team:
                # User turn
                recommendations = self._get_recommendations(current_team)
                
                yield DraftEvent(
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
                )
                
                # Wait for user input
                self._awaiting_user_input = True
                self._user_pick = None
                
                while self._awaiting_user_input:
                    for event in self._check_and_process_interrupts():
                        yield event
                    if self._user_pick:
                        break
                    yield None
                
                # Execute user pick
                if self._user_pick and self._user_pick in self.prospects:
                    prospect = self.prospects[self._user_pick]
                    command = MakePickCommand(
                        pick_number=self.state.current_pick,
                        team=current_team,
                        prospect=prospect,
                        sequence_getter=self._next_sequence,
                    )
                    event = self.command_history.execute(command, self.state)
                    if event:
                        event.ui_hints = UIHints.for_user_pick()
                        event.ui_hints.confetti = True
                        yield event
                    
                    self.iron_logic.record_pick(self.state.current_pick - 1, prospect.position)
                    self._picks_since_sync += 1
            else:
                # AI turn
                prospect = self._ai_select_prospect(current_team)
                if prospect:
                    command = MakePickCommand(
                        pick_number=self.state.current_pick,
                        team=current_team,
                        prospect=prospect,
                        sequence_getter=self._next_sequence,
                    )
                    event = self.command_history.execute(command, self.state)
                    if event:
                        yield event
                    self._picks_since_sync += 1
        
        # Draft complete
        yield DraftEvent(
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
        )


# =============================================================================
# DRAFT ROOM FACADE
# =============================================================================

class DraftRoom:
    """High-level facade for draft simulation."""
    
    def __init__(
        self,
        user_team: str = "NYG",
        enable_trades: bool = True,
    ):
        self.user_team = user_team
        self.enable_trades = enable_trades
        
        # Build prospects from sparring benchmarks
        self.prospects = self._build_prospects()
        
        # Initialize state
        self.state = DraftState(user_team=user_team)
        
        # Initialize value engine
        self.value_engine = ValueEngine()
        
        # Initialize team needs (simplified for demo)
        self.team_needs = self._initialize_team_needs()
        
        # Create engine
        self.engine = IronLogicStepEngine(
            state=self.state,
            prospects=self.prospects,
            value_engine=self.value_engine,
            team_needs=self.team_needs,
        )
        
        self._generator: Optional[Generator] = None
    
    def _build_prospects(self) -> List[Prospect]:
        """Build prospect list from sparring benchmarks."""
        prospects = []
        for name, card in PROSPECT_CARDS.items():
            prospects.append(Prospect.from_prospect_card(card))
        
        # Sort by consensus rank
        prospects.sort(key=lambda p: p.rank)
        return prospects
    
    def _initialize_team_needs(self) -> Dict[str, List[str]]:
        """Initialize team needs (would come from external data in production)."""
        # Simplified team needs for demo
        return {
            "LV": ["QB", "CB", "WR"],
            "NYJ": ["EDGE", "OT", "CB"],
            "ARI": ["OT", "EDGE", "CB"],
            "TEN": ["EDGE", "WR", "CB"],
            "NYG": ["OT", "EDGE", "WR"],
            "CLE": ["WR", "CB", "EDGE"],
            "WAS": ["WR", "LB", "CB"],
            "NO": ["WR", "EDGE", "CB"],
            "KC": ["WR", "EDGE", "OT"],
            "CIN": ["EDGE", "OT", "CB"],
            "MIA": ["OT", "LB", "EDGE"],
            "DAL": ["EDGE", "OT", "CB"],
            "LAR": ["EDGE", "CB", "OT"],
            "BAL": ["WR", "CB", "EDGE"],
            "TB": ["QB", "EDGE", "OT"],
            "DET": ["EDGE", "CB", "S"],
            "MIN": ["QB", "CB", "OT"],
            "CAR": ["QB", "EDGE", "OT"],
            "GB": ["EDGE", "S", "WR"],
            "PIT": ["QB", "CB", "OT"],
            "LAC": ["OT", "WR", "EDGE"],
            "PHI": ["CB", "EDGE", "LB"],
            "JAX": ["OT", "EDGE", "WR"],
            "CHI": ["CB", "EDGE", "OT"],
            "BUF": ["WR", "EDGE", "CB"],
            "SF": ["CB", "EDGE", "OT"],
            "HOU": ["EDGE", "CB", "OT"],
            "DEN": ["QB", "EDGE", "CB"],
            "NE": ["WR", "CB", "OT"],
            "SEA": ["EDGE", "CB", "OT"],
            "ATL": ["EDGE", "CB", "DL"],
            "IND": ["QB", "EDGE", "WR"],
        }
    
    def start(self) -> Generator[DraftEvent, None, None]:
        """Start the draft simulation."""
        self._generator = self.engine.run()
        return self._generator
    
    def next_event(self) -> Optional[DraftEvent]:
        """Get next event from simulation."""
        if not self._generator:
            self._generator = self.engine.run()
        
        try:
            event = next(self._generator)
            return event
        except StopIteration:
            return None
    
    # Passthrough methods to engine
    def submit_pick(self, prospect_id: str):
        self.engine.submit_pick(prospect_id)
    
    def accept_trade(self):
        self.engine.submit_trade_decision(True)
    
    def reject_trade(self):
        self.engine.submit_trade_decision(False)
    
    def undo(self):
        self.engine.request_undo()
    
    def redo(self):
        self.engine.request_redo()
    
    def pause(self):
        self.engine.request_pause()
    
    def resume(self):
        self.engine.request_resume()
    
    def request_sync(self):
        self.engine.request_sync()
    
    def get_state_snapshot(self) -> Dict[str, Any]:
        return self.state.to_snapshot()
    
    def can_undo(self) -> bool:
        return self.engine.command_history.can_undo()
    
    def can_redo(self) -> bool:
        return self.engine.command_history.can_redo()


# =============================================================================
# SWIFT BRIDGE INTERFACE
# =============================================================================

class SwiftBridgeInterface:
    """
    Interface designed for PythonKit/Swift interop.
    
    All methods return JSON strings for easy Swift decoding.
    All inputs are primitive types (str, int, bool).
    """
    
    def __init__(self, user_team: str = "NYG"):
        self.room = DraftRoom(user_team=user_team)
        self._generator = None
        self._is_started = False
    
    def start_draft(self) -> str:
        """Start draft and return first event as JSON."""
        self._generator = self.room.start()
        self._is_started = True
        return self.next_event()
    
    def next_event(self) -> str:
        """Get next event as JSON string."""
        if not self._generator:
            return json.dumps({"error": "Draft not started"})
        
        try:
            event = next(self._generator)
            if event is None:
                return json.dumps({"type": "waiting"})
            return event.to_json()
        except StopIteration:
            return json.dumps({"type": "draft_complete"})
    
    def submit_pick(self, prospect_id: str) -> str:
        """Submit user pick."""
        self.room.submit_pick(prospect_id)
        return json.dumps({"success": True})
    
    def accept_trade(self) -> str:
        """Accept pending trade offer."""
        self.room.accept_trade()
        return json.dumps({"success": True})
    
    def reject_trade(self) -> str:
        """Reject pending trade offer."""
        self.room.reject_trade()
        return json.dumps({"success": True})
    
    def request_undo(self) -> str:
        """Request undo."""
        self.room.undo()
        return json.dumps({"success": True})
    
    def request_redo(self) -> str:
        """Request redo."""
        self.room.redo()
        return json.dumps({"success": True})
    
    def request_pause(self) -> str:
        """Pause simulation."""
        self.room.pause()
        return json.dumps({"success": True})
    
    def request_resume(self) -> str:
        """Resume simulation."""
        self.room.resume()
        return json.dumps({"success": True})
    
    def request_sync(self) -> str:
        """Request state sync."""
        self.room.request_sync()
        return json.dumps({"success": True})
    
    def get_state(self) -> str:
        """Get current state as JSON."""
        return json.dumps(self.room.get_state_snapshot())
    
    def can_undo(self) -> bool:
        return self.room.can_undo()
    
    def can_redo(self) -> bool:
        return self.room.can_redo()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "DraftRoom",
    "IronLogicStepEngine",
    "SwiftBridgeInterface",
    "DraftEvent",
    "Prospect",
    "UIHints",
    "EventType",
    "HapticType",
    "UrgencyLevel",
]
