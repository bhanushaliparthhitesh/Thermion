"""Export recent OpenSearch decision documents for the PartyRock snapshot.

Run:
    python export_decisions.py
Optional:
    python export_decisions.py --limit 50 --output decisions_export.md
"""
import argparse
from datetime import datetime

from decision_logger import get_recent_decisions

def format_value(value):
    if value is None:
        return "N/A"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)

def decision_to_markdown(d, index):
    step_id = d.get("step_id", f"unknown-{index}")
    action = d.get("action_label", d.get("action", "N/A"))
    reason = d.get("strategy_reason", d.get("reason", "N/A"))
    safety = d.get("safety_verdict", d.get("safety_allowed", "N/A"))
    cedar = d.get("cedar_verdict", d.get("cedar_allowed", "N/A"))

    return f"""## Step {step_id}

- **Action:** {format_value(action)}
- **Strategy reason:** {format_value(reason)}
- **Safety verdict:** {format_value(safety)}
- **Cedar verdict:** {format_value(cedar)}
- **Temperature deviation:** {format_value(d.get("temperature_deviation"))}
- **Water usage:** {format_value(d.get("water_usage"))}
- **Cooling efficiency:** {format_value(d.get("cooling_efficiency"))}

### Full decision JSON

```json
{__import__("json").dumps(d, indent=2, default=str)}
```
"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--output", default="decisions_export.md")
    args = parser.parse_args()

    decisions = get_recent_decisions(max(1, min(args.limit, 500)))

    content = f"""# Cooling System Decision Log

Generated: {datetime.now().isoformat(timespec="seconds")}

This is a snapshot exported from the local OpenSearch decision log.
PartyRock should use this document as its grounding source.

"""
    if not decisions:
        content += "No decisions were found. Run the pipeline first.\n"
    else:
        for index, decision in enumerate(decisions, start=1):
            content += decision_to_markdown(decision, index)
            content += "\n"

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Exported {len(decisions)} decisions to {args.output}")

if __name__ == "__main__":
    main()
