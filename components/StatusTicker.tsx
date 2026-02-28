/**
 * StatusTicker.tsx — Header Bar
 * ==============================
 * From the Rose Cinema header: round indicator, pick number,
 * user team badge, pause/resume toggle.
 *
 * The "On The Clock" state uses a Framer Motion spring pulse
 * instead of the CSS keyframe from the monolith.
 */

"use client";

import React, { memo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { T } from "../lib/types";
import type { ConnectionStatus } from "../lib/types";

// ─── Framer Spring Config ────────────────────────────────────────
const SPRING = { type: "spring" as const, stiffness: 300, damping: 30 };

// ─── Team Badge ──────────────────────────────────────────────────

interface TeamBadgeProps {
  team: string;
  size?: number;
  isUser?: boolean;
}

const TeamBadge = memo(({ team, size = 38, isUser = false }: TeamBadgeProps) => (
  <div
    style={{
      width: size,
      height: size,
      borderRadius: size / 2,
      backgroundColor: isUser ? T.rose200 : T.border,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      color: isUser ? T.rose500 : T.muted,
      fontSize: size < 36 ? 10 : 12,
      fontWeight: 700,
      letterSpacing: "0.02em",
      border: isUser ? `1.5px solid ${T.rose300}` : "1px solid transparent",
      flexShrink: 0,
    }}
  >
    {team}
  </div>
));
TeamBadge.displayName = "TeamBadge";

// ─── Connection Dot ──────────────────────────────────────────────

const CONNECTION_COLORS: Record<ConnectionStatus, string> = {
  connected: "#30d158",
  connecting: "#ff9f0a",
  reconnecting: "#ff9f0a",
  disconnected: "#ff3b30",
};

// ─── StatusTicker (exported) ─────────────────────────────────────

interface StatusTickerProps {
  currentPick: number;
  currentRound: number;
  userTeam: string;
  isPaused: boolean;
  isUserTurn: boolean;
  onTheClockTeam: string;
  connectionStatus: ConnectionStatus;
  onTogglePause: () => void;
}

function StatusTickerInner({
  currentPick,
  currentRound,
  userTeam,
  isPaused,
  isUserTurn,
  onTheClockTeam,
  connectionStatus,
  onTogglePause,
}: StatusTickerProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={SPRING}
      style={{
        background: "rgba(255,252,252,0.82)",
        backdropFilter: "blur(32px) saturate(1.6)",
        WebkitBackdropFilter: "blur(32px) saturate(1.6)",
        padding: "14px 18px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        borderBottom: `0.5px solid ${T.border}`,
        zIndex: 10,
        willChange: "transform",
        isolation: "isolate",
      }}
    >
      {/* Left: Round + Pick */}
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        {/* Connection indicator */}
        <motion.div
          animate={{
            backgroundColor: CONNECTION_COLORS[connectionStatus],
            scale: connectionStatus === "reconnecting" ? [1, 1.3, 1] : 1,
          }}
          transition={
            connectionStatus === "reconnecting"
              ? { repeat: Infinity, duration: 1 }
              : { duration: 0.2 }
          }
          style={{
            width: 6,
            height: 6,
            borderRadius: 3,
            flexShrink: 0,
          }}
        />
        <div>
          <div
            style={{
              fontSize: 10,
              fontWeight: 700,
              color: T.muted,
              letterSpacing: "0.08em",
            }}
          >
            ROUND {currentRound}
          </div>
          <div
            style={{
              fontSize: 19,
              fontWeight: 600,
              color: T.rose950,
              letterSpacing: "-0.02em",
            }}
          >
            Pick {currentPick}
          </div>
        </div>
      </div>

      {/* Center: On The Clock indicator (when not user turn) */}
      <AnimatePresence mode="wait">
        {!isUserTurn && currentPick <= 257 && (
          <motion.div
            key={`clock-${onTheClockTeam}`}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={SPRING}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "6px 12px",
              background: T.rose100,
              borderRadius: 20,
            }}
          >
            <motion.span
              animate={{ scale: [1, 1.12, 1] }}
              transition={{
                repeat: Infinity,
                duration: 2,
                ease: "easeInOut",
              }}
              style={{ fontSize: 12 }}
            >
              ⏱
            </motion.span>
            <span
              style={{
                fontSize: 11,
                fontWeight: 700,
                color: T.rose500,
                letterSpacing: "0.04em",
              }}
            >
              {onTheClockTeam}
            </span>
          </motion.div>
        )}

        {isUserTurn && (
          <motion.div
            key="your-pick"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={SPRING}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              padding: "6px 14px",
              background: `linear-gradient(135deg, ${T.rose400}, ${T.rose500})`,
              borderRadius: 20,
              boxShadow: `0 2px 12px ${T.rose300}`,
            }}
          >
            <motion.span
              animate={{ scale: [1, 1.15, 1] }}
              transition={{
                repeat: Infinity,
                duration: 1.5,
                ease: "easeInOut",
              }}
              style={{ fontSize: 12 }}
            >
              🏈
            </motion.span>
            <span
              style={{
                fontSize: 11,
                fontWeight: 700,
                color: "#fff",
                letterSpacing: "0.04em",
              }}
            >
              YOUR PICK
            </span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Right: User team + Pause */}
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <TeamBadge team={userTeam} isUser />
        <motion.button
          onClick={onTogglePause}
          whileTap={{ scale: 0.9 }}
          animate={{
            backgroundColor: isPaused ? T.rose200 : T.bg,
            color: isPaused ? T.rose500 : T.muted,
          }}
          transition={{ duration: 0.15 }}
          style={{
            width: 40,
            height: 40,
            borderRadius: 20,
            border: "none",
            cursor: "pointer",
            fontSize: 16,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          {isPaused ? "▶" : "⏸"}
        </motion.button>
      </div>
    </motion.div>
  );
}

export const StatusTicker = memo(StatusTickerInner);
StatusTicker.displayName = "StatusTicker";

export { TeamBadge };
