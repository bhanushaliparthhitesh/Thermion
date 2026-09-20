# THERMION frontend

Vite + React + Tailwind. IBM Plex Sans/Mono. Talks to the SAM-local API — no AWS account needed.

## Run it

```bash
# 1. OpenSearch (from the repo root)
docker-compose up -d

# 2. Backend API (from the repo root)
sam build
sam local start-api
# note the port it prints — defaults to :3000

# 3. Frontend (from this folder)
npm install
npm run dev
# opens on :5173
```

Confirm `.env.local`'s `VITE_API_BASE_URL` matches whatever port `sam local start-api` actually printed.

For the Ask Thermion page, also have Ollama running locally (`ollama serve`) with the model pulled that `strands_agent/agent.py` references.

## What's real vs. not yet

| Page | Status |
|---|---|
| Command Center | Real — reads `/decisions`, triggers `/run` |
| AI Decisions | Real — list + full pipeline detail per decision |
| Safety Center | Real — intervention timeline derived from logged Cedar/safety verdicts |
| Ask Thermion | Real — calls `/agent/ask` |
| Digital Twin | Stub — needs per-rack telemetry + a 3D scene |
| Live Telemetry | Stub — buildable now from existing decision history, just not wired up yet |
| Analytics | Stub — needs an energy metric the backend doesn't currently produce |
| Alerts | Stub — needs a severity/alerts model on top of decision history |

Nothing on the built pages shows an invented number — where the backend doesn't have a metric, the UI says so instead of estimating one.
