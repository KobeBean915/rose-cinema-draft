/**
 * haptics.ts — Web Haptic Feedback
 * ==================================
 * Maps HapticType enum to navigator.vibrate() patterns.
 * Falls back silently on desktop/unsupported browsers.
 *
 * Pattern encoding: [vibrate_ms, pause_ms, vibrate_ms, ...]
 *
 * Why this matters:
 * On mobile Safari (16.4+) and Chrome Android, navigator.vibrate()
 * is supported. Combined with CSS spring animations, this bridges
 * the gap between "web app" and "native app" feel. The patterns
 * are tuned to match iOS UIKit impact feedback intensities.
 */

import type { HapticType } from "./types";

const PATTERNS: Record<HapticType, number[] | null> = {
  none:      null,
  light:     [10],
  medium:    [20],
  heavy:     [40],
  success:   [15, 50, 15, 50, 30],    // ta-ta-TAP
  warning:   [30, 100, 30],           // tap--tap
  error:     [50, 50, 50, 50, 50],    // buzz-buzz-buzz
  selection: [5],                      // micro-tap
  rigid:     [25],                     // hard single
  soft:      [8],                      // whisper
};

let _supported: boolean | null = null;

function isSupported(): boolean {
  if (_supported !== null) return _supported;
  _supported =
    typeof navigator !== "undefined" &&
    typeof navigator.vibrate === "function";
  return _supported;
}

/**
 * Fire a haptic feedback pattern.
 * Safe to call unconditionally — no-ops on unsupported platforms.
 */
export function triggerHaptic(type: HapticType): void {
  if (!isSupported()) return;
  const pattern = PATTERNS[type];
  if (!pattern) return;

  try {
    navigator.vibrate(pattern);
  } catch {
    // Swallow — some browsers throw in specific contexts (e.g. background tab)
  }
}

/**
 * Cancel any ongoing vibration.
 */
export function cancelHaptic(): void {
  if (!isSupported()) return;
  try {
    navigator.vibrate(0);
  } catch {
    // Swallow
  }
}
