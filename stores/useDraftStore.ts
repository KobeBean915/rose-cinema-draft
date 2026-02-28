/**
 * useDraftStore.ts — Three-Layer Optimistic Architecture (v2: Jitter-Proof)
 * ==========================================================================
 *
 * RECONCILIATION CONTRACT:
 * ────────────────────────
 * When a PICK event arrives from the server, there are exactly 3 cases:
 *
 *   CASE A — Confirmation of optimistic pick (prospect.id ∈ pendingPicks)
 *     → "Silent Promote": overwrite isOptimistic=false, update sequenceNumber.
 *     → If the server sequence matches the optimistic sequence AND the pick
 *       content is identical, return the SAME array reference (no re-render).
 *     → If the sequence differs, splice to correct position (binary insert).
 *     → Remove from pendingPicks.
 *     → UI stays static. Zero flicker.
 *
 *   CASE B — New AI pick (prospect.id ∉ pendingPicks, ∉ draftedIds)
 *     → "Soft Insert": binary-insert at correct sequenceNumber index.
 *     → New array reference → triggers list re-render with Framer layout anim.
 *
 *   CASE C — Duplicate/stale event (prospect.id ∈ draftedIds, ∉ pendingPicks)
 *     → Discard. No state mutation. No re-render.
 *
 * ERROR ROLLBACK:
 *   When an ERROR event arrives with a prospectId in payload:
 *     → Remove the optimistic pick from picks[]
 *     → Remove from draftedIds and pendingPicks
 *     → Set shakeTarget = prospectId (triggers shake animation in UI)
 *     → Restore isUserTurn = true so the user can re-pick
 *     → Auto-clear shakeTarget after 600ms
 */

import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";
import type {
  PickRecord,
  Prospect,
  DraftEvent,
  TradeOffer,
  DraftStateSnapshot,
  ConnectionStatus,
  UIHints,
  TradeFairness,
} from "../lib/types";

// ─── Store Shape ──────────────────────────────────────────────────

interface DraftStore {
  // === Server-Mirrored State ===
  picks: PickRecord[];
  currentPick: number;
  currentRound: number;
  picksRemaining: number;
  draftedIds: Set<string>;
  userTeam: string;
  isStarted: boolean;
  isComplete: boolean;

  // === Optimistic Tracking ===
  pendingPicks: Set<string>;
  lastConfirmedSequence: number;
  highWaterSequence: number;

  // === UI Interaction State ===
  isUserTurn: boolean;
  tradeOffer: TradeOffer | null;
  isPaused: boolean;
  warRoomSecret: string;
  lastUiHints: UIHints | null;

  // === Error / Rollback Animation ===
  shakeTarget: string | null;

  // === Recommendations ===
  recommendations: Prospect[];

  // === Connection ===
  connectionStatus: ConnectionStatus;

  // === Undo/Redo ===
  canUndo: boolean;
  canRedo: boolean;
  undoDescription: string | null;

  // === Actions: Layer 1 (Optimistic) ===
  makePick: (prospect: Prospect) => void;
  acceptTrade: () => void;
  rejectTrade: () => void;
  togglePause: () => void;

  // === Actions: Layer 2 (Server Events) ===
  processIncomingEvent: (event: DraftEvent) => void;

  // === Actions: Layer 3 (Reconciliation) ===
  syncFullState: (snapshot: DraftStateSnapshot, serverPicks: PickRecord[]) => void;

  // === Actions: Connection ===
  setConnectionStatus: (status: ConnectionStatus) => void;
  setUserTeam: (team: string) => void;
  clearShake: () => void;
}

// ─── Helpers ──────────────────────────────────────────────────────

function insertPickSorted(picks: PickRecord[], pick: PickRecord): PickRecord[] {
  const next = [...picks];
  const seq = pick.sequenceNumber;

  // Fast path: append (most common)
  if (next.length === 0 || seq > next[next.length - 1].sequenceNumber) {
    next.push(pick);
    return next;
  }

  // Exact duplicate sequence → replace in place
  const dupeIdx = next.findIndex(p => p.sequenceNumber === seq);
  if (dupeIdx !== -1) {
    next[dupeIdx] = pick;
    return next;
  }

  // Out-of-order: binary search for insertion point
  let lo = 0;
  let hi = next.length;
  while (lo < hi) {
    const mid = (lo + hi) >>> 1;
    if (next[mid].sequenceNumber < seq) lo = mid + 1;
    else hi = mid;
  }
  next.splice(lo, 0, pick);
  return next;
}

/**
 * Content equality (ignoring isOptimistic and sequenceNumber).
 * If true, the confirmation changes nothing visible → skip re-render.
 */
function pickContentEqual(a: PickRecord, b: PickRecord): boolean {
  return (
    a.pickNumber === b.pickNumber &&
    a.team === b.team &&
    a.prospect.id === b.prospect.id
  );
}

function prospectFromPayload(payload: Record<string, any>): Prospect {
  const p = payload.prospect || payload;
  return {
    id: p.id,
    rank: p.rank,
    name: p.name,
    position: p.position,
    school: p.school,
    positionColorHex: p.positionColorHex || "#888",
    primaryTrait: p.primaryTrait || p.primary_trait || "",
    proComp: p.proComp || p.pro_comp || "",
    systemFit: p.systemFit || p.system_fit,
    systemFitPct: p.systemFitPct ?? p.system_fit_pct,
    tier: p.tier,
    isHybridEraser: p.isHybridEraser ?? p.is_hybrid_eraser,
    isGenerational: p.isGenerational ?? p.is_generational,
    warRoomSecret: payload.war_room_secret || payload.warRoomSecret || p.warRoomSecret,
    measurables: p.measurables,
    percentiles: p.percentiles,
    archetypeTag: p.archetypeTag || p.archetype_tag,
  };
}

function tradeOfferFromPayload(payload: Record<string, any>): TradeOffer {
  return {
    offerId: payload.offer_id,
    fromTeam: payload.from_team,
    toTeam: payload.to_team,
    youReceive: payload.you_receive,
    youGive: payload.you_give,
    valuation: {
      offerValue: payload.valuation?.offer_value ?? 0,
      receiveValue: payload.valuation?.receive_value ?? 0,
      difference: payload.valuation?.difference ?? 0,
      differencePct: payload.valuation?.difference_pct ?? 0,
      isFair: payload.valuation?.is_fair ?? true,
      fairnessCategory: (payload.valuation?.fairness_category ?? "fair") as TradeFairness,
    },
  };
}

// ─── Store ────────────────────────────────────────────────────────

export const useDraftStore = create<DraftStore>()(
  subscribeWithSelector((set, get) => ({
    picks: [],
    currentPick: 1,
    currentRound: 1,
    picksRemaining: 257,
    draftedIds: new Set<string>(),
    userTeam: "NYG",
    isStarted: false,
    isComplete: false,

    pendingPicks: new Set<string>(),
    lastConfirmedSequence: 0,
    highWaterSequence: 0,

    isUserTurn: false,
    tradeOffer: null,
    isPaused: false,
    warRoomSecret: "",
    lastUiHints: null,

    shakeTarget: null,

    recommendations: [],
    connectionStatus: "connecting",

    canUndo: false,
    canRedo: false,
    undoDescription: null,

    // ═════════════════════════════════════════════════════════════
    // LAYER 1 — Optimistic
    // ═════════════════════════════════════════════════════════════

    makePick: (prospect) => {
      const state = get();
      if (!state.isUserTurn) return;

      const optimisticSeq = state.highWaterSequence + 1;

      const optimisticPick: PickRecord = {
        pickNumber: state.currentPick,
        team: state.userTeam,
        prospect,
        sequenceNumber: optimisticSeq,
        isOptimistic: true,
        warRoomSecret: prospect.warRoomSecret,
      };

      set({
        picks: insertPickSorted(state.picks, optimisticPick),
        currentPick: state.currentPick + 1,
        draftedIds: new Set([...state.draftedIds, prospect.id]),
        pendingPicks: new Set([...state.pendingPicks, prospect.id]),
        isUserTurn: false,
        recommendations: [],
        warRoomSecret: prospect.warRoomSecret ?? "",
        highWaterSequence: optimisticSeq,
      });
    },

    acceptTrade: () => set({ tradeOffer: null }),
    rejectTrade: () => set({ tradeOffer: null }),
    togglePause: () => set((s) => ({ isPaused: !s.isPaused })),
    clearShake: () => set({ shakeTarget: null }),

    // ═════════════════════════════════════════════════════════════
    // LAYER 2 — Server Events (Jitter-Proof)
    // ═════════════════════════════════════════════════════════════

    processIncomingEvent: (event) => {
      const state = get();
      const seq = event.sequenceNumber;
      const newHigh = Math.max(state.highWaterSequence, seq);

      const baseUpdate: Partial<DraftStore> = {
        currentPick: event.currentPick,
        currentRound: event.currentRound,
        picksRemaining: event.picksRemaining,
        lastUiHints: event.uiHints,
        lastConfirmedSequence: Math.max(state.lastConfirmedSequence, seq),
        highWaterSequence: newHigh,
      };

      switch (event.type) {
        case "draft_start": {
          set({
            ...baseUpdate,
            isStarted: true,
            userTeam: event.payload.user_team ?? state.userTeam,
          });
          break;
        }

        // ─── PICK — Three-Case Reconciliation ───────────────────
        case "pick": {
          const prospect = prospectFromPayload(event.payload);
          const team = event.payload.team as string;
          const pickNum = event.payload.pick as number;

          const confirmedPick: PickRecord = {
            pickNumber: pickNum,
            team,
            prospect,
            sequenceNumber: seq,
            isOptimistic: false,
            warRoomSecret: event.payload.war_room_secret,
          };

          // ── CASE C: Stale duplicate ──
          if (state.draftedIds.has(prospect.id) && !state.pendingPicks.has(prospect.id)) {
            set(baseUpdate);
            break;
          }

          // ── CASE A: Optimistic confirmation ──
          if (state.pendingPicks.has(prospect.id)) {
            const optimisticIdx = state.picks.findIndex(
              (p) => p.prospect.id === prospect.id && p.isOptimistic,
            );

            if (optimisticIdx !== -1) {
              const existing = state.picks[optimisticIdx];
              const nextPending = new Set(state.pendingPicks);
              nextPending.delete(prospect.id);

              // Silent promote: same sequence, same content → minimal mutation
              if (existing.sequenceNumber === seq && pickContentEqual(existing, confirmedPick)) {
                const silentPicks = [...state.picks];
                silentPicks[optimisticIdx] = {
                  ...existing,
                  isOptimistic: false,
                  sequenceNumber: seq,
                  warRoomSecret: confirmedPick.warRoomSecret ?? existing.warRoomSecret,
                  // Merge server-enriched fields (measurables, percentiles)
                  prospect: { ...existing.prospect, ...confirmedPick.prospect },
                };

                set({
                  ...baseUpdate,
                  picks: silentPicks,
                  pendingPicks: nextPending,
                  warRoomSecret: confirmedPick.warRoomSecret ?? state.warRoomSecret,
                });
                break;
              }

              // Sequence mismatch → remove optimistic, re-insert at correct position
              const withoutOptimistic = state.picks.filter(
                (_, i) => i !== optimisticIdx,
              );

              set({
                ...baseUpdate,
                picks: insertPickSorted(withoutOptimistic, confirmedPick),
                pendingPicks: nextPending,
                warRoomSecret: confirmedPick.warRoomSecret ?? state.warRoomSecret,
              });
              break;
            }

            // Edge case: pending but not in picks array
            const nextPending = new Set(state.pendingPicks);
            nextPending.delete(prospect.id);
            set({
              ...baseUpdate,
              picks: insertPickSorted(state.picks, confirmedPick),
              draftedIds: new Set([...state.draftedIds, prospect.id]),
              pendingPicks: nextPending,
              warRoomSecret: confirmedPick.warRoomSecret ?? state.warRoomSecret,
            });
            break;
          }

          // ── CASE B: New AI pick ──
          const nextDrafted = new Set(state.draftedIds);
          nextDrafted.add(prospect.id);

          set({
            ...baseUpdate,
            picks: insertPickSorted(state.picks, confirmedPick),
            draftedIds: nextDrafted,
            warRoomSecret: event.payload.war_room_secret ?? state.warRoomSecret,
          });
          break;
        }

        // ─── ERROR — Rollback + Shake ───────────────────────────
        case "error": {
          const errorProspectId = event.payload.prospect_id as string | undefined;

          if (errorProspectId && state.pendingPicks.has(errorProspectId)) {
            const rolledBackPicks = state.picks.filter(
              (p) => !(p.prospect.id === errorProspectId && p.isOptimistic),
            );
            const nextDrafted = new Set(state.draftedIds);
            nextDrafted.delete(errorProspectId);
            const nextPending = new Set(state.pendingPicks);
            nextPending.delete(errorProspectId);

            set({
              ...baseUpdate,
              picks: rolledBackPicks,
              draftedIds: nextDrafted,
              pendingPicks: nextPending,
              isUserTurn: true,
              currentPick: state.currentPick - 1,
              shakeTarget: errorProspectId,
            });

            setTimeout(() => get().clearShake(), 600);
          } else {
            set(baseUpdate);
          }
          break;
        }

        case "user_turn": {
          const recs = (event.payload.recommendations || []).map(
            (r: any): Prospect => prospectFromPayload(r),
          );
          set({ ...baseUpdate, isUserTurn: true, recommendations: recs });
          break;
        }

        case "trade_offer": {
          set({ ...baseUpdate, tradeOffer: tradeOfferFromPayload(event.payload) });
          break;
        }

        case "trade_accepted":
        case "trade_rejected": {
          set({ ...baseUpdate, tradeOffer: null });
          break;
        }

        case "round_start":
        case "round_end": {
          set(baseUpdate);
          break;
        }

        case "sync_state": {
          const snapshot = event.payload.snapshot as DraftStateSnapshot | undefined;
          if (snapshot) {
            set({
              ...baseUpdate,
              draftedIds: new Set(snapshot.prospectsDrafted),
              canUndo: event.payload.can_undo ?? state.canUndo,
              canRedo: event.payload.can_redo ?? state.canRedo,
              undoDescription: event.payload.undo_description ?? null,
            });
          }
          break;
        }

        case "reconciliation": {
          const snapshot = event.payload.snapshot as DraftStateSnapshot | undefined;
          if (snapshot) {
            set({ ...baseUpdate, draftedIds: new Set(snapshot.prospectsDrafted) });
          }
          break;
        }

        case "undo_complete": {
          const lastPick = state.picks[state.picks.length - 1];
          if (lastPick) {
            const nextDrafted = new Set(state.draftedIds);
            nextDrafted.delete(lastPick.prospect.id);
            set({
              ...baseUpdate,
              picks: state.picks.slice(0, -1),
              draftedIds: nextDrafted,
            });
          } else {
            set(baseUpdate);
          }
          break;
        }

        case "redo_complete": {
          set(baseUpdate);
          break;
        }

        case "draft_complete": {
          set({ ...baseUpdate, isComplete: true });
          break;
        }

        case "interrupt_ack": {
          const action = event.payload.action as string;
          if (action === "paused") set({ ...baseUpdate, isPaused: true });
          else if (action === "resumed") set({ ...baseUpdate, isPaused: false });
          else set(baseUpdate);
          break;
        }

        default: {
          set(baseUpdate);
          break;
        }
      }
    },

    // ═════════════════════════════════════════════════════════════
    // LAYER 3 — Full Reconciliation
    // ═════════════════════════════════════════════════════════════

    syncFullState: (snapshot, serverPicks) => {
      const state = get();
      const confirmedIds = new Set(serverPicks.map((p) => p.prospect.id));
      const survivingOptimistic = state.picks.filter(
        (p) => p.isOptimistic && !confirmedIds.has(p.prospect.id),
      );

      const merged = [...serverPicks, ...survivingOptimistic].sort(
        (a, b) => a.sequenceNumber - b.sequenceNumber,
      );

      set({
        picks: merged,
        currentPick: snapshot.currentPick,
        draftedIds: new Set(snapshot.prospectsDrafted),
        pendingPicks: new Set(survivingOptimistic.map((p) => p.prospect.id)),
        userTeam: snapshot.userTeam,
        lastConfirmedSequence:
          serverPicks.length > 0
            ? serverPicks[serverPicks.length - 1].sequenceNumber
            : state.lastConfirmedSequence,
      });
    },

    setConnectionStatus: (status) => set({ connectionStatus: status }),
    setUserTeam: (team) => set({ userTeam: team }),
  })),
);

// ─── Derived Selectors ────────────────────────────────────────────

export const selectAvailableProspects = (
  allProspects: Prospect[],
  draftedIds: Set<string>,
): Prospect[] => allProspects.filter((p) => !draftedIds.has(p.id));

export const selectUserPicks = (state: DraftStore): PickRecord[] =>
  state.picks.filter((p) => p.team === state.userTeam);

export const selectOnTheClockTeam = (
  draftOrder: string[],
  currentPick: number,
): string => draftOrder[(currentPick - 1) % draftOrder.length];

export const selectHasPendingPicks = (state: DraftStore): boolean =>
  state.pendingPicks.size > 0;
