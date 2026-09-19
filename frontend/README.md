# Thermion — AI-Powered Data-Center Cooling

Thermion makes AI-driven cooling decisions safe, transparent, and explainable. A digital twin and PPO reinforcement-learning agent choose AIR, LIQUID, or HYBRID cooling for each timestep. Cedar safety checks guard the proposed action, OpenSearch stores the complete decision trace, and a Strands operations agent explains decisions in plain language.

The frontend is the operator console: it displays the logged telemetry and reward context, Cedar and safety verdicts, pipeline status, and explanations from the operations agent. It does not simulate decisions or provide mock backend data.

## Run locally

Prerequisite: Node.js.

```bash
npm install
npm run dev
```

The Vite frontend opens at `http://localhost:5173/`.

The frontend calls the local backend API at `http://127.0.0.1:3000` by default.
