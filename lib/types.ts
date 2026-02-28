/**
 * types.ts — Source of Truth
 * ===========================
 * 1:1 mirror of Python dataclasses from draft_room_v3.py, iron_logic.py,
 * sparring_benchmarks_v2.py. Field names match the camelCase output of
 * `to_swift_dict()` — which is already JS-native. Zero transformation needed.
 */

// ─── Position Enum ────────────────────────────────────────────────
// Maps to POSITION_DVM keys in iron_logic.py

export const Position = {
  QB: "QB", RB: "RB", WR: "WR", TE: "TE",
  OT: "OT", IOL: "IOL", EDGE: "EDGE",
  DL: "DL", DT: "DT", LB: "LB", CB: "CB", S: "S",
} as const;

export type Position = (typeof Position)[keyof typeof Position];

export const POSITIONS: Position[] = [
  "QB", "RB", "WR", "TE", "OT", "IOL", "EDGE", "DL", "DT", "LB", "CB", "S",
];

// ─── Position Colors ──────────────────────────────────────────────
// From BigBoardView.swift positionColor + Prospect.to_swift_dict()

export const POSITION_COLOR: Record<Position, string> = {
  QB: "#d44040", RB: "#30b8c8", WR: "#9050d0", TE: "#d08030",
  OT: "#c8b020", IOL: "#c8b020", EDGE: "#30a060", DL: "#30a060",
  DT: "#30a060", LB: "#40b8a0", CB: "#5060a0", S: "#d050a0",
};

// ─── Haptic Type ──────────────────────────────────────────────────
// From HapticType(Enum) in draft_room_v3.py
// Web mapping: animation intensity class

export const HapticType = {
  NONE: "none",
  LIGHT: "light",       // 200ms ease, subtle opacity shift
  MEDIUM: "medium",     // 300ms spring, scale 1.02
  HEAVY: "heavy",       // 500ms spring + Vibration API
  SUCCESS: "success",   // Green flash + confetti
  WARNING: "warning",   // Orange pulse
  ERROR: "error",       // Red shake
  SELECTION: "selection",// Instant snap, no easing
  RIGID: "rigid",       // Hard stop, no overshoot
  SOFT: "soft",         // 400ms ease-out, gentle fade
} as const;

export type HapticType = (typeof HapticType)[keyof typeof HapticType];

// ─── Urgency Level ────────────────────────────────────────────────
// From UrgencyLevel(Enum) in draft_room_v3.py

export const UrgencyLevel = {
  LOW: 1,
  MEDIUM: 2,
  HIGH: 3,
  CRITICAL: 4,
} as const;

export type UrgencyLevel = (typeof UrgencyLevel)[keyof typeof UrgencyLevel];

// ─── Event Type ───────────────────────────────────────────────────
// From EventType(Enum) in draft_room_v3.py — ALL 16 variants

export const EventType = {
  PICK: "pick",
  TRADE: "trade",
  ROUND_START: "round_start",
  ROUND_END: "round_end",
  USER_TURN: "user_turn",
  DRAFT_START: "draft_start",
  DRAFT_COMPLETE: "draft_complete",
  TRADE_OFFER: "trade_offer",
  TRADE_ACCEPTED: "trade_accepted",
  TRADE_REJECTED: "trade_rejected",
  CLOCK_TICK: "clock_tick",
  ERROR: "error",
  SYNC_STATE: "sync_state",
  INTERRUPT_ACK: "interrupt_ack",
  RECONCILIATION: "reconciliation",
  UNDO_COMPLETE: "undo_complete",
  REDO_COMPLETE: "redo_complete",
} as const;

export type EventType = (typeof EventType)[keyof typeof EventType];

// ─── UI Hints ─────────────────────────────────────────────────────
// From UIHints dataclass in draft_room_v3.py
// to_swift_dict() output shape — already camelCase

export interface UIHints {
  id: string;
  haptic: HapticType;
  urgency: UrgencyLevel;
  colorHex: string;
  glowEffect: boolean;
  animationDurationMs: number;
  soundEffect: string | null;
  pulseAnimation: boolean;
  shakeAnimation: boolean;
  confetti: boolean;
}

// ─── Prospect ─────────────────────────────────────────────────────
// From Prospect dataclass → to_swift_dict() in draft_room_v3.py
// Extended with ProspectCard fields from sparring_benchmarks_v2.py

export interface CombineMeasurables {
  fortyTime?: number;      // e.g. 4.34
  height: string;          // e.g. "6'4\""
  weight: number;          // e.g. 218
  armLength?: number;      // inches, e.g. 33.5
  verticalJump?: number;   // inches
  broadJump?: number;      // inches
  threeConeDrill?: number; // seconds
  shuttle?: number;        // seconds
  benchPress?: number;     // reps at 225
  ras?: number;            // Relative Athletic Score 0-10
}

// Position-relative percentiles for bar rendering.
// 1.0 = elite for position, 0.0 = bottom of position group.
// Computed server-side against position averages.
export interface AthleticPercentiles {
  speed: number;           // from fortyTime (inverted — lower is better)
  explosiveness: number;   // from vertical + broad
  agility: number;         // from 3-cone + shuttle
  size: number;            // from height + weight vs position avg
}

export interface Prospect {
  id: string;
  rank: number;
  name: string;
  position: Position;
  school: string;
  positionColorHex: string;
  primaryTrait: string;
  proComp: string;
  // Extended fields from ProspectCard
  systemFit?: string;          // narrative label: "Shanahan Zone Fit"
  systemFitPct?: number;       // 0–100, drives glow threshold
  tier?: number;
  isHybridEraser?: boolean;
  isGenerational?: boolean;
  warRoomSecret?: string;
  // Combine + Athletic Profile
  measurables?: CombineMeasurables;
  percentiles?: AthleticPercentiles;
  // Archetype tag shown as cinematic subtitle
  archetypeTag?: string;       // "Generational Speed" | "Hybrid Eraser" | etc
}

// ─── Draft Event ──────────────────────────────────────────────────
// From DraftEvent dataclass → to_swift_dict() in draft_room_v3.py
// This is the WebSocket message envelope.

export interface DraftEvent {
  id: string;
  type: EventType;
  timestamp: string;
  sequenceNumber: number;
  uiHints: UIHints;
  currentPick: number;
  currentRound: number;
  picksRemaining: number;
  isReconciliation: boolean;
  requiresAck: boolean;
  payload: Record<string, any>;
}

// ─── Pick Record ──────────────────────────────────────────────────
// Client-side representation of a completed pick.
// Assembled from PICK event payload.

export interface PickRecord {
  pickNumber: number;
  team: string;
  prospect: Prospect;
  sequenceNumber: number;
  isOptimistic: boolean; // true until server confirms
  warRoomSecret?: string;
}

// ─── Trade Offer ──────────────────────────────────────────────────
// From TRADE_OFFER event payload in draft_room_v3.py

export type TradeFairness = "steal" | "fair" | "overpay" | "bad";

export interface TradeOffer {
  offerId: string;
  fromTeam: string;
  toTeam: string;
  youReceive: number[];     // pick numbers
  youGive: number[];        // pick numbers
  valuation: {
    offerValue: number;
    receiveValue: number;
    difference: number;
    differencePct: number;
    isFair: boolean;
    fairnessCategory: TradeFairness;
  };
}

// ─── Draft State Snapshot ─────────────────────────────────────────
// From DraftState.to_snapshot() in draft_room_v3.py
// Used for Layer 3 full reconciliation.

export interface DraftStateSnapshot {
  id: string;
  currentPick: number;
  userTeam: string;
  pickOwnership: Record<string, string>; // "1" → "LV"
  prospectsDrafted: string[];            // prospect IDs
  totalPicksMade: number;
  totalTrades: number;
}

// ─── Connection Status ────────────────────────────────────────────

export const ConnectionStatus = {
  CONNECTING: "connecting",
  CONNECTED: "connected",
  RECONNECTING: "reconnecting",
  DISCONNECTED: "disconnected",
} as const;

export type ConnectionStatus =
  (typeof ConnectionStatus)[keyof typeof ConnectionStatus];

// ─── User Commands (Client → Server) ─────────────────────────────
// Sent over WebSocket to FastAPI

export interface ClientCommand {
  type: "start" | "submit_pick" | "accept_trade" | "reject_trade"
      | "undo" | "redo" | "pause" | "resume" | "sync" | "resume_session";
  payload?: Record<string, any>;
}

// ─── Aggression Tier ──────────────────────────────────────────────
// From AggressionTier(Enum) in iron_logic.py
// Informational — used for UI trade offer styling.

export const AggressionTier = {
  PREDATOR: "predator",
  CALCULATED: "calculated",
  STRATEGIC: "strategic",
  ANCHOR: "anchor",
} as const;

export type AggressionTier =
  (typeof AggressionTier)[keyof typeof AggressionTier];

// ─── Coaching Tree ────────────────────────────────────────────────
// From CoachingTree(Enum) in iron_logic.py

export const CoachingTree = {
  SHANAHAN_MCVAY: "shanahan_mcvay",
  GREEN_BAY: "green_bay",
  BELICHICK: "belichick",
  REID: "reid",
  HARBAUGH: "harbaugh",
  DEFAULT: "default",
} as const;

export type CoachingTree = (typeof CoachingTree)[keyof typeof CoachingTree];

// ─── Rose Cinema Design Tokens ────────────────────────────────────
// Exported so every component uses the same truth.

export const T = {
  rose50:  "#fef7f7",
  rose100: "#fdeef0",
  rose200: "#f9d5db",
  rose300: "#f2adb8",
  rose400: "#e87d90",
  rose500: "#d95070",
  rose900: "#3d1c22",
  rose950: "#2a1016",
  surface: "#fefcfc",
  muted:   "#b0a5a8",
  border:  "#f0e8ea",
  bg:      "#faf6f7",
  steal:   "#4aba7a",
  fair:    "#5c8dd6",
  overpay: "#e0a030",
  bad:     "#d44040",
} as const;
