import { useEffect, useRef, useState } from 'react'
import { listCardNames } from '../../api/cards'
import { getDeviceLogs, updateDevice } from '../../api/devices'
import { useSSE } from '../../hooks/useSSE'

const DOTS = {
  online:       { color: '#27ae60', label: 'Online'     },
  offline:      { color: '#e74c3c', label: 'Offline'    },
  active:       { color: '#27ae60', label: 'Разрешён'   },
  inactive:     { color: '#e74c3c', label: 'Запрещён'   },
  connected:    { color: '#27ae60', label: 'Активно'    },
  disconnected: { color: '#e74c3c', label: 'Неактивно'  },
}

const EVENT_CONFIG = {
  connected:    { label: 'Подключение',                color: '#b8bb26' },
  disconnected: { label: 'Отключение',                 color: '#e74c3c' },
  timeout:      { label: 'Таймаут бездействия',        color: '#d79921' },
  online:       { label: 'Устройство появилось в ADB', color: '#27ae60' },
  offline:      { label: 'Устройство пропало из ADB',  color: '#928374' },
  video_saved:  { label: 'Видео сохранено',            color: '#458588' },
}

function StatusDot({ type }) {
  const s = DOTS[type] ?? DOTS.offline
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
      <span style={{
        width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
        background: s.color, boxShadow: `0 0 4px ${s.color}`,
      }} />
      <span style={{ fontSize: 12 }}>{s.label}</span>
    </span>
  )
}

const fmtDateTime = (d) => new Date(d).toLocaleString('ru-RU', {
  day: '2-digit', month: '2-digit', year: 'numeric',
  hour: '2-digit', minute: '2-digit', second: '2-digit',
})

export default function DeviceDetailModal({ device: initialDevice, onClose, onSaved }) {
  const [device, setDevice] = useState(initialDevice)

  // Sync status fields when parent pushes updated device data
  useEffect(() => {
    setDevice(prev => ({ ...prev, ...initialDevice }))
  }, [initialDevice.status, initialDevice.session_status, initialDevice.connected])
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({
    label:      initialDevice.label      ?? '',
    owner_name: initialDevice.owner_name ?? '',
  })
  const [names, setNames]   = useState([])
  const [saving, setSaving] = useState(false)
  const [error, setError]   = useState(null)

  const [logs, setLogs]             = useState([])
  const [logsLoading, setLogsLoading] = useState(true)
  const logsRef = useRef(null)

  const loadLogs = async () => {
    try {
      const data = await getDeviceLogs(device.serial)
      setLogs(data)
    } catch {}
    setLogsLoading(false)
  }

  useEffect(() => {
    loadLogs()
    listCardNames().then(setNames).catch(() => {})
  }, [])

  // Real-time: обновляем логи сразу при любом событии с устройствами
  useSSE((e) => {
    if (e.type === 'devices_updated') loadLogs()
  })

  const handleSave = async () => {
    if (!form.label.trim() && !form.owner_name.trim()) {
      setError('Необходимо указать название или владельца')
      return
    }
    setSaving(true)
    setError(null)
    try {
      const updated = await updateDevice(device.serial, {
        label:      form.label.trim()      || null,
        owner_name: form.owner_name.trim() || null,
      })
      setDevice(updated)
      setEditing(false)
      onSaved?.()
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  const handleCancel = () => {
    setForm({ label: device.label ?? '', owner_name: device.owner_name ?? '' })
    setEditing(false)
    setError(null)
  }

  return (
    <div className="overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div
        className="modal modal-animated"
        style={{ width: 800, maxWidth: '95vw', overflow: 'hidden', padding: 0 }}
      >
        {/* Header */}
        <div className="modal-header" style={{ padding: '18px 24px', borderBottom: '1px solid var(--bg-hover)', marginBottom: 0 }}>
          <div>
            <div className="modal-title">{device.label || device.owner_name || device.serial}</div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'monospace', marginTop: 2 }}>
              {device.serial}
            </div>
          </div>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        {/* Body — two columns */}
        <div style={{ display: 'flex', height: 500, overflow: 'hidden' }}>

          {/* Left: device info + edit */}
          <div style={{
            flex: '0 0 300px', padding: '20px 24px',
            overflowY: 'auto',
            borderRight: '1px solid var(--bg-hover)',
          }}>
            {/* Status rows */}
            <div style={{ marginBottom: 20 }}>
              {[
                ['ADB статус',   <StatusDot type={device.status} />],
                ['Доступ',       <StatusDot type={device.session_status} />],
                ['Сессия',       <StatusDot type={device.connected ? 'connected' : 'disconnected'} />],
              ].map(([label, value]) => (
                <div key={label} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '6px 0', borderBottom: '1px solid var(--bg-hover)',
                }}>
                  <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{label}</span>
                  {value}
                </div>
              ))}
            </div>

            {/* Edit form */}
            {error && (
              <div style={{ color: 'var(--danger)', fontSize: 12, marginBottom: 10 }}>{error}</div>
            )}

            {editing ? (
              <>
                <div className="form-group">
                  <label className="label">Название (label)</label>
                  <input
                    className="input"
                    value={form.label}
                    onChange={e => setForm(f => ({ ...f, label: e.target.value }))}
                    placeholder="Redmi Note 12"
                  />
                </div>
                <div className="form-group">
                  <label className="label">Владелец</label>
                  <select
                    className="input"
                    value={form.owner_name}
                    onChange={e => setForm(f => ({ ...f, owner_name: e.target.value }))}
                  >
                    <option value="">— не указан —</option>
                    {names.map(n => <option key={n} value={n}>{n}</option>)}
                  </select>
                </div>
                <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                  <button className="btn btn-primary btn-sm" onClick={handleSave} disabled={saving}>
                    {saving ? 'Сохранение…' : 'Сохранить'}
                  </button>
                  <button className="btn btn-ghost btn-sm" onClick={handleCancel} disabled={saving}>
                    Отмена
                  </button>
                </div>
              </>
            ) : (
              <>
                {[
                  ['Название', device.label || '—'],
                  ['Владелец', device.owner_name || '—'],
                ].map(([label, value]) => (
                  <div key={label} style={{
                    display: 'flex', justifyContent: 'space-between',
                    padding: '6px 0', borderBottom: '1px solid var(--bg-hover)',
                    fontSize: 13,
                  }}>
                    <span style={{ color: 'var(--text-muted)' }}>{label}</span>
                    <span>{value}</span>
                  </div>
                ))}
                <button
                  className="btn btn-ghost btn-sm"
                  style={{ marginTop: 14, width: '100%' }}
                  onClick={() => setEditing(true)}
                >
                  Изменить
                </button>
              </>
            )}
          </div>

          {/* Right: logs */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <div style={{
              padding: '14px 20px 10px',
              fontSize: 11, fontWeight: 600, textTransform: 'uppercase',
              letterSpacing: '0.06em', color: 'var(--text-muted)',
              borderBottom: '1px solid var(--bg-hover)',
              flexShrink: 0,
            }}>
              Журнал событий
            </div>

            <div ref={logsRef} style={{ flex: 1, overflowY: 'auto', padding: '8px 20px' }}>
              {logsLoading && (
                <div className="loader" style={{ padding: '20px 0' }}>Загрузка…</div>
              )}

              {!logsLoading && logs.length === 0 && (
                <div className="empty-state" style={{ padding: '40px 0' }}>
                  <div>Нет событий</div>
                  <p>Подключение, отключение и изменения статуса появятся здесь</p>
                </div>
              )}

              {logs.map((log) => {
                const cfg = EVENT_CONFIG[log.event_type] ?? { label: log.event_type, color: 'var(--text-muted)' }
                return (
                  <div key={log.id} style={{
                    display: 'flex', alignItems: 'flex-start', gap: 10,
                    padding: '9px 0',
                    borderBottom: '1px solid var(--bg-hover)',
                  }}>
                    <span style={{
                      width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                      marginTop: 4, background: cfg.color,
                      boxShadow: `0 0 5px ${cfg.color}`,
                    }} />
                    <div style={{ minWidth: 0 }}>
                      <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>
                        {cfg.label}
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                        {fmtDateTime(log.created_at)}
                      </div>
                      {log.detail && (
                        <div style={{
                          fontSize: 11, color: 'var(--accent)',
                          fontFamily: 'monospace', marginTop: 3,
                          wordBreak: 'break-all',
                        }}>
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
      </div>
    </div>
  )
}
