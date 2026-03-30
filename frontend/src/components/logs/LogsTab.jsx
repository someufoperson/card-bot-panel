import { useCallback, useEffect, useRef, useState } from 'react'

const SOURCES = [
  { id: null,      label: 'Все' },
  { id: 'backend', label: 'Backend' },
  { id: 'bot',     label: 'Bot' },
  { id: 'flask',   label: 'Flask' },
]

const LEVEL_COLOR = {
  DEBUG:    '#928374',
  INFO:     '#83a598',
  SUCCESS:  '#b8bb26',
  WARNING:  '#fabd2f',
  ERROR:    '#fb4934',
  CRITICAL: '#cc241d',
}

const SOURCE_COLOR = {
  backend: '#d3869b',
  bot:     '#fabd2f',
  flask:   '#83a598',
}

export default function LogsTab() {
  const [entries, setEntries]       = useState([])
  const [source, setSource]         = useState(null)
  const [autoScroll, setAutoScroll] = useState(true)
  const [error, setError]           = useState(false)
  const bottomRef                   = useRef(null)

  const fetchLogs = useCallback(async () => {
    try {
      const url = source ? `/api/v1/logs?source=${source}` : '/api/v1/logs'
      const res = await fetch(url)
      if (!res.ok) throw new Error()
      setEntries(await res.json())
      setError(false)
    } catch {
      setError(true)
    }
  }, [source])

  useEffect(() => {
    fetchLogs()
    const id = setInterval(fetchLogs, 2000)
    return () => clearInterval(id)
  }, [fetchLogs])

  useEffect(() => {
    if (autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [entries, autoScroll])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Toolbar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
        <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: 'var(--text-primary)' }}>
          Логи
        </h2>

        {/* Source filter */}
        <div style={{ display: 'flex', gap: 4, marginLeft: 12 }}>
          {SOURCES.map(s => (
            <button
              key={String(s.id)}
              className="btn btn-ghost btn-sm"
              onClick={() => setSource(s.id)}
              style={{
                background: source === s.id ? 'rgba(131,165,152,0.15)' : 'transparent',
                color: source === s.id ? 'var(--accent)' : 'var(--text-muted)',
                border: source === s.id ? '1px solid rgba(131,165,152,0.3)' : '1px solid transparent',
              }}
            >
              {s.label}
            </button>
          ))}
        </div>

        {error && (
          <span style={{
            fontSize: 12, padding: '2px 8px', borderRadius: 4,
            background: 'rgba(251,73,52,0.15)', color: 'var(--danger)',
            border: '1px solid rgba(251,73,52,0.3)',
          }}>
            Ошибка загрузки
          </span>
        )}

        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8, alignItems: 'center' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: 'var(--text-muted)', cursor: 'pointer' }}>
            <input type="checkbox" checked={autoScroll} onChange={e => setAutoScroll(e.target.checked)} />
            Автопрокрутка
          </label>
          <button className="btn btn-ghost btn-sm" onClick={() => setEntries([])}>Очистить</button>
          <button className="btn btn-ghost btn-sm" onClick={fetchLogs}>Обновить</button>
        </div>
      </div>

      {/* Terminal */}
      <div style={{
        flex: 1,
        background: '#1d2021',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius)',
        overflowY: 'auto',
        padding: '12px 14px',
        fontFamily: '"Cascadia Code", "Fira Code", "Consolas", monospace',
        fontSize: 12.5,
        lineHeight: 1.65,
        minHeight: 0,
      }}>
        {entries.length === 0 ? (
          <span style={{ color: '#504945' }}>— Логов нет —</span>
        ) : entries.map((e, i) => (
          <div key={i} style={{ display: 'flex', gap: 8, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
            <span style={{ color: '#665c54', flexShrink: 0 }}>{e.t}</span>
            <span style={{ color: LEVEL_COLOR[e.l] ?? '#ebdbb2', flexShrink: 0, minWidth: 52 }}>{e.l}</span>
            <span style={{ color: SOURCE_COLOR[e.s] ?? '#928374', flexShrink: 0, minWidth: 52 }}>[{e.s}]</span>
            <span style={{ color: '#ebdbb2' }}>{e.m}</span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
