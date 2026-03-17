import { useEffect, useState } from 'react'
import { getAllDeviceLogs } from '../../api/devices'
import { useSSE } from '../../hooks/useSSE'

const EVENT_CONFIG = {
  connected:    { label: 'Подключение',                color: '#b8bb26' },
  disconnected: { label: 'Отключение',                 color: '#e74c3c' },
  timeout:      { label: 'Таймаут бездействия',        color: '#d79921' },
  online:       { label: 'Появилось в ADB',            color: '#27ae60' },
  offline:      { label: 'Пропало из ADB',             color: '#928374' },
  video_saved:  { label: 'Видео сохранено',            color: '#458588' },
}

const fmtDateTime = (d) => new Date(d).toLocaleString('ru-RU', {
  day: '2-digit', month: '2-digit', year: 'numeric',
  hour: '2-digit', minute: '2-digit', second: '2-digit',
})

export default function AllLogsModal({ onClose }) {
  const [logs, setLogs]       = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch]   = useState('')

  const load = async () => {
    try {
      const data = await getAllDeviceLogs()
      setLogs(data)
    } catch {}
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  useSSE((e) => { if (e.type === 'devices_updated') load() })

  const filtered = search.trim()
    ? logs.filter(l => {
        const q = search.toLowerCase()
        return l.serial.toLowerCase().includes(q)
          || (EVENT_CONFIG[l.event_type]?.label ?? l.event_type).toLowerCase().includes(q)
          || (l.detail ?? '').toLowerCase().includes(q)
          || (l.label ?? '').toLowerCase().includes(q)
          || (l.owner_name ?? '').toLowerCase().includes(q)
      })
    : logs

  return (
    <div className="overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div
        className="modal modal-animated"
        style={{ width: 700, maxWidth: '95vw', padding: 0, maxHeight: '85vh', display: 'flex', flexDirection: 'column' }}
      >
        <div className="modal-header" style={{ padding: '16px 24px', borderBottom: '1px solid var(--bg-hover)', marginBottom: 0, flexShrink: 0 }}>
          <span className="modal-title">Журнал событий устройств</span>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div style={{ padding: '12px 24px', borderBottom: '1px solid var(--bg-hover)', flexShrink: 0 }}>
          <input
            className="input"
            placeholder="Поиск по serial, событию, пути…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            autoFocus
          />
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '8px 24px 16px' }}>
          {loading && <div className="loader" style={{ padding: '30px 0' }}>Загрузка…</div>}

          {!loading && filtered.length === 0 && (
            <div className="empty-state" style={{ padding: '40px 0' }}>
              <div>{search ? 'Ничего не найдено' : 'Нет событий'}</div>
            </div>
          )}

          {!loading && filtered.map((log) => {
            const cfg = EVENT_CONFIG[log.event_type] ?? { label: log.event_type, color: 'var(--text-muted)' }
            return (
              <div key={log.id} style={{
                display: 'flex', alignItems: 'flex-start', gap: 12,
                padding: '9px 0',
                borderBottom: '1px solid var(--bg-hover)',
              }}>
                <span style={{
                  width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                  marginTop: 5, background: cfg.color,
                  boxShadow: `0 0 5px ${cfg.color}`,
                }} />
                <div style={{ minWidth: 0, flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap' }}>
                    <span style={{ fontSize: 13, fontWeight: 500 }}>{cfg.label}</span>
                    <span style={{ fontSize: 11, fontFamily: 'monospace', color: 'var(--accent)' }}>{log.serial}</span>
                    {(log.label || log.owner_name) && (
                      <span style={{ fontSize: 12, color: 'var(--text-primary)' }}>
                        {[log.label, log.owner_name].filter(Boolean).join(' · ')}
                      </span>
                    )}
                    <span style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 'auto' }}>{fmtDateTime(log.created_at)}</span>
                  </div>
                  {log.detail && (
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'monospace', marginTop: 3, wordBreak: 'break-all' }}>
                      {log.detail}
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
