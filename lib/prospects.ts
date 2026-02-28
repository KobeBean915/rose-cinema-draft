/**
 * prospects.ts — Static Prospect Data
 * ======================================
 * In production, this would be a Server Component fetch from /api/prospects.
 * For now, this mirrors the 20 prospects from sparring_benchmarks_v2.py
 * that the monolith uses. The engine sends the full list in DRAFT_START payload.
 *
 * The page subscribes to the store and replaces this with server data
 * once the DRAFT_START event arrives.
 */

import type { Prospect } from "./types";

export const DRAFT_ORDER: string[] = [
  "LV", "NYJ", "ARI", "TEN", "NYG", "CLE", "WAS", "NO",
  "KC", "CIN", "MIA", "DAL", "LAR", "BAL", "TB", "NYJ",
  "DET", "MIN", "CAR", "GB", "PIT", "LAC", "PHI", "JAX",
  "CHI", "BUF", "SF", "HOU", "LAR", "DEN", "NE", "SEA",
];

export const TEAM_DISPLAY_NAMES: Record<string, string> = {
  LV: "Las Vegas Raiders", NYJ: "New York Jets", ARI: "Arizona Cardinals",
  TEN: "Tennessee Titans", NYG: "New York Giants", CLE: "Cleveland Browns",
  WAS: "Washington Commanders", NO: "New Orleans Saints", KC: "Kansas City Chiefs",
  CIN: "Cincinnati Bengals", MIA: "Miami Dolphins", DAL: "Dallas Cowboys",
  LAR: "Los Angeles Rams", BAL: "Baltimore Ravens", TB: "Tampa Bay Buccaneers",
  DET: "Detroit Lions", MIN: "Minnesota Vikings", CAR: "Carolina Panthers",
  GB: "Green Bay Packers", PIT: "Pittsburgh Steelers", LAC: "Los Angeles Chargers",
  PHI: "Philadelphia Eagles", JAX: "Jacksonville Jaguars", CHI: "Chicago Bears",
  BUF: "Buffalo Bills", SF: "San Francisco 49ers", HOU: "Houston Texans",
  DEN: "Denver Broncos", NE: "New England Patriots", SEA: "Seattle Seahawks",
};

export const INITIAL_PROSPECTS: Prospect[] = [
  { id: "p1", rank: 1, name: "Fernando Mendoza", position: "QB", school: "Indiana", positionColorHex: "#d44040", primaryTrait: "Elite arm talent, ideal frame, poise", proComp: "Flacco on the field, Russ on the mic", warRoomSecret: "Raiders scouts see shades of Josh Allen — the arm, the frame, the upside.", archetypeTag: "Franchise QB" },
  { id: "p2", rank: 2, name: "Caleb Downs", position: "S", school: "Ohio State", positionColorHex: "#d050a0", primaryTrait: "Range, ball skills, tackling", proComp: "Minkah Fitzpatrick", warRoomSecret: "The 'Minkah replacement' whispers are real — elite single-high eraser.", archetypeTag: "Hybrid Eraser", isHybridEraser: true },
  { id: "p3", rank: 3, name: "Arvell Reese", position: "LB", school: "Ohio State", positionColorHex: "#40b8a0", primaryTrait: "Sideline-to-sideline speed, instincts", proComp: "Jihaad Campbell", warRoomSecret: "Ohio State's LB factory rolls on. Coverage ability separates him.", archetypeTag: "Coverage LB" },
  { id: "p4", rank: 4, name: "Carnell Tate", position: "WR", school: "Ohio State", positionColorHex: "#9050d0", primaryTrait: "Route running, contested catches", proComp: "Tony Hawk's Pro Skater", warRoomSecret: "The route-running is elite — he makes DBs look silly.", archetypeTag: "Route Technician" },
  { id: "p5", rank: 5, name: "David Bailey", position: "EDGE", school: "Texas Tech", positionColorHex: "#30a060", primaryTrait: "High motor, elite bend", proComp: "Chop Robinson", warRoomSecret: "High motor + elite bend = the Maxx Crosby comp.", archetypeTag: "Relentless Motor" },
  { id: "p6", rank: 6, name: "Rueben Bain Jr.", position: "EDGE", school: "Miami FL", positionColorHex: "#30a060", primaryTrait: "Power, inside counter", proComp: "Kwity Paye", warRoomSecret: "Miami's pass rush terror. Power-speed combo.", archetypeTag: "Power Rusher" },
  { id: "p7", rank: 7, name: "Francis Mauigoa", position: "OT", school: "Miami FL", positionColorHex: "#c8b020", primaryTrait: "Power, nastiness, versatility", proComp: "Darnell Wright", warRoomSecret: "Miami's mauler. The nastiness jumps off tape.", archetypeTag: "Mauler" },
  { id: "p8", rank: 8, name: "Jeremiyah Love", position: "RB", school: "Notre Dame", positionColorHex: "#30b8c8", primaryTrait: "Receiving, vision, burst", proComp: "Travis Etienne Jr.", warRoomSecret: "The 'Kamara comp' isn't lazy — true three-down back.", archetypeTag: "Three-Down Back", isGenerational: true },
  { id: "p9", rank: 9, name: "Makai Lemon", position: "WR", school: "USC", positionColorHex: "#9050d0", primaryTrait: "Separation, YAC ability", proComp: "Doug Baldwin", warRoomSecret: "Lincoln Riley's latest weapon. Separation is elite.", archetypeTag: "YAC Monster" },
  { id: "p10", rank: 10, name: "Mansoor Delane", position: "CB", school: "LSU", positionColorHex: "#5060a0", primaryTrait: "Ball skills, length", proComp: "Kamari Lassiter", warRoomSecret: "LSU's latest DB export. Turnover machine.", archetypeTag: "Ball Hawk" },
  { id: "p11", rank: 11, name: "Spencer Fano", position: "OT", school: "Utah", positionColorHex: "#c8b020", primaryTrait: "Athleticism, technique, versatility", proComp: "Spencer Brown", warRoomSecret: "Utah's zone scheme master. Either tackle spot Day 1." },
  { id: "p12", rank: 12, name: "Vega Ioane", position: "IOL", school: "Penn State", positionColorHex: "#c8b020", primaryTrait: "Power, anchor, intelligence", proComp: "Steve Avila", warRoomSecret: "Penn State's anchor. Makes line calls immediately." },
  { id: "p13", rank: 13, name: "Avieon Terrell", position: "CB", school: "Clemson", positionColorHex: "#5060a0", primaryTrait: "Technique, football IQ", proComp: "A.J. Terrell's little brother", warRoomSecret: "Yes, A.J.'s actual brother. Football IQ off the charts." },
  { id: "p14", rank: 14, name: "Keldric Faulk", position: "EDGE", school: "Auburn", positionColorHex: "#30a060", primaryTrait: "Length, power, upside", proComp: "Travon Walker", warRoomSecret: "Auburn's athletic freak. Length creates problems." },
  { id: "p15", rank: 15, name: "Akheem Mesidor", position: "EDGE", school: "Miami FL", positionColorHex: "#30a060", primaryTrait: "Versatility, motor", proComp: "Jim Carrey in 'The Cable Guy'", warRoomSecret: "Miami's other edge terror. Motor never stops." },
  { id: "p16", rank: 16, name: "Peter Woods", position: "DT", school: "Clemson", positionColorHex: "#30a060", primaryTrait: "Penetration, disruption", proComp: "Shai-Hulud", warRoomSecret: "Clemson's interior disruptor. Lives in backfields." },
  { id: "p17", rank: 17, name: "Jordyn Tyson", position: "WR", school: "Arizona State", positionColorHex: "#9050d0", primaryTrait: "Speed, vertical threat", proComp: "Christian Watson", warRoomSecret: "Speed is legit 4.3 range. Tracks the deep ball.", archetypeTag: "Generational Speed" },
  { id: "p18", rank: 18, name: "KC Concepcion", position: "WR", school: "Texas A&M", positionColorHex: "#9050d0", primaryTrait: "Route running, hands", proComp: "Khalil Shakir", warRoomSecret: "Hands are vice grips. Best pure slot in the class." },
  { id: "p19", rank: 19, name: "Denzel Boston", position: "WR", school: "Washington", positionColorHex: "#9050d0", primaryTrait: "Size, contested catches", proComp: "Courtland Sutton", warRoomSecret: "Contested catch rate is elite. Red zone monster." },
  { id: "p20", rank: 20, name: "Kenyon Sadiq", position: "TE", school: "Oregon", positionColorHex: "#d08030", primaryTrait: "Receiving, athleticism", proComp: "Sam LaPorta", warRoomSecret: "Oregon's matchup nightmare. Seam routes automatic." },
];
