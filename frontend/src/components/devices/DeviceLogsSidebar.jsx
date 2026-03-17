import { useEffect, useState } from 'react'
import { getDeviceLogs } from '../../api/devices'
import { useSSE } from '../../hooks/useSSE'

const EVENT_CONFIG = {
  connected:    { label: 'Подключение',           color: 'var(--success)' },
  disconnected: { label: 'Отключение',             color: 'var(--danger)'  },
  timeout:      { label: 'Таймаут бездействия',    color: '#d79921'        },
  online:       { label: 'Устройство появилось в ADB', color: 'var(--success)' },
  offline:      { label: 'Устройство пропало из ADB',  color: 'var(--text-muted)' },
}

const fmtDateTime = (d) => new Date(d).toLocaleString('ru-RU', {
  day: '2-digit', month: '2-digit', year: 'numeric',
  hour: '2-digit', minute: '2-digit', second: '2-digit',
})

export default function DeviceLogsSidebar({ device, onClose }) {
  const open = !!device

  const [logs, setLogs]       = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)

  const load = async (serial) => {
    setLoading(true)
    setError(null)
    try {
      const data = await getDeviceLogs(serial)
      setLogs(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (device) {
      setLogs([])
      load(device.serial)
    }
  }, [device?.serial])

  useSSE((e) => {
    if (e.type === 'devices_updated' && device) load(device.serial)
  })

  return (
    <>
      {open && (
        <div
          onClick={onClose}
          style={{ position: 'fixed', inset: 0, zIndex: 49, background: 'transparent' }}
        />
      )}
      <aside className={`sidebar ${open ? 'open' : ''}`}>
        {device && (
          <>
            <div className="sidebar-header">
              <div>
                <div style={{ fontWeight: 600 }}>
                  {device.label || device.owner_name || device.serial}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                  {device.serial}
                </div>
              </div>
              <button className="modal-close" onClick={onClose}>×</button>
            </div>

            <div className="sidebar-body">
              <div style={{
                fontSize: 11, fontWeight: 600, textTransform: 'uppercase',
                letterSpacing: '0.06em', color: 'var(--text-muted)', marginBottom: 12,
              }}>
                Журнал событий
              </div>

              {error && (
                <div style={{ color: 'var(--danger)', fontSize: 12, marginBottom: 8 }}>{error}</div>
              )}

              {loading && (
                <div className="loader" style={{ padding: '20px 0' }}>Загрузка…</div>
              )}

              {!loading && logs.length === 0 && (
                <div className="empty-state" style={{ padding: '24px 0' }}>
                  <div>Нет событий</div>
                  <p>Подключение, отключение и изменения статуса появятся здесь</p>
                </div>
              )}

              {!loading && logs.map((log) => {
                const cfg = EVENT_CONFIG[log.event_type] ?? { label: log.event_type, color: 'var(--text-muted)' }
                return (
                  <div key={log.id} style={{
                    display: 'flex', alignItems: 'flex-start', gap: 10,
                    padding: '8px 0',
                    borderBottom: '1px solid var(--bg-hover)',
                  }}>
                    <span style={{
                      width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                      marginTop: 5, background: cfg.color,
                      boxShadow: `0 0 4px ${cfg.color}`,
                    }} />
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>
                        {cfg.label}
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                        {fmtDateTime(log.created_at)}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </>
        )}
      </aside>
    </>
  )
}
