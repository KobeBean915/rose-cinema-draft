"""
THE DRAFT ROOM - Iron Logic Module
===================================
Implements the sophisticated AI decision-making system:
- Team Aggression Scores (Trade Probability Weights)
- Dynamic Value Multipliers (Position Tier System)
- Organizational DNA (Coaching Tree Archetypes)
- Scarcity Momentum (Run-on-Position Psychology)
- Trade Psychology (Gamblers vs Hoarders)

Based on the Iron Logic Spec v1.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
import random
import math


# =============================================================================
# TEAM AGGRESSION SYSTEM
# =============================================================================

class AggressionTier(Enum):
    """Team aggression classification."""
    PREDATOR = "predator"           # 8-10: Will overpay to move up
    CALCULATED = "calculated"       # 7-9: Strategic aggression
    STRATEGIC = "strategic"         # 3-6: Patient, value-focused
    ANCHOR = "anchor"               # 1-3: Almost never trades up


# Team Aggression Scores (1-10 scale)
# Higher = more likely to trade up aggressively
TEAM_AGGRESSION: Dict[str, float] = {
    # Predators (8-10)
    "PHI": 9.5,   # Eagles - historically aggressive
    "JAX": 9.5,   # Jaguars - cap space, impatient
    "NO": 9.0,    # Saints - win-now mode
    "WAS": 8.5,   # Commanders - new regime proving
    "ATL": 8.5,   # Falcons - desperate for QB/edge
    "LV": 8.0,    # Raiders - new coach needs QB
    "SEA": 8.0,   # Seahawks - Pete Carroll tree aggressive
    "LAR": 8.0,   # Rams - McVay all-in mentality
    "DET": 8.0,   # Lions - Dan Campbell aggression
    "CHI": 8.0,   # Bears - impatient rebuild
    "BUF": 8.0,   # Bills - Super Bowl window
    
    # Calculated Aggressors (7-9)
    "SF": 8.0,    # 49ers - Shanahan precision
    "HOU": 8.0,   # Texans - young core building
    "DEN": 7.5,   # Broncos - Payton wants weapons
    "NYG": 7.0,   # Giants - need immediate help
    "PIT": 7.0,   # Steelers - transitioning
    
    # Strategic/Passive (3-6)
    "NYJ": 5.0,   # Jets - cautious with assets
    "MIA": 5.0,   # Dolphins - Grier conservative
    "DAL": 5.0,   # Cowboys - Jerry unpredictable
    "BAL": 5.0,   # Ravens - value-focused
    "TEN": 4.0,   # Titans - patient rebuild
    "MIN": 4.0,   # Vikings - Kwesi analytics
    "CLE": 4.0,   # Browns - Berry hoards picks
    "LAC": 4.0,   # Chargers - Harbaugh methodical
    "ARI": 4.0,   # Cardinals - rebuilding
    "KC": 3.5,    # Chiefs - trust the process
    "TB": 3.5,    # Bucs - measured approach
    
    # Anchors (1-3)
    "NE": 2.5,    # Patriots - Belichick hoards
    "GB": 2.5,    # Packers - Gute rarely moves up
    "CAR": 2.5,   # Panthers - asset accumulation
    "IND": 2.0,   # Colts - Ballard conservative
    "CIN": 2.0,   # Bengals - rarely trade up
}


def get_aggression_tier(team: str) -> AggressionTier:
    """Get aggression tier for a team."""
    score = TEAM_AGGRESSION.get(team, 5.0)
    if score >= 8.0:
        return AggressionTier.PREDATOR
    elif score >= 7.0:
        return AggressionTier.CALCULATED
    elif score >= 3.0:
        return AggressionTier.STRATEGIC
    return AggressionTier.ANCHOR


def get_trade_up_probability(team: str, desperation_bonus: float = 0.0) -> float:
    """
    Calculate probability team will attempt to trade up.
    
    Args:
        team: Team abbreviation
        desperation_bonus: Additional probability from scarcity momentum (0-0.3)
    
    Returns:
        Probability 0.0-1.0
    """
    base = TEAM_AGGRESSION.get(team, 5.0) / 10.0
    return min(1.0, base * 0.15 + desperation_bonus)  # Base 0-15% + desperation


def get_overpay_willingness(team: str) -> float:
    """
    How much extra value a team will pay to move up.
    
    Returns multiplier (1.0 = fair value, 1.15 = 15% overpay)
    """
    tier = get_aggression_tier(team)
    overpay_map = {
        AggressionTier.PREDATOR: 1.15,    # Will overpay 15%
        AggressionTier.CALCULATED: 1.08,  # Slight overpay
        AggressionTier.STRATEGIC: 1.02,   # Near fair value
        AggressionTier.ANCHOR: 0.95,      # Wants discount
    }
    return overpay_map[tier]


# =============================================================================
# DYNAMIC VALUE MULTIPLIERS (Position Tiers)
# =============================================================================

class PositionTier(Enum):
    """Position value tiers for draft evaluation."""
    PREMIUM = 1      # 1.5x - QB, OT, EDGE
    PERIMETER = 2    # 1.2x - WR, CB
    INTERIOR = 3     # 1.0x - G, C, DT
    TACTICAL = 4     # 0.8x - RB, TE, ILB
    HYBRID = 5       # 1.2x - Elite S/LB hybrids (Caleb Downs clause)


# Dynamic Value Multipliers
POSITION_DVM: Dict[str, Tuple[PositionTier, float]] = {
    # Tier 1 - Premium (1.5x)
    "QB": (PositionTier.PREMIUM, 1.5),
    "OT": (PositionTier.PREMIUM, 1.5),
    "EDGE": (PositionTier.PREMIUM, 1.5),
    
    # Tier 2 - Perimeter (1.2x)
    "WR": (PositionTier.PERIMETER, 1.2),
    "CB": (PositionTier.PERIMETER, 1.2),
    
    # Tier 3 - Interior (1.0x)
    "IOL": (PositionTier.INTERIOR, 1.0),
    "C": (PositionTier.INTERIOR, 1.0),
    "G": (PositionTier.INTERIOR, 1.0),
    "DL": (PositionTier.INTERIOR, 1.0),
    "DT": (PositionTier.INTERIOR, 1.0),
    
    # Tier 4 - Tactical (0.8x)
    "RB": (PositionTier.TACTICAL, 0.8),
    "TE": (PositionTier.TACTICAL, 0.8),
    "LB": (PositionTier.TACTICAL, 0.8),
    "ILB": (PositionTier.TACTICAL, 0.8),
    
    # Tier 5 - Hybrid (variable)
    "S": (PositionTier.PERIMETER, 1.1),  # Base safety value
}

# Elite prospects that get the "Caleb Downs Hybrid Clause" - elevated to Tier 2
HYBRID_ERASERS: Set[str] = {
    "Caleb Downs",      # Elite hybrid safety
    "Sonny Styles",     # Hybrid LB/S
    "Arvell Reese",     # Sideline-to-sideline LB
}

# Generational talents that override Tier 4 penalty
GENERATIONAL_TALENTS: Set[str] = {
    "Jeremiyah Love",   # Elite RB with receiving
}


def get_position_dvm(position: str, prospect_name: str = "") -> float:
    """
    Get Dynamic Value Multiplier for a position.
    
    Accounts for:
    - Base position tier
    - Hybrid Eraser clause (elite S/LB)
    - Generational talent override
    """
    # Check for generational override
    if prospect_name in GENERATIONAL_TALENTS:
        return 1.3  # Elevated from 0.8 to 1.3
    
    # Check for hybrid eraser clause
    if prospect_name in HYBRID_ERASERS:
        return 1.3  # Elevated to Tier 2+
    
    # Default position DVM
    _, dvm = POSITION_DVM.get(position, (PositionTier.INTERIOR, 1.0))
    return dvm


def calculate_adjusted_rank(base_rank: int, position: str, prospect_name: str = "") -> float:
    """
    Calculate DVM-adjusted prospect rank.
    
    Lower = better value for draft position.
    """
    dvm = get_position_dvm(position, prospect_name)
    # Invert DVM effect: premium positions get LOWER adjusted rank (better)
    return base_rank / dvm


# =============================================================================
# ORGANIZATIONAL DNA (Coaching Tree Archetypes)
# =============================================================================

class CoachingTree(Enum):
    """NFL coaching tree archetypes."""
    SHANAHAN_MCVAY = "shanahan_mcvay"   # Wide zone, YAC, lateral agility
    GREEN_BAY = "green_bay"             # RAS, premium positions
    BELICHICK = "belichick"             # Value, versatility
    REID = "reid"                       # Creative offense, weapons
    HARBAUGH = "harbaugh"               # Power, physical OL
    DEFAULT = "default"


# Team coaching tree mapping
TEAM_COACHING_TREE: Dict[str, CoachingTree] = {
    # Shanahan/McVay Tree (Wide Zone, YAC emphasis)
    "SF": CoachingTree.SHANAHAN_MCVAY,
    "LAR": CoachingTree.SHANAHAN_MCVAY,
    "MIA": CoachingTree.SHANAHAN_MCVAY,
    "DEN": CoachingTree.SHANAHAN_MCVAY,
    "CIN": CoachingTree.SHANAHAN_MCVAY,
    "MIN": CoachingTree.SHANAHAN_MCVAY,
    
    # Green Bay Discipline (RAS, Premium Positions)
    "GB": CoachingTree.GREEN_BAY,
    "TEN": CoachingTree.GREEN_BAY,
    "HOU": CoachingTree.GREEN_BAY,
    
    # Belichick Tree (Value, Versatility)
    "NE": CoachingTree.BELICHICK,
    "DET": CoachingTree.BELICHICK,
    "NYG": CoachingTree.BELICHICK,
    
    # Reid Tree (Creative Offense)
    "KC": CoachingTree.REID,
    "PHI": CoachingTree.REID,
    "LAC": CoachingTree.HARBAUGH,
    
    # Harbaugh Tree (Physical, Power)
    "BAL": CoachingTree.HARBAUGH,
    "SEA": CoachingTree.HARBAUGH,
}


# Position preferences by coaching tree
TREE_POSITION_BOOSTS: Dict[CoachingTree, Dict[str, float]] = {
    CoachingTree.SHANAHAN_MCVAY: {
        "WR": 1.15,   # YAC receivers
        "RB": 1.2,    # Zone scheme backs
        "OT": 1.1,    # Athletic OL
        "TE": 1.1,    # Move TEs
    },
    CoachingTree.GREEN_BAY: {
        "EDGE": 1.15,  # Premium pass rush
        "OT": 1.1,
        "CB": 1.1,
        "WR": 0.9,     # Often wait on WR
    },
    CoachingTree.BELICHICK: {
        "LB": 1.15,    # Versatile defenders
        "S": 1.1,
        "OT": 1.1,
        "IOL": 1.05,
    },
    CoachingTree.REID: {
        "WR": 1.15,
        "TE": 1.2,     # Kelce effect
        "RB": 1.1,
    },
    CoachingTree.HARBAUGH: {
        "OT": 1.2,     # Physical OL
        "IOL": 1.15,
        "EDGE": 1.1,
        "RB": 1.1,     # Power backs
    },
    CoachingTree.DEFAULT: {},
}


def get_coaching_tree_boost(team: str, position: str) -> float:
    """Get position value boost based on team's coaching tree."""
    tree = TEAM_COACHING_TREE.get(team, CoachingTree.DEFAULT)
    boosts = TREE_POSITION_BOOSTS.get(tree, {})
    return boosts.get(position, 1.0)


# =============================================================================
# SCARCITY MOMENTUM SYSTEM
# =============================================================================

@dataclass
class ScarcityTracker:
    """
    Tracks position runs to trigger scarcity momentum.
    
    Rule: If 3+ of same position go within 10 picks,
    increase desperation weight by 20% for needy teams.
    """
    recent_picks: List[Tuple[int, str]] = field(default_factory=list)  # (pick, position)
    window_size: int = 10
    trigger_count: int = 3
    desperation_boost: float = 0.20
    
    def record_pick(self, pick_number: int, position: str) -> None:
        """Record a pick for scarcity tracking."""
        self.recent_picks.append((pick_number, position))
        # Keep only recent window
        self.recent_picks = [
            (p, pos) for p, pos in self.recent_picks 
            if pick_number - p <= self.window_size
        ]
    
    def get_scarcity_positions(self, current_pick: int) -> Dict[str, float]:
        """
        Get positions currently in scarcity with their desperation boosts.
        
        Returns: {position: desperation_boost}
        """
        # Count positions in window
        position_counts: Dict[str, int] = {}
        for pick, pos in self.recent_picks:
            if current_pick - pick <= self.window_size:
                position_counts[pos] = position_counts.get(pos, 0) + 1
        
        # Return positions at or above trigger
        return {
            pos: self.desperation_boost 
            for pos, count in position_counts.items() 
            if count >= self.trigger_count
        }
    
    def get_desperation_for_team(
        self, 
        team: str, 
        team_needs: List[str], 
        current_pick: int
    ) -> float:
        """
        Calculate total desperation boost for a team based on their needs
        and current scarcity momentum.
        """
        scarcity = self.get_scarcity_positions(current_pick)
        
        # Sum desperation for positions team needs that are in scarcity
        total_boost = 0.0
        for need in team_needs[:3]:  # Top 3 needs
            if need in scarcity:
                total_boost += scarcity[need]
        
        return min(total_boost, 0.30)  # Cap at 30%


# =============================================================================
# TRADE PSYCHOLOGY
# =============================================================================

class TradePersonality(Enum):
    """Team trade personality types."""
    GAMBLER = "gambler"       # Overpays to jump rivals
    HOARDER = "hoarder"       # Seeks trade-downs, accumulates
    BALANCED = "balanced"     # Situational


# Trade personality mapping
TEAM_TRADE_PERSONALITY: Dict[str, TradePersonality] = {
    # Gamblers - will overpay 10% to jump a rival
    "PHI": TradePersonality.GAMBLER,
    "ARI": TradePersonality.GAMBLER,
    "JAX": TradePersonality.GAMBLER,
    "NO": TradePersonality.GAMBLER,
    "ATL": TradePersonality.GAMBLER,
    "LV": TradePersonality.GAMBLER,
    "CHI": TradePersonality.GAMBLER,
    
    # Hoarders - seek trade-downs if Tier 1 gone
    "BAL": TradePersonality.HOARDER,
    "CLE": TradePersonality.HOARDER,
    "NE": TradePersonality.HOARDER,
    "GB": TradePersonality.HOARDER,
    "IND": TradePersonality.HOARDER,
    
    # Balanced
    "SF": TradePersonality.BALANCED,
    "KC": TradePersonality.BALANCED,
    "DAL": TradePersonality.BALANCED,
    "NYG": TradePersonality.BALANCED,
}


def get_trade_personality(team: str) -> TradePersonality:
    """Get team's trade personality."""
    return TEAM_TRADE_PERSONALITY.get(team, TradePersonality.BALANCED)


def should_seek_trade_down(
    team: str, 
    best_available_tier: PositionTier,
    team_needs: List[str]
) -> bool:
    """
    Determine if team should seek trade-down.
    
    Hoarders trade down if no Tier 1 talent matches needs.
    """
    personality = get_trade_personality(team)
    
    if personality != TradePersonality.HOARDER:
        return False
    
    # Hoarders trade down if best available isn't premium
    if best_available_tier not in [PositionTier.PREMIUM, PositionTier.HYBRID]:
        return random.random() < 0.4  # 40% chance to try trade-down
    
    return False


def get_rival_jump_bonus(trading_team: str, target_pick_team: str) -> float:
    """
    Get bonus willingness to overpay when jumping a divisional rival.
    
    Gamblers pay 10% extra to jump rivals.
    """
    # Division rivalries
    DIVISIONS = {
        "AFC_EAST": ["BUF", "MIA", "NE", "NYJ"],
        "AFC_NORTH": ["BAL", "CIN", "CLE", "PIT"],
        "AFC_SOUTH": ["HOU", "IND", "JAX", "TEN"],
        "AFC_WEST": ["DEN", "KC", "LV", "LAC"],
        "NFC_EAST": ["DAL", "NYG", "PHI", "WAS"],
        "NFC_NORTH": ["CHI", "DET", "GB", "MIN"],
        "NFC_SOUTH": ["ATL", "CAR", "NO", "TB"],
        "NFC_WEST": ["ARI", "LAR", "SF", "SEA"],
    }
    
    # Check if same division
    for teams in DIVISIONS.values():
        if trading_team in teams and target_pick_team in teams:
            if get_trade_personality(trading_team) == TradePersonality.GAMBLER:
                return 0.10  # 10% extra willingness
            return 0.05  # 5% for non-gamblers
    
    return 0.0


# =============================================================================
# IRON LOGIC AI DECISION ENGINE
# =============================================================================

@dataclass
class IronLogicEngine:
    """
    The Iron Logic AI decision engine.
    
    Combines all subsystems to make intelligent draft decisions:
    - Team aggression for trade probability
    - DVM for prospect evaluation  
    - Coaching tree for scheme fit
    - Scarcity momentum for panic picks
    - Trade psychology for negotiation
    """
    scarcity_tracker: ScarcityTracker = field(default_factory=ScarcityTracker)
    
    def evaluate_prospect_for_team(
        self,
        prospect_name: str,
        prospect_position: str,
        prospect_rank: int,
        team: str,
        team_needs: List[str],
    ) -> Dict[str, any]:
        """
        Comprehensive prospect evaluation for a specific team.
        
        Returns evaluation with adjusted value and reasoning.
        """
        # Base DVM adjustment
        dvm = get_position_dvm(prospect_position, prospect_name)
        adjusted_rank = calculate_adjusted_rank(prospect_rank, prospect_position, prospect_name)
        
        # Coaching tree boost
        tree_boost = get_coaching_tree_boost(team, prospect_position)
        
        # Need multiplier (1.0-1.3 based on need priority)
        need_mult = 1.0
        if prospect_position in team_needs:
            need_index = team_needs.index(prospect_position)
            need_mult = 1.3 - (need_index * 0.1)  # 1.3 for #1 need, 1.2 for #2, etc.
        
        # Final score (lower = better)
        final_score = adjusted_rank / (tree_boost * need_mult)
        
        return {
            "prospect_name": prospect_name,
            "position": prospect_position,
            "base_rank": prospect_rank,
            "dvm": dvm,
            "adjusted_rank": adjusted_rank,
            "tree_boost": tree_boost,
            "need_mult": need_mult,
            "final_score": final_score,
            "fills_need": prospect_position in team_needs,
            "is_hybrid_eraser": prospect_name in HYBRID_ERASERS,
            "is_generational": prospect_name in GENERATIONAL_TALENTS,
        }
    
    def should_trade_up(
        self,
        team: str,
        team_needs: List[str],
        current_pick: int,
        target_pick: int,
        target_prospect_position: str,
    ) -> Tuple[bool, float, str]:
        """
        Determine if team should attempt to trade up.
        
        Returns: (should_trade, overpay_willingness, reason)
        """
        # Get base probability
        desperation = self.scarcity_tracker.get_desperation_for_team(
            team, team_needs, current_pick
        )
        trade_prob = get_trade_up_probability(team, desperation)
        
        # Check if target position matches need
        position_matches_need = target_prospect_position in team_needs[:3]
        if not position_matches_need:
            trade_prob *= 0.3  # Much less likely if not a need
        
        # Premium position bonus
        tier, _ = POSITION_DVM.get(target_prospect_position, (PositionTier.INTERIOR, 1.0))
        if tier == PositionTier.PREMIUM:
            trade_prob *= 1.3
        
        # Roll the dice
        should_trade = random.random() < trade_prob
        
        # Calculate overpay willingness
        base_overpay = get_overpay_willingness(team)
        if desperation > 0:
            base_overpay += desperation * 0.5  # Desperate teams overpay more
        
        # Generate reason
        if should_trade:
            if desperation > 0.1:
                reason = f"Scarcity momentum on {target_prospect_position}"
            elif tier == PositionTier.PREMIUM:
                reason = f"Premium position ({target_prospect_position}) available"
            else:
                reason = f"Filling top need ({target_prospect_position})"
        else:
            reason = "Holding position"
        
        return should_trade, base_overpay, reason
    
    def record_pick(self, pick_number: int, position: str) -> None:
        """Record a pick for scarcity tracking."""
        self.scarcity_tracker.record_pick(pick_number, position)
    
    def get_war_room_secret(
        self,
        team: str,
        prospect_name: str,
        prospect_position: str,
        was_trade: bool = False,
    ) -> str:
        """
        Generate a one-sentence "War Room Secret" explaining the pick.
        """
        tree = TEAM_COACHING_TREE.get(team, CoachingTree.DEFAULT)
        aggression = get_aggression_tier(team)
        
        secrets = []
        
        # Coaching tree insight
        if tree == CoachingTree.SHANAHAN_MCVAY:
            if prospect_position in ["WR", "RB"]:
                secrets.append(f"Shanahan tree values YAC and lateral agility")
            elif prospect_position == "OT":
                secrets.append(f"Zone scheme demands athletic blockers")
        elif tree == CoachingTree.GREEN_BAY:
            secrets.append(f"Gute prioritizes premium positions and RAS scores")
        elif tree == CoachingTree.BELICHICK:
            secrets.append(f"Values versatility over measurables")
        
        # Trade insight
        if was_trade:
            if aggression == AggressionTier.PREDATOR:
                secrets.append(f"Predator mentality—{team} paid the premium")
            elif aggression == AggressionTier.ANCHOR:
                secrets.append(f"Rare aggressive move for conservative {team}")
        
        # Hybrid/Generational
        if prospect_name in HYBRID_ERASERS:
            secrets.append(f"'Eraser' trait for Big Nickel packages")
        if prospect_name in GENERATIONAL_TALENTS:
            secrets.append(f"Generational talent overrides positional value")
        
        return secrets[0] if secrets else f"{team} fills a roster need"


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Aggression
    "TEAM_AGGRESSION",
    "AggressionTier",
    "get_aggression_tier",
    "get_trade_up_probability",
    "get_overpay_willingness",
    
    # DVM
    "POSITION_DVM",
    "PositionTier",
    "get_position_dvm",
    "calculate_adjusted_rank",
    "HYBRID_ERASERS",
    "GENERATIONAL_TALENTS",
    
    # Coaching Trees
    "CoachingTree",
    "TEAM_COACHING_TREE",
    "get_coaching_tree_boost",
    
    # Scarcity
    "ScarcityTracker",
    
    # Trade Psychology
    "TradePersonality",
    "get_trade_personality",
    "should_seek_trade_down",
    "get_rival_jump_bonus",
    
    # Engine
    "IronLogicEngine",
]
