import clsx from 'clsx'

const TONES = {
  safe: 'bg-safe-50 text-safe-700',
  warn: 'bg-warn-50 text-warn-700',
  critical: 'bg-critical-50 text-critical-700',
  info: 'bg-primary-50 text-primary-700',
  neutral: 'bg-ink-faint/10 text-ink-soft',
}

const DOT_TONES = {
  safe: 'bg-safe-500',
  warn: 'bg-warn-500',
  critical: 'bg-critical-500',
  info: 'bg-primary-500',
  neutral: 'bg-ink-faint',
}

/**
 * tone: 'safe' | 'warn' | 'critical' | 'info' | 'neutral'
 * Caps text is deliberate here — status indicators, not prose labels.
 * Never rely on color alone: every pill carries a dot + a glyph + text.
 */
export default function StatusBadge({ tone = 'neutral', glyph, children, className }) {
  return (
    <span className={clsx('status-pill', TONES[tone], className)}>
      <span className={clsx('h-1.5 w-1.5 rounded-full', DOT_TONES[tone])} aria-hidden="true" />
      {glyph && <span aria-hidden="true">{glyph}</span>}
      <span className="uppercase">{children}</span>
    </span>
  )
}
