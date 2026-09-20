import clsx from 'clsx'

/**
 * value/unit: the headline number, in mono (it's measured data, not prose).
 * rows: [{ label, value }] — secondary facts shown below the headline.
 * status: optional <StatusBadge /> element.
 */
export default function KPICard({ icon: Icon, label, value, unit, rows = [], status, className }) {
  return (
    <div className={clsx('card flex flex-col gap-3 p-4', className)}>
      <div className="flex items-center justify-between">
        <span className="flex items-center gap-1.5 text-xs font-medium text-ink-soft">
          {Icon && <Icon size={14} strokeWidth={1.8} aria-hidden="true" />}
          {label}
        </span>
        {status}
      </div>

      {value !== undefined && (
        <p className="font-mono text-2xl font-medium text-ink">
          {value}
          {unit && <span className="ml-1 text-sm text-ink-faint">{unit}</span>}
        </p>
      )}

      {rows.length > 0 && (
        <dl className="flex flex-col gap-1 border-t border-border pt-2.5">
          {rows.map((row) => (
            <div key={row.label} className="flex items-center justify-between text-xs">
              <dt className="text-ink-faint">{row.label}</dt>
              <dd className="font-mono text-ink-soft">{row.value}</dd>
            </div>
          ))}
        </dl>
      )}
    </div>
  )
}
