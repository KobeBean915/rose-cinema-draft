/**
 * BigBoard.tsx — High-Performance Prospect Rankings (v2)
 * ========================================================
 * Additions over v1:
 *   - Team Fit badge with rose-glow at ≥85%
 *   - Archetype tag as cinematic subtitle ("Generational Speed", "Hybrid Eraser")
 *   - layoutId on each row → organic spring reflow when a pick exits
 *   - Haptic tap on selection
 *   - IntersectionObserver lazy-mount (unchanged strategy)
 *
 * Virtualization: IntersectionObserver Lazy Mount
 * ────────────────────────────────────────────────
 * We mount ALL row containers (lightweight div shells with fixed height),
 * but only render EXPENSIVE inner content when the shell enters the
 * viewport. Shells outside render a static placeholder (rank + name).
 * Zero flicker. Native scroll momentum. Accurate scrollbar.
 */

"use client";

import React, {
  useState, useMemo, useRef, useCallback, useEffect, memo,
} from "react";
import { motion, AnimatePresence, LayoutGroup } from "framer-motion";
import type { Prospect, Position } from "../lib/types";
import { T, POSITION_COLOR, POSITIONS } from "../lib/types";
import { triggerHaptic } from "../lib/haptics";

// ─── Constants ───────────────────────────────────────────────────
const ROW_HEIGHT = 72;
const OVERSCAN = 4;
const OBSERVER_MARGIN = `${OVERSCAN * ROW_HEIGHT}px`;

const SPRING = { type: "spring" as const, stiffness: 300, damping: 30 };
const STAGGER_DELAY = 0.02;

// ─── Position Badge ──────────────────────────────────────────────

const PositionBadge = memo(({ position }: { position: Position }) => {
  const color = POSITION_COLOR[position] || "#888";
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", justifyContent: "center",
      padding: "3px 8px", borderRadius: 6,
      backgroundColor: color + "18", color,
      fontSize: 10, fontWeight: 650, letterSpacing: "0.06em", lineHeight: 1,
      flexShrink: 0,
    }}>
      {position}
    </span>
  );
});
PositionBadge.displayName = "PositionBadge";

// ─── Team Fit Badge ──────────────────────────────────────────────
// Glows when systemFitPct ≥ 85. Subtle when < 85.

interface FitBadgeProps {
  fitLabel?: string;
  fitPct?: number;
}

const TeamFitBadge = memo(({ fitLabel, fitPct }: FitBadgeProps) => {
  if (!fitLabel && fitPct == null) return null;
  const isElite = (fitPct ?? 0) >= 85;
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 3,
      padding: "2px 7px", borderRadius: 6,
      fontSize: 9, fontWeight: 650, letterSpacing: "0.04em",
      backgroundColor: isElite ? T.rose200 : T.bg,
      color: isElite ? T.rose500 : T.muted,
      boxShadow: isElite ? `0 0 8px ${T.rose300}` : "none",
      transition: "box-shadow 0.3s ease",
    }}>
      {isElite && <span style={{ fontSize: 8 }}>✦</span>}
      {fitLabel ?? `${fitPct}%`}
    </span>
  );
});
TeamFitBadge.displayName = "TeamFitBadge";

// ─── Archetype Tag ───────────────────────────────────────────────
// Cinematic subtitle: "Generational Speed", "Hybrid Eraser", etc.

const ArchetypeTag = memo(({ tag }: { tag?: string }) => {
  if (!tag) return null;
  return (
    <span style={{
      fontSize: 9, fontWeight: 600, letterSpacing: "0.1em",
      textTransform: "uppercase",
      color: T.rose400, opacity: 0.85,
    }}>
      {tag}
    </span>
  );
});
ArchetypeTag.displayName = "ArchetypeTag";

// ─── Prospect Row ────────────────────────────────────────────────

interface ProspectRowProps {
  prospect: Prospect;
  isDrafted: boolean;
  index: number;
  isVisible: boolean;
  onTap?: (prospect: Prospect) => void;
}

const ProspectRow = memo(
  ({ prospect, isDrafted, index, isVisible, onTap }: ProspectRowProps) => {
    if (!isVisible) {
      return (
        <div style={{
          height: ROW_HEIGHT - 8, display: "flex", alignItems: "center",
          padding: "0 14px", opacity: 0.35,
        }}>
          <span style={{
            fontSize: 12, fontWeight: 700, color: T.muted,
            width: 26, textAlign: "center", fontVariantNumeric: "tabular-nums",
          }}>
            #{prospect.rank}
          </span>
          <span style={{ fontSize: 13, color: T.muted, marginLeft: 12 }}>
            {prospect.name}
          </span>
        </div>
      );
    }

    return (
      <motion.button
        layoutId={`prospect-row-${prospect.id}`}
        initial={{ opacity: 0, x: 8 }}
        animate={{ opacity: isDrafted ? 0.35 : 1, x: 0 }}
        exit={{ opacity: 0, x: -12, height: 0, marginBottom: 0, overflow: "hidden" }}
        transition={{ ...SPRING, delay: Math.min(index * STAGGER_DELAY, 0.3) }}
        onClick={() => {
          if (!isDrafted && onTap) {
            triggerHaptic("selection");
            onTap(prospect);
          }
        }}
        disabled={isDrafted}
        style={{
          width: "100%",
          display: "flex", alignItems: "center", gap: 10,
          padding: "10px 14px",
          height: ROW_HEIGHT - 8,
          background: isDrafted ? T.bg : T.surface,
          borderRadius: 12,
          border: `0.5px solid ${T.border}`,
          cursor: isDrafted ? "default" : "pointer",
          textAlign: "left",
          textDecoration: isDrafted ? "line-through" : "none",
          textDecorationColor: T.muted,
        }}
        whileHover={isDrafted ? undefined : {
          scale: 1.005,
          boxShadow: "0 4px 16px rgba(60,20,30,0.06)",
        }}
        whileTap={isDrafted ? undefined : { scale: 0.995 }}
      >
        {/* Rank */}
        <span style={{
          fontSize: 12, fontWeight: 700, color: T.muted,
          width: 26, textAlign: "center", fontVariantNumeric: "tabular-nums",
        }}>
          #{prospect.rank}
        </span>

        {/* Position */}
        <PositionBadge position={prospect.position} />

        {/* Name + Archetype + School */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{
            display: "flex", alignItems: "center", gap: 6,
            marginBottom: 1,
          }}>
            <span style={{
              fontSize: 13, fontWeight: 600, color: T.rose950,
              whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
            }}>
              {prospect.name}
            </span>
            <TeamFitBadge fitLabel={prospect.systemFit} fitPct={prospect.systemFitPct} />
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ fontSize: 11, color: T.muted }}>{prospect.school}</span>
            <ArchetypeTag tag={prospect.archetypeTag} />
          </div>
        </div>

        {/* Comp + Trait */}
        <div style={{ textAlign: "right", flexShrink: 0, maxWidth: 140 }}>
          <div style={{
            fontSize: 11, color: T.rose400, fontWeight: 500,
            whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
          }}>
            {prospect.proComp}
          </div>
          <div style={{
            fontSize: 10, color: T.muted, marginTop: 1,
            whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
          }}>
            {prospect.primaryTrait}
          </div>
        </div>
      </motion.button>
    );
  },
  (prev, next) =>
    prev.prospect.id === next.prospect.id &&
    prev.isDrafted === next.isDrafted &&
    prev.isVisible === next.isVisible,
);
ProspectRow.displayName = "ProspectRow";

// ─── Position Filter Bar ─────────────────────────────────────────

interface FilterBarProps {
  selectedPositions: Set<Position>;
  onToggle: (pos: Position) => void;
  onClear: () => void;
}

const FilterBar = memo(({ selectedPositions, onToggle, onClear }: FilterBarProps) => (
  <div style={{
    display: "flex", gap: 7, overflowX: "auto", paddingBottom: 2,
    scrollbarWidth: "none", msOverflowStyle: "none",
  }}>
    <AnimatePresence>
      {selectedPositions.size > 0 && (
        <motion.button
          key="clear"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.9 }}
          transition={SPRING}
          onClick={onClear}
          style={{
            padding: "5px 10px", borderRadius: 20,
            border: `0.5px solid ${T.border}`, background: "transparent",
            fontSize: 10, fontWeight: 600, color: T.muted,
            cursor: "pointer", flexShrink: 0, whiteSpace: "nowrap",
          }}
        >
          Clear ✕
        </motion.button>
      )}
    </AnimatePresence>
    {POSITIONS.map((pos) => {
      const isSelected = selectedPositions.has(pos);
      const color = POSITION_COLOR[pos] || "#888";
      return (
        <motion.button
          key={pos}
          onClick={() => {
            triggerHaptic("light");
            onToggle(pos);
          }}
          animate={{
            backgroundColor: isSelected ? color : T.rose100,
            color: isSelected ? "#fff" : T.rose500,
          }}
          transition={{ duration: 0.15 }}
          whileTap={{ scale: 0.95 }}
          style={{
            padding: "5px 12px", borderRadius: 20, border: "none",
            cursor: "pointer", flexShrink: 0,
            fontSize: 11, fontWeight: 600, letterSpacing: "0.02em",
          }}
        >
          {pos}
        </motion.button>
      );
    })}
  </div>
));
FilterBar.displayName = "FilterBar";

// ─── BigBoard (exported) ─────────────────────────────────────────

interface BigBoardProps {
  prospects: Prospect[];
  draftedIds: Set<string>;
  onProspectTap?: (prospect: Prospect) => void;
}

function BigBoardInner({ prospects, draftedIds, onProspectTap }: BigBoardProps) {
  const [searchText, setSearchText] = useState("");
  const [selectedPositions, setSelectedPositions] = useState<Set<Position>>(new Set());
  const [visibleIds, setVisibleIds] = useState<Set<string>>(new Set());
  const observerRef = useRef<IntersectionObserver | null>(null);
  const rowRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  const filtered = useMemo(() => {
    return prospects.filter((p) => {
      if (draftedIds.has(p.id)) return false;
      if (searchText) {
        const q = searchText.toLowerCase();
        if (
          !p.name.toLowerCase().includes(q) &&
          !p.school.toLowerCase().includes(q) &&
          !p.position.toLowerCase().includes(q) &&
          !(p.archetypeTag?.toLowerCase().includes(q))
        ) return false;
      }
      if (selectedPositions.size > 0 && !selectedPositions.has(p.position)) return false;
      return true;
    });
  }, [prospects, draftedIds, searchText, selectedPositions]);

  // ─── IntersectionObserver ─────────────────────────────────────
  useEffect(() => {
    observerRef.current = new IntersectionObserver(
      (entries) => {
        setVisibleIds((prev) => {
          const next = new Set(prev);
          let changed = false;
          for (const entry of entries) {
            const id = entry.target.getAttribute("data-prospect-id");
            if (!id) continue;
            if (entry.isIntersecting && !next.has(id)) { next.add(id); changed = true; }
            else if (!entry.isIntersecting && next.has(id)) { next.delete(id); changed = true; }
          }
          return changed ? next : prev;
        });
      },
      { rootMargin: `${OBSERVER_MARGIN} 0px`, threshold: 0 },
    );
    return () => { observerRef.current?.disconnect(); };
  }, []);

  useEffect(() => {
    const observer = observerRef.current;
    if (!observer) return;
    observer.disconnect();
    rowRefs.current.forEach((el) => observer.observe(el));
  }, [filtered]);

  const registerRef = useCallback((id: string, el: HTMLDivElement | null) => {
    if (el) {
      rowRefs.current.set(id, el);
      observerRef.current?.observe(el);
    } else {
      const existing = rowRefs.current.get(id);
      if (existing) observerRef.current?.unobserve(existing);
      rowRefs.current.delete(id);
    }
  }, []);

  const handleToggle = useCallback((pos: Position) => {
    setSelectedPositions((prev) => {
      const next = new Set(prev);
      if (next.has(pos)) next.delete(pos); else next.add(pos);
      return next;
    });
  }, []);

  const handleClear = useCallback(() => setSelectedPositions(new Set()), []);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      {/* Search + Filter Header */}
      <div style={{
        padding: "12px 16px",
        background: "rgba(255,252,252,0.85)",
        backdropFilter: "blur(24px) saturate(1.6)",
        WebkitBackdropFilter: "blur(24px) saturate(1.6)",
        borderBottom: `0.5px solid ${T.border}`,
        zIndex: 2, willChange: "transform", isolation: "isolate",
      }}>
        <div style={{
          display: "flex", alignItems: "center", gap: 9,
          padding: "9px 13px", background: T.bg, borderRadius: 10, marginBottom: 10,
        }}>
          <span style={{ color: T.muted, fontSize: 14 }}>⌕</span>
          <input
            type="text" placeholder="Search prospects..."
            value={searchText} onChange={(e) => setSearchText(e.target.value)}
            style={{
              flex: 1, border: "none", background: "transparent",
              fontSize: 14, color: T.rose950, outline: "none",
              fontFamily: "inherit", letterSpacing: "0.02em",
            }}
          />
          <AnimatePresence>
            {searchText && (
              <motion.button
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                transition={SPRING}
                onClick={() => setSearchText("")}
                style={{
                  background: "none", border: "none", color: T.muted,
                  cursor: "pointer", fontSize: 13, padding: 0,
                }}
              >
                ✕
              </motion.button>
            )}
          </AnimatePresence>
        </div>
        <FilterBar
          selectedPositions={selectedPositions}
          onToggle={handleToggle}
          onClear={handleClear}
        />
      </div>

      {/* Prospect List */}
      <div style={{
        flex: 1, overflowY: "auto", overflowX: "hidden",
        padding: "10px 16px", WebkitOverflowScrolling: "touch",
      }}>
        <LayoutGroup>
          <AnimatePresence mode="popLayout">
            {filtered.map((p, i) => (
              <div
                key={p.id}
                ref={(el) => registerRef(p.id, el)}
                data-prospect-id={p.id}
                style={{ marginBottom: 8 }}
              >
                <ProspectRow
                  prospect={p}
                  isDrafted={draftedIds.has(p.id)}
                  index={i}
                  isVisible={visibleIds.has(p.id)}
                  onTap={onProspectTap}
                />
              </div>
            ))}
          </AnimatePresence>
        </LayoutGroup>
      </div>

      {/* Footer */}
      <div style={{
        padding: "9px 16px", background: T.rose100,
        display: "flex", justifyContent: "space-between",
        fontSize: 11, color: T.muted, fontWeight: 500, flexShrink: 0,
      }}>
        <span>{filtered.length} of {prospects.length} available</span>
        <span>{draftedIds.size} drafted</span>
      </div>
    </div>
  );
}

export const BigBoard = memo(BigBoardInner);
BigBoard.displayName = "BigBoard";
