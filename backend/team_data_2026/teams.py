"""
2026 NFL TEAM NEEDS & TRADE TENDENCIES
======================================
Updated: February 27, 2026
Sources: Underdog Network, FantasyPros, CBS Sports, PFF

Comprehensive team needs for Draft Room AI training.
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


# =============================================================================
# 2026 DRAFT ORDER (Post-Season)
# =============================================================================

DRAFT_ORDER_2026 = [
    "LV",   # 1 - Raiders (3-14)
    "NYJ",  # 2 - Jets (3-14)
    "ARI",  # 3 - Cardinals (3-14) 
    "TEN",  # 4 - Titans (3-14)
    "NYG",  # 5 - Giants (4-13)
    "CLE",  # 6 - Browns (5-12)
    "WAS",  # 7 - Commanders (5-12)
    "NO",   # 8 - Saints (6-11)
    "KC",   # 9 - Chiefs (6-11)
    "CIN",  # 10 - Bengals (6-11)
    "MIA",  # 11 - Dolphins (7-10)
    "DAL",  # 12 - Cowboys (7-9-1)
    "LAR",  # 13 - Rams (via ATL trade) (8-9)
    "BAL",  # 14 - Ravens (8-9)
    "TB",   # 15 - Buccaneers (8-9)
    "NYJ",  # 16 - Jets (via IND trade) (8-9)
    "DET",  # 17 - Lions (9-8)
    "MIN",  # 18 - Vikings (9-8)
    "CAR",  # 19 - Panthers (8-9)
    "DAL",  # 20 - Cowboys (via GB trade) (9-7-1)
    "PIT",  # 21 - Steelers (10-7)
    "LAC",  # 22 - Chargers (11-6)
    "PHI",  # 23 - Eagles (11-6)
    "CLE",  # 24 - Browns (via JAX trade) (13-4)
    "CHI",  # 25 - Bears (11-6)
    "BUF",  # 26 - Bills (12-5)
    "SF",   # 27 - 49ers (12-5)
    "HOU",  # 28 - Texans (12-5)
    "LAR",  # 29 - Rams (12-5)
    "DEN",  # 30 - Broncos (14-3)
    "NE",   # 31 - Patriots (14-3)
    "SEA",  # 32 - Seahawks (14-3)
]


# =============================================================================
# 2026 TEAM NEEDS - FROM UNDERDOG NETWORK, CBS, FANTASYPROS
# =============================================================================

# Format: Team -> List of needs in priority order (most urgent first)
TEAM_NEEDS_2026: Dict[str, List[str]] = {
    # AFC EAST
    "BUF": ["S", "EDGE", "IOL", "WR", "DT", "LB"],
    "MIA": ["QB", "EDGE", "WR", "CB", "IOL"],
    "NE": ["EDGE", "S", "OT", "TE", "DT"],
    "NYJ": ["QB", "IOL", "DT", "EDGE", "CB"],
    
    # AFC NORTH
    "BAL": ["DT", "IOL", "EDGE", "S", "WR", "TE", "CB"],
    "CIN": ["EDGE", "DT", "S", "IOL", "CB", "LB"],
    "CLE": ["OT", "IOL", "QB", "WR", "CB", "LB"],
    "PIT": ["QB", "IOL", "CB", "WR", "DT"],
    
    # AFC SOUTH
    "HOU": ["IOL", "DT", "RB", "S", "OT"],
    "IND": ["LB", "EDGE", "S", "WR", "OT"],
    "JAX": ["DT", "LB", "CB", "S", "RB"],
    "TEN": ["EDGE", "WR", "CB", "IOL"],
    
    # AFC WEST
    "DEN": ["LB", "DT", "TE", "RB", "WR"],
    "KC": ["CB", "S", "RB", "EDGE", "WR"],
    "LAC": ["EDGE", "IOL", "DT", "S", "CB"],
    "LV": ["QB", "IOL", "LB", "DT", "OT", "WR"],
    
    # NFC EAST
    "DAL": ["LB", "CB", "EDGE", "RB", "S"],
    "NYG": ["OT", "IOL", "WR", "CB", "LB", "DT"],
    "PHI": ["CB", "IOL", "TE", "OT", "S"],
    "WAS": ["EDGE", "WR", "LB", "IOL"],
    
    # NFC NORTH
    "CHI": ["DT", "EDGE", "S", "LB", "OT"],
    "DET": ["DT", "EDGE", "LB", "CB", "IOL"],
    "GB": ["DT", "LB", "CB", "OT", "IOL"],
    "MIN": ["QB", "LB", "DT", "S", "CB", "WR"],
    
    # NFC SOUTH
    "ATL": ["CB", "DT", "LB", "TE", "QB", "WR"],
    "CAR": ["IOL", "LB", "S", "EDGE", "CB", "DT"],
    "NO": ["WR", "IOL", "DT", "EDGE", "CB", "LB", "RB"],
    "TB": ["LB", "EDGE", "DT", "TE", "WR", "CB"],
    
    # NFC WEST
    "ARI": ["QB", "OT", "RB", "S", "LB"],
    "LAR": ["CB", "S", "WR", "OT", "LB"],
    "SF": ["WR", "IOL", "DT", "CB"],
    "SEA": ["CB", "EDGE", "RB", "S", "IOL"],
}


# =============================================================================
# TRADE TENDENCY UPDATES - FROM PFF ANALYSIS
# =============================================================================

# Teams likely to TRADE UP (aggressive buyers)
TRADE_UP_CANDIDATES_2026 = {
    "PIT": {
        "reason": "Five picks inside top 100, desperate for WR help",
        "targets": ["WR"],
        "aggression_boost": 2.0,
    },
    "DAL": {
        "reason": "Two first-round picks, need defensive help everywhere",
        "targets": ["CB", "LB", "EDGE"],
        "aggression_boost": 1.5,
    },
    "HOU": {
        "reason": "Four picks in top 75, need OL help in weak class",
        "targets": ["OT", "IOL"],
        "aggression_boost": 1.5,
    },
}

# Teams likely to TRADE DOWN (accumulating picks)
TRADE_DOWN_CANDIDATES_2026 = {
    "WAS": {
        "reason": "Only 3 picks in top 150, needs to reload defense",
        "target_positions": ["EDGE", "LB", "CB"],
        "trade_down_likelihood": 0.7,
    },
    "LAR": {
        "reason": "Two 1st rounders, might package for veteran (McDuffie?)",
        "target_positions": ["CB"],
        "trade_down_likelihood": 0.6,
    },
}


# =============================================================================
# UPDATED TEAM AGGRESSION SCORES
# =============================================================================

# Scale 1-10, incorporating 2026 trade tendencies
TEAM_AGGRESSION_2026: Dict[str, float] = {
    # PREDATORS (8-10) - Will overpay to move up
    "PHI": 9.5,  # Howie Roseman always aggressive
    "JAX": 9.5,  # Travis Hunter trade shows aggression
    "LAR": 9.0,  # Les Snead loves big moves
    "PIT": 8.5,  # Five picks in top 100, will package for WR
    "DAL": 8.0,  # Two 1sts, aggressive for defense
    "HOU": 8.0,  # Need OL, will trade up
    "SF": 8.0,   # Lynch/Shanahan aggressive historically
    "ATL": 7.5,  # New coach might swing
    
    # OPPORTUNISTS (5-7) - Will trade if value is right
    "DET": 7.0,  # Holmes finds value
    "KC": 6.5,   # Veach makes moves
    "MIN": 6.5,  # New GM might be aggressive
    "BUF": 6.0,  # Beane is calculated
    "BAL": 6.0,  # EDC finds value
    "TB": 6.0,   # Licht is opportunistic
    "IND": 5.5,  # Ballard conservative but capable
    "LAC": 5.5,  # Telesco calculated
    "SEA": 5.5,  # Schneider trades often
    "CAR": 5.0,  # New regime, unknown
    "NO": 5.0,   # Cap strapped
    "ARI": 5.0,  # Rebuilding
    "TEN": 5.0,  # New coach, unknown
    "DEN": 5.0,  # Payton calculated
    
    # ANCHORS (2-4) - Rarely trade up, prefer BPA
    "GB": 4.5,   # Gutekunst drafts BPA
    "WAS": 4.0,  # Peters likely trades DOWN
    "CLE": 3.5,  # Berry conservative
    "NYG": 3.5,  # Schoen building through draft
    "CHI": 3.0,  # Poles patient
    "NYJ": 2.5,  # New regime, cautious
    "NE": 2.5,   # Belichick-era hangover
    "CIN": 2.0,  # Brown family conservative
    "LV": 2.0,   # Rebuilding, staying put
    "MIA": 2.0,  # New regime
}


# =============================================================================
# DIVISION RIVALRY BONUSES
# =============================================================================

# Teams that HATE each other (bonus to trade up and block)
DIVISION_RIVALRIES = {
    "PHI": ["DAL", "NYG", "WAS"],
    "DAL": ["PHI", "NYG", "WAS"],
    "NYG": ["PHI", "DAL", "WAS"],
    "WAS": ["PHI", "DAL", "NYG"],
    
    "GB": ["CHI", "MIN", "DET"],
    "CHI": ["GB", "MIN", "DET"],
    "MIN": ["GB", "CHI", "DET"],
    "DET": ["GB", "CHI", "MIN"],
    
    "NE": ["NYJ", "MIA", "BUF"],
    "NYJ": ["NE", "MIA", "BUF"],
    "MIA": ["NE", "NYJ", "BUF"],
    "BUF": ["NE", "NYJ", "MIA"],
    
    "BAL": ["PIT", "CLE", "CIN"],
    "PIT": ["BAL", "CLE", "CIN"],
    "CLE": ["BAL", "PIT", "CIN"],
    "CIN": ["BAL", "PIT", "CLE"],
    
    "KC": ["LV", "LAC", "DEN"],
    "LV": ["KC", "LAC", "DEN"],
    "LAC": ["KC", "LV", "DEN"],
    "DEN": ["KC", "LV", "LAC"],
    
    "SF": ["LAR", "SEA", "ARI"],
    "LAR": ["SF", "SEA", "ARI"],
    "SEA": ["SF", "LAR", "ARI"],
    "ARI": ["SF", "LAR", "SEA"],
    
    "TB": ["NO", "ATL", "CAR"],
    "NO": ["TB", "ATL", "CAR"],
    "ATL": ["TB", "NO", "CAR"],
    "CAR": ["TB", "NO", "ATL"],
    
    "HOU": ["TEN", "IND", "JAX"],
    "TEN": ["HOU", "IND", "JAX"],
    "IND": ["HOU", "TEN", "JAX"],
    "JAX": ["HOU", "TEN", "IND"],
}


def get_rival_jump_bonus(trading_team: str, blocking_team: str) -> float:
    """Get bonus for trading to block a division rival."""
    rivals = DIVISION_RIVALRIES.get(trading_team, [])
    if blocking_team in rivals:
        return 0.15  # 15% bonus to jump a rival
    return 0.0


def get_team_needs(team: str) -> List[str]:
    """Get prioritized needs for a team."""
    return TEAM_NEEDS_2026.get(team, ["BPA"])


def get_team_aggression(team: str) -> float:
    """Get aggression score for a team (1-10)."""
    return TEAM_AGGRESSION_2026.get(team, 5.0)


def is_trade_up_candidate(team: str) -> bool:
    """Check if team is likely to trade up."""
    return team in TRADE_UP_CANDIDATES_2026


def is_trade_down_candidate(team: str) -> bool:
    """Check if team is likely to trade down."""
    return team in TRADE_DOWN_CANDIDATES_2026


# =============================================================================
# COACHING TREE UPDATES FOR 2026
# =============================================================================

# New head coaches and their scheme preferences
NEW_COACHES_2026 = {
    "LV": {"coach": "Mike Zimmer", "scheme": "defense_first", "oline_pref": 1.1},
    "NYJ": {"coach": "???", "scheme": "unknown", "oline_pref": 1.0},
    "ARI": {"coach": "Mike LaFleur", "scheme": "shanahan_mcvay", "rb_pref": 1.2},
    "TEN": {"coach": "Robert Saleh", "scheme": "defense_first", "edge_pref": 1.2},
    "CLE": {"coach": "Todd Monken", "scheme": "air_raid", "wr_pref": 1.15},
    "BAL": {"coach": "Jesse Minter", "scheme": "defense_first", "dl_pref": 1.1},
    "CHI": {"coach": "Ben Johnson", "scheme": "shanahan_mcvay", "rb_pref": 1.15, "wr_pref": 1.1},
    "MIN": {"coach": "???", "scheme": "unknown", "qb_pref": 1.2},
    "CAR": {"coach": "???", "scheme": "unknown", "oline_pref": 1.1},
    "ATL": {"coach": "Kevin Stefanski", "scheme": "shanahan_mcvay", "te_pref": 1.15},
}


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "DRAFT_ORDER_2026",
    "TEAM_NEEDS_2026",
    "TEAM_AGGRESSION_2026",
    "TRADE_UP_CANDIDATES_2026",
    "TRADE_DOWN_CANDIDATES_2026",
    "DIVISION_RIVALRIES",
    "NEW_COACHES_2026",
    "get_team_needs",
    "get_team_aggression",
    "get_rival_jump_bonus",
    "is_trade_up_candidate",
    "is_trade_down_candidate",
]
