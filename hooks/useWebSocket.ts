/**
 * useWebSocket.ts — Three-Layer Connectivity Bridge
 * ====================================================
 *
 * ┌─────────────────────────────────────────────────────┐
 * │  LIFECYCLE                                          │
 * │                                                     │
 * │  mount → connect → onOpen → resume_from(lastSeq)    │
 * │    ↓                  ↓                              │
 * │  onMessage → parse → gap check → processIncoming    │
 * │    ↓                                                 │
 * │  onClose → exponential backoff → reconnect           │
 * │    ↓                                                 │
 * │  unmount → close(1000) → cleanup                     │
 * └─────────────────────────────────────────────────────┘
 *
 * RESUME SESSION PROTOCOL:
 * ────────────────────────
 * On every successful connection (including reconnects), the hook sends:
 *   { "action": "resume_from", "last_sequence": N }
 *
 * where N = useDraftStore.lastConfirmedSequence.
 *
 * The server responds by replaying all DraftEvents with sequence > N.
 * The Zustand store's processIncomingEvent handles deduplication:
 *   - Events already in picks[] are detected by CASE C (stale duplicate)
 *   - Events confirming optimistic picks are handled by CASE A (silent promote)
 *   - Genuinely missed events insert via CASE B (soft insert)
 *
 * This means the client can seamlessly resume after:
 *   - Wi-Fi → cellular handoff
 *   - Elevator/tunnel signal loss
 *   - Laptop sleep/wake
 *   - Tab backgrounding (WebSocket timeout)
 *
 * GAP DETECTION:
 * ──────────────
 * If an incoming event's sequenceNumber > lastConfirmedSequence + 1,
 * there's a gap in the event stream (dropped packet, partial replay).
 * The hook requests a full sync:
 *   { "action": "sync" }
 * The server responds with a SYNC_STATE event containing the full
 * DraftStateSnapshot — Layer 3 truth.
 *
 * OFFLINE COMMAND QUEUE:
 * ──────────────────────
 * Commands sent while disconnected are queued in memory.
 * On reconnect, after the resume_from handshake, all queued commands
 * are flushed in FIFO order. This ensures a "Draft" tap in an elevator
 * isn't lost — it fires the instant connectivity returns.
 *
 * The queue is bounded at 20 commands to prevent unbounded memory growth
 * during extended outages.
 */

import { useEffect, useRef, useCallback } from "react";
import { useDraftStore } from "../stores/useDraftStore";
import type { DraftEvent, ClientCommand } from "../lib/types";
import { triggerHaptic } from "../lib/haptics";

// ─── Configuration ───────────────────────────────────────────────

interface UseWebSocketOptions {
  /** WebSocket URL (e.g. "ws://localhost:8000/ws/draft/abc?team=NYG") */
  url: string;
  /** Auto-connect on mount. Default: true */
  autoConnect?: boolean;
  /** Enable logging to console. Default: false in production */
  debug?: boolean;
}

interface UseWebSocketReturn {
  /** Send a command to the server. Queues if disconnected. */
  sendCommand: (type: ClientCommand["type"], payload?: Record<string, any>) => void;
  /** Force a full state sync (Layer 3). */
  requestSync: () => void;
  /** Manually disconnect. */
  disconnect: () => void;
  /** Manually reconnect. */
  reconnect: () => void;
}

// ─── Constants ───────────────────────────────────────────────────

const BACKOFF_INITIAL_MS = 1000;
const BACKOFF_MAX_MS = 30_000;
const BACKOFF_MULTIPLIER = 2;
const BACKOFF_JITTER = 0.3;             // ±30% randomization
const OFFLINE_QUEUE_MAX = 20;
const HEARTBEAT_INTERVAL_MS = 25_000;   // Keep-alive ping
const STALE_THRESHOLD_MS = 45_000;      // Consider stale if no message in 45s

// ─── Server Action Mapping ───────────────────────────────────────
// Maps our ClientCommand types to the server's "action" field names.
// The server uses { "action": "pick", "prospect_id": "..." }
// while our store uses { type: "submit_pick", payload: { prospectId: "..." } }.

const ACTION_MAP: Record<ClientCommand["type"], string> = {
  start: "start",
  submit_pick: "pick",
  accept_trade: "accept_trade",
  reject_trade: "reject_trade",
  undo: "undo",
  redo: "redo",
  pause: "pause",
  resume: "resume",
  sync: "sync",
  resume_session: "resume_from",
};

/**
 * Transform a ClientCommand into the server's wire format.
 */
function toServerMessage(type: ClientCommand["type"], payload?: Record<string, any>): Record<string, any> {
  const action = ACTION_MAP[type] || type;
  const msg: Record<string, any> = { action };

  if (type === "submit_pick" && payload?.prospectId) {
    msg.prospect_id = payload.prospectId;
  } else if (type === "resume_session" && payload?.lastSequence != null) {
    msg.last_sequence = payload.lastSequence;
  } else if (payload) {
    // Pass through any other payload fields
    Object.assign(msg, payload);
  }

  return msg;
}

// ─── Hook ────────────────────────────────────────────────────────

export function useWebSocket(options: UseWebSocketOptions): UseWebSocketReturn {
  const { url, autoConnect = true, debug = false } = options;

  // Refs for values that must survive re-renders without triggering them
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastMessageTimeRef = useRef<number>(Date.now());
  const offlineQueueRef = useRef<Array<Record<string, any>>>([]);
  const isUnmountedRef = useRef(false);
  const isManualCloseRef = useRef(false);
  const pendingSyncRef = useRef(false);
  const urlRef = useRef(url);
  urlRef.current = url;

  // Store access — non-reactive (getState, not subscribe)
  const store = useDraftStore;

  const log = useCallback(
    (...args: any[]) => {
      if (debug) console.log("[WS]", ...args);
    },
    [debug],
  );

  // ─── Backoff Calculator ─────────────────────────────────────
  const getBackoffMs = useCallback(() => {
    const attempt = reconnectAttemptRef.current;
    const base = Math.min(
      BACKOFF_INITIAL_MS * Math.pow(BACKOFF_MULTIPLIER, attempt),
      BACKOFF_MAX_MS,
    );
    // Add jitter to prevent thundering herd on server restart
    const jitter = base * BACKOFF_JITTER * (Math.random() * 2 - 1);
    return Math.round(base + jitter);
  }, []);

  // ─── Heartbeat (Keep-Alive) ─────────────────────────────────
  const startHeartbeat = useCallback(() => {
    stopHeartbeat();
    heartbeatTimerRef.current = setInterval(() => {
      const ws = wsRef.current;
      if (!ws || ws.readyState !== WebSocket.OPEN) return;

      // If no message received in STALE_THRESHOLD, request sync
      const elapsed = Date.now() - lastMessageTimeRef.current;
      if (elapsed > STALE_THRESHOLD_MS && !pendingSyncRef.current) {
        log("Stale connection detected, requesting sync");
        pendingSyncRef.current = true;
        ws.send(JSON.stringify({ action: "sync" }));
      }
    }, HEARTBEAT_INTERVAL_MS);
  }, [log]);

  const stopHeartbeat = useCallback(() => {
    if (heartbeatTimerRef.current) {
      clearInterval(heartbeatTimerRef.current);
      heartbeatTimerRef.current = null;
    }
  }, []);

  // ─── Flush Offline Queue ────────────────────────────────────
  const flushQueue = useCallback(() => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;

    const queue = offlineQueueRef.current;
    if (queue.length === 0) return;

    log(`Flushing ${queue.length} queued commands`);
    for (const msg of queue) {
      ws.send(JSON.stringify(msg));
    }
    offlineQueueRef.current = [];
  }, [log]);

  // ─── Gap Detection ──────────────────────────────────────────
  const checkForGap = useCallback(
    (incomingSeq: number) => {
      const { lastConfirmedSequence } = store.getState();

      // A gap exists if the incoming sequence skips ahead
      // by more than 1 from our last confirmed.
      // We allow +1 because that's the next expected event.
      if (incomingSeq > lastConfirmedSequence + 2 && !pendingSyncRef.current) {
        log(
          `Gap detected: expected ≤${lastConfirmedSequence + 1}, got ${incomingSeq}. Requesting sync.`,
        );
        pendingSyncRef.current = true;
        const ws = wsRef.current;
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ action: "sync" }));
        }
      }
    },
    [log, store],
  );

  // ─── Connect ────────────────────────────────────────────────
  const connect = useCallback(() => {
    if (isUnmountedRef.current) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    if (wsRef.current?.readyState === WebSocket.CONNECTING) return;

    const isReconnect = reconnectAttemptRef.current > 0;
    store.getState().setConnectionStatus(isReconnect ? "reconnecting" : "connecting");
    log(`${isReconnect ? "Reconnecting" : "Connecting"} to ${urlRef.current} (attempt ${reconnectAttemptRef.current})`);

    const ws = new WebSocket(urlRef.current);
    wsRef.current = ws;

    // ── onOpen ──────────────────────────────────────────────
    ws.onopen = () => {
      if (isUnmountedRef.current) { ws.close(); return; }

      log("Connected");
      reconnectAttemptRef.current = 0;
      store.getState().setConnectionStatus("connected");
      triggerHaptic("soft");

      // Resume Session Handshake
      // Send our last known sequence so the server replays missed events.
      const { lastConfirmedSequence } = store.getState();
      const resumeMsg = toServerMessage("resume_session", {
        lastSequence: lastConfirmedSequence,
      });
      ws.send(JSON.stringify(resumeMsg));
      log(`Resume handshake sent: last_sequence=${lastConfirmedSequence}`);

      // Flush any commands queued while disconnected
      // (after a small delay to let resume_from events arrive first)
      setTimeout(flushQueue, 100);

      // Start keep-alive heartbeat
      startHeartbeat();
    };

    // ── onMessage ───────────────────────────────────────────
    ws.onmessage = (event) => {
      lastMessageTimeRef.current = Date.now();
      pendingSyncRef.current = false;

      let data: any;
      try {
        data = JSON.parse(event.data);
      } catch {
        log("Failed to parse message:", event.data);
        return;
      }

      // Server may send raw error objects (not DraftEvents)
      if (data.error && !data.type) {
        log("Server error:", data.error);
        return;
      }

      // Treat as DraftEvent
      const draftEvent = data as DraftEvent;

      // Gap detection before processing
      if (draftEvent.sequenceNumber != null) {
        checkForGap(draftEvent.sequenceNumber);
      }

      // Route to Zustand store
      store.getState().processIncomingEvent(draftEvent);
    };

    // ── onClose ─────────────────────────────────────────────
    ws.onclose = (event) => {
      log(`Closed: code=${event.code}, reason=${event.reason}, clean=${event.wasClean}`);
      stopHeartbeat();

      if (isUnmountedRef.current || isManualCloseRef.current) {
        store.getState().setConnectionStatus("disconnected");
        isManualCloseRef.current = false;
        return;
      }

      // Automatic reconnection with exponential backoff
      store.getState().setConnectionStatus("reconnecting");
      const backoff = getBackoffMs();
      reconnectAttemptRef.current += 1;
      log(`Reconnecting in ${backoff}ms (attempt ${reconnectAttemptRef.current})`);

      reconnectTimerRef.current = setTimeout(() => {
        reconnectTimerRef.current = null;
        connect();
      }, backoff);
    };

    // ── onError ─────────────────────────────────────────────
    ws.onerror = (event) => {
      log("Error:", event);
      // onClose will fire next — reconnection handled there
    };
  }, [store, log, getBackoffMs, flushQueue, startHeartbeat, stopHeartbeat, checkForGap]);

  // ─── Send Command ───────────────────────────────────────────
  const sendCommand = useCallback(
    (type: ClientCommand["type"], payload?: Record<string, any>) => {
      const msg = toServerMessage(type, payload);
      const ws = wsRef.current;

      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(msg));
        log("Sent:", msg);
      } else {
        // Queue for later delivery
        if (offlineQueueRef.current.length < OFFLINE_QUEUE_MAX) {
          offlineQueueRef.current.push(msg);
          log("Queued (offline):", msg);
        } else {
          log("Queue full, dropping command:", msg);
        }
      }
    },
    [log],
  );

  // ─── Request Sync (Layer 3) ─────────────────────────────────
  const requestSync = useCallback(() => {
    sendCommand("sync");
  }, [sendCommand]);

  // ─── Manual Disconnect ──────────────────────────────────────
  const disconnect = useCallback(() => {
    isManualCloseRef.current = true;

    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    stopHeartbeat();

    const ws = wsRef.current;
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
      ws.close(1000, "Client disconnect");
    }
    wsRef.current = null;
  }, [stopHeartbeat]);

  // ─── Manual Reconnect ───────────────────────────────────────
  const reconnect = useCallback(() => {
    disconnect();
    isManualCloseRef.current = false;
    reconnectAttemptRef.current = 0;
    // Small delay to ensure close completes
    setTimeout(connect, 50);
  }, [disconnect, connect]);

  // ─── Mount / Unmount ────────────────────────────────────────
  useEffect(() => {
    isUnmountedRef.current = false;

    if (autoConnect) {
      connect();
    }

    return () => {
      isUnmountedRef.current = true;

      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      stopHeartbeat();

      const ws = wsRef.current;
      if (ws) {
        // Clean close — code 1000 tells the server this is intentional
        ws.onclose = null; // Prevent reconnection logic from firing
        ws.close(1000, "Component unmount");
        wsRef.current = null;
      }
    };
  }, [autoConnect, connect, stopHeartbeat]);

  return { sendCommand, requestSync, disconnect, reconnect };
}

// ─── Convenience: Build WebSocket URL ─────────────────────────────

export function buildDraftWsUrl(
  sessionId: string,
  team: string,
  host?: string,
): string {
  // Priority: explicit host arg → env var → derive from window.location → fallback
  // In development, NEXT_PUBLIC_WS_URL should point directly to FastAPI (ws://localhost:8000)
  // because Next.js rewrites don't proxy WebSocket upgrades.
  const base = host
    ?? (typeof process !== "undefined" && process.env?.NEXT_PUBLIC_WS_URL)
    ?? (typeof window !== "undefined"
      ? `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}`
      : "ws://localhost:8000"
    );
  return `${base}/ws/draft/${encodeURIComponent(sessionId)}?team=${encodeURIComponent(team)}`;
}
