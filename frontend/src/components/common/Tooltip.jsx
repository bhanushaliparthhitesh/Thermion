import { useState } from 'react'
import { HelpCircle } from 'lucide-react'

export default function Tooltip({ label }) {
  const [open, setOpen] = useState(false)
  return (
    <span className="relative inline-flex">
      <button
        type="button"
        aria-label="What does this mean?"
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        className="text-ink-faint hover:text-ink-soft"
      >
        <HelpCircle size={13} />
      </button>
      {open && (
        <span
          role="tooltip"
          className="absolute bottom-full left-1/2 z-10 mb-1.5 w-48 -translate-x-1/2 rounded-md bg-ink px-2.5 py-1.5 text-xs leading-snug text-white shadow-card"
        >
          {label}
        </span>
      )}
    </span>
  )
}
