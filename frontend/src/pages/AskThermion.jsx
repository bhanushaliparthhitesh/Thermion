import { useState, useRef, useEffect } from 'react'
import { Send, Bot } from 'lucide-react'
import { askAgent } from '../api/assistant'

const SUGGESTIONS = [
  'Why did Thermion change the cooling mode?',
  'Why was the last action rejected?',
  'What happened during the last safety intervention?',
  'What cooling strategy is active?',
]

export default function AskThermion() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [pending, setPending] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function send(question) {
    if (!question.trim() || pending) return
    setMessages((m) => [...m, { role: 'user', text: question }])
    setInput('')
    setPending(true)
    try {
      const res = await askAgent(question)
      setMessages((m) => [...m, { role: 'assistant', text: res.answer }])
    } catch (err) {
      setMessages((m) => [
        ...m,
        { role: 'assistant', text: `Couldn't reach the agent: ${err.message}`, isError: true },
      ])
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="flex h-full flex-col gap-4">
      <div>
        <h1 className="flex items-center gap-2 text-lg font-semibold text-ink">
          <Bot size={19} className="text-primary-600" aria-hidden="true" />
          Ask Thermion
        </h1>
        <p className="text-sm text-ink-soft">
          Answers strictly from logged OpenSearch decisions — it won't invent a decision it hasn't fetched.
        </p>
      </div>

      <div className="card flex flex-1 flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto p-4">
          {messages.length === 0 ? (
            <div className="flex flex-col gap-2">
              <p className="mb-1 text-xs font-medium text-ink-soft">Try asking:</p>
              {SUGGESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => send(q)}
                  className="w-fit rounded-md border border-border px-3 py-1.5 text-left text-xs text-ink-soft hover:bg-ink-faint/5"
                >
                  {q}
                </button>
              ))}
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {messages.map((m, i) => (
                <div
                  key={i}
                  className={
                    m.role === 'user'
                      ? 'ml-auto max-w-[75%] rounded-lg bg-primary-600 px-3 py-2 text-sm text-white'
                      : `mr-auto max-w-[75%] rounded-lg border px-3 py-2 text-sm ${
                          m.isError ? 'border-critical-500/30 bg-critical-50 text-critical-700' : 'border-border bg-canvas text-ink'
                        }`
                  }
                >
                  {m.text}
                </div>
              ))}
              {pending && <p className="text-xs text-ink-faint">Thermion is thinking…</p>}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault()
            send(input)
          }}
          className="flex items-center gap-2 border-t border-border p-3"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about a decision, e.g. 'why did you pick LIQUID at step 12?'"
            className="flex-1 rounded-md border border-border bg-canvas px-3 py-2 text-sm outline-none focus:border-primary-500"
          />
          <button
            type="submit"
            disabled={pending}
            className="rounded-md bg-primary-600 p-2 text-white disabled:opacity-60"
            aria-label="Send"
          >
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  )
}
