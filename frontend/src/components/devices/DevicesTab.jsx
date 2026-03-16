import { useCallback, useEffect, useRef, useState } from 'react'
import { listDevices, releaseSession } from '../../api/devices'
import { useApp } from '../../context/AppContext'

const POLL_INTERVAL = 30_000

const STATUS_LABEL = { online: 'Online', offline: 'Offline', busy: 'Busy' }
const STATUS_CLASS  = { online: 'badge-online', offline: 'badge-offline', busy: 'badge-busy' }

export default function DevicesTab() {
  const { settings } = useApp()
  const [devices, setDevices]   = useState([])
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState(null)
  const [releasing, setReleasing] = useState(null)
  const timerRef = useRef(null)

  const load = useCallback(async () => {
    setError(null)
    try {
      const data = await listDevices()
      setDevices(data)
    } catch (e) {
      setError(e.message)
    }
  }, [])

  useEffect(() => {
    setLoading(true)
    load().finally(() => setLoading(false))
    timerRef.current = setInterval(load, POLL_INTERVAL)
    return () => clearInterval(timerRef.current)
  }, [load])

  const handleRelease = async (deviceId, e) => {
    e.stopPropagation()
    setReleasing(deviceId)
    try {
      await releaseSession(deviceId)
      await load()
    } finally {
      setReleasing(null)
    }
  }

  const handleConnect = (deviceId, e) => {
    e.stopPropagation()
    const domain = settings.device_domain || 'http://localhost'
    window.open(`${domain}/${deviceId}`, '_blank')
  }

  const fmtTime = (iso) => iso
    ? new Date(iso).toLocaleString('ru-RU', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' })
    : '—'

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
        <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>
          Обновление каждые 30 сек
        </span>
        <button className="btn btn-ghost btn-sm" onClick={load}>
          ↻ Обновить
        </button>
      </div>

      <div className="card" style={{ padding: 0 }}>
        {error && (
          <div style={{ padding: 16, color: 'var(--danger)', fontSize: 13 }}>{error}</div>
        )}
        {loading && <div className="loader">Загрузка…</div>}
        {!loading && !error && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Device ID</th>
                  <th>Модель</th>
                  <th>Статус</th>
                  <th>Сессия начата</th>
                  <th>Действия</th>
                </tr>
              </thead>
              <tbody>
                {devices.length === 0 ? (
                  <tr>
                    <td colSpan={5}>
                      <div className="empty-state">
                        <div>Нет устройств</div>
                        <p>Подключите Android-устройство по USB и запустите web-scrcpy</p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  devices.map(d => (
                    <tr key={d.device_id} style={{ cursor: 'default' }}>
                      <td className="td-mono">{d.device_id}</td>
                      <td>{d.model || '—'}</td>
                      <td>
                        <span className={`badge ${STATUS_CLASS[d.status]}`}>
                          {STATUS_LABEL[d.status]}
                        </span>
                      </td>
                      <td style={{ color: 'var(--text-muted)' }}>
                        {fmtTime(d.session_started)}
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: 6 }}>
                          <button
                            className="btn btn-primary btn-sm"
                            onClick={e => handleConnect(d.device_id, e)}
                            disabled={d.status === 'offline'}
                          >
                            Подключиться
                          </button>
                          {d.status === 'busy' && (
                            <button
                              className="btn btn-danger btn-sm"
                              onClick={e => handleRelease(d.device_id, e)}
                              disabled={releasing === d.device_id}
                            >
                              {releasing === d.device_id ? '…' : 'Разорвать'}
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
