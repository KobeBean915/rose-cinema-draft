/**
 * DraftBoard.tsx — Pick History Feed
 * ====================================
 * The "default tab" — a vertical timeline of every pick made so far.
 * Auto-scrolls to the latest pick. Shows war room intel after user picks.
 *
 * From the monolith's Draft tab: PickCard + OnTheClock + WarRoomSecret.
 */

"use client";

import React, { memo, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { PickRecord, Position, ConnectionStatus } from "../lib/types";
import { T, POSITION_COLOR } from "../lib/types";

const SPRING = { type: "spring" as const, stiffness: 300, damping: 30 };

// ─── Position Badge (self-contained) ─────────────────────────────

const PosBadge = memo(({ position }: { position: Position }) => {
  const color = POSITION_COLOR[position] || "#888";
  return (
    <span style={{
      padding: "3px 8px", borderRadius: 6,
      backgroundColor: color + "18", color,
      fontSize: 10, fontWeight: 650, letterSpacing: "0.06em",
    }}>
      {position}
    </span>
  );
});
PosBadge.displayName = "PosBadge";

// ─── Team Badge ──────────────────────────────────────────────────

const TeamBadge = memo(({ team, isUser }: { team: string; isUser: boolean }) => (
  <div style={{
    width: 32, height: 32, borderRadius: 16,
    backgroundColor: isUser ? T.rose200 : T.border,
    display: "flex", alignItems: "center", justifyContent: "center",
    color: isUser ? T.rose500 : T.muted,
    fontSize: 10, fontWeight: 700, letterSpacing: "0.02em",
    border: isUser ? `1.5px solid ${T.rose300}` : "1px solid transparent",
    flexShrink: 0,
  }}>
    {team}
  </div>
));
TeamBadge.displayName = "TeamBadge";

// ─── Pick Card ───────────────────────────────────────────────────

interface PickCardProps {
  pick: PickRecord;
  isLatest: boolean;
  isUser: boolean;
}

const PickCard = memo(({ pick, isLatest, isUser }: PickCardProps) => (
  <motion.div
    layout
    initial={isLatest ? { opacity: 0, x: 16 } : false}
    animate={{ opacity: pick.isOptimistic ? 0.7 : 1, x: 0 }}
    transition={SPRING}
    style={{
      display: "flex", alignItems: "center", gap: 12, padding: "13px 15px",
      background: isUser
        ? "linear-gradient(135deg, #fef0f2 0%, #fefcfc 100%)"
        : T.surface,
      borderRadius: 14,
      border: isUser ? `1.5px solid ${T.rose200}` : `0.5px solid ${T.border}`,
      boxShadow: isLatest
        ? "0 6px 24px rgba(60,20,30,0.07)"
        : "0 1px 4px rgba(60,20,30,0.03)",
    }}
  >
    <span style={{
      fontSize: 12, fontWeight: 700, color: T.muted, width: 26,
      fontVariantNumeric: "tabular-nums", textAlign: "center",
    }}>
      {pick.pickNumber}
    </span>
    <TeamBadge team={pick.team} isUser={isUser} />
    <div style={{ flex: 1, minWidth: 0 }}>
      <div style={{
        fontSize: 14, fontWeight: 600, color: T.rose950,
        letterSpacing: "-0.01em", marginBottom: 2,
      }}>
        {pick.prospect.name}
        {pick.isOptimistic && (
          <span style={{ fontSize: 9, color: T.muted, marginLeft: 6 }}>
            confirming…
          </span>
        )}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
        <PosBadge position={pick.prospect.position} />
        <span style={{ fontSize: 11, color: T.muted }}>
          {pick.prospect.school}
        </span>
      </div>
    </div>
    <div style={{ textAlign: "right", flexShrink: 0 }}>
      <div style={{
        fontSize: 10, fontWeight: 700, color: T.muted,
        letterSpacing: "0.04em",
      }}>
        #{pick.prospect.rank}
      </div>
    </div>
  </motion.div>
), (prev, next) =>
  prev.pick.sequenceNumber === next.pick.sequenceNumber &&
  prev.pick.isOptimistic === next.pick.isOptimistic &&
  prev.isLatest === next.isLatest
);
PickCard.displayName = "PickCard";

// ─── On The Clock Indicator ──────────────────────────────────────

const OnTheClock = memo(({ pickNumber, team }: { pickNumber: number; team: string }) => (
  <motion.div
    initial={{ opacity: 0, y: 6 }}
    animate={{ opacity: 1, y: 0 }}
    transition={SPRING}
    style={{
      display: "flex", alignItems: "center", gap: 12, padding: "13px 15px",
      background: `linear-gradient(135deg, ${T.rose100} 0%, ${T.rose50} 100%)`,
      borderRadius: 14, border: `1px solid ${T.rose200}`,
    }}
  >
    <span style={{
      fontSize: 12, fontWeight: 700, color: T.muted, width: 26, textAlign: "center",
    }}>
      {pickNumber}
    </span>
    <motion.div
      animate={{ scale: [1, 1.08, 1] }}
      transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
      style={{
        width: 32, height: 32, borderRadius: 16, backgroundColor: T.rose200,
        display: "flex", alignItems: "center", justifyContent: "center",
      }}
    >
      <span style={{ fontSize: 13 }}>⏱</span>
    </motion.div>
    <div>
      <span style={{
        fontSize: 12, fontWeight: 700, color: T.rose500, letterSpacing: "0.04em",
      }}>
        ON THE CLOCK
      </span>
      <div style={{ fontSize: 11, color: T.muted, marginTop: 1 }}>{team}</div>
    </div>
  </motion.div>
));
OnTheClock.displayName = "OnTheClock";

// ─── War Room Secret ─────────────────────────────────────────────

const WarRoomSecret = memo(({ secret }: { secret: string }) => {
  if (!secret) return null;
  return (
    <motion.div
      initial={{ opacity: 0, x: 12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={SPRING}
      style={{
        margin: "0 16px 12px", padding: "14px 16px",
        background: `linear-gradient(135deg, ${T.rose100} 0%, ${T.rose50} 100%)`,
        borderRadius: 14, border: `0.5px solid ${T.rose200}`,
      }}
    >
      <div style={{
        fontSize: 10, fontWeight: 700, color: T.rose500,
        letterSpacing: "0.08em", marginBottom: 6,
      }}>
        🏈 WAR ROOM INTEL
      </div>
      <div style={{
        fontSize: 13, color: T.rose900, fontStyle: "italic",
        lineHeight: 1.55, letterSpacing: "0.01em",
      }}>
        "{secret}"
      </div>
    </motion.div>
  );
});
WarRoomSecret.displayName = "WarRoomSecret";

// ─── DraftBoard (exported) ───────────────────────────────────────

interface DraftBoardProps {
  picks: PickRecord[];
  currentPick: number;
  onTheClockTeam: string;
  userTeam: string;
  warRoomSecret: string;
  isUserTurn: boolean;
}

function DraftBoardInner({
  picks, currentPick, onTheClockTeam, userTeam,
  warRoomSecret, isUserTurn,
}: DraftBoardProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new picks
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [picks.length]);

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <div
        ref={scrollRef}
        style={{
          flex: 1, overflowY: "auto", padding: "12px 16px",
          paddingBottom: isUserTurn ? 280 : 12,
          WebkitOverflowScrolling: "touch",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <AnimatePresence mode="popLayout">
            {picks.map((pick, i) => (
              <PickCard
                key={`${pick.sequenceNumber}-${pick.prospect.id}`}
                pick={pick}
                isLatest={i === picks.length - 1}
                isUser={pick.team === userTeam}
              />
            ))}
          </AnimatePresence>
          {currentPick <= 257 && !isUserTurn && (
            <OnTheClock pickNumber={currentPick} team={onTheClockTeam} />
          )}
        </div>
      </div>
      {warRoomSecret && picks.length > 0 && (
        <WarRoomSecret secret={warRoomSecret} />
      )}
    </div>
  );
}

export const DraftBoard = memo(DraftBoardInner);
DraftBoard.displayName = "DraftBoard";
