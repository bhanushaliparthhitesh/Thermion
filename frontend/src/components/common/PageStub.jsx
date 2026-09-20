import { Construction } from 'lucide-react'

/**
 * needs: plain-language list of what has to exist on the backend before
 * this page can show real data — keeps the placeholder honest instead
 * of silently shipping empty charts that look like real ones.
 */
export default function PageStub({ title, subtitle, needs = [] }) {
  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-lg font-semibold text-ink">{title}</h1>
        {subtitle && <p className="text-sm text-ink-soft">{subtitle}</p>}
      </div>

      <div className="card flex flex-col items-start gap-3 p-6">
        <Construction size={20} className="text-ink-faint" aria-hidden="true" />
        <p className="text-sm font-medium text-ink">Not built yet</p>
        <p className="max-w-md text-sm text-ink-soft">
          This screen is scaffolded in the app shell but doesn't render real data yet.
        </p>
        {needs.length > 0 && (
          <div className="text-sm">
            <p className="mb-1 font-medium text-ink-soft">Needs, before this is real:</p>
            <ul className="list-inside list-disc text-ink-faint">
              {needs.map((n) => (
                <li key={n}>{n}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}
