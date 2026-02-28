/**
 * MyRoster.tsx — User's Drafted Players
 * =======================================
 * Shows the user's team header and all their drafted picks.
 * Empty state with icon. Mirrors the monolith's Roster tab.
 */

"use client";

import React, { memo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { PickRecord, Position } from "../lib/types";
import { T, POSITION_COLOR } from "../lib/types";

const SPRING = { type: "spring" as const, stiffness: 300, damping: 30 };

// ─── Inline Badges ───────────────────────────────────────────────

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

// ─── Roster Pick Card ────────────────────────────────────────────

const RosterCard = memo(({ pick, index }: { pick: PickRecord; index: number }) => (
  <motion.div
    initial={{ opacity: 0, y: 8 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ ...SPRING, delay: index * 0.04 }}
    style={{
      display: "flex", alignItems: "center", gap: 12, padding: "13px 15px",
      background: "linear-gradient(135deg, #fef0f2 0%, #fefcfc 100%)",
      borderRadius: 14, border: `1.5px solid ${T.rose200}`,
      boxShadow: "0 1px 4px rgba(60,20,30,0.03)",
    }}
  >
    <span style={{
      fontSize: 12, fontWeight: 700, color: T.muted, width: 26,
      fontVariantNumeric: "tabular-nums", textAlign: "center",
    }}>
      {pick.pickNumber}
    </span>
    <div style={{ flex: 1, minWidth: 0 }}>
      <div style={{
        fontSize: 14, fontWeight: 600, color: T.rose950,
        letterSpacing: "-0.01em", marginBottom: 2,
      }}>
        {pick.prospect.name}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
        <PosBadge position={pick.prospect.position} />
        <span style={{ fontSize: 11, color: T.muted }}>{pick.prospect.school}</span>
      </div>
    </div>
    <div style={{ textAlign: "right", flexShrink: 0 }}>
      <div style={{ fontSize: 11, color: T.rose400, fontWeight: 500 }}>
        {pick.prospect.proComp}
      </div>
      <div style={{
        fontSize: 10, fontWeight: 700, color: T.muted, letterSpacing: "0.04em",
      }}>
        #{pick.prospect.rank}
      </div>
    </div>
  </motion.div>
));
RosterCard.displayName = "RosterCard";

// ─── MyRoster (exported) ─────────────────────────────────────────

interface MyRosterProps {
  userTeam: string;
  teamDisplayName: string;
  picks: PickRecord[];
}

function MyRosterInner({ userTeam, teamDisplayName, picks }: MyRosterProps) {
  return (
    <div style={{ height: "100%", overflowY: "auto", padding: "12px 16px" }}>
      {/* Team Header */}
      <div style={{
        display: "flex", alignItems: "center", gap: 14, padding: 18,
        background: `linear-gradient(135deg, ${T.rose100}, ${T.surface})`,
        borderRadius: 16, marginBottom: 14, border: `1.5px solid ${T.rose200}`,
      }}>
        <div style={{
          width: 48, height: 48, borderRadius: 24,
          backgroundColor: T.rose200,
          display: "flex", alignItems: "center", justifyContent: "center",
          color: T.rose500, fontSize: 16, fontWeight: 700,
          border: `1.5px solid ${T.rose300}`,
        }}>
          {userTeam}
        </div>
        <div>
          <div style={{ fontSize: 16, fontWeight: 600, color: T.rose950 }}>
            {teamDisplayName}
          </div>
          <div style={{ fontSize: 12, color: T.muted }}>
            {picks.length} player{picks.length !== 1 ? "s" : ""} drafted
          </div>
        </div>
      </div>

      {/* Picks or Empty State */}
      {picks.length === 0 ? (
        <div style={{ textAlign: "center", padding: 48, color: T.muted }}>
          <div style={{ fontSize: 36, marginBottom: 10, opacity: 0.5 }}>👤</div>
          <div style={{ fontSize: 14 }}>No players drafted yet</div>
          <div style={{ fontSize: 12, marginTop: 4 }}>
            Your picks will appear here
          </div>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <AnimatePresence>
            {picks.map((pick, i) => (
              <RosterCard
                key={`${pick.sequenceNumber}-${pick.prospect.id}`}
                pick={pick}
                index={i}
              />
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}

export const MyRoster = memo(MyRosterInner);
MyRoster.displayName = "MyRoster";
