import { AlertTriangle } from 'lucide-react'

export default function ErrorState({ error, onRetry }) {
  return (
    <div className="flex flex-col items-start gap-3 rounded-card border border-critical-500/20 bg-critical-50 px-4 py-4 text-sm">
      <div className="flex items-center gap-2 font-medium text-critical-700">
        <AlertTriangle size={16} aria-hidden="true" />
        Backend unavailable
      </div>
      <p className="text-ink-soft">
        {error?.message || 'Could not reach the Thermion backend.'} Showing last available data where possible.
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="rounded-md border border-critical-500/30 px-3 py-1.5 text-xs font-medium text-critical-700 hover:bg-critical-50/60"
        >
          Retry
        </button>
      )}
    </div>
  )
}
