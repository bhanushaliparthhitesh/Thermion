import clsx from 'clsx'
import { Fan } from 'lucide-react'

const COOLING_LABEL = { AIR: 'Air cooling', LIQUID: 'Liquid cooling', HYBRID: 'Hybrid cooling' }

function rackTone(deviation) {
  if (deviation === undefined || deviation === null) return 'bg-ink-faint/20'
  if (deviation > 6) return 'bg-critical-500'
  if (deviation > 3) return 'bg-warn-500'
  return 'bg-safe-500'
}

/**
 * decision: latest logged decision, or null. The backend logs one
 * system-wide temperature_deviation, not per-rack readings — so this
 * is a schematic overview, not real rack-by-rack telemetry. Said so
 * on the card rather than implying more precision than exists.
 */
export default function DataCenterOverview({ decision }) {
  const deviation = decision?.state?.temperature_deviation
  const coolingMode = decision?.action_label

  return (
    <div className="card flex flex-col gap-3 p-4">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-ink">Live data center overview</p>
        {coolingMode && (
          <span className="flex items-center gap-1.5 text-xs text-cooling-700">
            <Fan size={13} aria-hidden="true" />
            {COOLING_LABEL[coolingMode] || coolingMode}
          </span>
        )}
      </div>

      <div className="grid grid-cols-4 gap-2 sm:grid-cols-8">
        {Array.from({ length: 16 }).map((_, i) => (
          <div
            key={i}
            className={clsx('aspect-[2/3] rounded-sm', rackTone(deviation))}
            title={deviation !== undefined ? `Temperature deviation: ${deviation}` : 'No data'}
          />
        ))}
      </div>

      <p className="text-[11px] text-ink-faint">
        Schematic layout, colored by the current system-wide temperature deviation — not per-rack
        telemetry. A real rack-level view needs per-rack sensor data from the backend.
      </p>
    </div>
  )
}
