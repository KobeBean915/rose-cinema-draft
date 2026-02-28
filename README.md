# Draft Room — Rose Cinema

NFL Draft Simulation Engine with a cinematic scouting UI.

## Architecture

```
Frontend (Next.js 15 + React 19)     Backend (FastAPI + Iron Logic)
┌────────────────────────────┐       ┌────────────────────────────┐
│  app/draft/page.tsx        │       │  main.py (FastAPI)         │
│  ├── StatusTicker          │       │  ├── /ws/draft/{session}   │
│  ├── TabBar                │  WS   │  ├── /api/prospects        │
│  ├── DraftBoard / BigBoard │◄─────►│  ├── connection_manager.py │
│  ├── MyRoster              │       │  ├── draft_engine_async.py │
│  └── UserTurnSheet         │       │  ├── draft_room_v3.py      │
│                            │       │  ├── iron_logic.py         │
│  Zustand Store (3-layer)   │       │  ├── sparring_benchmarks.py│
│  useWebSocket (resilient)  │       │  └── team_data_2026.py     │
└────────────────────────────┘       └────────────────────────────┘
```

## Quick Start

### 1. Backend (Python 3.11+)

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Verify: `http://localhost:8000/api/health`

### 2. Frontend (Node 20+)

```bash
# From project root
npm install
npm run dev
```

Open: `http://localhost:3000/draft`

### 3. Both at Once

```bash
npm run dev:all
```

Requires `concurrently` (installed as dev dependency) and the Python venv
activated in your shell.

## Environment

`.env.local` (created by default):

```
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

The WebSocket connects directly to FastAPI (port 8000), bypassing the
Next.js dev server. The REST API (`/api/*`) is proxied through Next.js
rewrites for convenience.

In production, remove `NEXT_PUBLIC_WS_URL` — the hook will derive the
WebSocket URL from `window.location` (works behind nginx/Caddy with
proper upstream config).

## How It Works

1. Page mounts → `useWebSocket` connects to FastAPI on port 8000
2. `onopen` fires → sends `resume_from(lastConfirmedSequence)`
3. Server replays buffered events (reconnect) or returns silence (fresh)
4. After 600ms grace period, page sends `start` if engine isn't running
5. Engine emits `DRAFT_START` → Loading Shutter lifts → Draft begins
6. AI picks stream in via WebSocket → Zustand store processes them
7. User's turn → Bottom Sheet slides up → Select + Confirm
8. Optimistic pick (Layer 1) → Server confirmation (Layer 2) → Silent promote
9. If Wi-Fi drops → exponential backoff → reconnect → `resume_from` → seamless

## Project Structure

```
draft-room-web/
├── app/
│   ├── layout.tsx              Root HTML + viewport
│   ├── page.tsx                Redirect → /draft
│   └── draft/
│       └── page.tsx            ★ Main orchestrator (481 lines)
├── components/
│   ├── DraftShell.tsx          Grain filter + CSS vars
│   ├── StatusTicker.tsx        Fixed header + connection dot
│   ├── BigBoard.tsx            Prospect rankings + IO lazy-mount
│   ├── DraftBoard.tsx          Pick history feed
│   ├── MyRoster.tsx            User's drafted players
│   └── UserTurnSheet.tsx       Bottom sheet + athletic bars
├── hooks/
│   └── useWebSocket.ts        Backoff + resume + queue + gap detection
├── stores/
│   └── useDraftStore.ts       Three-layer optimistic Zustand store
├── lib/
│   ├── types.ts               TypeScript source of truth
│   ├── haptics.ts             Vibration API bridge
│   └── prospects.ts           Static seed data + draft order
├── backend/
│   ├── main.py                FastAPI routes + command router
│   ├── connection_manager.py  Session + OrderedDict buffer + replay
│   ├── draft_engine_async.py  Async engine adapter
│   ├── draft_room_v3.py       Original draft simulation (UNCHANGED)
│   ├── iron_logic.py          AI pick algorithm (UNCHANGED)
│   ├── sparring_benchmarks.py Prospect data (UNCHANGED)
│   ├── team_data_2026.py      Team needs + draft order (UNCHANGED)
│   └── requirements.txt       Python dependencies
├── package.json
├── tsconfig.json
├── next.config.ts
├── .env.local
└── .gitignore
```
