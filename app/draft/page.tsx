/**
 * page.tsx — Draft Room Orchestrator
 * =====================================
 * The entry point. Composes every sub-system into a running application.
 *
 * Layout:
 *   ┌──────────────────────────────┐
 *   │  StatusTicker  (fixed)       │  ← always visible, flex-shrink: 0
 *   ├──────────────────────────────┤
 *   │  TabBar                      │  ← draft / board / roster
 *   ├──────────────────────────────┤
 *   │                              │
 *   │  Active Tab Panel (scrolls)  │  ← flex: 1, overflow-y: auto
 *   │                              │
 *   ├──────────────────────────────┤
 *   │  UserTurnSheet (overlay)     │  ← AnimatePresence, position: fixed
 *   └──────────────────────────────┘
 *
 * DraftShell wraps everything in a 100vh flex-column with the grain
 * overlay and CSS custom properties already injected.
 *
 * AUTO-START FLOW:
 * ─────────────────
 * 1. Mount → useWebSocket connects → onopen fires → auto resume_from(lastSeq=0)
 * 2. Server replays buffered events (if reconnecting) or returns silence (new session)
 * 3. Page watches: if connectionStatus === "connected" AND isStarted is still false
 *    after 600ms → sends "start" command to create the engine
 * 4. Engine emits DRAFT_START → store sets isStarted=true → shutter lifts
 *
 * On reconnect, the resume_from replay hydrates isStarted before the 600ms
 * timer fires, so we never double-start. hasStartedRef guards the edge case.
 */

"use client";

import React, {
  useState, useCallback, useMemo, useEffect, useRef, memo,
} from "react";
import { motion, AnimatePresence } from "framer-motion";

// ─── Sub-systems ─────────────────────────────────────────────────
import { DraftShell } from "../../components/DraftShell";
import { StatusTicker } from "../../components/StatusTicker";
import { BigBoard } from "../../components/BigBoard";
import { DraftBoard } from "../../components/DraftBoard";
import { MyRoster } from "../../components/MyRoster";
import { UserTurnSheet } from "../../components/UserTurnSheet";
import { useWebSocket, buildDraftWsUrl } from "../../hooks/useWebSocket";
import { useDraftStore, selectOnTheClockTeam } from "../../stores/useDraftStore";
import { INITIAL_PROSPECTS, DRAFT_ORDER, TEAM_DISPLAY_NAMES } from "../../lib/prospects";
import { triggerHaptic } from "../../lib/haptics";
import { T } from "../../lib/types";
import type { Prospect } from "../../lib/types";

// ─── Stable Session ID ───────────────────────────────────────────
// Persists in localStorage so a page refresh reconnects to the same engine.
// Falls back to crypto.randomUUID() if storage is unavailable (SSR, incognito).

function getOrCreateSessionId(): string {
  if (typeof window === "undefined") return crypto.randomUUID();
  try {
    const KEY = "draft_room_session_id";
    let id = localStorage.getItem(KEY);
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem(KEY, id);
    }
    return id;
  } catch {
    return crypto.randomUUID();
  }
}

// ─── Framer Config ───────────────────────────────────────────────
const SPRING = { type: "spring" as const, stiffness: 300, damping: 30 };

// ─── Tab Definitions ─────────────────────────────────────────────
type TabId = "draft" | "board" | "roster";

const TABS: ReadonlyArray<{ id: TabId; label: string; icon: string }> = [
  { id: "draft", label: "Draft", icon: "📋" },
  { id: "board", label: "Big Board", icon: "📊" },
  { id: "roster", label: "My Roster", icon: "👤" },
];

// ═════════════════════════════════════════════════════════════════
// SUB-COMPONENTS — extracted to prevent re-render of the full tree
// ═════════════════════════════════════════════════════════════════

// ─── Tab Bar ─────────────────────────────────────────────────────

interface TabBarProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
  userPickCount: number;
}

const TabBar = memo(({ activeTab, onTabChange, userPickCount }: TabBarProps) => (
  <div style={{
    display: "flex", padding: "5px 16px", gap: 4,
    background: T.bg, borderBottom: `0.5px solid ${T.border}`,
    flexShrink: 0,
  }}>
    {TABS.map((tab) => {
      const isActive = activeTab === tab.id;
      const label = tab.id === "roster" && userPickCount > 0
        ? `${tab.label} (${userPickCount})`
        : tab.label;
      return (
        <button
          key={tab.id}
          onClick={() => {
            triggerHaptic("light");
            onTabChange(tab.id);
          }}
          style={{
            flex: 1, padding: "9px 6px",
            background: isActive ? T.surface : "transparent",
            border: "none",
            borderRadius: isActive ? 9 : 0,
            cursor: "pointer",
            color: isActive ? T.rose500 : T.muted,
            fontSize: 11, fontWeight: 600,
            letterSpacing: "0.02em",
            boxShadow: isActive ? "0 1px 6px rgba(60,20,30,0.06)" : "none",
            transition: "all 0.15s ease",
            display: "flex", alignItems: "center", justifyContent: "center",
            gap: 4,
          }}
        >
          <span style={{ fontSize: 12 }}>{tab.icon}</span>
          {label}
        </button>
      );
    })}
  </div>
));
TabBar.displayName = "TabBar";

// ─── Loading Shutter ─────────────────────────────────────────────
// Full-screen cinematic overlay. No spinners. Content-aware transition.
// Lifts with a smooth ease when connected + data arrives.

const LoadingShutter = memo(({ isVisible }: { isVisible: boolean }) => (
  <AnimatePresence>
    {isVisible && (
      <motion.div
        key="shutter"
        initial={{ opacity: 1 }}
        exit={{ opacity: 0, y: -20 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        style={{
          position: "fixed", inset: 0, zIndex: 100,
          background: `linear-gradient(180deg, ${T.rose100} 0%, ${T.rose50} 50%, ${T.surface} 100%)`,
          display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center",
          gap: 16,
        }}
      >
        {/* Grain texture on shutter surface */}
        <svg aria-hidden style={{
          position: "absolute", inset: 0, width: "100%", height: "100%",
          pointerEvents: "none", opacity: 0.04, mixBlendMode: "multiply",
        }}>
          <filter id="shutter-grain">
            <feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch" />
            <feColorMatrix type="saturate" values="0" />
          </filter>
          <rect width="100%" height="100%" filter="url(#shutter-grain)" />
        </svg>

        {/* Logo */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1, duration: 0.5 }}
          style={{ textAlign: "center", zIndex: 1 }}
        >
          <div style={{
            fontSize: 28, fontWeight: 300, color: T.rose950,
            letterSpacing: "-0.03em", marginBottom: 6,
            fontFamily: "var(--rc-font)",
          }}>
            Draft Room
          </div>
          <div style={{
            fontSize: 10, fontWeight: 700, color: T.rose400,
            letterSpacing: "0.15em", textTransform: "uppercase",
          }}>
            Rose Cinema
          </div>
        </motion.div>

        {/* Breathing bar — not a spinner, a pulse */}
        <motion.div
          animate={{ opacity: [0.3, 0.7, 0.3] }}
          transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
          style={{
            width: 32, height: 2, borderRadius: 1,
            backgroundColor: T.rose300, marginTop: 12,
          }}
        />
      </motion.div>
    )}
  </AnimatePresence>
));
LoadingShutter.displayName = "LoadingShutter";

// ─── Confetti Overlay ────────────────────────────────────────────
// NOTE: useMemo MUST be called before the early return to satisfy
// React's rules of hooks (consistent call order across renders).

const CONFETTI_PARTICLES = Array.from({ length: 12 }, (_, i) => ({
  id: i,
  left: `${10 + (((i * 37 + 13) % 80))}%`,
  delay: (i * 0.025),
  color: [T.rose400, T.rose300, T.rose500, "#ffd700", "#30b8c8"][i % 5],
  size: 4 + (i % 3) * 3,
  duration: 1.8 + (i % 4) * 0.3,
}));

const ConfettiOverlay = memo(({ active }: { active: boolean }) => {
  if (!active) return null;
  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 50, pointerEvents: "none",
      overflow: "hidden",
    }}>
      {CONFETTI_PARTICLES.map((p) => (
        <motion.div
          key={p.id}
          initial={{ y: -20, opacity: 1, scale: 1 }}
          animate={{ y: "110vh", opacity: 0, scale: 0.5, rotate: 360 }}
          transition={{ duration: p.duration, delay: p.delay, ease: "easeIn" }}
          style={{
            position: "absolute", top: 0, left: p.left,
            width: p.size, height: p.size, borderRadius: p.size / 2,
            backgroundColor: p.color,
          }}
        />
      ))}
    </div>
  );
});
ConfettiOverlay.displayName = "ConfettiOverlay";

// =================================================================
// PAGE COMPONENT
// =================================================================

export default function DraftPage() {
  // ─── Local UI State ─────────────────────────────────────────
  const [activeTab, setActiveTab] = useState<TabId>("draft");
  const [selectedProspectId, setSelectedProspectId] = useState<string | null>(null);
  const [showConfetti, setShowConfetti] = useState(false);
  const [prospects] = useState<Prospect[]>(INITIAL_PROSPECTS);

  // Guards against double-sending "start"
  const hasSentStartRef = useRef(false);

  // ─── Store Selectors (individual for minimal re-renders) ────
  const picks = useDraftStore((s) => s.picks);
  const currentPick = useDraftStore((s) => s.currentPick);
  const currentRound = useDraftStore((s) => s.currentRound);
  const userTeam = useDraftStore((s) => s.userTeam);
  const isUserTurn = useDraftStore((s) => s.isUserTurn);
  const isPaused = useDraftStore((s) => s.isPaused);
  const isStarted = useDraftStore((s) => s.isStarted);
  const draftedIds = useDraftStore((s) => s.draftedIds);
  const recommendations = useDraftStore((s) => s.recommendations);
  const connectionStatus = useDraftStore((s) => s.connectionStatus);
  const warRoomSecret = useDraftStore((s) => s.warRoomSecret);
  const lastUiHints = useDraftStore((s) => s.lastUiHints);
  const makePick = useDraftStore((s) => s.makePick);
  const togglePause = useDraftStore((s) => s.togglePause);

  // ─── Derived ────────────────────────────────────────────────
  const userPicks = useMemo(
    () => picks.filter((p) => p.team === userTeam),
    [picks, userTeam],
  );
  const onTheClockTeam = useMemo(
    () => selectOnTheClockTeam(DRAFT_ORDER, currentPick),
    [currentPick],
  );

  // ─── Shutter Visibility ─────────────────────────────────────
  // Holds until: connected AND (engine started OR picks replayed)
  const shutterVisible =
    connectionStatus !== "connected" || (!isStarted && picks.length === 0);

  // ─── WebSocket ──────────────────────────────────────────────
  // Session ID is stable across refreshes (localStorage).
  // URL includes team so server can create the engine with the right side.
  const sessionId = useMemo(getOrCreateSessionId, []);
  const wsUrl = useMemo(
    () => buildDraftWsUrl(sessionId, userTeam),
    [sessionId, userTeam],
  );

  const { sendCommand } = useWebSocket({
    url: wsUrl,
    autoConnect: true,
    debug: process.env.NODE_ENV === "development",
  });

  // ─── Auto-Start Engine ──────────────────────────────────────
  //
  // The useWebSocket hook already sends `resume_from(lastConfirmedSeq)`
  // in its onopen handler. For reconnections, this replays events and
  // hydrates isStarted. For fresh sessions, the server has nothing to
  // replay, so after a 600ms grace period we send "start" to create
  // the engine. The ref guard prevents double-start on StrictMode or
  // rapid reconnects.
  //
  useEffect(() => {
    if (connectionStatus !== "connected") return;
    if (hasSentStartRef.current) return;

    // Give the resume_from replay time to arrive before starting fresh
    const timer = setTimeout(() => {
      const state = useDraftStore.getState();
      if (!state.isStarted && state.picks.length === 0 && !hasSentStartRef.current) {
        hasSentStartRef.current = true;
        sendCommand("start");
      }
    }, 600);

    return () => clearTimeout(timer);
  }, [connectionStatus, sendCommand]);

  // Mark start-sent if the engine starts by any path (resume replay, etc.)
  useEffect(() => {
    if (isStarted) {
      hasSentStartRef.current = true;
    }
  }, [isStarted]);

  // ─── Confetti from UI Hints ─────────────────────────────────
  useEffect(() => {
    if (lastUiHints?.confetti) {
      setShowConfetti(true);
      const t = setTimeout(() => setShowConfetti(false), 3000);
      return () => clearTimeout(t);
    }
  }, [lastUiHints]);

  // ─── Auto-switch to Draft tab on user turn ──────────────────
  useEffect(() => {
    if (isUserTurn && activeTab !== "draft" && activeTab !== "board") {
      setActiveTab("draft");
    }
  }, [isUserTurn, activeTab]);

  // ─── Handlers ───────────────────────────────────────────────

  const handleProspectTap = useCallback(
    (prospect: Prospect) => {
      if (isUserTurn) {
        triggerHaptic("selection");
        setSelectedProspectId(prospect.id);
      }
    },
    [isUserTurn],
  );

  const handleSheetSelect = useCallback((prospect: Prospect) => {
    triggerHaptic("selection");
    setSelectedProspectId(prospect.id);
  }, []);

  const handleConfirmPick = useCallback(() => {
    if (!selectedProspectId) return;

    // Find the prospect in recommendations or the full board
    const prospect = [...recommendations, ...prospects].find(
      (p) => p.id === selectedProspectId,
    );
    if (!prospect) return;

    // Layer 1: Optimistic update (immediate UI response)
    makePick(prospect);

    // Layer 2: Send to server (confirmation or error will follow)
    sendCommand("submit_pick", { prospectId: selectedProspectId });

    // Reset selection + haptic
    setSelectedProspectId(null);
    triggerHaptic("success");

    // Switch to draft feed to see the pick land
    setActiveTab("draft");
  }, [selectedProspectId, recommendations, prospects, makePick, sendCommand]);

  const handleTogglePause = useCallback(() => {
    togglePause();
    sendCommand(isPaused ? "resume" : "pause");
  }, [isPaused, togglePause, sendCommand]);

  // ─── Build recommendation list for the sheet ────────────────
  // Prefer server recommendations. Fall back to top-5 available from
  // the static prospect list when the engine hasn't sent recs yet.
  const sheetRecommendations = useMemo(() => {
    if (recommendations.length > 0) return recommendations;
    return prospects.filter((p) => !draftedIds.has(p.id)).slice(0, 5);
  }, [recommendations, prospects, draftedIds]);

  // ─── Render ─────────────────────────────────────────────────
  return (
    <DraftShell>
      {/* ── Cinematic Shutter ── */}
      <LoadingShutter isVisible={shutterVisible} />

      {/* ── Confetti ── */}
      <ConfettiOverlay active={showConfetti} />

      {/* ── Fixed Header ── */}
      <StatusTicker
        currentPick={currentPick}
        currentRound={currentRound}
        userTeam={userTeam}
        isPaused={isPaused}
        isUserTurn={isUserTurn}
        onTheClockTeam={onTheClockTeam}
        connectionStatus={connectionStatus}
        onTogglePause={handleTogglePause}
      />

      {/* ── Tab Bar ── */}
      <TabBar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        userPickCount={userPicks.length}
      />

      {/* ── Tab Panels (scrolling body) ── */}
      <div style={{
        flex: 1,
        overflow: "hidden",
        position: "relative",
      }}>
        {activeTab === "draft" && (
          <DraftBoard
            picks={picks}
            currentPick={currentPick}
            onTheClockTeam={onTheClockTeam}
            userTeam={userTeam}
            warRoomSecret={warRoomSecret}
            isUserTurn={isUserTurn}
          />
        )}

        {activeTab === "board" && (
          <BigBoard
            prospects={prospects}
            draftedIds={draftedIds}
            onProspectTap={handleProspectTap}
          />
        )}

        {activeTab === "roster" && (
          <MyRoster
            userTeam={userTeam}
            teamDisplayName={TEAM_DISPLAY_NAMES[userTeam] ?? userTeam}
            picks={userPicks}
          />
        )}
      </div>

      {/* ── User Turn Bottom Sheet ── */}
      <UserTurnSheet
        isOpen={isUserTurn}
        pickNumber={currentPick}
        recommendations={sheetRecommendations}
        selectedId={selectedProspectId}
        onSelect={handleSheetSelect}
        onConfirm={handleConfirmPick}
      />
    </DraftShell>
  );
}
