/**
 * UserTurnSheet.tsx — Bottom Sheet Pick Selector (v2: Athletic Profile)
 * ======================================================================
 * Additions over v1:
 *   - Metric bars: speed (40-time), explosiveness, size — relative to position
 *   - Height/weight display with position-relative context
 *   - System Fit badge with rose-glow at ≥85%
 *   - Archetype tag as cinematic subtitle
 *   - Haptic: light tap on card selection, success pattern on draft confirm
 */

"use client";

import React, { memo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { Prospect, Position } from "../lib/types";
import { T, POSITION_COLOR } from "../lib/types";
import { triggerHaptic } from "../lib/haptics";

const SPRING = { type: "spring" as const, stiffness: 300, damping: 30 };

const SHEET_VARIANTS = {
  hidden: { y: "100%", opacity: 0.5 },
  visible: { y: 0, opacity: 1 },
  exit: { y: "100%", opacity: 0 },
};

// ─── Relative Metric Bar ─────────────────────────────────────────
// Renders a thin horizontal bar. value is 0–1 (percentile).
// Label sits left, value sits right, bar fills proportionally.

interface MetricBarProps {
  label: string;
  value: number;       // 0–1 percentile
  displayValue: string; // e.g. "4.34s" or "6'4\" 218"
  color?: string;
}

const MetricBar = memo(({ label, value, displayValue, color }: MetricBarProps) => {
  const barColor = color ?? T.rose400;
  const clampedValue = Math.max(0, Math.min(1, value));

  return (
    <div style={{ marginBottom: 5 }}>
      <div style={{
        display: "flex", justifyContent: "space-between",
        fontSize: 9, fontWeight: 600, letterSpacing: "0.04em",
        marginBottom: 2,
      }}>
        <span style={{ color: T.muted, textTransform: "uppercase" }}>{label}</span>
        <span style={{ color: T.rose950, fontVariantNumeric: "tabular-nums" }}>
          {displayValue}
        </span>
      </div>
      <div style={{
        height: 3, borderRadius: 2, backgroundColor: T.border,
        overflow: "hidden",
      }}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${clampedValue * 100}%` }}
          transition={{ ...SPRING, delay: 0.1 }}
          style={{
            height: "100%", borderRadius: 2,
            background: clampedValue >= 0.85
              ? `linear-gradient(90deg, ${barColor}, ${T.rose500})`
              : barColor,
          }}
        />
      </div>
    </div>
  );
});
MetricBar.displayName = "MetricBar";

// ─── Team Fit Badge (inline) ─────────────────────────────────────

const FitBadge = memo(({ label, pct }: { label?: string; pct?: number }) => {
  if (!label && pct == null) return null;
  const isElite = (pct ?? 0) >= 85;
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 3,
      padding: "2px 7px", borderRadius: 6,
      fontSize: 9, fontWeight: 650, letterSpacing: "0.04em",
      backgroundColor: isElite ? T.rose200 : T.bg,
      color: isElite ? T.rose500 : T.muted,
      boxShadow: isElite ? `0 0 8px ${T.rose300}` : "none",
    }}>
      {isElite && <span style={{ fontSize: 8 }}>✦</span>}
      {label ?? `${pct}% fit`}
    </span>
  );
});
FitBadge.displayName = "FitBadge";

// ─── Position Badge ──────────────────────────────────────────────

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

// ─── Athletic Profile Grid ──────────────────────────────────────
// Compact 3-metric display inside each prospect card.

const AthleticProfile = memo(({ prospect }: { prospect: Prospect }) => {
  const m = prospect.measurables;
  const p = prospect.percentiles;
  if (!m && !p) return null;

  return (
    <div style={{
      marginTop: 8, padding: "6px 0",
      borderTop: `0.5px solid ${T.border}`,
    }}>
      {/* Speed */}
      {(p?.speed != null || m?.fortyTime != null) && (
        <MetricBar
          label="Speed"
          value={p?.speed ?? 0.5}
          displayValue={m?.fortyTime ? `${m.fortyTime}s` : "—"}
          color="#30b8c8"
        />
      )}
      {/* Explosiveness */}
      {(p?.explosiveness != null) && (
        <MetricBar
          label="Explosive"
          value={p.explosiveness}
          displayValue={
            m?.verticalJump
              ? `${m.verticalJump}″ vert`
              : "—"
          }
          color="#af52de"
        />
      )}
      {/* Size */}
      {(m?.height || m?.weight) && (
        <MetricBar
          label="Size"
          value={p?.size ?? 0.5}
          displayValue={
            [m?.height, m?.weight ? `${m.weight}lb` : null]
              .filter(Boolean)
              .join(" · ")
          }
          color={T.rose400}
        />
      )}
    </div>
  );
});
AthleticProfile.displayName = "AthleticProfile";

// ─── Prospect Card ───────────────────────────────────────────────

interface CardProps {
  prospect: Prospect;
  isSelected: boolean;
  onSelect: (p: Prospect) => void;
  index: number;
}

const ProspectCard = memo(
  ({ prospect, isSelected, onSelect, index }: CardProps) => (
    <motion.button
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ ...SPRING, delay: index * 0.05 }}
      whileTap={{ scale: 0.97 }}
      onClick={() => {
        triggerHaptic("selection");
        onSelect(prospect);
      }}
      style={{
        flexShrink: 0, width: 164, padding: 12, borderRadius: 14,
        cursor: "pointer", textAlign: "left",
        border: isSelected
          ? `2px solid ${T.rose400}`
          : `0.5px solid ${T.border}`,
        backgroundColor: isSelected ? T.rose100 : T.surface,
        boxShadow: isSelected
          ? `0 4px 16px ${T.rose200}`
          : "0 1px 4px rgba(0,0,0,0.03)",
        transform: isSelected ? "scale(1.02)" : "scale(1)",
        transition: "border 0.15s, background-color 0.15s, box-shadow 0.2s, transform 0.2s",
      }}
    >
      {/* Header: Position + Rank */}
      <div style={{
        display: "flex", justifyContent: "space-between",
        alignItems: "center", marginBottom: 6,
      }}>
        <PosBadge position={prospect.position} />
        <span style={{ fontSize: 10, fontWeight: 700, color: T.muted }}>
          #{prospect.rank}
        </span>
      </div>

      {/* Name */}
      <div style={{
        fontSize: 13, fontWeight: 600, color: T.rose950,
        marginBottom: 1, letterSpacing: "-0.01em",
        whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
      }}>
        {prospect.name}
      </div>

      {/* Archetype Subtitle */}
      {prospect.archetypeTag && (
        <div style={{
          fontSize: 9, fontWeight: 600, letterSpacing: "0.08em",
          textTransform: "uppercase", color: T.rose400, marginBottom: 2,
        }}>
          {prospect.archetypeTag}
        </div>
      )}

      {/* School + Fit */}
      <div style={{
        display: "flex", alignItems: "center", gap: 4,
        marginBottom: 2, flexWrap: "wrap",
      }}>
        <span style={{ fontSize: 11, color: T.muted }}>{prospect.school}</span>
        <FitBadge label={prospect.systemFit} pct={prospect.systemFitPct} />
      </div>

      {/* Primary Trait */}
      <div style={{
        fontSize: 10, color: T.rose400, fontWeight: 500,
        whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
      }}>
        {prospect.primaryTrait}
      </div>

      {/* Athletic Profile Bars */}
      <AthleticProfile prospect={prospect} />
    </motion.button>
  ),
  (prev, next) =>
    prev.prospect.id === next.prospect.id &&
    prev.isSelected === next.isSelected,
);
ProspectCard.displayName = "ProspectCard";

// ─── UserTurnSheet (exported) ────────────────────────────────────

interface UserTurnSheetProps {
  isOpen: boolean;
  pickNumber: number;
  recommendations: Prospect[];
  selectedId: string | null;
  onSelect: (prospect: Prospect) => void;
  onConfirm: () => void;
}

function UserTurnSheetInner({
  isOpen,
  pickNumber,
  recommendations,
  selectedId,
  onSelect,
  onConfirm,
}: UserTurnSheetProps) {
  const selectedProspect = recommendations.find((p) => p.id === selectedId);

  const handleConfirm = () => {
    triggerHaptic("success");
    onConfirm();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          key="user-turn-sheet"
          variants={SHEET_VARIANTS}
          initial="hidden"
          animate="visible"
          exit="exit"
          transition={SPRING}
          style={{
            position: "fixed", bottom: 0, left: 0, right: 0, zIndex: 30,
            background: "rgba(255,252,252,0.92)",
            backdropFilter: "blur(32px) saturate(1.6)",
            WebkitBackdropFilter: "blur(32px) saturate(1.6)",
            borderTop: `0.5px solid ${T.rose200}`,
            borderRadius: "24px 24px 0 0",
            boxShadow: "0 -12px 48px rgba(60,20,30,0.10)",
            padding: "16px 18px 24px",
            maxHeight: "60vh", overflowY: "auto",
            overscrollBehavior: "contain",
          }}
        >
          {/* Drag Handle */}
          <div style={{
            width: 36, height: 4, backgroundColor: T.border,
            borderRadius: 2, margin: "0 auto 16px",
          }} />

          {/* Header */}
          <div style={{
            display: "flex", justifyContent: "space-between",
            alignItems: "center", marginBottom: 16,
          }}>
            <div>
              <div style={{
                fontSize: 10, fontWeight: 700, color: T.muted,
                letterSpacing: "0.08em", marginBottom: 2,
              }}>
                YOUR SELECTION
              </div>
              <div style={{
                fontSize: 20, fontWeight: 600, color: T.rose950,
                letterSpacing: "-0.02em",
              }}>
                Pick {pickNumber}
              </div>
            </div>
            <motion.div
              animate={{ scale: [1, 1.05, 1] }}
              transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
              style={{
                padding: "7px 14px", backgroundColor: T.rose100,
                borderRadius: 20, display: "flex", alignItems: "center", gap: 5,
              }}
            >
              <span style={{ fontSize: 12 }}>⏱</span>
              <span style={{ fontSize: 12, fontWeight: 700, color: T.rose500 }}>
                On the Clock
              </span>
            </motion.div>
          </div>

          {/* Horizontal Carousel */}
          <div style={{
            display: "flex", gap: 10, overflowX: "auto", paddingBottom: 6,
            margin: "0 -4px", scrollbarWidth: "none",
            msOverflowStyle: "none", WebkitOverflowScrolling: "touch",
          }}>
            {recommendations.map((p, i) => (
              <ProspectCard
                key={p.id}
                prospect={p}
                isSelected={selectedId === p.id}
                onSelect={onSelect}
                index={i}
              />
            ))}
          </div>

          {/* Confirm Button */}
          <AnimatePresence>
            {selectedProspect && (
              <motion.button
                key="confirm-btn"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 8 }}
                transition={SPRING}
                whileTap={{ scale: 0.98 }}
                onClick={handleConfirm}
                style={{
                  width: "100%", marginTop: 14, padding: "15px 24px",
                  background: `linear-gradient(135deg, ${T.rose400} 0%, ${T.rose500} 100%)`,
                  color: "#fff", border: "none", borderRadius: 14,
                  fontSize: 15, fontWeight: 600, cursor: "pointer",
                  display: "flex", alignItems: "center",
                  justifyContent: "center", gap: 8,
                  letterSpacing: "0.01em",
                  boxShadow: `0 4px 20px ${T.rose300}`,
                }}
              >
                Draft {selectedProspect.name}
                <span style={{ fontSize: 17, opacity: 0.8 }}>→</span>
              </motion.button>
            )}
          </AnimatePresence>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export const UserTurnSheet = memo(UserTurnSheetInner);
UserTurnSheet.displayName = "UserTurnSheet";
