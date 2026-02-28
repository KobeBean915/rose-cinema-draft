"""
SPARRING BENCHMARKS - 2026 NFL Draft Prospect Database
======================================================
Updated: February 27, 2026
Sources: The Ringer Big Board, PFF, CBS Sports

Complete prospect cards for Draft Room AI training.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class ProspectTier(Enum):
    ELITE = 1      # Top 5 pick lock
    PREMIUM = 2    # Top 15 pick
    FIRST_ROUND = 3  # Round 1
    DAY_TWO = 4    # Rounds 2-3
    DEPTH = 5      # Day 3


@dataclass
class ProspectCard:
    """Complete scouting profile for a prospect."""
    name: str
    position: str
    school: str
    tier: int
    consensus_rank: Optional[int] = None
    
    # Physical profile
    height: str = ""
    weight: int = 0
    forty_time: float = 0.0
    
    # Scouting notes
    primary_trait: str = ""
    system_fit: str = ""
    pro_comp: str = ""
    
    # Draft Room AI hints
    is_hybrid_eraser: bool = False
    is_generational: bool = False
    
    # War room narrative
    war_room_secret: str = ""


# =============================================================================
# 2026 PROSPECT DATABASE - THE RINGER BIG BOARD
# =============================================================================

PROSPECT_CARDS: Dict[str, ProspectCard] = {
    # === TOP 10 ===
    
    "Fernando Mendoza": ProspectCard(
        name="Fernando Mendoza",
        position="QB",
        school="Indiana",
        tier=1,
        consensus_rank=1,
        height="6'5\"",
        weight=225,
        forty_time=4.65,
        primary_trait="Elite arm talent, ideal frame, poise",
        system_fit="Pro-style, vertical passing game",
        pro_comp="Flacco on the field, Russ on the mic",
        is_generational=True,
        war_room_secret="Raiders scouts see shades of Josh Allen—the arm, the frame, the upside. Indiana's breakout season put him on the map, but it's the arm talent that has teams salivating. Day 1 starter with franchise ceiling."
    ),
    
    "Caleb Downs": ProspectCard(
        name="Caleb Downs",
        position="S",
        school="Ohio State",
        tier=1,
        consensus_rank=2,
        height="6'0\"",
        weight=200,
        forty_time=4.38,
        primary_trait="Range, ball skills, tackling",
        system_fit="Single-high eraser, versatile safety",
        pro_comp="Minkah Fitzpatrick",
        is_hybrid_eraser=True,
        war_room_secret="The 'Minkah replacement' whispers are real—this is the single best coverage safety prospect since Fitzpatrick himself. Elite range, ball skills, and the tackling chops to play in the box. Scheme-proof."
    ),
    
    "Arvell Reese": ProspectCard(
        name="Arvell Reese",
        position="LB",
        school="Ohio State",
        tier=1,
        consensus_rank=3,
        height="6'2\"",
        weight=235,
        forty_time=4.48,
        primary_trait="Sideline-to-sideline speed, instincts",
        system_fit="4-3 MIKE, any scheme",
        pro_comp="Jihaad Campbell",
        war_room_secret="Ohio State's LB factory rolls on. Sideline-to-sideline speed with the instincts to diagnose plays pre-snap. Coverage ability is what separates him from typical thumpers. Three-down player."
    ),
    
    "Carnell Tate": ProspectCard(
        name="Carnell Tate",
        position="WR",
        school="Ohio State",
        tier=1,
        consensus_rank=4,
        height="6'2\"",
        weight=195,
        forty_time=4.42,
        primary_trait="Route running, contested catches",
        system_fit="X receiver, any scheme",
        pro_comp="Tony Hawk's Pro Skater",
        war_room_secret="Steelers are circling hard. The route-running is elite—he makes DBs look silly with his breaks. Contested catch ability gives QBs a bailout option. WR1 upside with polished technique."
    ),
    
    "David Bailey": ProspectCard(
        name="David Bailey",
        position="EDGE",
        school="Texas Tech",
        tier=1,
        consensus_rank=5,
        height="6'4\"",
        weight=255,
        forty_time=4.55,
        primary_trait="High motor, elite bend",
        system_fit="4-3 DE, versatile front",
        pro_comp="Chop Robinson",
        war_room_secret="High motor + elite bend = the Maxx Crosby comp that scouts can't unsee. Texas Tech's scheme let him rush from multiple alignments. Pass rush win rate was absurd against Big 12 tackles."
    ),
    
    "Rueben Bain Jr.": ProspectCard(
        name="Rueben Bain Jr.",
        position="EDGE",
        school="Miami FL",
        tier=1,
        consensus_rank=6,
        height="6'4\"",
        weight=250,
        forty_time=4.62,
        primary_trait="Power, inside counter",
        system_fit="4-3 DE, power scheme",
        pro_comp="Kwity Paye",
        war_room_secret="Miami's pass rush terror. Power-speed combo with a devastating inside counter move. Run defense is already NFL-ready. Could start Day 1 for any team needing edge help."
    ),
    
    "Francis Mauigoa": ProspectCard(
        name="Francis Mauigoa",
        position="OT",
        school="Miami FL",
        tier=1,
        consensus_rank=7,
        height="6'5\"",
        weight=320,
        forty_time=5.15,
        primary_trait="Power, nastiness, versatility",
        system_fit="Gap scheme, can play RT or G",
        pro_comp="Darnell Wright",
        war_room_secret="Miami's mauler. The nastiness jumps off tape—he finishes blocks and sets the tone. Can slide inside to guard if needed. Texans and Giants both have him circled."
    ),
    
    "Jeremiyah Love": ProspectCard(
        name="Jeremiyah Love",
        position="RB",
        school="Notre Dame",
        tier=1,
        consensus_rank=8,
        height="5'11\"",
        weight=210,
        forty_time=4.38,
        primary_trait="Receiving, vision, burst",
        system_fit="Any scheme, true three-down back",
        pro_comp="Travis Etienne Jr.",
        is_generational=True,
        war_room_secret="The 'Kamara comp' isn't lazy—he's a true three-down back with elite receiving chops. Notre Dame used him everywhere. Vision and burst combo is special. RB1 in this class by a mile."
    ),
    
    "Makai Lemon": ProspectCard(
        name="Makai Lemon",
        position="WR",
        school="USC",
        tier=1,
        consensus_rank=9,
        height="5'11\"",
        weight=185,
        forty_time=4.35,
        primary_trait="Separation, YAC ability",
        system_fit="Slot or Z receiver",
        pro_comp="Doug Baldwin",
        war_room_secret="Lincoln Riley's latest weapon. Separation is elite—he wins at the line and creates after the catch. Smaller frame but plays bigger. Steelers love him as a Metcalf complement."
    ),
    
    "Mansoor Delane": ProspectCard(
        name="Mansoor Delane",
        position="CB",
        school="LSU",
        tier=1,
        consensus_rank=10,
        height="6'1\"",
        weight=195,
        forty_time=4.40,
        primary_trait="Ball skills, length",
        system_fit="Press-man, outside CB",
        pro_comp="Kamari Lassiter",
        war_room_secret="LSU's latest DB export. Length and ball skills make him a turnover machine. Press technique is already polished. Cowboys and Titans both desperate for CB help."
    ),
    
    # === 11-20 ===
    
    "Spencer Fano": ProspectCard(
        name="Spencer Fano",
        position="OT",
        school="Utah",
        tier=2,
        consensus_rank=11,
        height="6'5\"",
        weight=315,
        forty_time=5.05,
        primary_trait="Athleticism, technique, versatility",
        system_fit="Zone scheme specialist",
        pro_comp="Spencer Brown",
        war_room_secret="Utah's zone scheme master. Can slide to either tackle spot Day 1. Athleticism is special for his size. Giants have him as OT1 on their board."
    ),
    
    "Vega Ioane": ProspectCard(
        name="Vega Ioane",
        position="IOL",
        school="Penn State",
        tier=2,
        consensus_rank=12,
        height="6'4\"",
        weight=325,
        forty_time=5.20,
        primary_trait="Power, anchor, intelligence",
        system_fit="Any scheme, true center or guard",
        pro_comp="Steve Avila",
        war_room_secret="Penn State's anchor. Can play all three interior spots. Intelligence allows him to make line calls immediately. Browns desperately need interior OL help."
    ),
    
    "Avieon Terrell": ProspectCard(
        name="Avieon Terrell",
        position="CB",
        school="Clemson",
        tier=2,
        consensus_rank=13,
        height="6'0\"",
        weight=190,
        forty_time=4.38,
        primary_trait="Technique, football IQ",
        system_fit="Any coverage scheme",
        pro_comp="Like if A.J. Terrell had a little brother",
        war_room_secret="Yes, A.J.'s actual brother. The technique is eerily similar. Football IQ off the charts. Could start immediately in any scheme. Falcons reunion narrative writes itself."
    ),
    
    "Keldric Faulk": ProspectCard(
        name="Keldric Faulk",
        position="EDGE",
        school="Auburn",
        tier=2,
        consensus_rank=14,
        height="6'5\"",
        weight=265,
        forty_time=4.68,
        primary_trait="Length, power, upside",
        system_fit="4-3 DE, developmental",
        pro_comp="Travon Walker",
        war_room_secret="Auburn's athletic freak. Length creates problems for tackles. Upside is immense but technique needs polish. High-ceiling, high-floor prospect for patient teams."
    ),
    
    "Akheem Mesidor": ProspectCard(
        name="Akheem Mesidor",
        position="EDGE",
        school="Miami FL",
        tier=2,
        consensus_rank=15,
        height="6'3\"",
        weight=260,
        forty_time=4.60,
        primary_trait="Versatility, motor",
        system_fit="Multiple fronts",
        pro_comp="Jim Carrey in 'The Cable Guy'",
        war_room_secret="Miami's other edge terror. Can play inside or outside. Motor never stops. Pairs perfectly with Bain in Miami's scheme. Commanders desperately need edge help."
    ),
    
    "Peter Woods": ProspectCard(
        name="Peter Woods",
        position="DT",
        school="Clemson",
        tier=2,
        consensus_rank=16,
        height="6'3\"",
        weight=305,
        forty_time=4.95,
        primary_trait="Penetration, disruption",
        system_fit="One-gap penetrator",
        pro_comp="Shai-Hulud",
        war_room_secret="Clemson's interior disruptor. Penetration ability is elite—he lives in backfields. Lions and Bears both need DT help badly. Could be the steal of the draft."
    ),
    
    "Jordyn Tyson": ProspectCard(
        name="Jordyn Tyson",
        position="WR",
        school="Arizona State",
        tier=2,
        consensus_rank=17,
        height="6'1\"",
        weight=195,
        forty_time=4.40,
        primary_trait="Speed, vertical threat",
        system_fit="Field stretcher, Z receiver",
        pro_comp="Christian Watson",
        war_room_secret="Arizona State's deep threat. Speed is legit 4.3 range. Tracks the deep ball as well as anyone. Steelers have him as WR2 behind Tate. Big play waiting to happen."
    ),
    
    "KC Concepcion": ProspectCard(
        name="KC Concepcion",
        position="WR",
        school="Texas A&M",
        tier=2,
        consensus_rank=18,
        height="5'11\"",
        weight=190,
        forty_time=4.45,
        primary_trait="Route running, hands",
        system_fit="Slot specialist",
        pro_comp="Khalil Shakir",
        war_room_secret="Texas A&M's reliable target. Hands are vice grips. Route running from the slot is polished. Could be the best pure slot in the class. Chiefs need receiver help."
    ),
    
    "Denzel Boston": ProspectCard(
        name="Denzel Boston",
        position="WR",
        school="Washington",
        tier=2,
        consensus_rank=19,
        height="6'3\"",
        weight=210,
        forty_time=4.48,
        primary_trait="Size, contested catches",
        system_fit="X receiver, red zone threat",
        pro_comp="Courtland Sutton",
        war_room_secret="Washington's big-bodied X. Contested catch rate is elite. Red zone monster. 49ers desperately need WR help after Aiyuk drama. Size-speed combo is rare."
    ),
    
    "Kenyon Sadiq": ProspectCard(
        name="Kenyon Sadiq",
        position="TE",
        school="Oregon",
        tier=2,
        consensus_rank=20,
        height="6'5\"",
        weight=250,
        forty_time=4.65,
        primary_trait="Receiving, athleticism",
        system_fit="Move TE, seam threat",
        pro_comp="Sam LaPorta",
        war_room_secret="Oregon's matchup nightmare. Athleticism for a TE is special. Seam routes are automatic. Broncos need a TE for Payton's offense. Could be TE1 immediately."
    ),
    
    # === 21-32 ===
    
    "T.J. Parker": ProspectCard(
        name="T.J. Parker",
        position="EDGE",
        school="Clemson",
        tier=3,
        consensus_rank=21,
        height="6'4\"",
        weight=255,
        forty_time=4.58,
        primary_trait="Bend, speed-to-power",
        system_fit="4-3 DE",
        pro_comp="Jermaine Johnson",
        war_room_secret="Clemson's edge depth is ridiculous. Parker has the bend to win around the corner. Speed-to-power conversion improving. Bengals need edge help after losing Hendrickson."
    ),
    
    "Cashius Howell": ProspectCard(
        name="Cashius Howell",
        position="EDGE",
        school="Texas A&M",
        tier=3,
        consensus_rank=22,
        height="6'3\"",
        weight=250,
        forty_time=4.62,
        primary_trait="Motor, versatility",
        system_fit="Multiple fronts",
        pro_comp="Byron Young",
        war_room_secret="Texas A&M's relentless rusher. Motor is elite—he never takes plays off. Can drop into coverage in a pinch. Chargers need edge depth behind Mack."
    ),
    
    "Sonny Styles": ProspectCard(
        name="Sonny Styles",
        position="LB",
        school="Ohio State",
        tier=3,
        consensus_rank=23,
        height="6'4\"",
        weight=225,
        forty_time=4.52,
        primary_trait="Size/speed, versatility, range",
        system_fit="Big Nickel, Sub-LB, hybrid",
        pro_comp="Devin Lloyd",
        is_hybrid_eraser=True,
        war_room_secret="Ohio State's Swiss Army knife. Can play safety, linebacker, or nickel. Size-speed combo is rare. True position TBD but versatility is the selling point. Cowboys would love him."
    ),
    
    "Jermod McCoy": ProspectCard(
        name="Jermod McCoy",
        position="CB",
        school="Tennessee",
        tier=3,
        consensus_rank=24,
        height="6'0\"",
        weight=190,
        forty_time=4.42,
        primary_trait="Ball skills, physicality",
        system_fit="Press-man corner",
        pro_comp="Eric Stokes",
        war_room_secret="Tennessee's ballhawk. Ball skills are elite—he attacks the ball at its highest point. Physical at the line. Dolphins need CB help desperately."
    ),
    
    "Kadyn Proctor": ProspectCard(
        name="Kadyn Proctor",
        position="OT",
        school="Alabama",
        tier=3,
        consensus_rank=25,
        height="6'7\"",
        weight=330,
        forty_time=5.25,
        primary_trait="Size, power, potential",
        system_fit="Power scheme, LT or RT",
        pro_comp="Orlando Brown Jr.",
        war_room_secret="Alabama's massive tackle. Size is overwhelming—he engulfs pass rushers. Footwork needs work but the physical tools are elite. Ravens need OT depth."
    ),
    
    "Kayden McDonald": ProspectCard(
        name="Kayden McDonald",
        position="DT",
        school="Ohio State",
        tier=3,
        consensus_rank=26,
        height="6'3\"",
        weight=310,
        forty_time=5.00,
        primary_trait="Anchor, two-gap ability",
        system_fit="3-4 nose, two-gap",
        pro_comp="An event horizon",
        war_room_secret="Ohio State's space-eater. Nothing gets past him. Two-gap ability is rare—he holds the point and sheds blocks. Packers need DT help after trading Clark."
    ),
    
    "Emmanuel Pregnon": ProspectCard(
        name="Emmanuel Pregnon",
        position="IOL",
        school="Oregon",
        tier=3,
        consensus_rank=27,
        height="6'4\"",
        weight=320,
        forty_time=5.15,
        primary_trait="Athleticism, movement skills",
        system_fit="Zone scheme guard",
        pro_comp="John Simpson",
        war_room_secret="Oregon's athletic guard. Movement skills are elite for interior lineman. Zone scheme specialist. Chargers need IOL help badly."
    ),
    
    "Chris Brazzell II": ProspectCard(
        name="Chris Brazzell II",
        position="WR",
        school="Tennessee",
        tier=3,
        consensus_rank=28,
        height="6'3\"",
        weight=205,
        forty_time=4.45,
        primary_trait="Size, catch radius",
        system_fit="X receiver",
        pro_comp="Brian Thomas Jr.",
        war_room_secret="Tennessee's big target. Catch radius is massive. Tracks the deep ball well. Ravens need outside WR help. Could pair nicely with Flowers."
    ),
    
    "Caleb Lomu": ProspectCard(
        name="Caleb Lomu",
        position="OT",
        school="Utah",
        tier=3,
        consensus_rank=29,
        height="6'5\"",
        weight=315,
        forty_time=5.10,
        primary_trait="Technique, consistency",
        system_fit="Zone or gap scheme",
        pro_comp="Roger Rosengarten",
        war_room_secret="Utah's other tackle. Less athletic than Fano but more refined. Consistent performer. Could start immediately at RT. Browns need all the OL help they can get."
    ),
    
    "Brandon Cisse": ProspectCard(
        name="Brandon Cisse",
        position="CB",
        school="South Carolina",
        tier=3,
        consensus_rank=30,
        height="6'0\"",
        weight=195,
        forty_time=4.45,
        primary_trait="Length, recovery speed",
        system_fit="Press-man corner",
        pro_comp="Jaylon Johnson",
        war_room_secret="South Carolina's lockdown corner. Length and recovery speed bail him out when beat. Improving rapidly. Eagles need CB2 opposite Mitchell."
    ),
    
    "C.J. Allen": ProspectCard(
        name="C.J. Allen",
        position="LB",
        school="Georgia",
        tier=3,
        consensus_rank=31,
        height="6'2\"",
        weight=230,
        forty_time=4.50,
        primary_trait="Instincts, tackling",
        system_fit="4-3 MIKE or WILL",
        pro_comp="Devin White",
        war_room_secret="Georgia's latest LB product. Instincts are exceptional—he finds the ball. Sure tackler. Cowboys desperately need LB help. Could be a Day 1 starter."
    ),
    
    "Colton Hood": ProspectCard(
        name="Colton Hood",
        position="CB",
        school="Tennessee",
        tier=3,
        consensus_rank=32,
        height="6'1\"",
        weight=200,
        forty_time=4.48,
        primary_trait="Size, physicality",
        system_fit="Press-man corner",
        pro_comp="Marlon Humphrey",
        war_room_secret="Tennessee's physical corner. Size allows him to match up with bigger receivers. Run support is a plus. Seahawks need CB help after losing Woolen."
    ),
}


def get_prospect_by_rank(rank: int) -> Optional[ProspectCard]:
    """Get prospect by consensus rank."""
    for card in PROSPECT_CARDS.values():
        if card.consensus_rank == rank:
            return card
    return None


def get_war_room_secret(name: str) -> str:
    """Get war room secret for a prospect."""
    card = PROSPECT_CARDS.get(name)
    return card.war_room_secret if card else f"Scouts see NFL starter potential."


def get_consensus_top_n(n: int = 32) -> List[ProspectCard]:
    """Get top N prospects by consensus rank."""
    ranked = [c for c in PROSPECT_CARDS.values() if c.consensus_rank]
    return sorted(ranked, key=lambda x: x.consensus_rank)[:n]


def get_prospects_by_position(position: str) -> List[ProspectCard]:
    """Get all prospects at a position."""
    return [c for c in PROSPECT_CARDS.values() if c.position == position]


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ProspectCard",
    "ProspectTier",
    "PROSPECT_CARDS",
    "get_prospect_by_rank",
    "get_war_room_secret",
    "get_consensus_top_n",
    "get_prospects_by_position",
]
